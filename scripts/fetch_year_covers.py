#!/usr/bin/env python3
"""Fetch small cover JPEGs for FUNBOY year-report cards (public sources only).

Sources (in order):
  1. Existing covers/public-oct-2026/*.jpg
  2. Base64 tile images in august/september recap HTML
  3. Instagram embed/captioned EmbeddedMediaImage src
  4. TikTok public video page "cover" field

Writes covers/year-ig/{id}.jpg and covers/year-tt/{id}.jpg (max 160px wide),
updates cover_path on posts in data/funboy-ig-year-oct2025-oct2026.json.
"""

from __future__ import annotations

import base64
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "funboy-ig-year-oct2025-oct2026.json"
COVERS_IG = ROOT / "covers" / "year-ig"
COVERS_TT = ROOT / "covers" / "year-tt"
OCT_COVERS = ROOT / "covers" / "public-oct-2026"
RECAP_FILES = (
    ROOT / "august-2026-recap.html",
    ROOT / "september-2026-recap.html",
)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
THUMB_W = 160
JPEG_Q = 82
MIN_BYTES = 400
SLEEP_S = 2.75
RETRY_SLEEP_S = 12.0


def shortcode_from_permalink(permalink: str) -> str | None:
    m = re.search(r"instagram\.com/(?:funboy/)?(?:reel|p)/([^/?#]+)", permalink or "")
    return m.group(1) if m else None


def tiktok_id_from_permalink(permalink: str) -> str | None:
    m = re.search(r"tiktok\.com/@funboy/video/(\d+)", permalink or "")
    return m.group(1) if m else None


def resize_jpeg(raw: bytes) -> bytes:
    img = Image.open(BytesIO(raw))
    img = img.convert("RGB")
    w, h = img.size
    if w > THUMB_W:
        nh = max(1, int(h * THUMB_W / w))
        img = img.resize((THUMB_W, nh), Image.Resampling.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=JPEG_Q, optimize=True)
    return out.getvalue()


def write_cover(dest: Path, raw: bytes) -> bool:
    try:
        data = resize_jpeg(raw)
    except Exception:
        return False
    if len(data) < MIN_BYTES:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def download_url(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30) as r:
            return r.read()
    except Exception:
        return None


def harvest_recap_images() -> dict[tuple[str, str], bytes]:
    out: dict[tuple[str, str], bytes] = {}
    cell_pat = re.compile(
        r'<a class="post-cell[^"]*" href="([^"]+)"[^>]*>(.*?)</a>',
        re.S,
    )
    img_pat = re.compile(r'<img class="tile-img" src="([^"]+)"')
    for path in RECAP_FILES:
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        for m in cell_pat.finditer(html):
            href, inner = m.group(1), m.group(2)
            im = img_pat.search(inner)
            if not im:
                continue
            src = im.group(1)
            if src.startswith("covers/"):
                fs = ROOT / src
                if fs.is_file():
                    raw = fs.read_bytes()
                else:
                    continue
            elif src.startswith("data:image"):
                try:
                    raw = base64.b64decode(src.split(",", 1)[1])
                except Exception:
                    continue
            else:
                continue
            if "tiktok.com" in href:
                vid = tiktok_id_from_permalink(href)
                if vid:
                    out[("tiktok", vid)] = raw
            elif "instagram.com" in href:
                sc = shortcode_from_permalink(href)
                if sc:
                    out[("instagram", sc)] = raw
    return out


def ig_permalink_og_image(shortcode: str, permalink: str) -> bytes | None:
    """Open-graph preview from public permalink / reel page (carousels, some reels)."""
    candidates = []
    if permalink:
        candidates.append(permalink)
        if "/p/" in permalink:
            candidates.append(permalink.replace("/p/", "/reel/", 1))
    candidates.append(f"https://www.instagram.com/p/{shortcode}/")
    candidates.append(f"https://www.instagram.com/reel/{shortcode}/")
    seen: set[str] = set()
    for url in candidates:
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=25) as r:
                html = r.read().decode("utf-8", "replace")
            if "content unavailable" in html.lower() or ">unavailable<" in html.lower():
                continue
            m = re.search(r'property="og:image" content="([^"]+)"', html)
            if not m:
                m = re.search(r'name="twitter:image" content="([^"]+)"', html)
            if m:
                img_url = m.group(1).replace("&amp;", "&")
                if "scontent" in img_url or "cdninstagram" in img_url:
                    data = download_url(img_url)
                    if data and len(data) > MIN_BYTES:
                        return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(RETRY_SLEEP_S)
            continue
        except Exception:
            continue
        time.sleep(0.8)
    return None


def ig_media_jpeg(shortcode: str) -> bytes | None:
    url = f"https://www.instagram.com/p/{shortcode}/media/?size=l"
    data = download_url(url)
    if data and data[:3] == b"\xff\xd8\xff" and len(data) > MIN_BYTES:
        return data
    return None


def ig_embed_src(shortcode: str, permalink: str) -> str | None:
    path = "reel" if "/reel/" in (permalink or "") else "p"
    url = f"https://www.instagram.com/{path}/{shortcode}/embed/captioned/"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=25) as r:
                html = r.read().decode("utf-8", "replace")
            m = re.search(r'EmbeddedMediaImage[^>]+src="([^"]+)"', html)
            return m.group(1) if m else None
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(RETRY_SLEEP_S * (attempt + 1))
                continue
            return None
        except Exception:
            return None
    return None


def tiktok_page_cover(video_id: str) -> str | None:
    url = f"https://www.tiktok.com/@funboy/video/{video_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=25) as r:
            html = r.read().decode("utf-8", "replace")
        m = re.search(r'"cover":"([^"]+)"', html)
        if not m:
            return None
        cover = m.group(1).encode("utf-8").decode("unicode_escape").replace("\\u002F", "/")
        return cover.replace("\\/", "/")
    except urllib.error.HTTPError as e:
        if e.code in {403, 429}:
            time.sleep(8)
        return None
    except Exception:
        return None


def rel_cover(platform: str, post_id: str) -> str:
    if platform == "tiktok":
        return f"covers/year-tt/{post_id}.jpg"
    return f"covers/year-ig/{post_id}.jpg"


def cover_file(platform: str, post_id: str) -> Path:
    return (COVERS_TT if platform == "tiktok" else COVERS_IG) / f"{post_id}.jpg"


def ensure_cover(
    platform: str,
    post_id: str,
    *,
    recap: dict[tuple[str, str], bytes],
    permalink: str,
    network: bool,
) -> str | None:
    dest = cover_file(platform, post_id)
    if dest.is_file() and dest.stat().st_size > MIN_BYTES:
        return rel_cover(platform, post_id)

    if platform == "instagram":
        oct_file = OCT_COVERS / f"{post_id}.jpg"
        if oct_file.is_file() and oct_file.stat().st_size > MIN_BYTES:
            if write_cover(dest, oct_file.read_bytes()):
                return rel_cover(platform, post_id)

    key = (platform, post_id)
    if key in recap and write_cover(dest, recap[key]):
        return rel_cover(platform, post_id)

    if not network:
        return None

    remote: bytes | None = None
    if platform == "instagram":
        remote = ig_media_jpeg(post_id)
        if not remote:
            src = ig_embed_src(post_id, permalink)
            if src:
                remote = download_url(src)
        if not remote:
            remote = ig_permalink_og_image(post_id, permalink)
        time.sleep(0.45 if remote else SLEEP_S)
    else:
        src = tiktok_page_cover(post_id)
        if src:
            remote = download_url(src)
            time.sleep(SLEEP_S)

    if remote and write_cover(dest, remote):
        return rel_cover(platform, post_id)
    return None


def all_posts(data: dict) -> list[dict]:
    posts: list[dict] = []
    for block in data.get("quarters") or []:
        for p in block.get("posts") or []:
            posts.append(p)
    for block in data.get("tiktok_quarters") or []:
        for p in block.get("posts") or []:
            posts.append(p)
    return posts


def sync_cover_paths(data: dict, paths: dict[tuple[str, str], str | None]) -> None:
    for block in data.get("quarters") or []:
        for p in block.get("posts") or []:
            p["cover_path"] = paths.get(("instagram", p["shortcode"]))
    for block in data.get("tiktok_quarters") or []:
        for p in block.get("posts") or []:
            p["cover_path"] = paths.get(("tiktok", p["shortcode"]))
    for key, platform in (("posts", "instagram"), ("tiktok_posts", "tiktok")):
        for p in data.get(key) or []:
            p["cover_path"] = paths.get((platform, p["shortcode"]))


def main() -> int:
    network = "--offline" not in sys.argv
    if not DATA_PATH.is_file():
        print("Missing dataset; run collect_funboy_ig_year.py first", file=sys.stderr)
        return 1

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    recap = harvest_recap_images()
    print(f"Recap harvest: {len(recap)} embedded images", flush=True)

    paths: dict[tuple[str, str], str | None] = {}
    total = len(all_posts(data))
    done = 0
    for p in all_posts(data):
        platform = p.get("platform") or "instagram"
        post_id = p["shortcode"]
        paths[(platform, post_id)] = ensure_cover(
            platform,
            post_id,
            recap=recap,
            permalink=p.get("permalink") or "",
            network=network,
        )
        done += 1
        if done % 25 == 0:
            have = sum(1 for v in paths.values() if v)
            print(f"  {done}/{total} processed · {have} covers", flush=True)

    sync_cover_paths(data, paths)
    ig_total = sum(1 for k in paths if k[0] == "instagram")
    tt_total = sum(1 for k in paths if k[0] == "tiktok")
    ig_have = sum(1 for k, v in paths.items() if k[0] == "instagram" and v)
    tt_have = sum(1 for k, v in paths.items() if k[0] == "tiktok" and v)
    meta = data.setdefault("meta", {})
    meta["covers"] = {
        "instagram_with_photo": ig_have,
        "instagram_missing_photo": ig_total - ig_have,
        "tiktok_with_photo": tt_have,
        "tiktok_missing_photo": tt_total - tt_have,
        "thumb_max_width_px": THUMB_W,
    }
    gaps = meta.setdefault("gaps", [])
    note = (
        f"Covers: {ig_have}/{ig_total} Instagram and {tt_have}/{tt_total} TikTok cards have "
        f"saved thumbnails ({THUMB_W}px wide); remainder show date tiles."
    )
    gaps[:] = [g for g in gaps if not g.startswith("Covers:")]
    gaps.append(note)

    DATA_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(
        f"Done. IG {ig_have}/{ig_total} · TikTok {tt_have}/{tt_total} · missing "
        f"{ig_total - ig_have + tt_total - tt_have}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
