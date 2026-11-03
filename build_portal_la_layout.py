#!/usr/bin/env python3
"""Build Funboy portal pages using the la-reels layout (Dream Aspect report chrome)."""
from __future__ import annotations

import math
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# Reuse collected public data from the prior generator.
from build_public_report import (  # noqa: E402
    BSB_POSTS_WINDOW,
    BSB_PINNED,
    COLLECTED,
    FUN_POSTS,
    SEP_IG_LIKES,
    WINDOW_LABEL,
    fmt,
    ig_url,
    log_normal_band,
    median,
    pop_std,
    week_buckets,
)

LA_REELS_SOURCE = "https://www.dreamaspect.co/la-reels/ (Dream Aspect worker da-report-la-reels; layout and fonts copied Nov 3, 2026)"

# Public competitor shelf (inflatable / pool decor). Reels only where collected in this pass.
COMPETITOR_SHELF = [
    {
        "handle": "funboy",
        "label": "FUNBOY",
        "role": "Subject brand",
        "followers": 337_091,
        "tiktok": "46.1K followers · video grid did not load logged out",
        "brand": True,
    },
    {
        "handle": "bigshinyballs",
        "label": "Big Shiny Balls",
        "role": "Competitor · collected",
        "followers": 63_495,
        "tiktok": "24 followers · 0 public videos",
        "brand": False,
    },
    {
        "handle": "poolcandy",
        "label": "PoolCandy",
        "role": "Competitor · profile only",
        "followers": 9_412,
        "tiktok": "Not collected this pass",
        "brand": False,
    },
    {
        "handle": "bigmouthinc",
        "label": "BigMouth Inc.",
        "role": "Competitor · profile only",
        "followers": 24_402,
        "tiktok": "Not collected this pass",
        "brand": False,
    },
]

CSS = """@font-face {
  font-family: Nohemi;
  src: url("fonts/Nohemi-Medium.ttf") format("truetype");
  font-weight: 500;
  font-display: swap;
}
@font-face {
  font-family: "Red Hat Display";
  src: url("fonts/RedHatDisplay-VariableFont_wght.ttf") format("truetype");
  font-weight: 300 900;
  font-display: swap;
}
:root {
  --black: #000;
  --white: #fff;
  --fog: #fafafa;
  --blue: #9dc9f5;
  --ice: #d8e9fb;
  --gray: #d9d9d9;
  --muted: color-mix(in srgb, var(--black) 48%, var(--fog));
  --mark: #c73333;
  --good: #1b9500;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--white); color: var(--black); font-family: "Red Hat Display", sans-serif; }
a { color: inherit; }
.chrome {
  min-height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 28px;
  font-size: 14px;
  border-bottom: 1px solid var(--gray);
  flex-wrap: wrap;
}
.brand { font-family: Nohemi, sans-serif; font-weight: 500; letter-spacing: -0.02em; }
.nav { display: flex; gap: 10px; flex-wrap: wrap; }
.nav a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--black);
  border-radius: 4px;
  background: var(--white);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.01em;
  text-decoration: none;
}
.nav a[aria-current="page"] { background: var(--black); color: var(--white); }
main { max-width: 1180px; margin: 0 auto; padding: 28px 28px 72px; }
.eyebrow { margin: 0 0 10px; font-size: 11px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
h1 { font-family: Nohemi, sans-serif; font-weight: 500; letter-spacing: -0.03em; font-size: clamp(32px, 4vw, 48px); line-height: 1.05; margin: 0 0 12px; }
h2 { font-family: Nohemi, sans-serif; font-weight: 500; letter-spacing: -0.02em; font-size: 26px; margin: 0 0 8px; }
.lead { max-width: 44rem; margin: 0 0 22px; font-size: 16px; line-height: 1.5; }
.rules {
  border: 1px solid var(--gray);
  background: var(--fog);
  border-radius: 4px;
  padding: 16px 18px;
  margin: 0 0 28px;
  max-width: 44rem;
  font-size: 14px;
  line-height: 1.5;
}
.rules ul { margin: 10px 0 0; padding-left: 18px; }
.kpi-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0 0 28px; }
.kpi {
  border: 1px solid var(--gray);
  border-radius: 4px;
  padding: 10px 12px;
  background: var(--fog);
}
.kpi b {
  display: block;
  font-family: Nohemi, sans-serif;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: -0.03em;
}
.kpi span { font-size: 12px; color: var(--muted); }
.section { margin-top: 36px; padding-top: 24px; border-top: 1px solid var(--gray); }
.grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--gray);
  background: var(--white);
  text-decoration: none;
  overflow: hidden;
  border-radius: 4px;
  color: inherit;
}
.card:hover { border-color: var(--black); }
.thumb { position: relative; aspect-ratio: 9 / 16; background: var(--fog); }
.thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.meta { padding: 10px 10px 12px; }
.place { font-family: Nohemi, sans-serif; font-size: 14px; margin: 0 0 4px; line-height: 1.25; }
.who { color: var(--muted); font-size: 12px; margin: 0 0 8px; }
.stats { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; align-items: baseline; }
.stats b { font-size: 14px; font-variant-numeric: tabular-nums; }
.eng { background: var(--blue); padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 12px; }
.counts { list-style: none; margin: 8px 0 0; padding: 0; font-size: 12px; color: var(--muted); display: grid; gap: 2px; }
.counts b { color: var(--black); }
.tag { display: inline-block; background: var(--black); color: var(--white); font-size: 10px; font-weight: 700; letter-spacing: 0.06em; padding: 2px 6px; margin-top: 6px; }
.tag.boost { background: var(--good); }
.tag.warn { background: var(--mark); }
table.data { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
table.data th, table.data td { border: 1px solid var(--gray); padding: 8px 10px; text-align: left; vertical-align: top; }
table.data th { background: var(--fog); font-weight: 700; }
.foot { margin: 28px 0 0; color: var(--muted); font-size: 12px; line-height: 1.45; max-width: 46rem; }
.mark-circle { display: inline-block; border: 2px solid var(--mark); border-radius: 999px; padding: 0 6px; }
.mark-underline { background-image: linear-gradient(transparent 62%, var(--mark) 62%, var(--mark) 78%, transparent 78%); }
.worse { color: var(--mark); font-weight: 700; }
.chart-wrap { margin: 16px 0; max-width: 680px; }
.chart-wrap svg { width: 100%; height: auto; display: block; border: 1px solid var(--gray); border-radius: 4px; background: var(--white); }
.bar-chart { display: flex; align-items: flex-end; gap: 12px; height: 180px; border-bottom: 2px solid var(--black); padding: 0 4px 0; margin-top: 12px; }
.bar-col { flex: 1; text-align: center; font-size: 11px; color: var(--muted); }
.bar-col b { display: block; color: var(--black); font-size: 13px; margin-bottom: 6px; }
.bar-col i { display: block; width: 100%; background: var(--blue); border-radius: 4px 4px 0 0; min-height: 4px; }
.archive-note {
  max-width: 1180px;
  margin: 0 auto;
  padding: 12px 28px;
  background: var(--ice);
  border-bottom: 1px solid var(--gray);
  font-size: 13px;
}
.archive-list { display: grid; gap: 10px; margin-top: 16px; }
.archive-list a {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--gray);
  border-radius: 4px;
  padding: 14px 16px;
  text-decoration: none;
}
.archive-list a:hover { border-color: var(--black); }
.pill { display: inline-block; background: var(--black); color: var(--white); font-size: 10px; font-weight: 700; letter-spacing: 0.06em; padding: 3px 7px; }
.reach-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.reach-grid div { border: 1px solid var(--gray); border-radius: 4px; padding: 12px; background: var(--fog); }
.reach-grid b { display: block; font-family: Nohemi, sans-serif; font-size: 24px; }
.comp-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 0 0 28px; }
.comp-card {
  border: 1px solid var(--gray);
  border-radius: 4px;
  padding: 14px 14px 12px;
  background: var(--fog);
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 100%;
}
.comp-card.is-brand { border-color: var(--black); background: var(--white); }
.comp-card .handle { font-family: Nohemi, sans-serif; font-size: 18px; letter-spacing: -0.02em; margin: 0; }
.comp-card .role { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 0; }
.comp-card dl { margin: 0; display: grid; gap: 6px; font-size: 12px; }
.comp-card dt { color: var(--muted); font-weight: 600; }
.comp-card dd { margin: 0; font-variant-numeric: tabular-nums; }
.comp-card .tt { font-size: 11px; color: var(--muted); line-height: 1.35; margin: 0; }
.comp-block { margin-top: 28px; }
.comp-block h3 { font-family: Nohemi, sans-serif; font-size: 20px; margin: 0 0 10px; }
@keyframes edgeGlowOneOff { 0%, 100% { outline: 2px solid var(--blue); outline-offset: 3px; } 50% { outline: 2px solid var(--black); outline-offset: 3px; } }
.mold2-card { animation: 2.8s ease-in-out infinite edgeGlowOneOff; border-radius: 4px; }
.archive-list.mold2 { gap: 14px; margin-top: 20px; }
.archive-list.mold2 a { transition: border-color 0.2s ease, transform 0.2s ease; }
.archive-list.mold2 a:hover { border-color: var(--black); transform: translateY(-2px); }
.empty-shelf { border: 1px dashed var(--gray); border-radius: 4px; padding: 18px; color: var(--muted); font-size: 14px; margin: 0 0 16px; }
@media (prefers-reduced-motion: reduce) { .mold2-card { animation: none; } }
@media (max-width: 980px) { .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .kpi-row { grid-template-columns: repeat(2, 1fr); } .comp-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 680px) {
  .chrome, main, .archive-note { padding-left: 16px; padding-right: 16px; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .kpi-row, .reach-grid { grid-template-columns: 1fr; }
}
"""


def nav(current: str) -> str:
    items = [
        ("index.html", "October report", "october"),
        ("benchmarks.html", "Benchmarks", "benchmarks"),
        ("competitor-research.html", "Competitor research", "competitor"),
        ("all-reports.html", "All reports", "all"),
    ]
    links = []
    for href, label, key in items:
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    return f"""<header class="chrome">
  <span class="brand">FUNBOY · Dream Aspect</span>
  <nav class="nav">{"".join(links)}</nav>
</header>"""


def page_shell(title: str, current: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex" />
  <title>{title}</title>
  <link rel="stylesheet" href="portal-styles.css" />
</head>
<body>
{nav(current)}
<main>
{body}
</main>
</body>
</html>
"""


def pct_change(new: float, old: float) -> str:
    if old == 0:
        return "—"
    ch = (new - old) / old * 100
    sign = "+" if ch > 0 else ""
    return f"{sign}{ch:.0f}%"


def cover_path(shortcode: str) -> str:
    return f"covers/public-oct-2026/{shortcode}.jpg"


def rules_block() -> str:
    return ""


def reel_posts_for(handle: str) -> list[dict]:
    if handle == "funboy":
        return [p for p in FUN_POSTS if p.get("views")]
    if handle == "bigshinyballs":
        return list(BSB_POSTS_WINDOW)
    return []


def competitor_shelf_cards(*, competitors_only: bool = False) -> str:
    html = '<div class="comp-grid">'
    for c in COMPETITOR_SHELF:
        if competitors_only and c.get("brand"):
            continue
        posts = reel_posts_for(c["handle"])
        med = median([p["views"] for p in posts]) if posts else None
        reels_n = len(posts)
        share = (med / c["followers"] * 100) if med else None
        brand_cls = " is-brand" if c.get("brand") else ""
        med_line = fmt(int(med)) if med is not None else "—"
        share_line = f"{share:.2f}%" if share is not None else "—"
        reels_line = str(reels_n) if reels_n else "—"
        html += f"""<article class="comp-card{brand_cls}">
  <p class="role">{c['role']}</p>
  <p class="handle">@{c['handle']}</p>
  <dl>
    <div><dt>Followers</dt><dd>{fmt(c['followers'])}</dd></div>
    <div><dt>Reels collected</dt><dd>{reels_line}</dd></div>
    <div><dt>Median views</dt><dd>{med_line}</dd></div>
    <div><dt>Views / followers</dt><dd>{share_line}</dd></div>
  </dl>
  <p class="tt">TikTok · {c['tiktok']}</p>
  <p class="tt">Instagram · <a href="https://www.instagram.com/{c['handle']}/" target="_blank" rel="noopener">@{c['handle']}</a></p>
</article>"""
    html += "</div>"
    return html


def competitor_ig_cards(posts: list[dict], handle: str, med: float) -> str:
    if not posts:
        return f'<p class="empty-shelf">No reels collected for @{handle} in this pass. TikTok and Instagram grids can be added when public video rows load.</p>'
    html = '<div class="grid">'
    for p in sorted(posts, key=lambda x: x["date"]):
        mult = p["views"] / med if med else 0
        badge = ""
        if p.get("breakthrough"):
            badge = '<span class="tag boost">Breakthrough · reach</span>'
        elif p.get("note"):
            badge = f'<span class="tag warn">{p["note"]}</span>'
        title = p.get("caption", p.get("shortcode", ""))[:48]
        html += f"""<a class="card" href="{ig_url(p['shortcode'], 'reel')}" target="_blank" rel="noopener">
      <div class="meta" style="padding:14px">
        <p class="place">{title or p['date']}</p>
        <p class="who">@{handle} · {p['date']} · {fmt(p['views'])} views · {mult:.2f}× median</p>
        <ul class="counts"><li><b>{p['likes']}</b> likes</li><li><b>{p['comments']}</b> comments</li></ul>
        {badge}
      </div></a>"""
    html += "</div>"
    return html


def all_collected_reels() -> list[dict]:
    rows: list[dict] = []
    for p in reel_posts_for("funboy"):
        rows.append({**p, "account": "funboy"})
    for p in reel_posts_for("bigshinyballs"):
        rows.append({**p, "account": "bigshinyballs", "caption": p.get("shortcode", ""), "type": "reel"})
    return rows


def post_cards(posts: list[dict], reels_only: bool = False) -> str:
    html = '<div class="grid">'
    for p in posts:
        if reels_only and not p.get("views"):
            continue
        cover = cover_path(p["shortcode"])
        typ = "Reel" if p.get("views") else "Photo"
        eng = ""
        if p.get("views"):
            er = (p["likes"] + p["comments"]) / p["views"] * 100
            eng = f'<span class="eng">{er:.2f}%</span>'
        badge = ""
        if p.get("breakthrough"):
            badge = '<span class="tag boost">Breakthrough · reach</span>'
        elif p.get("note"):
            badge = f'<span class="tag warn">{p["note"]}</span>'
        views_line = f"<li><b>{fmt(p['views'])}</b> views</li>" if p.get("views") else ""
        html += f"""<a class="card" href="{ig_url(p['shortcode'], p['type'])}" target="_blank" rel="noopener">
      <div class="thumb"><img src="{cover}" alt="" loading="lazy" /></div>
      <div class="meta">
        <p class="place">{p['caption'][:48]}</p>
        <p class="who">@funboy · {p['date']} · {typ}</p>
        <div class="stats"><span><b>{fmt(p['likes'])}</b> likes</span>{eng}</div>
        <ul class="counts">{views_line}<li><b>{p['comments']}</b> comments</li></ul>
        {badge}
      </div>
    </a>"""
    html += "</div>"
    return html


def histogram_svg(values: list[int], label: str) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    bins = 6
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - lo) / max(hi - lo, 1) * bins))
        counts[idx] += 1
    max_c = max(counts) or 1
    bars = ""
    w = 560 / bins
    for i, c in enumerate(counts):
        h = 120 * c / max_c
        x = 40 + i * w
        bars += f'<rect x="{x:.1f}" y="{140 - h:.1f}" width="{w - 8:.1f}" height="{h:.1f}" fill="#9dc9f5" stroke="#000" stroke-width="1"/>'
        bars += f'<text x="{x + w/2:.1f}" y="158" text-anchor="middle" font-size="10" fill="#666">{i+1}</text>'
    return f"""<div class="chart-wrap"><p class="who">{label}</p>
<svg viewBox="0 0 600 170" role="img" aria-label="{label}">
  <line x1="36" y1="140" x2="580" y2="140" stroke="#000" stroke-width="2"/>
  {bars}
</svg></div>"""


def normal_curve_svg(values: list[float], center: float, lo: float, hi: float, subject: float) -> str:
    logs = [math.log(v) for v in values if v > 0]
    mu = sum(logs) / len(logs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in logs) / len(logs))
    pts = []
    for i in range(80):
        x = mu - 3 * sd + (6 * sd * i / 79)
        y = math.exp(-0.5 * ((x - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
        pts.append((x, y))
    max_y = max(p[1] for p in pts) or 1
    path = []
    for i, (x, y) in enumerate(pts):
        sx = 40 + (x - (mu - 3 * sd)) / (6 * sd) * 520
        sy = 150 - (y / max_y) * 110
        path.append(f"{'M' if i == 0 else 'L'}{sx:.1f},{sy:.1f}")
    sub_x = 40 + (math.log(subject) - (mu - 3 * sd)) / (6 * sd) * 520
    return f"""<div class="chart-wrap"><p class="who">Normal curve on log(view count). Center {center:,.0f} · 1σ band {lo:,.0f} – {hi:,.0f}</p>
<svg viewBox="0 0 600 170" role="img" aria-label="Log-normal view curve">
  <path d="{' '.join(path)}" fill="none" stroke="#000" stroke-width="2"/>
  <line x1="{sub_x:.1f}" y1="30" x2="{sub_x:.1f}" y2="150" stroke="#c73333" stroke-width="2" stroke-dasharray="4 3"/>
  <text x="{sub_x:.1f}" y="22" text-anchor="middle" font-size="10" fill="#c73333">subject</text>
</svg></div>"""


def build_october() -> str:
    reels = [p for p in FUN_POSTS if p.get("views")]
    total_likes = sum(p["likes"] for p in FUN_POSTS)
    total_comments = sum(p["comments"] for p in FUN_POSTS)
    total_views = sum(p["views"] for p in reels)
    like_delta = pct_change(total_likes, SEP_IG_LIKES)
    outlier = max(reels, key=lambda p: p["views"])
    weeks = week_buckets(FUN_POSTS)
    max_v = max(w["views"] for w in weeks) or 1
    bars = ""
    for w in weeks:
        h = int(120 * w["views"] / max_v)
        bars += f'<div class="bar-col"><b>{fmt(w["views"])}</b><i style="height:{h}px"></i>{w["label"]}</div>'

    w_rows = ""
    for w in weeks:
        w_rows += f"<tr><td>{w['label']}</td><td>{w['posts']}</td><td>{fmt(w['likes'])}</td><td>{fmt(w['comments'])}</td><td>{fmt(w['views'])}</td></tr>"

    body = f"""<p class="eyebrow">Current report · public social</p>
<h1>October report</h1>
<div class="kpi-row">
  <div class="kpi"><b>12</b><span>Instagram posts (11 reels + 1 photo)</span></div>
  <div class="kpi"><b>{fmt(total_likes)}</b><span>Instagram likes</span></div>
  <div class="kpi"><b>{fmt(total_comments)}</b><span>Instagram comments</span></div>
  <div class="kpi"><b>{fmt(total_views)}</b><span>Public reel views</span></div>
  <div class="kpi"><b>{total_likes/len(FUN_POSTS):.0f}</b><span>Avg likes / post</span></div>
  <div class="kpi"><b>46.1K</b><span>TikTok followers (grid did not load)</span></div>
</div>
<div class="section"><h2>Month over month</h2>
<p class="lead">Instagram likes vs September recap tile. Views not compared — September used Insights.</p>
<table class="data">
<tr><th></th><th>Oct 10–Nov 1 (public)</th><th>September recap</th><th>Result</th></tr>
<tr><td>Instagram likes</td><td><span class="mark-circle">{fmt(total_likes)}</span></td><td>{fmt(SEP_IG_LIKES)}</td><td class="worse">{like_delta} vs September</td></tr>
<tr><td>Instagram posts</td><td>12</td><td>17</td><td>—</td></tr>
<tr><td>Days covered</td><td>23</td><td>30</td><td>—</td></tr>
</table></div>
<div class="section"><h2>Week over week</h2>
<p class="who">Public reel views by week · Instagram only</p>
<div class="bar-chart">{bars}</div>
<table class="data"><tr><th>Week</th><th>Posts</th><th>Likes</th><th>Comments</th><th>Reel views</th></tr>{w_rows}</table></div>
<div class="section"><h2>Every post</h2>
<p class="who">Oldest to newest on the first public grid · tap opens Instagram</p>
{post_cards(FUN_POSTS)}
</div>
<div class="section"><h2>Engagement detail</h2>
<p class="who">Reels only · sorted by (likes + comments) / views · outlier view count marked</p>
<table class="data"><tr><th>Date</th><th>Caption</th><th>Likes</th><th>Views</th><th>Comments</th><th>Engagement</th></tr>"""
    for p in sorted(reels, key=lambda x: (x["likes"] + x["comments"]) / x["views"], reverse=True):
        er = (p["likes"] + p["comments"]) / p["views"] * 100
        v = fmt(p["views"])
        if p["shortcode"] == outlier["shortcode"]:
            v = f'<span class="mark-circle">{v}</span>'
        body += f"<tr><td>{p['date']}</td><td>{p['caption']}</td><td>{p['likes']}</td><td>{v}</td><td>{p['comments']}</td><td>{er:.2f}%</td></tr>"
    body += f"""</table></div>
<p class="foot">Layout follows the Dream Aspect la-reels report chrome ({LA_REELS_SOURCE}). Data is public-only for this window.</p>"""
    return page_shell("FUNBOY · October report (public)", "october", body)


def build_benchmarks() -> str:
    pool = all_collected_reels()
    views = [float(p["views"]) for p in pool]
    avg = sum(views) / len(views)
    sd = pop_std(views)
    med = median(views)
    subject = min(pool, key=lambda p: abs(p["views"] - med))
    center, lo, hi = log_normal_band(views)
    ranked = sorted(pool, key=lambda p: p["views"], reverse=True)
    rows = ""
    for i, p in enumerate(ranked, 1):
        er = (p["likes"] + p["comments"]) / p["views"] * 100
        cap = (p.get("caption") or p["shortcode"])[:36]
        rows += f"<tr><td>{i:02d}</td><td>@{p['account']}</td><td>{p['date']}</td><td>{fmt(p['views'])}</td><td>{er:.2f}%</td><td>{cap}</td></tr>"

    body = f"""<p class="eyebrow">Benchmarks · MULE-14 math</p>
<h1>View benchmark</h1>
<p class="lead">Population statistics on every public reel we collected — FUNBOY October window plus competitor grids ({COLLECTED}). Engagement is (likes + comments) / views.</p>
{competitor_shelf_cards()}
<div class="section"><h2>Combined pool</h2>
<table class="data">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Reels in pool</td><td>{len(pool)} (@funboy {len(reel_posts_for('funboy'))} · @bigshinyballs {len(reel_posts_for('bigshinyballs'))})</td></tr>
<tr><td>Sum of views</td><td>{fmt(int(sum(views)))}</td></tr>
<tr><td>Average views</td><td>{avg:,.0f}</td></tr>
<tr><td>Median views (subject)</td><td>{fmt(int(med))} · {subject['date']} · @{subject['account']}</td></tr>
<tr><td>Population std. dev.</td><td>{sd:,.0f}</td></tr>
<tr><td>Average + 1σ</td><td>{avg + sd:,.0f}</td></tr>
<tr><td>Subject vs average</td><td>{fmt(int(abs(avg - subject['views'])))} {'below' if subject['views'] < avg else 'above'} ({abs((avg-subject['views'])/avg*100):.1f}%)</td></tr>
<tr><td>Subject engagement</td><td>{(subject['likes']+subject['comments'])/subject['views']*100:.2f}% vs pool {(sum((p['likes']+p['comments'])/p['views'] for p in pool)/len(pool)*100):.2f}%</td></tr>
</table>
{histogram_svg([int(v) for v in views], "View count histogram · combined collected reels")}
{normal_curve_svg(views, center, lo, hi, float(subject["views"]))}
</div>
<div class="section"><h2>Ranked reels</h2>
<table class="data"><tr><th>Rank</th><th>Account</th><th>Date</th><th>Views</th><th>Engagement</th><th>Caption</th></tr>{rows}</table></div>
<p class="foot">Benchmark method from MULE-14 · Market Reel Report. Layout from la-reels ({LA_REELS_SOURCE}). Archive month recaps (Aug/Sep) stay on All reports — not merged into this pool yet.</p>"""
    return page_shell("FUNBOY · Benchmarks", "benchmarks", body)


def build_competitor() -> str:
    bsb_posts = reel_posts_for("bigshinyballs")
    bsb_med = median([p["views"] for p in bsb_posts]) if bsb_posts else 0
    comp_blocks = ""
    for c in COMPETITOR_SHELF:
        if c.get("brand"):
            continue
        posts = reel_posts_for(c["handle"])
        med = median([p["views"] for p in posts]) if posts else 0.0
        comp_blocks += f"""<div class="comp-block">
<h3>@{c['handle']} · {c['label']}</h3>
<p class="who">Instagram public reels · TikTok: {c['tiktok']}</p>
{competitor_ig_cards(posts, c['handle'], med or bsb_med or 1.0)}
</div>"""

    body = f"""<p class="eyebrow">Competitor research · mold 1</p>
<h1>Competitor research</h1>
<p class="lead">Inflatable / pool decor set — public Instagram (and TikTok where collected). FUNBOY October posts live on the main report; this page is competitors only.</p>
<div class="section"><h2>01 · Competitor shelf</h2>
{competitor_shelf_cards()}
</div>
<div class="section"><h2>02 · Signals</h2>
<div class="reach-grid">
<div><b>1</b><span>@bigshinyballs reach breakthrough (Oct 19)</span></div>
<div><b>{fmt(BSB_POSTS_WINDOW[-1]['views'])}</b><span>BSB Oct 29 reach spike · low engagement</span></div>
<div><b>2</b><span>Named shelf accounts without reel rows: @poolcandy, @bigmouthinc</span></div>
</div></div>
<div class="section"><h2>03 · Competitor content</h2>
<p class="who">Instagram reels in window · TikTok rows when the logged-out grid loads</p>
{comp_blocks}
<p class="who" style="margin-top:16px">@bigshinyballs pinned outside window: {BSB_PINNED['date']} reel ({fmt(BSB_PINNED['views'])} public views) — excluded from Oct medians.</p>
</div>
<p class="foot">Competitor shelf follows DA Portal competitor-watch mold. Layout from la-reels ({LA_REELS_SOURCE}).</p>"""
    return page_shell("FUNBOY · Competitor research", "competitor", body)


def build_all_reports() -> str:
    body = """<p class="eyebrow">Archive · mold 2</p>
<h1>All reports</h1>
<p class="lead">Earlier full-month recaps. Legacy brown styling on August and September; active window is the October public report.</p>
<div class="archive-list mold2">
  <a class="mold2-card" href="september-2026-recap.html"><span><strong>September 2026</strong><br><span class="who">Full month · Instagram Insights + TikTok</span></span><span class="pill">Archive</span></a>
  <a class="mold2-card" href="august-2026-recap.html"><span><strong>August 2026</strong><br><span class="who">Full month · Instagram + TikTok</span></span><span class="pill">Archive</span></a>
</div>
<p class="foot">Card edge glow matches the Dream Aspect pricing selector animation. Return to the <a href="index.html">October report</a> for the active public-only window.</p>"""
    return page_shell("FUNBOY · All reports", "all", body)


def patch_archives() -> None:
    shell = nav("all")
    note = """<link rel="stylesheet" href="portal-styles.css" />
<style>.report-nav{display:none!important}</style>
<p class="archive-note">Archived report — not the current window. Active report: <a href="index.html">October public report</a> · <a href="all-reports.html">All reports</a></p>"""
    for name in ("august-2026-recap.html", "september-2026-recap.html"):
        path = os.path.join(ROOT, name)
        text = open(path, encoding="utf-8").read()
        text = re.sub(r"<nav class=\"report-nav\".*?</nav>", "", text, count=1, flags=re.S)
        if "portal-styles.css" not in text:
            text = text.replace("<body>", f"<body>\n{shell}\n{note}", 1)
        open(path, "w", encoding="utf-8").write(text)


def sync_funboy_path() -> None:
    dst = os.path.join(ROOT, "funboy-path", "public")
    if not os.path.isdir(dst):
        return
    import shutil

    for fn in (
        "index.html",
        "benchmarks.html",
        "competitor-research.html",
        "all-reports.html",
        "portal-styles.css",
        "august-2026-recap.html",
        "september-2026-recap.html",
    ):
        shutil.copy2(os.path.join(ROOT, fn), os.path.join(dst, fn))
    shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(dst, "fonts"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "covers"), os.path.join(dst, "covers"), dirs_exist_ok=True)


def main() -> None:
    open(os.path.join(ROOT, "portal-styles.css"), "w", encoding="utf-8").write(CSS)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(build_october())
    open(os.path.join(ROOT, "benchmarks.html"), "w", encoding="utf-8").write(build_benchmarks())
    open(os.path.join(ROOT, "competitor-research.html"), "w", encoding="utf-8").write(build_competitor())
    open(os.path.join(ROOT, "all-reports.html"), "w", encoding="utf-8").write(build_all_reports())
    patch_archives()
    for obsolete in ("october-public-2026-recap.html", "competitor-watch.html"):
        p = os.path.join(ROOT, obsolete)
        if os.path.isfile(p):
            os.remove(p)
    sync_funboy_path()
    print("Built la-reels layout portal pages.")


if __name__ == "__main__":
    main()
