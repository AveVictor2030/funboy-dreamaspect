#!/usr/bin/env python3
"""Build FUNBOY public Instagram + TikTok year dataset (Oct 2025–Oct 2026, quartered).

Instagram sources (deduped by shortcode):
  - Notion Nectarine SQL exports in data/sources/nectarine-batch-*.json
  - august-2026-recap.html / september-2026-recap.html (Nectarine lag after ~2026-08-25)
  - build_public_report.FUN_POSTS (October 2026 public window)

TikTok sources (deduped by video id):
  - Notion Nectarine tiktok-batch-*.json (public likes/comments/views only)
  - August / September recap HTML for late-Aug–Sep posts Nectarine missed
  - No logged-out @funboy grid scrape (TikTok blocks datacenter fetches).

Regenerate:
  python3 scripts/collect_funboy_ig_year.py
"""

from __future__ import annotations

import calendar
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
# Portal month completeness is evaluated against this date (month must be closed).
DATA_AS_OF = date(2026, 11, 10)
# Calendar months with known TikTok collection gaps (see meta.gaps).
TT_INCOMPLETE_MONTHS = frozenset({"2026-10"})

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
TIKTOK_BATCH_FILES = (
    "nectarine-tiktok-batch-a-2025-10-01_2026-05-31.json",
    "nectarine-tiktok-batch-b-2026-06-01_2026-10-31.json",
)


def shortcode_from_permalink(permalink: str) -> str | None:
    m = re.search(r"instagram\.com/(?:funboy/)?(?:reel|p)/([^/?#]+)", permalink or "")
    return m.group(1) if m else None


def tiktok_id_from_permalink(permalink: str) -> str | None:
    m = re.search(r"tiktok\.com/@funboy/video/(\d+)", permalink or "")
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


def normalize_nectarine_tiktok_row(row: dict, source: str) -> dict | None:
    posted = row.get("posted")
    if not posted:
        return None
    permalink = row.get("Permalink") or ""
    video_id = tiktok_id_from_permalink(permalink)
    if not video_id:
        return None
    return {
        "shortcode": video_id,
        "date": posted,
        "title": row.get("Name"),
        "permalink": permalink,
        "type": "video",
        "post_type_raw": row.get("Post Type") or "TikTok",
        "likes": row.get("Likes"),
        "comments": row.get("comments") if "comments" in row else row.get("Comment Count"),
        "views": views_from_million(row.get("views_m")),
        "cover_path": None,
        "platform": "tiktok",
        "source": source,
    }


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
        "platform": "instagram",
        "source": source,
    }


def extract_recap_post_date(inner: str) -> str | None:
    m = re.search(r'class="post-date">\s*([A-Za-z]{3,9}\s+\d{1,2})', inner)
    return m.group(1).strip() if m else None


def parse_tiktok_recap_html(path: Path, source_label: str) -> list[dict]:
    html = path.read_text(encoding="utf-8", errors="replace")
    block_pat = re.compile(
        r'<a class="post-cell[^"]*" href="(https://www\.tiktok\.com/@funboy/video/(\d+))"[^>]*>'
        r"(.*?)</a>",
        re.S,
    )
    out: list[dict] = []
    for m in block_pat.finditer(html):
        permalink, video_id, inner = m.group(1), m.group(2), m.group(3)
        date_txt = extract_recap_post_date(inner)
        if not date_txt:
            continue
        posted = parse_recap_date(date_txt)
        if not posted:
            continue
        likes = comments = views = None
        stat_m = re.search(r'class="post-stat">(.+?)</div>', inner, re.S)
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
        out.append(
            {
                "shortcode": video_id,
                "date": posted.isoformat(),
                "title": None,
                "permalink": permalink,
                "type": "video",
                "post_type_raw": "TikTok",
                "likes": likes,
                "comments": comments,
                "views": views,
                "cover_path": None,
                "platform": "tiktok",
                "source": source_label,
            }
        )
    return out


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
        date_txt = extract_recap_post_date(inner)
        if not date_txt:
            continue
        posted = parse_recap_date(date_txt)
        if not posted:
            continue
        stat_m = re.search(r'class="post-stat">(.+?)</div>', inner, re.S)
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
                "platform": "instagram",
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
                "platform": "instagram",
                "source": "build_public_report.FUN_POSTS",
            }
        )
    return rows


def load_nectarine_tiktok_rows() -> list[dict]:
    rows: list[dict] = []
    for name in TIKTOK_BATCH_FILES:
        path = SOURCES_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing TikTok source file: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("results", payload):
            if isinstance(raw, dict) and "Permalink" in raw:
                norm = normalize_nectarine_tiktok_row(raw, f"notion:{name}")
                if norm:
                    rows.append(norm)
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


MONTH_NAMES = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def month_label_short(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTH_NAMES[int(m) - 1]} '{y[2:]}"


def iter_year_months(start: date, end: date) -> list[str]:
    out: list[str] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def prior_year_month(ym: str) -> str:
    y, m = ym.split("-")
    return f"{int(y) - 1}-{m}"


def month_calendar_bounds(ym: str) -> tuple[date, date]:
    y, m = map(int, ym.split("-"))
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def load_ig_monthly_current() -> dict[str, dict]:
    sys.path.insert(0, str(ROOT))
    from build_public_report import FUN_IG_MONTHLY  # noqa: WPS433

    return {row["month"]: row for row in FUN_IG_MONTHLY}


def month_dataset_complete(
    platform: str,
    ym: str,
    post_count: int,
    *,
    as_of: date,
    ig_authority: dict | None = None,
) -> tuple[bool, str | None]:
    _, cal_end = month_calendar_bounds(ym)
    month_closed = as_of > cal_end

    if platform == "instagram":
        if ig_authority:
            expected = int(ig_authority["posts"])
            note = (ig_authority.get("note") or "").strip()
            if month_closed:
                if post_count >= expected:
                    return True, f"Full month · {post_count} posts in dataset"
                return False, f"Incomplete month · {post_count}/{expected} posts in dataset"
            if note and "not full month" in note.lower():
                return False, note
            if post_count >= expected:
                return True, note or f"On track · {post_count}/{expected} posts"
            return False, note or f"Collecting · {post_count}/{expected} posts"
        if month_closed:
            return True, "Full month · no Nectarine monthly row"
        if post_count:
            return False, "Month in progress"
        return False, "No posts in month"

    if platform == "tiktok":
        if ym in TT_INCOMPLETE_MONTHS:
            return False, "No October 2026 TikTok rows in public sources"
        if month_closed:
            return True, "Full month · period closed in dataset window"
        if post_count:
            return False, "Month in progress"
        return False, "No posts in month"

    return month_closed, None


def month_post_coverage(
    posts: list[dict],
    ym: str,
    *,
    platform: str = "generic",
    as_of: date | None = None,
    ig_authority: dict | None = None,
) -> dict:
    as_of = as_of or DATA_AS_OF
    dates = sorted(p["date"] for p in posts if p["date"].startswith(ym))
    post_count = len(dates)
    first, last = (dates[0], dates[-1]) if dates else (None, None)
    full, note = month_dataset_complete(
        platform,
        ym,
        post_count,
        as_of=as_of,
        ig_authority=ig_authority,
    )
    if not dates and not note:
        note = "No posts in month"
    return {
        "post_count": post_count,
        "first_post": first,
        "last_post": last,
        "calendar_full_month": full,
        "note": note,
    }


def aggregate_posts_by_month(posts: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in posts:
        ym = p["date"][:7]
        bucket = out.setdefault(
            ym,
            {"posts": 0, "likes": 0, "comments": 0, "views": 0, "views_posts": 0},
        )
        bucket["posts"] += 1
        bucket["likes"] += p.get("likes") or 0
        bucket["comments"] += p.get("comments") or 0
        views = p.get("views")
        if views is not None:
            bucket["views"] += int(views)
            bucket["views_posts"] += 1
    return out


def load_ig_monthly_history() -> dict[str, dict]:
    sys.path.insert(0, str(ROOT))
    from build_public_report import FUN_IG_MONTHLY, FUN_IG_MONTHLY_PRIOR  # noqa: WPS433

    lookup: dict[str, dict] = {}
    for row in FUN_IG_MONTHLY_PRIOR + FUN_IG_MONTHLY:
        lookup[row["month"]] = row
    return lookup


def build_monthly_timeline(ig_posts: list[dict], tt_posts: list[dict]) -> dict:
    ig_by_month = aggregate_posts_by_month(ig_posts)
    tt_by_month = aggregate_posts_by_month(tt_posts)
    ig_history = load_ig_monthly_history()
    ig_current = load_ig_monthly_current()
    months: list[dict] = []
    for ym in iter_year_months(WINDOW_START, WINDOW_END):
        pym = prior_year_month(ym)
        ig = ig_by_month.get(ym, {"posts": 0, "likes": 0, "comments": 0, "views": 0, "views_posts": 0})
        tt = tt_by_month.get(ym, {"posts": 0, "likes": 0, "comments": 0, "views": 0, "views_posts": 0})
        hist = ig_history.get(pym)
        prior_ig_posts = int(hist["posts"]) if hist else None
        prior_ig = {
            "posts": prior_ig_posts,
            "likes": None,
            "comments": None,
            "views": None,
            "source": "nectarine_monthly_history" if hist else None,
        }
        prior_tt = {"posts": 0, "likes": None, "comments": None, "views": None, "source": None}
        ig_cov = month_post_coverage(
            ig_posts,
            ym,
            platform="instagram",
            ig_authority=ig_current.get(ym),
        )
        tt_cov = month_post_coverage(tt_posts, ym, platform="tiktok")
        combined_posts = ig["posts"] + tt["posts"]
        _, cal_end = month_calendar_bounds(ym)
        month_closed = DATA_AS_OF > cal_end
        combined_full = ig_cov["calendar_full_month"] and (
            tt_cov["calendar_full_month"]
            or (month_closed and tt_cov["post_count"] == 0)
        )
        months.append(
            {
                "month": ym,
                "label": month_label_short(ym),
                "prior_month": pym,
                "prior_label": month_label_short(pym),
                "instagram": dict(ig),
                "tiktok": dict(tt),
                "posts_total": combined_posts,
                "coverage": {
                    "instagram": ig_cov,
                    "tiktok": tt_cov,
                    "combined_posts": combined_posts,
                    "combined_full_month": combined_full,
                },
                "prior_year": {"instagram": prior_ig, "tiktok": prior_tt},
            }
        )
    return {
        "window_start": WINDOW_START.isoformat(),
        "window_end": WINDOW_END.isoformat(),
        "months": months,
        "notes": [
            "Posts = public post count in each calendar month (Instagram + TikTok in Both view).",
            "Full month = dataset has expected posts for that calendar month (Nectarine monthly count for Instagram; closed period for TikTok).",
            f"Completeness evaluated as of {DATA_AS_OF.isoformat()}.",
            "Prior-year Instagram post counts are Nectarine monthly rollups.",
            "Prior-year TikTok: no public export before Nov 2025; prior bars are zero for TikTok.",
            "Prior-year likes/views not in monthly history unless post-level rows exist.",
        ],
    }


def quarter_blocks(posts: list[dict]) -> list[dict]:
    out = []
    for qid, start, end in QUARTERS:
        q_posts = [p for p in posts if p.get("quarter") == qid]
        out.append(
            {
                "id": qid,
                "label": f"{start.isoformat()} – {end.isoformat()}",
                "post_count": len(q_posts),
                "posts": q_posts,
            }
        )
    return out


def build_dataset() -> dict:
    nectarine = load_nectarine_rows()
    aug_gap = parse_recap_html(ROOT / "august-2026-recap.html", "august-2026-recap.html")
    sep_gap = parse_recap_html(ROOT / "september-2026-recap.html", "september-2026-recap.html")
    fun_oct = load_fun_posts()
    all_ig = merge_posts(nectarine, aug_gap, sep_gap, fun_oct)

    ig_filtered: list[dict] = []
    for p in all_ig:
        d = date.fromisoformat(p["date"])
        if not in_window(d):
            continue
        p = dict(p)
        p["quarter"] = assign_quarter(d)
        ig_filtered.append(p)

    null_views_ig = sum(1 for p in ig_filtered if p.get("views") is None)
    tagged = sum(1 for p in ig_filtered if p.get("is_tagged"))

    tiktok_nectarine = load_nectarine_tiktok_rows()
    tik_aug = parse_tiktok_recap_html(ROOT / "august-2026-recap.html", "august-2026-recap.html")
    tik_sep = parse_tiktok_recap_html(ROOT / "september-2026-recap.html", "september-2026-recap.html")
    all_tt = merge_posts(tiktok_nectarine, tik_aug, tik_sep)

    tt_filtered: list[dict] = []
    for p in all_tt:
        d = date.fromisoformat(p["date"])
        if not in_window(d):
            continue
        p = dict(p)
        p["quarter"] = assign_quarter(d)
        tt_filtered.append(p)

    null_views_tt = sum(1 for p in tt_filtered if p.get("views") is None)

    gaps = [
        "Instagram: Nectarine export stops at ~2026-08-25; Aug 26–Sep 2026 from recap HTML; Oct from FUN_POSTS.",
        "TikTok: Nectarine batches plus August/September recap HTML (recap date tiles include nested spans).",
        "TikTok: no Oct 2025–Oct 2026 posts in Nectarine before Nov 12, 2025; no October 2026 TikTok rows collected.",
        "TikTok: logged-out https://www.tiktok.com/@funboy returns HTTP 403 from this environment; no grid scrape.",
        "Public counts only (likes, comments, views on the open video page / recap tiles). No TikTok Insights.",
        "Instagram carousels often have null views in Nectarine; reels use Views (Million).",
        f"{tagged} Instagram Tagged UGC rows included.",
        "Cover images: Oct 2026 Instagram covers under covers/public-oct-2026/; TikTok uses date tiles.",
    ]

    timeline = build_monthly_timeline(ig_filtered, tt_filtered)
    gaps.extend(timeline["notes"])

    return {
        "meta": {
            "account": "funboy",
            "window_start": WINDOW_START.isoformat(),
            "window_end": WINDOW_END.isoformat(),
            "generated_by": "scripts/collect_funboy_ig_year.py",
            "timeline": timeline,
            "instagram": {
                "post_count": len(ig_filtered),
                "owned_post_count": len(ig_filtered) - tagged,
                "tagged_post_count": tagged,
                "null_views_count": null_views_ig,
            },
            "tiktok": {
                "post_count": len(tt_filtered),
                "null_views_count": null_views_tt,
            },
            "gaps": gaps,
            "planned_page_parts": [
                "year_report_quarters_ig_tiktok",
                "ads_placeholder",
                "competitor_watch_existing",
            ],
        },
        "quarters": quarter_blocks(ig_filtered),
        "posts": ig_filtered,
        "tiktok_quarters": quarter_blocks(tt_filtered),
        "tiktok_posts": tt_filtered,
    }


def main() -> int:
    dataset = build_dataset()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")
    ig_n = dataset["meta"]["instagram"]["post_count"]
    tt_n = dataset["meta"]["tiktok"]["post_count"]
    print(f"Wrote {OUT_PATH} (Instagram {ig_n}, TikTok {tt_n})")
    for q in dataset["quarters"]:
        print(f"  IG {q['id']}: {q['post_count']}")
    for q in dataset["tiktok_quarters"]:
        print(f"  TT {q['id']}: {q['post_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
