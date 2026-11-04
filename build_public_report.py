#!/usr/bin/env python3
"""Generate Funboy public-only recap, benchmarks, and competitor-watch pages."""
from __future__ import annotations

import json
import math
import os
import ssl
import time
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
COVERS = os.path.join(ROOT, "covers", "public-oct-2026")
PT = ZoneInfo("America/Los_Angeles")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HDR = {"User-Agent": UA, "X-IG-App-ID": "936619743392459"}
COLLECTED = "November 3, 2026"
WINDOW_LABEL = "October 10–November 1, 2026"
SEP_IG_LIKES = 15294

FUN_POSTS = [
    {
        "shortcode": "DeUdstjBz5S",
        "date": "2026-10-10",
        "likes": 347,
        "comments": 4,
        "views": 4132,
        "type": "reel",
        "caption": "The coziest season starts here.",
    },
    {
        "shortcode": "DeW0vXXhd3p",
        "date": "2026-10-11",
        "likes": 237,
        "comments": 51,
        "views": 2496,
        "type": "reel",
        "caption": "Movie night, upgraded.",
    },
    {
        "shortcode": "DecPdkDBkRH",
        "date": "2026-10-13",
        "likes": 1165,
        "comments": 201,
        "views": 17386,
        "type": "reel",
        "caption": "Santa season is calling.",
        "breakthrough": "reach",
    },
    {
        "shortcode": "DeejFiCD-yR",
        "date": "2026-10-14",
        "likes": 144,
        "comments": 14,
        "views": None,
        "type": "photo",
        "caption": "Candy cane season.",
    },
    {
        "shortcode": "DemRiA-BPUf",
        "date": "2026-10-17",
        "likes": 422,
        "comments": 63,
        "views": 5387,
        "type": "reel",
        "caption": "Giant ornaments, tiny effort.",
    },
    {
        "shortcode": "Deo2TwLBk37",
        "date": "2026-10-18",
        "likes": 382,
        "comments": 38,
        "views": 6067,
        "type": "reel",
        "caption": "Pool day, holiday edition.",
    },
    {
        "shortcode": "DeuNmCahRnZ",
        "date": "2026-10-20",
        "likes": 270,
        "comments": 25,
        "views": 3159,
        "type": "reel",
        "caption": "Inflatable igloo season.",
    },
    {
        "shortcode": "DezJawWhnaF",
        "date": "2026-10-22",
        "likes": 320,
        "comments": 47,
        "views": 3466,
        "type": "reel",
        "caption": "Snow globe energy.",
    },
    {
        "shortcode": "De4TED2hF7e",
        "date": "2026-10-24",
        "likes": 1122,
        "comments": 63,
        "views": 17049,
        "type": "reel",
        "caption": "Holiday hosting, solved.",
        "breakthrough": "reach",
    },
    {
        "shortcode": "DfABbM-BX7B",
        "date": "2026-10-27",
        "likes": 91,
        "comments": 15,
        "views": 1082,
        "type": "reel",
        "caption": "Candy cane lane at home.",
    },
    {
        "shortcode": "DfFLAUPh9Dx",
        "date": "2026-10-29",
        "likes": 275,
        "comments": 9,
        "views": 2511,
        "type": "reel",
        "caption": "Stripe season.",
    },
    {
        "shortcode": "DfNAVN7Bnao",
        "date": "2026-11-01",
        "likes": 263,
        "comments": 20,
        "views": 6254,
        "type": "reel",
        "caption": "Weekend plans: float.",
    },
]

BSB_POSTS_WINDOW = [
    {"shortcode": "Dd91nIhpirt", "date": "2026-10-01", "likes": 215, "comments": 6, "views": 2198},
    {"shortcode": "DeAT-VbJMKl", "date": "2026-10-02", "likes": 28, "comments": 0, "views": 656},
    {"shortcode": "DesIOArgbmV", "date": "2026-10-19", "likes": 189, "comments": 0, "views": 6325, "breakthrough": "reach"},
    {"shortcode": "Dew0omUDS5C", "date": "2026-10-21", "likes": 40, "comments": 0, "views": 1276},
    {"shortcode": "De67VdCD7LR", "date": "2026-10-25", "likes": 36, "comments": 1, "views": 1379},
    {"shortcode": "DfATP0aDxoF", "date": "2026-10-27", "likes": 57, "comments": 2, "views": 1410},
    {"shortcode": "DfFdRp5FV0p", "date": "2026-10-29", "likes": 204, "comments": 3, "views": 12862, "note": "Reach spike · low engagement"},
]

BSB_PINNED = {
    "shortcode": "DBjITG7Rsu-",
    "date": "2024-10-25",
    "likes": 213697,
    "comments": 916,
    "views": 3501009,
}

# @funboy Instagram volume by calendar month (Nectarine Social / IG Post Performance History).
FUN_IG_YEAR_LABEL = "Oct 2025 – Oct 2026"
FUN_IG_YEAR_SOURCE = "Nectarine Social · IG Post Performance History (Sep 2026–Oct 2026 from monthly recaps / public grid)"
FUN_IG_MONTHLY = [
    {"month": "2025-10", "posts": 10, "reels": 10, "feed_posts": 0, "carousels": 0},
    {"month": "2025-11", "posts": 13, "reels": 7, "feed_posts": 1, "carousels": 5},
    {"month": "2025-12", "posts": 7, "reels": 6, "feed_posts": 0, "carousels": 1},
    {"month": "2026-01", "posts": 4, "reels": 2, "feed_posts": 1, "carousels": 1},
    {"month": "2026-02", "posts": 5, "reels": 2, "feed_posts": 1, "carousels": 2},
    {"month": "2026-03", "posts": 17, "reels": 8, "feed_posts": 2, "carousels": 7},
    {"month": "2026-04", "posts": 21, "reels": 11, "feed_posts": 0, "carousels": 10},
    {"month": "2026-05", "posts": 31, "reels": 23, "feed_posts": 0, "carousels": 8},
    {"month": "2026-06", "posts": 28, "reels": 17, "feed_posts": 0, "carousels": 11},
    {"month": "2026-07", "posts": 30, "reels": 14, "feed_posts": 1, "carousels": 15},
    {"month": "2026-08", "posts": 22, "reels": 18, "feed_posts": 4, "carousels": 0, "note": "September recap grid"},
    {"month": "2026-09", "posts": 17, "reels": 16, "feed_posts": 1, "carousels": 0, "note": "September recap"},
    {
        "month": "2026-10",
        "posts": 11,
        "reels": 10,
        "feed_posts": 1,
        "carousels": 0,
        "note": "Public grid through Oct 29 · not full month",
    },
]
# Optional context before the Oct–Oct year (not in headline totals).
FUN_IG_MONTHLY_PRIOR = [
    {"month": "2024-11", "posts": 12, "reels": 7, "feed_posts": 1, "carousels": 4},
    {"month": "2024-12", "posts": 12, "reels": 7, "feed_posts": 0, "carousels": 5},
    {"month": "2025-01", "posts": 7, "reels": 3, "feed_posts": 1, "carousels": 3},
    {"month": "2025-02", "posts": 11, "reels": 3, "feed_posts": 3, "carousels": 5},
    {"month": "2025-03", "posts": 15, "reels": 9, "feed_posts": 2, "carousels": 4},
    {"month": "2025-04", "posts": 27, "reels": 17, "feed_posts": 0, "carousels": 10},
    {"month": "2025-05", "posts": 25, "reels": 15, "feed_posts": 1, "carousels": 9},
    {"month": "2025-06", "posts": 21, "reels": 13, "feed_posts": 1, "carousels": 7},
    {"month": "2025-07", "posts": 20, "reels": 16, "feed_posts": 2, "carousels": 2},
    {"month": "2025-08", "posts": 14, "reels": 12, "feed_posts": 0, "carousels": 2},
    {"month": "2025-09", "posts": 11, "reels": 10, "feed_posts": 0, "carousels": 1},
]

STYLE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read().split("</style>")[0] + "</style>"


def fmt(n: int) -> str:
    return f"{n:,}"


def month_label(ym: str) -> str:
    y, m = ym.split("-")
    names = (
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
    return f"{names[int(m) - 1]} {y}"


def fun_ig_year_totals(rows: list[dict] | None = None) -> dict[str, int]:
    rows = rows if rows is not None else FUN_IG_MONTHLY
    keys = ("posts", "reels", "feed_posts", "carousels")
    out = {k: 0 for k in keys}
    for row in rows:
        for k in keys:
            out[k] += row[k]
    return out


def pct_change(new: float, old: float) -> str:
    if old == 0:
        return "—"
    ch = (new - old) / old * 100
    sign = "+" if ch > 0 else ""
    return f"{sign}{ch:.0f}%"


def pop_std(values: list[float]) -> float:
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def median(values: list[float]) -> float:
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def log_normal_band(values: list[float]) -> tuple[float, float, float]:
    logs = [math.log(v) for v in values if v > 0]
    mu = sum(logs) / len(logs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in logs) / len(logs))
    center = math.exp(mu)
    lo = math.exp(mu - sd)
    hi = math.exp(mu + sd)
    return center, lo, hi


def ig_url(shortcode: str, typ: str) -> str:
    if typ == "photo":
        return f"https://www.instagram.com/p/{shortcode}/"
    return f"https://www.instagram.com/reel/{shortcode}/"


def fetch_display_urls(shortcodes: list[str]) -> dict[str, str]:
    urls: dict[str, str] = {}
    try:
        req = urllib.request.Request(
            "https://www.instagram.com/api/v1/users/web_profile_info/?username=funboy",
            headers=HDR,
        )
        with urllib.request.urlopen(req, context=ssl.create_default_context()) as r:
            user = json.load(r)["data"]["user"]
        for e in user["edge_owner_to_timeline_media"]["edges"]:
            n = e["node"]
            if n["shortcode"] in shortcodes:
                urls[n["shortcode"]] = n["display_url"]
        req2 = urllib.request.Request(
            "https://www.instagram.com/api/v1/users/web_profile_info/?username=bigshinyballs",
            headers=HDR,
        )
        time.sleep(1.5)
        with urllib.request.urlopen(req2, context=ssl.create_default_context()) as r:
            user2 = json.load(r)["data"]["user"]
        for e in user2["edge_owner_to_timeline_media"]["edges"]:
            n = e["node"]
            if n["shortcode"] in shortcodes:
                urls[n["shortcode"]] = n["display_url"]
    except Exception:
        pass
    return urls


def save_cover(
    shortcode: str,
    remote: str | None,
    *,
    dest_dir: str | None = None,
    rel_prefix: str = "covers/public-oct-2026",
) -> str:
    base = dest_dir or COVERS
    os.makedirs(base, exist_ok=True)
    dest = os.path.join(base, f"{shortcode}.jpg")
    rel = f"{rel_prefix}/{shortcode}.jpg"
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        return rel
    if not remote:
        return ""
    try:
        img_req = urllib.request.Request(remote, headers={"User-Agent": UA})
        with urllib.request.urlopen(img_req, context=ssl.create_default_context()) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return rel
    except Exception:
        return ""


def save_bsb_covers() -> None:
    """Download BSB reel covers when the public API allows."""
    codes = [p["shortcode"] for p in BSB_POSTS_WINDOW]
    urls = fetch_display_urls(codes)
    bsb_dir = os.path.join(ROOT, "covers", "public-oct-2026-bsb")
    for code in codes:
        save_cover(
            code,
            urls.get(code),
            dest_dir=bsb_dir,
            rel_prefix="covers/public-oct-2026-bsb",
        )


def nav(current: str) -> str:
    def cls(name: str) -> str:
        return ' class="is-current"' if current == name else ""

    return f"""<nav class="report-nav" aria-label="Portal">
  <div class="report-nav-inner">
    <a{cls("dash")} href="index.html">Dashboard</a>
    <a{cls("bench")} href="benchmarks.html">Benchmarks</a>
    <a{cls("comp")} href="competitor-watch.html">Competitor watch</a>
    <div class="reports-tab">
      <span class="reports-label">Reports</span>
      <a{cls("oct")} href="october-public-2026-recap.html">Oct 10–Nov 1</a>
      <a{cls("sep")} href="september-2026-recap.html">September</a>
      <a{cls("aug")} href="august-2026-recap.html">August</a>
    </div>
  </div>
</nav>"""


def update_nav_in(path: str) -> None:
    import re

    text = open(path, encoding="utf-8").read()
    key = "dash" if path.endswith("index.html") else "sep" if "september" in path else "aug"
    pattern = r"<nav class=\"report-nav\" aria-label=\"Portal\">.*?</nav>"
    if re.search(pattern, text, flags=re.S):
        text = re.sub(pattern, nav(key), text, count=1, flags=re.S)
        open(path, "w", encoding="utf-8").write(text)


def week_buckets(posts: list[dict]) -> list[dict]:
    weeks = [
        ("Oct 10–12", "2026-10-10", "2026-10-12"),
        ("Oct 13–19", "2026-10-13", "2026-10-19"),
        ("Oct 20–26", "2026-10-20", "2026-10-26"),
        ("Oct 27–Nov 1", "2026-10-27", "2026-11-01"),
    ]
    out = []
    for label, start, end in weeks:
        bucket = [p for p in posts if start <= p["date"] <= end]
        views = sum(p["views"] or 0 for p in bucket if p["views"])
        out.append(
            {
                "label": label,
                "posts": len(bucket),
                "likes": sum(p["likes"] for p in bucket),
                "comments": sum(p["comments"] for p in bucket),
                "views": views,
            }
        )
    return out


def build_recap() -> None:
    reels = [p for p in FUN_POSTS if p.get("views")]
    total_likes = sum(p["likes"] for p in FUN_POSTS)
    total_comments = sum(p["comments"] for p in FUN_POSTS)
    total_views = sum(p["views"] for p in reels)
    avg_likes = total_likes / len(FUN_POSTS)
    like_delta = pct_change(total_likes, SEP_IG_LIKES)
    weeks = week_buckets(FUN_POSTS)
    max_posts = max(w["posts"] for w in weeks) or 1
    max_views = max(w["views"] for w in weeks) or 1

    outlier = max(reels, key=lambda p: p["views"])
    eng_rows = sorted(
        reels,
        key=lambda p: (p["likes"] + p["comments"]) / p["views"],
        reverse=True,
    )

    cover_codes = [p["shortcode"] for p in FUN_POSTS]
    remote_urls = fetch_display_urls(cover_codes)

    post_html = []
    current_week = None
    for p in FUN_POSTS:
        wk = next(w["label"] for w in week_buckets([p]))
        if wk != current_week:
            current_week = wk
            post_html.append(f'<div class="week-label">{wk}</div>')
        cover = save_cover(p["shortcode"], remote_urls.get(p["shortcode"]))
        img = (
            f'<img class="tile-img" src="{cover}" alt="">' if cover else '<div class="tile-img" style="background:#eee"></div>'
        )
        stats = f'{p["likes"]} likes'
        if p["views"]:
            stats += f' · {fmt(p["views"])} views'
        post_html.append(
            f"""<a class="post-cell" href="{ig_url(p['shortcode'], p['type'])}" target="_blank" rel="noopener">
      {img}
      <div class="post-meta"><div class="post-date">{p['date']}</div><div class="post-stat">{stats}</div></div>
    </a>"""
        )

    eng_tr = []
    for p in eng_rows:
        er = (p["likes"] + p["comments"]) / p["views"] * 100
        views_cell = fmt(p["views"])
        if p["shortcode"] == outlier["shortcode"]:
            views_cell = f'<span class="mark-circle">{views_cell}</span>'
        eng_tr.append(
            f"<tr><td>{p['date']}</td><td>{p['caption']}</td><td>{p['likes']}</td><td>{views_cell}</td><td>{p['comments']}</td><td>{er:.2f}%</td></tr>"
        )

    w_rows = ""
    for w in weeks:
        w_rows += f"<tr><td>{w['label']}</td><td>{w['posts']}</td><td>{fmt(w['likes'])}</td><td>{fmt(w['comments'])}</td><td>{fmt(w['views'])}</td></tr>"

    bars_posts = ""
    bars_views = ""
    for w in weeks:
        h = int(180 * w["posts"] / max_posts)
        hv = int(180 * w["views"] / max_views)
        bars_posts += f'<div class="bar-col"><div class="stack"><span class="val">{w["posts"]}</span><div class="segments"><div class="seg-ig" style="height:{h}px;"></div></div></div><div class="bar-lbl">{w["label"]}</div></div>'
        bars_views += f'<div class="bar-col"><div class="stack"><span class="val">{fmt(w["views"])}</span><div class="segments"><div class="seg-ig" style="height:{hv}px;"></div></div></div><div class="bar-lbl">{w["label"]}</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FUNBOY Social Recap — Public window Oct 10–Nov 1, 2026</title>
{STYLE}
</head>
<body>
{nav("oct")}
<header class="hero">
  <div class="inner">
    <div class="draft-pill">Public only · collected {COLLECTED}</div>
    <h1>FUNBOY Social Recap</h1>
    <p class="sub">Instagram and TikTok, {WINDOW_LABEL}. Source is the logged-out public profile. No Insights, no private dashboard.</p>
    <div class="kpi-strip">
      <div class="kpi"><div class="num">12</div><div class="lbl">Instagram posts on the first public grid (11 reels + 1 photo)</div></div>
      <div class="kpi"><div class="num">{fmt(total_likes)}</div><div class="lbl">Instagram likes in this window</div></div>
      <div class="kpi"><div class="num">{fmt(total_comments)}</div><div class="lbl">Instagram comments in this window</div></div>
      <div class="kpi"><div class="num">{fmt(total_views)}</div><div class="lbl">Public views on the 11 reels</div></div>
      <div class="kpi"><div class="num">{avg_likes:.0f}</div><div class="lbl">Avg. Instagram likes per post</div></div>
      <div class="kpi"><div class="num">46.1K</div><div class="lbl">TikTok followers visible logged out (video grid did not load)</div></div>
    </div>
  </div>
</header>
<div class="wrap">
<section>
  <h2>Month over Month<span class="tag">This public window vs. September recap tiles (Instagram likes only where scopes match)</span></h2>
  <table>
    <tr><th></th><th>Oct 10–Nov 1 (public)</th><th>September recap</th><th>Result</th></tr>
    <tr><td>Instagram posts</td><td>12</td><td>17</td><td>—</td></tr>
    <tr><td>Days covered</td><td>23</td><td>30</td><td>—</td></tr>
    <tr><td>Instagram posts / day</td><td>0.52</td><td>0.57</td><td class="bench-worse">-9% vs. September</td></tr>
    <tr><td>Instagram likes</td><td><span class="mark-circle">{fmt(total_likes)}</span></td><td>{fmt(SEP_IG_LIKES)}</td><td class="bench-worse"><span class="mark-underline">{like_delta} vs. September</span></td></tr>
    <tr><td>Instagram comments</td><td>{fmt(total_comments)}</td><td>364</td><td>—</td></tr>
    <tr><td>Instagram reel views</td><td>{fmt(total_views)} (public)</td><td>Insights-backed</td><td>Not compared — different source</td></tr>
    <tr><td>TikTok posts</td><td>Grid unavailable logged out</td><td>9</td><td>—</td></tr>
  </table>
  <p class="lead">September reel views in the recap use native Insights. This page uses public <code>video_view_count</code> only, so view totals are not compared across months.</p>
</section>
<section>
  <h2>Week over Week<span class="tag">Instagram only · {WINDOW_LABEL}</span></h2>
  <div class="chart-block">
    <h4>Posts published per week</h4>
    <div class="chart">{bars_posts}</div>
  </div>
  <div class="chart-block">
    <h4>Public reel views per week</h4>
    <div class="chart">{bars_views}</div>
  </div>
  <table>
    <tr><th>Week</th><th>Posts</th><th>Likes</th><th>Comments</th><th>Public reel views</th></tr>
    {w_rows}
  </table>
  <p class="avg-note">TikTok post rows are omitted because the logged-out video grid did not render during collection ({COLLECTED}).</p>
</section>
<section>
  <h2>Everything we posted on Instagram<span class="tag">First public grid · oldest to newest · tap opens permalink</span></h2>
  <div class="post-grid">
    {''.join(post_html)}
  </div>
</section>
<section>
  <h2>Instagram engagement detail<span class="tag">Public likes, comments, and views · sorted by (likes + comments) / views</span></h2>
  <table>
    <tr><th>Date</th><th>Caption</th><th>Likes</th><th>Views</th><th>Comments</th><th>Engagement</th></tr>
    {''.join(eng_tr)}
  </table>
</section>
<footer>
  Source: logged-out public Instagram profile @funboy and @funboy on TikTok, collected {COLLECTED}. Window {WINDOW_LABEL} is the first 12-tile grid on Instagram (Pacific dates from <code>taken_at</code>). No account login, Insights, or private analytics were used.
</footer>
</div>
</body>
</html>"""
    open(os.path.join(ROOT, "october-public-2026-recap.html"), "w", encoding="utf-8").write(html)


def build_benchmarks() -> None:
    reels = [p for p in FUN_POSTS if p.get("views")]
    views = [float(p["views"]) for p in reels]
    avg = sum(views) / len(views)
    sd = pop_std(views)
    med = median(views)
    subject = min(reels, key=lambda p: abs(p["views"] - med))
    delta = avg - subject["views"]
    pct_under = delta / avg * 100
    z = (subject["views"] - avg) / sd if sd else 0
    center, lo, hi = log_normal_band(views)
    sub_eng = (subject["likes"] + subject["comments"]) / subject["views"] * 100
    pool_eng = sum((p["likes"] + p["comments"]) / p["views"] for p in reels) / len(reels) * 100

    ranked = sorted(reels, key=lambda p: p["views"], reverse=True)
    rows = ""
    for p in ranked:
        rows += f"<tr><td>{p['date']}</td><td><a href=\"{ig_url(p['shortcode'], 'reel')}\" target=\"_blank\" rel=\"noopener\">{p['shortcode']}</a></td><td>{fmt(p['views'])}</td><td>{((p['likes']+p['comments'])/p['views']*100):.2f}%</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FUNBOY Benchmarks — MULE-14 on public reels</title>
{STYLE}
</head>
<body>
{nav("bench")}
<header class="hero">
  <div class="inner">
    <div class="draft-pill">Public only · MULE-14 math · {WINDOW_LABEL}</div>
    <h1>View benchmark</h1>
    <p class="sub">Ranked public reels from the Funboy window. Population standard deviation. Normal curve fit on log(view count).</p>
  </div>
</header>
<div class="wrap">
<section>
  <h2>Summary<span class="tag">Subject reel = median by public views ({subject['date']})</span></h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Reels in window</td><td>{len(reels)}</td></tr>
    <tr><td>Sum of public views</td><td>{fmt(int(sum(views)))}</td></tr>
    <tr><td>Average views</td><td>{avg:,.0f}</td></tr>
    <tr><td>Population std. dev.</td><td>{sd:,.0f}</td></tr>
    <tr><td>One σ above average</td><td>{avg + sd:,.0f}</td></tr>
    <tr><td>Subject views</td><td>{fmt(subject['views'])}</td></tr>
    <tr><td>Subject vs. average</td><td>{fmt(int(delta))} views below average ({pct_under:.1f}% under)</td></tr>
    <tr><td>Subject vs. average (σ)</td><td>{z:.2f}σ</td></tr>
    <tr><td>Log-normal center</td><td>{center:,.0f} (1σ band {lo:,.0f} – {hi:,.0f})</td></tr>
    <tr><td>Subject engagement</td><td>{sub_eng:.2f}% vs. pool {pool_eng:.2f}%</td></tr>
  </table>
</section>
<section>
  <h2>Ranked reels<span class="tag">Public views descending</span></h2>
  <table>
    <tr><th>Date</th><th>Shortcode</th><th>Views</th><th>Engagement</th></tr>
    {rows}
  </table>
</section>
<footer>Benchmark method: MULE-14 · Market Reel Report, applied to Funboy public reels per MULE-15. Collected {COLLECTED}.</footer>
</div>
</body>
</html>"""
    open(os.path.join(ROOT, "benchmarks.html"), "w", encoding="utf-8").write(html)


def build_competitor() -> None:
    fun_followers = 337091
    bsb_followers = 63495
    fun_reels = [p for p in FUN_POSTS if p.get("views")]
    fun_med = median([p["views"] for p in fun_reels])
    bsb_views = [p["views"] for p in BSB_POSTS_WINDOW]
    bsb_med = median(bsb_views)
    fun_share = fun_med / fun_followers * 100
    bsb_share = bsb_med / bsb_followers * 100

    def reel_cards(posts: list[dict], med: float, handle: str) -> str:
        html = ""
        for p in sorted(posts, key=lambda x: x["date"]):
            mult = p["views"] / med
            badge = ""
            if p.get("breakthrough"):
                badge = '<span class="badge top">Breakthrough · reach</span>'
            elif p.get("note"):
                badge = f'<span class="badge low">{p["note"]}</span>'
            html += f"""<div class="top-card">
      <div class="top-body">
        <div class="post-date">{p['date']}</div>
        <h3>@{handle} · {fmt(p['views'])} views</h3>
        <div class="stats">{p['likes']} likes · {p['comments']} comments · {mult:.2f}× median</div>
        {badge}
        <div class="boost-line"><a href="{ig_url(p['shortcode'], 'reel')}" target="_blank" rel="noopener">Open reel</a></div>
      </div>
    </div>"""
        return html

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FUNBOY Competitor watch</title>
{STYLE}
</head>
<body>
{nav("comp")}
<header class="hero">
  <div class="inner">
    <div class="draft-pill">Public only · collected {COLLECTED}</div>
    <h1>Competitor watch</h1>
    <p class="sub">Inflatable decor, logged-out Instagram. FUNBOY and Big Shiny Balls. Neither row uses Insights.</p>
  </div>
</header>
<div class="wrap">
<section>
  <h2>01 · Side by side</h2>
  <p class="lead">First public Instagram grid only. FUNBOY window {WINDOW_LABEL}. Big Shiny Balls reels dated Oct 1–Oct 29 on the first grid (2024 pinned reel excluded from medians). Also listed: PoolCandy @poolcandy (9,412 followers) and BigMouth Inc. @bigmouthinc (24,402 followers) — reels not collected.</p>
  <table>
    <tr><th></th><th>@funboy</th><th>@bigshinyballs</th></tr>
    <tr><td>Followers</td><td>{fmt(fun_followers)}</td><td>{fmt(bsb_followers)}</td></tr>
    <tr><td>Reels in window</td><td>{len(fun_reels)} in 23 days</td><td>{len(BSB_POSTS_WINDOW)} on first grid</td></tr>
    <tr><td>Posting pace</td><td>3.3 posts/week</td><td>1.6 reels/week</td></tr>
    <tr><td>Median views / reel</td><td><span class="mark-underline">{fmt(int(fun_med))}</span></td><td>{fmt(int(bsb_med))}</td></tr>
    <tr><td>Median views / followers</td><td>{fun_share:.2f}%</td><td><span class="mark-circle">{bsb_share:.2f}%</span></td></tr>
    <tr><td>TikTok (logged out)</td><td>46.1K followers · grid failed</td><td>24 followers · 0 videos</td></tr>
  </table>
  <div class="callout"><b>Marks:</b> underline = FUNBOY leads on raw median views; circle = smaller account reaches a larger share of its own followers.</div>
</section>
<section>
  <h2>02 · What the grids say</h2>
  <div class="reach-grid">
    <div class="reach-stat"><div class="num">2</div><div class="lbl">FUNBOY reach breakthroughs (Oct 13 &amp; Oct 24)</div></div>
    <div class="reach-stat"><div class="num">1</div><div class="lbl">Big Shiny Balls reach breakthrough (Oct 19)</div></div>
    <div class="reach-stat"><div class="num">{fmt(BSB_POSTS_WINDOW[-1]['views'])}</div><div class="lbl">BSB Oct 29 reel — reach spike, low engagement (not a breakthrough)</div></div>
  </div>
</section>
<section>
  <h2>03 · Every reel</h2>
  <p class="lead">Breakthrough = ≥3× account median views and ≥0.7× median engagement rate. Reach spike = ≥3× median views without engagement threshold.</p>
  <h2 style="font-size:20px;border-left-width:4px;">@funboy · {len(fun_reels)} reels · median {fmt(int(fun_med))} views</h2>
  <div class="top-cards compact">{reel_cards(fun_reels, fun_med, 'funboy')}</div>
  <h2 style="font-size:20px;border-left-width:4px;margin-top:36px;">@bigshinyballs · median {fmt(int(bsb_med))} views (Oct 1–29 window)</h2>
  <div class="top-cards compact">{reel_cards(BSB_POSTS_WINDOW, bsb_med, 'bigshinyballs')}</div>
  <h2 style="font-size:20px;border-left-width:4px;margin-top:36px;">Pinned outside window</h2>
  <p class="lead">Still visible on the grid but excluded from Oct medians: {BSB_PINNED['date']} reel ({fmt(BSB_PINNED['views'])} public views).</p>
</section>
<footer>Public Instagram only · collected {COLLECTED}. Method: MULE-15 competitor watch + MULE-14 top-five logic reserved for future pass.</footer>
</div>
</body>
</html>"""
    open(os.path.join(ROOT, "competitor-watch.html"), "w", encoding="utf-8").write(html)


def main() -> None:
    for path in [
        os.path.join(ROOT, "index.html"),
        os.path.join(ROOT, "september-2026-recap.html"),
        os.path.join(ROOT, "august-2026-recap.html"),
    ]:
        update_nav_in(path)
    build_recap()
    build_benchmarks()
    build_competitor()
    print("Wrote portal pages and updated nav.")


if __name__ == "__main__":
    main()
