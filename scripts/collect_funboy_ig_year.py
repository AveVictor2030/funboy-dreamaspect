#!/usr/bin/env python3
"""Build FUNBOY public Instagram year dataset (Oct 2025–Oct 2026, quartered).

Sources (merged, deduped by shortcode):
  - Notion Nectarine SQL exports in data/sources/nectarine-q*.json
  - august-2026-recap.html / september-2026-recap.html (Nectarine lag after ~2026-08-25)
  - build_public_report.FUN_POSTS (October 2026 public window)

Regenerate:
  python3 scripts/collect_funboy_ig_year.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "data" / "sources"
OUT_PATH = ROOT / "data" / "funboy-ig-year-oct2025-oct2026.json"

WINDOW_START = date(2025, 10, 1)
WINDOW_END = date(2026, 10, 31)

QUARTERS = (
    ("q1_oct_dec_2025", date(2025, 10, 1), date(2025, 12, 31)),
    ("q2_jan_mar_2026", date(2026, 1, 1), date(2026, 3, 31)),
    ("q3_apr_jun_2026", date(2026, 4, 1), date(2026, 6, 30)),
    ("q4_jul_oct_2026", date(2026, 7, 1), date(2026, 10, 31)),
)

SOURCE_FILES = (
    "nectarine-q1-octdec2025.json",
    "nectarine-q2-janmar2026.json",
    "nectarine-q3-aprjun2026.json",
    "nectarine-q4-jul-aug25-2026.json",
)
SOURCE_BATCH_FILES = (
    "nectarine-batch-a-2025-10-01_2026-05-23.json",
    "nectarine-batch-b-2026-05-24_2026-08-25.json",
)


def shortcode_from_permalink(permalink: str) -> str | None:
    m = re.search(r"instagram\.com/(?:funboy/)?(?:reel|p)/([^/?#]+)", permalink or "")
    return m.group(1) if m else None


def views_from_million(views_m) -> int | None:
    if views_m is None:
        return None
    try:
        v = float(views_m)
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return 0
    return int(round(v * 1_000_000))


def normalize_type(post_type: str | None, permalink: str) -> str:
    pt = (post_type or "").strip().lower()
    if pt == "tagged":
        return "tagged"
    if pt in {"carousel", "post"}:
        return "carousel" if pt == "carousel" else "photo"
    if pt == "reel" or "/reel/" in permalink:
        return "reel"
    return pt or "unknown"


def normalize_nectarine_row(row: dict, source: str) -> dict | None:
    posted = row.get("posted")
    if not posted:
        return None
    permalink = row.get("Permalink") or ""
    shortcode = shortcode_from_permalink(permalink)
    if not shortcode:
        return None
    post_type_raw = row.get("Post Type")
    return {
        "shortcode": shortcode,
        "date": posted,
        "title": row.get("Name"),
        "permalink": permalink,
        "type": normalize_type(post_type_raw, permalink),
        "post_type_raw": post_type_raw,
        "is_tagged": (post_type_raw or "").strip() == "Tagged",
        "likes": row.get("Likes"),
        "comments": row.get("comments") if "comments" in row else row.get("Comment Count"),
        "views": views_from_million(row.get("views_m")),
        "cover_path": None,
        "source": source,
    }


def parse_recap_html(path: Path, source_label: str) -> list[dict]:
    html = path.read_text(encoding="utf-8", errors="replace")
    block_pat = re.compile(
        r'<a class="post-cell[^"]*" href="(https://www\.instagram\.com/(?:funboy/)?(?:reel|p)/([^/]+)/)"[^>]*>'
        r"(.*?)</a>",
        re.S,
    )
    out: list[dict] = []
    for m in block_pat.finditer(html):
        permalink, shortcode, inner = m.group(1), m.group(2), m.group(3)
        date_m = re.search(r'class="post-date">([^<]+)</div>', inner)
        if not date_m:
            continue
        date_txt = date_m.group(1).split("<")[0].strip()
        posted = parse_recap_date(date_txt)
        if not posted:
            continue
        stat_m = re.search(r'class="post-stat">([^<]+)</div>', inner)
        likes = comments = views = None
        if stat_m:
            stat = stat_m.group(1).replace("&middot;", "·")
            sm = re.search(r"([\d,]+)\s+likes", stat)
            if sm:
                likes = int(sm.group(1).replace(",", ""))
            cm = re.search(r"([\d,]+)\s+comments", stat)
            if cm:
                comments = int(cm.group(1).replace(",", ""))
            vm = re.search(r"([\d,]+)\s+views", stat)
            if vm:
                views = int(vm.group(1).replace(",", ""))
        type_m = re.search(r'post-type">&middot;\s*([^<]+)</span>', inner)
        type_hint = (type_m.group(1).strip().lower() if type_m else "")
        ig_type = "reel" if "/reel/" in permalink else "photo"
        if "carousel" in type_hint:
            ig_type = "carousel"
        out.append(
            {
                "shortcode": shortcode,
                "date": posted.isoformat(),
                "title": None,
                "permalink": permalink,
                "type": ig_type,
                "post_type_raw": type_hint or ig_type,
                "is_tagged": False,
                "likes": likes,
                "comments": comments,
                "views": views,
                "cover_path": None,
                "source": source_label,
            }
        )
    return out


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_recap_date(label: str) -> date | None:
    # e.g. "Aug 27 · Reel" or "Sep 12" (August/September 2026 recaps)
    token = re.sub(r"<[^>]+>", "", label).split("·")[0].strip().lower()
    parts = token.split()
    if len(parts) != 2:
        return None
    mon, day_s = parts
    if mon not in MONTHS:
        return None
    try:
        day = int(day_s)
    except ValueError:
        return None
    year = 2026
    return date(year, MONTHS[mon], day)


def load_fun_posts() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from build_public_report import FUN_POSTS  # noqa: WPS433

    rows = []
    for p in FUN_POSTS:
        d = date.fromisoformat(p["date"])
        if d < WINDOW_START or d > WINDOW_END:
            continue
        rows.append(
            {
                "shortcode": p["shortcode"],
                "date": p["date"],
                "title": p.get("caption"),
                "permalink": f"https://www.instagram.com/{'reel' if p.get('type') == 'reel' else 'p'}/{p['shortcode']}/",
                "type": p.get("type", "reel"),
                "post_type_raw": p.get("type"),
                "is_tagged": False,
                "likes": p.get("likes"),
                "comments": p.get("comments"),
                "views": p.get("views"),
                "cover_path": f"covers/public-oct-2026/{p['shortcode']}.jpg",
                "source": "build_public_report.FUN_POSTS",
            }
        )
    return rows


def load_nectarine_rows() -> list[dict]:
    rows: list[dict] = []
    batch_paths = [SOURCES_DIR / name for name in SOURCE_BATCH_FILES]
    if all(p.is_file() for p in batch_paths):
        file_names = SOURCE_BATCH_FILES
        paths = batch_paths
    else:
        paths = [SOURCES_DIR / name for name in SOURCE_FILES]
        file_names = SOURCE_FILES
        if not all(p.is_file() for p in paths):
            missing = [str(p) for p in paths if not p.is_file()]
            raise FileNotFoundError(
                "Missing Nectarine source files. Expected quarter exports or batch pair:\n"
                + "\n".join(missing)
            )
    for name, path in zip(file_names, paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("results", payload):
            if isinstance(raw, dict) and "Permalink" in raw:
                norm = normalize_nectarine_row(raw, f"notion:{name}")
                if norm:
                    rows.append(norm)
    return rows


def merge_posts(*groups: list[dict]) -> list[dict]:
    """Later groups win on duplicate shortcodes (higher priority sources last)."""
    by_code: dict[str, dict] = {}
    for group in groups:
        for row in group:
            by_code[row["shortcode"]] = row
    merged = list(by_code.values())
    merged.sort(key=lambda r: (r["date"], r["shortcode"]))
    return merged


def in_window(d: date) -> bool:
    return WINDOW_START <= d <= WINDOW_END


def assign_quarter(d: date) -> str | None:
    for qid, start, end in QUARTERS:
        if start <= d <= end:
            return qid
    return None


def build_dataset() -> dict:
    nectarine = load_nectarine_rows()
    aug_gap = parse_recap_html(ROOT / "august-2026-recap.html", "august-2026-recap.html")
    sep_gap = parse_recap_html(ROOT / "september-2026-recap.html", "september-2026-recap.html")
    fun_oct = load_fun_posts()

    # Recap/fun posts override Nectarine for overlapping shortcodes (fresher metrics).
    all_posts = merge_posts(nectarine, aug_gap, sep_gap, fun_oct)

    filtered = []
    for p in all_posts:
        d = date.fromisoformat(p["date"])
        if not in_window(d):
            continue
        p = dict(p)
        p["quarter"] = assign_quarter(d)
        filtered.append(p)

    null_views = sum(1 for p in filtered if p.get("views") is None)
    tagged = sum(1 for p in filtered if p.get("is_tagged"))
    gaps = [
        "Nectarine Social export stops at ~2026-08-25; Aug 26–Sep 2026 from recap HTML.",
        "October 2026 through 2026-10-31 from build_public_report.FUN_POSTS (partial month).",
        "Many carousels/posts have null views in Nectarine; reels use Views (Million).",
        f"{tagged} Tagged UGC rows included (post_type Tagged); year UI may filter to owned-only.",
        "Cover images not bulk-fetched for the year set; October window covers may exist under covers/public-oct-2026/.",
    ]

    quarters_out = []
    for qid, start, end in QUARTERS:
        q_posts = [p for p in filtered if p.get("quarter") == qid]
        quarters_out.append(
            {
                "id": qid,
                "label": f"{start.isoformat()} – {end.isoformat()}",
                "post_count": len(q_posts),
                "posts": q_posts,
            }
        )

    return {
        "meta": {
            "account": "funboy",
            "platform": "instagram",
            "window_start": WINDOW_START.isoformat(),
            "window_end": WINDOW_END.isoformat(),
            "generated_by": "scripts/collect_funboy_ig_year.py",
            "post_count": len(filtered),
            "owned_post_count": len(filtered) - tagged,
            "tagged_post_count": tagged,
            "null_views_count": null_views,
            "gaps": gaps,
            "planned_page_parts": [
                "year_report_quarters",
                "ads_placeholder",
                "competitor_watch_existing",
            ],
        },
        "quarters": quarters_out,
        "posts": filtered,
    }


def main() -> int:
    dataset = build_dataset()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({dataset['meta']['post_count']} posts)")
    for q in dataset["quarters"]:
        print(f"  {q['id']}: {q['post_count']} posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
