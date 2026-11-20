#!/usr/bin/env python3
"""Fetch @funboy public Instagram grid into data/sources/public-ig-grid-through-2026-11-20.json.

Uses Instagram web_profile_info when the endpoint allows it (datacenter IPs may get HTTP 429).
Does not log in; public counts only.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources" / "public-ig-grid-through-2026-11-20.json"
WINDOW_START = date(2025, 10, 1)
WINDOW_END = date(2026, 11, 20)
PT = ZoneInfo("America/Los_Angeles")

sys.path.insert(0, str(ROOT))
from build_public_report import HDR  # noqa: E402


def pacific_date(ts: int) -> str:
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(PT).date().isoformat()
    )


def main() -> int:
    req = urllib.request.Request(
        "https://www.instagram.com/api/v1/users/web_profile_info/?username=funboy",
        headers=HDR,
    )
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=45) as r:
            payload = json.load(r)
    except Exception as exc:
        print(f"web_profile_info failed: {exc}", file=sys.stderr)
        return 1

    edges = payload["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
    posts = []
    for edge in edges:
        n = edge["node"]
        sc = n["shortcode"]
        ts = n.get("taken_at_timestamp")
        if not ts:
            continue
        posted = pacific_date(int(ts))
        d = date.fromisoformat(posted)
        if d < WINDOW_START or d > WINDOW_END:
            continue
        typename = n.get("__typename", "")
        typ = "reel" if typename == "GraphVideo" or n.get("is_video") else "photo"
        if typename == "GraphSidecar":
            typ = "carousel"
        posts.append(
            {
                "shortcode": sc,
                "date": posted,
                "likes": (n.get("edge_liked_by") or {}).get("count"),
                "comments": (n.get("edge_media_to_comment") or {}).get("count"),
                "views": n.get("video_view_count"),
                "type": typ,
                "permalink": f"https://www.instagram.com/{'reel' if typ == 'reel' else 'p'}/{sc}/",
                "caption": (n.get("edge_media_to_caption") or {})
                .get("edges", [{}])[0]
                .get("node", {})
                .get("text"),
            }
        )

    posts.sort(key=lambda p: (p["date"], p["shortcode"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "collected": date.today().isoformat(),
        "source": "instagram web_profile_info @funboy",
        "window_start": WINDOW_START.isoformat(),
        "window_end": WINDOW_END.isoformat(),
        "posts": posts,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(posts)} posts)")
    if posts:
        print(f"  dates {posts[0]['date']} .. {posts[-1]['date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())