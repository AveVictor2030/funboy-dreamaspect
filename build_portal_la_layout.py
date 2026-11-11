#!/usr/bin/env python3
"""Build Funboy portal pages using the la-reels layout (Dream Aspect report chrome)."""
from __future__ import annotations

import json
import math
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR_DATA_PATH = os.path.join(ROOT, "data", "funboy-ig-year-oct2025-oct2026.json")

# Reuse collected public data from the prior generator.
from build_public_report import (  # noqa: E402
    BSB_POSTS_WINDOW,
    BSB_PINNED,
    COLLECTED,
    FUN_IG_MONTHLY,
    FUN_IG_MONTHLY_PRIOR,
    FUN_IG_YEAR_LABEL,
    FUN_IG_YEAR_SOURCE,
    FUN_POSTS,
    SEP_IG_LIKES,
    WINDOW_LABEL,
    fmt,
    fun_ig_year_totals,
    ig_url,
    log_normal_band,
    median,
    month_label,
    pop_std,
    save_bsb_covers,
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
.grid-dense { grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; }
.grid-dense .card { flex-direction: column; }
.grid-dense .thumb {
  aspect-ratio: 1;
  max-height: 56px;
  height: 56px;
  overflow: hidden;
}
.grid-dense .thumb img {
  width: 100%;
  height: 56px;
  max-height: 56px;
  object-fit: cover;
}
.grid-dense .meta { padding: 6px 8px 8px; }
.grid-dense .place { font-size: 11px; margin: 0 0 2px; line-height: 1.25; }
.grid-dense .who { font-size: 10px; margin: 0 0 4px; }
.grid-dense .stats { font-size: 11px; }
.grid-dense .stats b { font-size: 11px; }
.grid-dense .eng { font-size: 10px; padding: 1px 4px; }
.grid-dense .counts, .grid-dense .tag { display: none; }
.grid-year { grid-template-columns: repeat(auto-fill, minmax(156px, 1fr)); gap: 10px; }
.grid-year .card { border-radius: 4px; }
.grid-year .year-thumb {
  height: 72px;
  max-height: 72px;
  aspect-ratio: auto;
  background: linear-gradient(135deg, var(--fog) 0%, var(--ice) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}
.grid-year .year-thumb img {
  width: 100%;
  height: 72px;
  max-height: 72px;
  object-fit: cover;
  display: block;
  position: absolute;
  inset: 0;
}
.grid-year .year-thumb-ph span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  position: relative;
  z-index: 1;
}
.grid-year .meta { padding: 8px 9px 10px; }
.grid-year .place { font-size: 12px; margin: 0 0 3px; line-height: 1.25; }
.grid-year .who { font-size: 10px; margin: 0 0 6px; }
.grid-year .stats { font-size: 11px; }
.grid-year .stats b { font-size: 12px; }
.grid-year .counts { font-size: 10px; margin-top: 4px; }
.grid-year .eng { font-size: 10px; padding: 1px 5px; }
.grid-year .card.is-tiktok { border-color: color-mix(in srgb, var(--black) 72%, transparent); }
.grid-year .platform-tt {
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--black);
  color: var(--white);
  padding: 1px 5px;
  margin-bottom: 4px;
}
.subplatform { margin: 18px 0 8px; font-size: 13px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.year-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  align-items: flex-end;
  margin: 0 0 20px;
  padding: 14px 16px;
  background: var(--ice);
  border: 1px solid color-mix(in srgb, var(--black) 8%, transparent);
  border-radius: 6px;
}
.year-filters .filter-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}
.year-filters .filter-group { min-width: 0; }
.filter-switch,
.filter-quarters {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.year-filters .filter-btn {
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border: 1px solid color-mix(in srgb, var(--black) 18%, transparent);
  border-radius: 999px;
  background: var(--white);
  color: var(--black);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.year-filters .filter-btn:hover { border-color: var(--black); }
.year-filters .filter-btn.is-active {
  background: var(--black);
  border-color: var(--black);
  color: var(--white);
}
.year-filter-card[hidden],
.year-quarter[hidden],
.year-subplatform[hidden],
.year-filter-note[hidden] { display: none !important; }
.year-timeline {
  margin: 0 0 24px;
  padding: 16px 18px 14px;
  background: var(--white);
  border: 1px solid color-mix(in srgb, var(--black) 10%, transparent);
  border-radius: 6px;
}
.year-timeline h2 { margin: 0 0 4px; font-size: 18px; }
.year-timeline .tl-head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 10px 16px; margin-bottom: 12px; }
.year-timeline .tl-metric-switch { display: inline-flex; flex-wrap: wrap; gap: 6px; }
.year-timeline .tl-chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  min-height: 168px;
  padding: 8px 4px 0;
  border-bottom: 2px solid var(--black);
  overflow-x: auto;
}
.year-timeline .tl-col {
  flex: 1 0 54px;
  max-width: 72px;
  text-align: center;
  font-size: 10px;
  color: var(--muted);
}
.year-timeline .tl-pair {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
  height: 140px;
  margin-bottom: 6px;
}
.year-timeline .tl-bar {
  display: block;
  width: 18px;
  min-height: 3px;
  border-radius: 3px 3px 0 0;
  transition: height 0.2s ease;
}
.year-timeline .tl-bar.tl-prior {
  background: color-mix(in srgb, var(--muted) 35%, var(--fog));
  border: 1px solid color-mix(in srgb, var(--black) 12%, transparent);
}
.year-timeline .tl-bar.tl-cur {
  background: linear-gradient(180deg, #b8dcfa 0%, #6eb5ef 100%);
  border: 1px solid #2a7fc7;
}
.year-timeline .tl-bar.tl-cur.tt-only {
  background: linear-gradient(180deg, #e8e8e8 0%, #1a1a1a 55%);
  border-color: var(--black);
}
.year-timeline .tl-lbl { display: block; font-weight: 700; color: var(--black); font-size: 10px; }
.year-timeline .tl-sub { display: block; font-size: 9px; line-height: 1.2; margin-top: 2px; }
.year-timeline .tl-val { display: block; font-size: 9px; font-variant-numeric: tabular-nums; color: var(--black); margin-top: 3px; }
.year-timeline .tl-legend { display: flex; flex-wrap: wrap; gap: 12px 20px; margin-top: 10px; font-size: 11px; color: var(--muted); }
.year-timeline .tl-legend span { display: inline-flex; align-items: center; gap: 6px; }
.year-timeline .tl-swatch { width: 12px; height: 12px; border-radius: 2px; }
.year-timeline .tl-swatch.prior { background: color-mix(in srgb, var(--muted) 35%, var(--fog)); border: 1px solid color-mix(in srgb, var(--black) 12%, transparent); }
.year-timeline .tl-swatch.cur { background: linear-gradient(180deg, #b8dcfa 0%, #6eb5ef 100%); border: 1px solid #2a7fc7; }
.quarter-block { margin-top: 28px; }
.quarter-block h3 { font-family: Nohemi, sans-serif; font-size: 20px; margin: 0 0 10px; font-weight: 500; }
.ads-waiting {
  border: 1px dashed var(--gray);
  border-radius: 6px;
  padding: 22px 20px;
  background: var(--fog);
  max-width: 40rem;
}
.ads-waiting .eyebrow { margin-bottom: 6px; }
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
.chart-wrap { margin: 20px 0; max-width: 680px; }
.chart-wrap .chart-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px 16px; margin-bottom: 8px; }
.chart-wrap .chart-head h3 { font-family: Nohemi, sans-serif; font-size: 15px; font-weight: 500; margin: 0; letter-spacing: -0.01em; }
.chart-wrap .chart-meta { font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }
.chart-wrap svg { width: 100%; height: auto; display: block; border: 1px solid var(--gray); border-radius: 6px; background: var(--white); }
.chart-wrap .chart-caption { font-size: 11px; color: var(--muted); margin: 8px 0 0; line-height: 1.45; max-width: 42rem; }
.chart-wrap .chart-legend { display: flex; flex-wrap: wrap; gap: 10px 18px; margin-top: 10px; font-size: 11px; color: var(--muted); }
.chart-wrap .chart-legend span { display: inline-flex; align-items: center; gap: 6px; }
.chart-wrap .swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.chart-wrap .swatch.bar { background: linear-gradient(180deg, #b8dcfa 0%, #6eb5ef 100%); border: 1px solid #2a7fc7; }
.chart-wrap .swatch.curve { background: none; border: 2px solid var(--black); border-radius: 0; width: 14px; height: 0; }
.chart-wrap .swatch.band { background: rgba(110, 181, 239, 0.22); border: 1px solid rgba(42, 127, 199, 0.35); }
.chart-wrap .swatch.subject { border-top: 2px dashed var(--mark); height: 0; width: 14px; background: none; border-radius: 0; }
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
.comp-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 160px)); gap: 8px; margin: 0 0 20px; justify-content: start; }
.comp-card {
  border: 1px solid var(--gray);
  border-radius: 4px;
  padding: 8px 10px 10px;
  background: var(--fog);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}
.comp-card.is-brand { border-color: var(--black); background: var(--white); }
.comp-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 160px)); gap: 8px; margin: 0 0 20px; justify-content: start; max-width: 100%; }
.comp-card { overflow: hidden; max-width: 160px; }
.comp-grid--no-covers .comp-card { max-width: 148px; padding-top: 10px; }
.comp-cover-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  margin: 0;
  height: 32px;
  max-height: 32px;
  overflow: hidden;
}
.comp-cover-row > a {
  display: block;
  height: 32px;
  max-height: 32px;
  overflow: hidden;
  min-width: 0;
}
.comp-cover-row img {
  width: 100%;
  height: 32px !important;
  max-height: 32px !important;
  object-fit: cover;
  object-position: center;
  border-radius: 2px;
  display: block;
  border: 1px solid var(--gray);
}
.comp-cover-row a.comp-cover-ph {
  height: 32px;
  max-height: 32px;
  border: 1px solid var(--gray);
  border-radius: 2px;
}
.comp-card .handle { font-size: 14px; margin: 0; }
.comp-card .role { font-size: 9px; margin: 0; }
.comp-kpis { grid-template-columns: repeat(2, 1fr); gap: 4px; margin: 0; }
.comp-kpis div { padding: 4px 6px; }
.comp-kpis b { font-size: 13px; }
.comp-kpis span { font-size: 9px; }
.comp-cover-row--empty { height: 32px; max-height: 32px; font-size: 10px; }
.comp-cover-ph { font-size: 10px; }
.comp-kpis { display: grid; }
.comp-kpis div { border: 1px solid var(--gray); border-radius: 2px; background: var(--white); }
.comp-kpis b { display: block; font-family: Nohemi, sans-serif; letter-spacing: -0.02em; }
.comp-kpis span { color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.comp-card .link-ig { font-weight: 700; text-decoration: none; border-bottom: 1px solid var(--black); }
.stat-strip { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 6px; margin: 0 0 18px; }
.stat-strip .kpi { padding: 8px 10px; }
.stat-strip .kpi b { font-size: 16px; }
.stat-strip .kpi span { font-size: 10px; }
.volume-note { font-size: 12px; color: var(--muted); margin: 0 0 10px; max-width: 44rem; line-height: 1.45; }
.volume-prior { margin-top: 14px; }
.volume-prior summary { cursor: pointer; font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.volume-prior .data { opacity: 0.92; }
.volume-chart { display: flex; align-items: flex-end; gap: 6px; height: 120px; margin: 12px 0 16px; padding-bottom: 2px; border-bottom: 2px solid var(--black); max-width: 680px; }
.volume-col { flex: 1; min-width: 0; text-align: center; font-size: 9px; color: var(--muted); }
.volume-col b { display: block; font-size: 10px; color: var(--black); margin-bottom: 4px; font-variant-numeric: tabular-nums; }
.volume-col i { display: block; width: 100%; border-radius: 3px 3px 0 0; min-height: 2px; }
.volume-col i.reel { background: var(--blue); }
.volume-col i.other { background: var(--gray); margin-top: 2px; }
.comp-block { margin-top: 28px; }
.comp-block h3 { font-family: Nohemi, sans-serif; font-size: 20px; margin: 0 0 10px; }
.comp-profile {
  border: 1px solid var(--gray);
  border-radius: 6px;
  padding: 14px 16px 16px;
  margin: 0 0 18px;
  background: var(--white);
}
.comp-profile.is-empty { background: var(--fog); }
.comp-profile-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px 16px; margin-bottom: 10px; }
.comp-profile-head h3 { font-family: Nohemi, sans-serif; font-size: 18px; margin: 0; font-weight: 500; }
.comp-profile-head .who { margin: 0; }
.comp-metric-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; margin: 0 0 12px; }
.comp-metric-row div { border: 1px solid var(--gray); border-radius: 4px; padding: 6px 8px; background: var(--fog); font-size: 11px; }
.comp-metric-row b { display: block; font-family: Nohemi, sans-serif; font-size: 15px; margin-bottom: 2px; }
.comp-metric-row span { color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: 0.05em; }
.comp-insights { list-style: none; margin: 0 0 12px; padding: 0; display: grid; gap: 8px; }
.comp-insights li { font-size: 13px; line-height: 1.4; padding: 8px 10px; background: var(--ice); border-radius: 4px; border-left: 3px solid var(--blue); }
.comp-insights li.warn { border-left-color: var(--mark); background: #fff8f8; }
.comp-reel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 10px; }
.comp-reel-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--gray);
  border-radius: 4px;
  text-decoration: none;
  color: inherit;
  overflow: hidden;
  background: var(--white);
}
.comp-reel-card:hover { border-color: var(--black); }
.comp-reel-thumb {
  height: 52px;
  background: linear-gradient(135deg, var(--fog) 0%, var(--ice) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  overflow: hidden;
  position: relative;
}
.comp-reel-thumb img { width: 100%; height: 100%; object-fit: cover; position: absolute; inset: 0; }
.comp-reel-thumb .comp-reel-date { font-size: 10px; font-weight: 700; letter-spacing: 0.04em; position: relative; z-index: 1; }
.comp-reel-thumb .comp-reel-views { font-size: 12px; font-family: Nohemi, sans-serif; position: relative; z-index: 1; }
.comp-reel-body { padding: 8px 10px 10px; }
.comp-reel-body .place { font-size: 12px; margin: 0 0 4px; line-height: 1.25; }
.comp-reel-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 8px; margin-top: 6px; font-size: 11px; }
.comp-reel-metrics div span { display: block; color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: 0.04em; }
.comp-reel-metrics b { font-size: 12px; font-variant-numeric: tabular-nums; }
.comp-view-bar { height: 4px; background: var(--fog); border-radius: 2px; margin-top: 8px; overflow: hidden; }
.comp-view-bar i { display: block; height: 100%; background: var(--blue); max-width: 100%; }
.comp-view-bar i.hot { background: var(--mark); }
.comp-compare { font-size: 12px; color: var(--muted); margin: 0 0 10px; line-height: 1.45; }
@media (max-width: 680px) { .comp-metric-row { grid-template-columns: repeat(2, 1fr); } }
.comp-watch-table { font-size: 12px; }
.comp-watch-table td.num, .comp-watch-table th.num { text-align: right; font-variant-numeric: tabular-nums; }
.comp-watch-table tr.is-subject { background: var(--ice); }
.comp-watch-table tr.is-empty { color: var(--muted); }
.comp-watch-callout { font-size: 12px; color: var(--muted); margin: 10px 0 0; line-height: 1.45; }
@keyframes edgeGlowOneOff { 0%, 100% { outline: 2px solid var(--blue); outline-offset: 3px; } 50% { outline: 2px solid var(--black); outline-offset: 3px; } }
.mold2-card { animation: 2.8s ease-in-out infinite edgeGlowOneOff; border-radius: 4px; }
.archive-list.mold2 { gap: 14px; margin-top: 20px; }
.archive-list.mold2 a { transition: border-color 0.2s ease, transform 0.2s ease; }
.archive-list.mold2 a:hover { border-color: var(--black); transform: translateY(-2px); }
.empty-shelf { border: 1px dashed var(--gray); border-radius: 4px; padding: 18px; color: var(--muted); font-size: 14px; margin: 0 0 16px; }
@media (prefers-reduced-motion: reduce) { .mold2-card { animation: none; } }
@media (max-width: 980px) { .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .grid-dense { grid-template-columns: repeat(4, minmax(0, 1fr)); } .kpi-row { grid-template-columns: repeat(2, 1fr); } .comp-grid { grid-template-columns: repeat(2, minmax(0, 160px)); } .stat-strip { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 680px) {
  .chrome, main, .archive-note { padding-left: 16px; padding-right: 16px; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .kpi-row, .reach-grid, .stat-strip { grid-template-columns: 1fr; }
  .comp-grid { grid-template-columns: 1fr; }
}
"""


def nav(current: str) -> str:
    items = [
        ("index.html", "Year report", "year"),
        ("benchmarks.html", "Benchmarks", "benchmarks"),
        ("competitor-watch.html", "Competitor watch", "competitor"),
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


def cover_path(shortcode: str, handle: str = "funboy") -> str:
    if handle == "bigshinyballs":
        return f"covers/public-oct-2026-bsb/{shortcode}.jpg"
    return f"covers/public-oct-2026/{shortcode}.jpg"


def engagement_rate(post: dict) -> float:
    return (post["likes"] + post["comments"]) / post["views"] * 100


def funboy_window_stats() -> dict[str, float]:
    posts = reel_posts_for("funboy")
    views = [p["views"] for p in posts]
    med = median(views)
    followers = next(c["followers"] for c in COMPETITOR_SHELF if c["handle"] == "funboy")
    return {
        "median_views": med,
        "avg_engagement": sum(engagement_rate(p) for p in posts) / len(posts),
        "views_per_follower": med / followers * 100,
        "reels": len(posts),
    }


def analyze_competitor(posts: list[dict], followers: int, *, window_label: str) -> dict | None:
    if not posts:
        return None
    from datetime import date as date_cls

    views = [p["views"] for p in posts]
    med = median(views)
    avg = sum(views) / len(views)
    eng = [engagement_rate(p) for p in posts]
    dates = sorted(p["date"] for p in posts)
    d0 = date_cls.fromisoformat(dates[0])
    d1 = date_cls.fromisoformat(dates[-1])
    span_days = max(1, (d1 - d0).days + 1)
    breakthroughs = [p for p in posts if p.get("breakthrough")]
    spikes = [p for p in posts if p.get("note")]
    top = max(posts, key=lambda p: p["views"])
    return {
        "posts": len(posts),
        "median_views": med,
        "avg_views": avg,
        "total_views": sum(views),
        "avg_engagement": sum(eng) / len(eng),
        "median_engagement": median(eng),
        "views_per_follower": med / followers * 100,
        "reels_per_week": len(posts) / span_days * 7,
        "breakthroughs": breakthroughs,
        "spikes": spikes,
        "top": top,
        "window_label": window_label,
        "span_days": span_days,
    }


def competitor_insights(
    handle: str,
    label: str,
    stats: dict,
    fun: dict[str, float],
) -> list[tuple[str, bool]]:
    """Return (text, is_warning) insight bullets."""
    lines: list[tuple[str, bool]] = []
    med = stats["median_views"]
    fun_med = fun["median_views"]
    raw_ratio = med / fun_med if fun_med else 0
    share = stats["views_per_follower"]
    fun_share = fun["views_per_follower"]
    lines.append(
        (
            f"Median public views {fmt(int(med))} vs FUNBOY {fmt(int(fun_med))} "
            f"({raw_ratio:.0%} of FUNBOY raw median) in the same collection window.",
            False,
        )
    )
    if share > fun_share:
        lines.append(
            (
                f"Reach efficiency: {share:.1f}% of followers see the typical reel vs "
                f"FUNBOY {fun_share:.1f}% — smaller account, larger share of its own audience.",
                False,
            )
        )
    else:
        lines.append(
            (
                f"Reach efficiency: {share:.1f}% views/followers vs FUNBOY {fun_share:.1f}%.",
                False,
            )
        )
    eng_gap = stats["avg_engagement"] - fun["avg_engagement"]
    lines.append(
        (
            f"Engagement (likes + comments / views): {stats['avg_engagement']:.1f}% avg vs "
            f"FUNBOY {fun['avg_engagement']:.1f}% ({eng_gap:+.1f} pts).",
            stats["avg_engagement"] < fun["avg_engagement"] * 0.5,
        )
    )
    lines.append(
        (
            f"Posting pace {stats['reels_per_week']:.1f} reels/week over {stats['span_days']} days "
            f"({stats['posts']} reels, {fmt(int(stats['total_views']))} total public views).",
            False,
        )
    )
    if stats["breakthroughs"]:
        d = stats["breakthroughs"][0]["date"][5:].replace("-", "/")
        lines.append(
            (
                f"Reach breakthrough on {d}: {fmt(stats['breakthroughs'][0]['views'])} views "
                f"({stats['breakthroughs'][0]['views'] / med:.1f}× account median).",
                False,
            )
        )
    for sp in stats["spikes"]:
        er = engagement_rate(sp)
        lines.append(
            (
                f"View spike {sp['date'][5:].replace('-', '/')} — {fmt(sp['views'])} views "
                f"({sp['views'] / med:.1f}× median) but {er:.1f}% engagement; treat as reach-only.",
                True,
            )
        )
    return lines


def competitor_reel_card(post: dict, handle: str, med: float) -> str:
    mult = post["views"] / med if med else 0
    er = engagement_rate(post)
    bar_pct = min(100, mult / 10 * 100)
    bar_cls = "hot" if mult >= 3 else ""
    href = ig_url(post["shortcode"], "reel")
    rel_cover = cover_path(post["shortcode"], handle)
    cover_fs = os.path.join(ROOT, rel_cover)
    if os.path.isfile(cover_fs) and os.path.getsize(cover_fs) > 500:
        thumb = f'<div class="comp-reel-thumb"><img src="{rel_cover}" alt="" loading="lazy" /></div>'
    else:
        thumb = (
            f'<div class="comp-reel-thumb">'
            f'<span class="comp-reel-date">{post["date"][5:].replace("-", " · ")}</span>'
            f'<span class="comp-reel-views">{_chart_axis_num(post["views"])} views</span></div>'
        )
    badge = ""
    if post.get("breakthrough"):
        badge = '<span class="tag boost">Breakthrough</span>'
    elif post.get("note"):
        badge = '<span class="tag warn">Low engagement</span>'
    if post.get("caption"):
        title = post["caption"][:32]
    else:
        title = f"{month_label(post['date'][:7])} · {post['date'][5:]}"
    return f"""<a class="comp-reel-card" href="{href}" target="_blank" rel="noopener">
  {thumb}
  <div class="comp-reel-body">
    <p class="place">{title}</p>
    <div class="comp-reel-metrics">
      <div><span>Views</span><b>{fmt(post['views'])}</b></div>
      <div><span>× median</span><b>{mult:.1f}×</b></div>
      <div><span>Likes</span><b>{post['likes']}</b></div>
      <div><span>Engagement</span><b>{er:.1f}%</b></div>
    </div>
    <div class="comp-view-bar" title="{mult:.1f}× median views"><i class="{bar_cls}" style="width:{bar_pct:.0f}%"></i></div>
    {badge}
  </div>
</a>"""


def competitor_profile_block(c: dict, fun: dict[str, float]) -> str:
    handle = c["handle"]
    posts = reel_posts_for(handle)
    stats = analyze_competitor(posts, c["followers"], window_label=WINDOW_LABEL)
    head = f"""<div class="comp-profile-head">
  <h3>{c['label']}</h3>
  <p class="who">@{handle} · {c['tiktok']}</p>
</div>"""
    if not stats:
        return f"""<article class="comp-profile is-empty">
{head}
<p class="comp-compare">Profile on shelf ({fmt(c['followers'])} followers). No public reels collected in this pass — cannot compute median views, engagement, or breakthrough flags until the logged-out grid is pulled.</p>
<a class="link-ig" href="https://www.instagram.com/{handle}/" target="_blank" rel="noopener">Open Instagram</a>
</article>"""

    insights_html = ""
    for text, warn in competitor_insights(handle, c["label"], stats, fun):
        cls = " class=\"warn\"" if warn else ""
        insights_html += f"<li{cls}>{text}</li>"

    reels = "".join(
        competitor_reel_card(p, handle, stats["median_views"])
        for p in sorted(posts, key=lambda x: x["date"])
    )
    return f"""<article class="comp-profile">
{head}
<div class="comp-metric-row">
  <div><b>{fmt(c['followers'])}</b><span>Followers</span></div>
  <div><b>{fmt(int(stats['median_views']))}</b><span>Median views</span></div>
  <div><b>{stats['views_per_follower']:.1f}%</b><span>Views / followers</span></div>
  <div><b>{stats['avg_engagement']:.1f}%</b><span>Avg engagement</span></div>
</div>
<ul class="comp-insights">{insights_html}</ul>
<div class="comp-reel-grid">{reels}</div>
<a class="link-ig" href="https://www.instagram.com/{handle}/" target="_blank" rel="noopener" style="display:inline-block;margin-top:12px">Open Instagram</a>
</article>"""


def competitor_watch_table(fun: dict[str, float]) -> str:
    rows = ""
    for c in COMPETITOR_SHELF:
        posts = reel_posts_for(c["handle"])
        stats = analyze_competitor(posts, c["followers"], window_label=WINDOW_LABEL)
        is_subject = c.get("brand")
        cls = "is-subject" if is_subject else ("is-empty" if not stats else "")
        label = c["label"]
        if is_subject:
            label = f"{label} · subject"
        reels = str(stats["posts"]) if stats else "—"
        med = fmt(int(stats["median_views"])) if stats else "—"
        if is_subject and stats:
            med = f'<span class="mark-circle">{med}</span>'
        elif stats and fun["median_views"] > stats["median_views"]:
            med = f'<span class="mark-underline">{med}</span>'
        share = f"{stats['views_per_follower']:.1f}%" if stats else "—"
        if stats and not is_subject and stats["views_per_follower"] > fun["views_per_follower"]:
            share = f'<span class="mark-circle">{share}</span>'
        eng = f"{stats['avg_engagement']:.1f}%" if stats else "—"
        brk = str(len(stats["breakthroughs"])) if stats else "—"
        rows += (
            f"<tr class=\"{cls}\"><td>@{c['handle']}<br><span class=\"who\">{label}</span></td>"
            f"<td class=\"num\">{fmt(c['followers'])}</td><td class=\"num\">{reels}</td>"
            f"<td class=\"num\">{med}</td><td class=\"num\">{share}</td>"
            f"<td class=\"num\">{eng}</td><td class=\"num\">{brk}</td></tr>"
        )
    return f"""<table class="data comp-watch-table">
<tr><th>Account</th><th class="num">Followers</th><th class="num">Reels</th><th class="num">Median views</th><th class="num">Views ÷ followers</th><th class="num">Avg engagement</th><th class="num">Breakthroughs</th></tr>
{rows}
</table>
<p class="comp-watch-callout">Circle = higher views÷followers than FUNBOY or FUNBOY median (subject). Underline = median below FUNBOY raw median. Window: {WINDOW_LABEL} · public Instagram only.</p>"""


def rules_block() -> str:
    return ""


def reel_posts_for(handle: str) -> list[dict]:
    if handle == "funboy":
        return [p for p in FUN_POSTS if p.get("views")]
    if handle == "bigshinyballs":
        return list(BSB_POSTS_WINDOW)
    return []


def cover_mosaic(posts: list[dict], handle: str, limit: int = 3) -> str:
    if not posts:
        return f'<div class="comp-cover-row comp-cover-row--empty">No public reels yet</div>'
    cells = ""
    for p in sorted(posts, key=lambda x: x["date"], reverse=True)[:limit]:
        href = ig_url(p["shortcode"], "reel")
        if handle == "funboy":
            src = cover_path(p["shortcode"])
            cells += (
                f'<a href="{href}" target="_blank" rel="noopener">'
                f'<img src="{src}" alt="" width="48" height="32" loading="lazy" decoding="async" /></a>'
            )
        else:
            cells += f'<a class="comp-cover-ph" href="{href}" target="_blank" rel="noopener">{p["date"][5:]}</a>'
    return (
        '<div class="comp-cover-row" style="height:32px;max-height:32px;overflow:hidden;'
        'display:grid;grid-template-columns:repeat(3,1fr);gap:3px">'
        f"{cells}</div>"
    )


def pool_reel_grid(pool: list[dict], limit: int = 8) -> str:
    html = '<div class="grid grid-dense">'
    for p in sorted(pool, key=lambda x: x["views"], reverse=True)[:limit]:
        handle = p["account"]
        href = ig_url(p["shortcode"], p.get("type", "reel"))
        er = (p["likes"] + p["comments"]) / p["views"] * 100
        if handle == "funboy":
            thumb = f'<div class="thumb"><img src="{cover_path(p["shortcode"])}" alt="" loading="lazy" /></div>'
        else:
            thumb = f'<div class="thumb comp-cover-ph">{p["date"][5:]}</div>'
        cap = (p.get("caption") or p["shortcode"])[:28]
        html += f"""<a class="card" href="{href}" target="_blank" rel="noopener">
      {thumb}
      <div class="meta">
        <p class="place">{cap}</p>
        <p class="who">@{handle} · {fmt(p['views'])}</p>
        <div class="stats"><span class="eng">{er:.1f}%</span></div>
      </div></a>"""
    html += "</div>"
    return html


def competitor_shelf_cards(*, competitors_only: bool = False, show_covers: bool = True) -> str:
    grid_cls = "comp-grid" if show_covers else "comp-grid comp-grid--no-covers"
    html = f'<div class="{grid_cls}">'
    for c in COMPETITOR_SHELF:
        if competitors_only and c.get("brand"):
            continue
        posts = reel_posts_for(c["handle"])
        med = median([p["views"] for p in posts]) if posts else None
        reels_n = len(posts)
        share = (med / c["followers"] * 100) if med else None
        brand_cls = " is-brand" if c.get("brand") else ""
        med_line = fmt(int(med)) if med is not None else "—"
        share_line = f"{share:.1f}%" if share is not None else "—"
        reels_line = str(reels_n) if reels_n else "—"
        mosaic = cover_mosaic(posts, c["handle"]) if show_covers else ""
        html += f"""<article class="comp-card{brand_cls}">
  {mosaic}
  <p class="role">{c['label']}</p>
  <p class="handle">@{c['handle']}</p>
  <div class="comp-kpis">
    <div><b>{fmt(c['followers'])}</b><span>Followers</span></div>
    <div><b>{reels_line}</b><span>Reels</span></div>
    <div><b>{med_line}</b><span>Median views</span></div>
    <div><b>{share_line}</b><span>Views / followers</span></div>
  </div>
  <a class="link-ig" href="https://www.instagram.com/{c['handle']}/" target="_blank" rel="noopener">Open Instagram</a>
</article>"""
    html += "</div>"
    return html


def competitor_ig_cards(posts: list[dict], handle: str, med: float) -> str:
    if not posts:
        return f'<div class="comp-cover-row comp-cover-row--empty">Profile only · reels not in this pass</div>'
    html = '<div class="grid grid-dense">'
    for p in sorted(posts, key=lambda x: x["date"]):
        mult = p["views"] / med if med else 0
        badge = ""
        if p.get("breakthrough"):
            badge = '<span class="tag boost">Breakthrough</span>'
        elif p.get("note"):
            badge = f'<span class="tag warn">Spike</span>'
        title = p.get("caption", p.get("shortcode", ""))[:28]
        href = ig_url(p["shortcode"], "reel")
        if handle == "funboy":
            thumb = f'<div class="thumb"><img src="{cover_path(p["shortcode"])}" alt="" loading="lazy" /></div>'
        else:
            thumb = f'<div class="thumb comp-cover-ph">{p["date"][5:]}</div>'
        html += f"""<a class="card" href="{href}" target="_blank" rel="noopener">
      {thumb}
      <div class="meta">
        <p class="place">{title or p['date']}</p>
        <p class="who">@{handle} · {fmt(p['views'])} · {mult:.1f}×</p>
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


def year_dataset() -> dict:
    with open(YEAR_DATA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def year_cover_thumb(post: dict) -> str:
    platform = post.get("platform") or "instagram"
    candidates: list[str] = []
    if post.get("cover_path"):
        candidates.append(post["cover_path"])
    if platform == "tiktok":
        candidates.append(f"covers/year-tt/{post['shortcode']}.jpg")
    else:
        candidates.extend(
            (
                f"covers/year-ig/{post['shortcode']}.jpg",
                cover_path(post["shortcode"]),
            )
        )
    for rel in candidates:
        fs = os.path.join(ROOT, rel)
        if os.path.isfile(fs) and os.path.getsize(fs) > 400:
            return f'<div class="year-thumb"><img src="{rel}" alt="" loading="lazy" decoding="async" /></div>'
    label = f"TT · {post['date'][5:]}" if platform == "tiktok" else post["date"][5:]
    return f'<div class="year-thumb year-thumb-ph"><span>{label}</span></div>'


def year_post_cards(
    posts: list[dict],
    *,
    platform: str = "instagram",
    quarter_id: str = "",
) -> str:
    """La-realtor-style cards: compact cover, link, stats (not full-height tiles)."""
    html = '<div class="grid grid-year">'
    is_tt = platform == "tiktok"
    card_extra = " is-tiktok" if is_tt else ""
    platform_badge = '<span class="platform-tt">TikTok</span>' if is_tt else ""
    for p in posts:
        ptype = p.get("type") or ("video" if is_tt else "reel")
        href = (
            p.get("permalink")
            or (
                f"https://www.tiktok.com/@funboy/video/{p['shortcode']}/"
                if is_tt
                else ig_url(p["shortcode"], ptype)
            )
        )
        thumb = year_cover_thumb(p)
        title = (p.get("title") or p.get("shortcode") or "Post")[:48]
        typ = (p.get("post_type_raw") or ptype or "").replace("_", " ")
        views_line = f"<li><b>{fmt(p['views'])}</b> views</li>" if p.get("views") else ""
        eng = ""
        likes_n = p.get("likes") or 0
        comments_n = p.get("comments") or 0
        if p.get("views"):
            er = (likes_n + comments_n) / p["views"] * 100
            eng = f'<span class="eng">{er:.2f}%</span>'
        tagged = '<span class="tag">Tagged UGC</span>' if p.get("is_tagged") else ""
        likes = fmt(likes_n) if p.get("likes") is not None else "—"
        comments_s = str(comments_n) if p.get("comments") is not None else "—"
        handle = "@funboy · TikTok" if is_tt else "@funboy"
        plat = "tiktok" if is_tt else "instagram"
        html += f"""<a class="card year-filter-card{card_extra}" href="{href}" target="_blank" rel="noopener" data-platform="{plat}" data-quarter="{quarter_id}">
      {thumb}
      <div class="meta">
        {platform_badge}
        <p class="place">{title}</p>
        <p class="who">{handle} · {p['date']} · {typ}</p>
        <div class="stats"><span><b>{likes}</b> likes</span>{eng}</div>
        <ul class="counts">{views_line}<li><b>{comments_s}</b> comments</li></ul>
        {tagged}
      </div>
    </a>"""
    html += "</div>"
    return html


def ads_placeholder_section() -> str:
    return """<div class="section" id="ads">
<h2>Ads</h2>
<div class="ads-waiting">
<p class="eyebrow">Waiting for data</p>
<p class="lead" style="margin:0;font-size:15px">Paid social performance will be added here when exports are available. No ad metrics are shown as placeholders.</p>
</div></div>"""


def year_timeline_section(timeline: dict) -> str:
    if not timeline or not timeline.get("months"):
        return ""
    data_json = json.dumps(timeline, separators=(",", ":"))
    return f"""<section class="year-timeline section" id="year-timeline" aria-label="Month over month timeline">
  <div class="tl-head">
    <div>
      <h2>Month over month</h2>
      <p class="who" style="margin:0">Each month vs same month prior year · Oct 2025–Oct 2026 window</p>
    </div>
    <div class="tl-metric-switch" role="group" aria-label="Timeline metric">
      <button type="button" class="filter-btn is-active" data-timeline-metric="posts">Posts</button>
      <button type="button" class="filter-btn" data-timeline-metric="views">Views</button>
      <button type="button" class="filter-btn" data-timeline-metric="likes">Likes</button>
    </div>
  </div>
  <div class="tl-chart" id="year-timeline-chart"></div>
  <div class="tl-legend">
    <span><i class="tl-swatch prior"></i> Prior year (same month)</span>
    <span><i class="tl-swatch cur"></i> Current period</span>
  </div>
  <p class="who" style="margin:10px 0 0;font-size:11px">Prior-year TikTok before Nov 2025 is not in the public export. Prior-year views/likes use post-level data when available; otherwise post counts from Nectarine monthly history.</p>
  <script type="application/json" id="year-timeline-data">{data_json}</script>
</section>"""


YEAR_FILTER_SCRIPT = """
<script>
(function () {
  var platform = "both";
  var quarter = "all";
  var timelineMetric = "posts";
  var timelineData = null;
  try {
    var el = document.getElementById("year-timeline-data");
    timelineData = el ? JSON.parse(el.textContent) : null;
  } catch (e) {
    timelineData = null;
  }
  function pickMetrics(block) {
    if (!block) return { posts: 0, likes: 0, views: 0 };
    return {
      posts: block.posts || 0,
      likes: block.likes || 0,
      views: block.views || 0,
    };
  }
  function combineMonth(row) {
    var ig = pickMetrics(row.instagram);
    var tt = pickMetrics(row.tiktok);
  if (platform === "instagram") return ig;
  if (platform === "tiktok") return tt;
    return {
      posts: ig.posts + tt.posts,
      likes: ig.likes + tt.likes,
      views: ig.views + tt.views,
    };
  }
  function combinePrior(row) {
    var ig = row.prior_year && row.prior_year.instagram ? row.prior_year.instagram : {};
    var tt = row.prior_year && row.prior_year.tiktok ? row.prior_year.tiktok : {};
    var igM = {
      posts: ig.posts == null ? 0 : ig.posts,
      likes: ig.likes == null ? 0 : ig.likes,
      views: ig.views == null ? 0 : ig.views,
    };
    var ttM = {
      posts: tt.posts || 0,
      likes: tt.likes || 0,
      views: tt.views || 0,
    };
  if (platform === "instagram") return igM;
  if (platform === "tiktok") return ttM;
    return {
      posts: igM.posts + ttM.posts,
      likes: igM.likes + ttM.likes,
      views: igM.views + ttM.views,
    };
  }
  function renderYearTimeline() {
    var root = document.getElementById("year-timeline-chart");
    if (!root || !timelineData || !timelineData.months) return;
    var rows = timelineData.months;
    var vals = [];
    rows.forEach(function (row) {
      var cur = combineMonth(row);
      var pri = combinePrior(row);
      vals.push(cur[timelineMetric] || 0, pri[timelineMetric] || 0);
    });
    var maxV = Math.max.apply(null, vals.concat([1]));
    var html = "";
    rows.forEach(function (row) {
      var cur = combineMonth(row);
      var pri = combinePrior(row);
      var cv = cur[timelineMetric] || 0;
      var pv = pri[timelineMetric] || 0;
      var hCur = Math.round((cv / maxV) * 100);
      var hPri = Math.round((pv / maxV) * 100);
      var curClass = platform === "tiktok" ? " tl-cur tt-only" : " tl-cur";
      html += '<div class="tl-col"><div class="tl-pair">';
      html += '<i class="tl-bar tl-prior" style="height:' + hPri + '%" title="' + row.prior_label + ": " + pv + '"></i>';
      html += '<i class="tl-bar' + curClass + '" style="height:' + hCur + '%" title="' + row.label + ": " + cv + '"></i>';
      html += '</div><span class="tl-lbl">' + row.label + '</span>';
      html += '<span class="tl-sub">vs ' + row.prior_label + '</span>';
      html += '<span class="tl-val">' + cv.toLocaleString() + " · " + (pv ? pv.toLocaleString() : "—") + "</span>";
      html += "</div>";
    });
    root.innerHTML = html;
  }
  function applyYearFilters() {
    document.querySelectorAll(".year-quarter").forEach(function (el) {
      var show = quarter === "all" || el.id === quarter;
      el.hidden = !show;
    });
    document.querySelectorAll(".year-filter-card").forEach(function (card) {
      var p = card.getAttribute("data-platform");
      var q = card.getAttribute("data-quarter");
      var showPlatform = platform === "both" || p === platform;
      var showQuarter = quarter === "all" || q === quarter;
      card.hidden = !(showPlatform && showQuarter);
    });
    document.querySelectorAll(".year-subplatform, .year-filter-note").forEach(function (el) {
      var p = el.getAttribute("data-platform");
      var q = el.getAttribute("data-quarter");
      var parent = el.closest(".year-quarter");
      var parentId = parent ? parent.id : q;
      var showPlatform = platform === "both" || p === platform;
      var showQuarter = quarter === "all" || parentId === quarter || q === quarter;
      el.hidden = !(showPlatform && showQuarter);
    });
  }
  document.querySelectorAll("[data-filter-platform]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      platform = btn.getAttribute("data-filter-platform") || "both";
      document.querySelectorAll("[data-filter-platform]").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      applyYearFilters();
      renderYearTimeline();
    });
  });
  document.querySelectorAll("[data-filter-quarter]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      quarter = btn.getAttribute("data-filter-quarter") || "all";
      document.querySelectorAll("[data-filter-quarter]").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      applyYearFilters();
      renderYearTimeline();
      if (quarter !== "all") {
        var target = document.getElementById(quarter);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
  document.querySelectorAll("[data-timeline-metric]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      timelineMetric = btn.getAttribute("data-timeline-metric") || "posts";
      document.querySelectorAll("[data-timeline-metric]").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      renderYearTimeline();
    });
  });
  applyYearFilters();
  renderYearTimeline();
})();
</script>
"""


def year_filter_toolbar() -> str:
    return """<div class="year-filters" id="year-filters">
  <div class="filter-group">
    <span class="filter-label">Platform</span>
    <div class="filter-switch" role="group" aria-label="Filter by platform">
      <button type="button" class="filter-btn" data-filter-platform="instagram">Instagram</button>
      <button type="button" class="filter-btn" data-filter-platform="tiktok">TikTok</button>
      <button type="button" class="filter-btn is-active" data-filter-platform="both">Both</button>
    </div>
  </div>
  <div class="filter-group">
    <span class="filter-label">Quarter</span>
    <div class="filter-quarters" role="group" aria-label="Filter by quarter">
      <button type="button" class="filter-btn is-active" data-filter-quarter="all">All</button>
      <button type="button" class="filter-btn" data-filter-quarter="q1_oct_dec_2025">Q1</button>
      <button type="button" class="filter-btn" data-filter-quarter="q2_jan_mar_2026">Q2</button>
      <button type="button" class="filter-btn" data-filter-quarter="q3_apr_jun_2026">Q3</button>
      <button type="button" class="filter-btn" data-filter-quarter="q4_jul_oct_2026">Q4</button>
    </div>
  </div>
</div>"""


def competitor_watch_embed() -> str:
    """Shelf + competitor profiles (not a FUNBOY year grid duplicate)."""
    fun = funboy_window_stats()
    profiles = ""
    for c in COMPETITOR_SHELF:
        if c.get("brand"):
            continue
        profiles += competitor_profile_block(c, fun)
    return f"""<div class="section" id="competitor-watch">
<h2>Competitor watch</h2>
<p class="who">Shelf comparison and peer reel profiles · {WINDOW_LABEL} · public Instagram</p>
{competitor_watch_table(fun)}
<div class="section" style="margin-top:24px;padding-top:0;border-top:0">
<h3 style="font-family:Nohemi,sans-serif;font-size:18px;margin:0 0 10px">Reel profiles (competitors)</h3>
{profiles}
<p class="who" style="margin-top:8px">@bigshinyballs pinned outside window: {BSB_PINNED['date']} reel ({fmt(BSB_PINNED['views'])} public views) — excluded from Oct medians.</p>
</div>
</div>"""


def build_year_report() -> str:
    data = year_dataset()
    meta = data["meta"]
    quarters = data["quarters"]
    tiktok_quarters = data.get("tiktok_quarters") or []
    ig_meta = meta.get("instagram") or {
        "post_count": meta.get("post_count", len(data.get("posts", []))),
        "owned_post_count": meta.get("owned_post_count", 0),
        "tagged_post_count": meta.get("tagged_post_count", 0),
        "null_views_count": meta.get("null_views_count", 0),
    }
    tt_meta = meta.get("tiktok") or {"post_count": len(data.get("tiktok_posts", [])), "null_views_count": 0}
    cover_meta = meta.get("covers") or {}
    ig_miss = cover_meta.get("instagram_missing_photo", 0)
    tt_miss = cover_meta.get("tiktok_missing_photo", 0)
    quarter_html = ""
    tt_by_id = {b["id"]: b for b in tiktok_quarters}
    labels = {
        "q1_oct_dec_2025": "Q1 · Oct–Dec 2025",
        "q2_jan_mar_2026": "Q2 · Jan–Mar 2026",
        "q3_apr_jun_2026": "Q3 · Apr–Jun 2026",
        "q4_jul_oct_2026": "Q4 · Jul–Oct 2026",
    }
    for block in quarters:
        qid = block["id"]
        label = labels.get(qid, block.get("label", qid))
        ig_posts = block.get("posts") or []
        tt_posts = (tt_by_id.get(qid) or {}).get("posts") or []
        tt_block = ""
        if tt_posts:
            tt_block = f"""<p class="subplatform year-subplatform" data-platform="tiktok" data-quarter="{qid}">TikTok · {len(tt_posts)} videos</p>
{year_post_cards(tt_posts, platform="tiktok", quarter_id=qid)}"""
        elif qid == "q2_jan_mar_2026":
            tt_block = (
                f'<p class="who year-filter-note" data-platform="tiktok" data-quarter="{qid}">'
                "No TikTok videos in Nectarine or recaps for this quarter.</p>"
            )
        quarter_html += f"""<div class="quarter-block year-quarter" id="{qid}">
<h3>{label}</h3>
<p class="subplatform year-subplatform" data-platform="instagram" data-quarter="{qid}">Instagram · {len(ig_posts)} posts</p>
<p class="who year-filter-note" data-platform="instagram" data-quarter="{qid}">Newest last · tap opens Instagram</p>
{year_post_cards(ig_posts, quarter_id=qid)}
{tt_block}
</div>"""

    gap_list = "".join(f"<li>{g}</li>" for g in meta.get("gaps", []))

    body = f"""<p class="eyebrow">Year report · public social</p>
<h1>Instagram & TikTok year report</h1>
<p class="lead">@funboy organic posts · {meta.get("window_start", "2025-10-01")} through {meta.get("window_end", "2026-10-31")} · Instagram {ig_meta.get("post_count", 0)} ({ig_meta.get("owned_post_count", 0)} owned · {ig_meta.get("tagged_post_count", 0)} tagged UGC) · TikTok {tt_meta.get("post_count", 0)} public videos.</p>
{year_timeline_section(meta.get("timeline") or {})}
<div class="kpi-row">
  <div class="kpi"><b>{ig_meta.get("post_count", 0)}</b><span>Instagram posts</span></div>
  <div class="kpi"><b>{tt_meta.get("post_count", 0)}</b><span>TikTok videos</span></div>
  <div class="kpi"><b>{quarters[0]["post_count"]}</b><span>IG Q1</span></div>
  <div class="kpi"><b>{quarters[2]["post_count"]}</b><span>IG Q3</span></div>
  <div class="kpi"><b>{(tt_by_id.get("q3_apr_jun_2026") or {}).get("post_count", 0)}</b><span>TT Q3</span></div>
  <div class="kpi"><b>{(tt_by_id.get("q4_jul_oct_2026") or {}).get("post_count", 0)}</b><span>TT Q4</span></div>
  <div class="kpi"><b>{ig_miss + tt_miss}</b><span>Cards without photo</span></div>
</div>
<details class="volume-prior"><summary>Collection notes (public data only)</summary><ul style="margin:8px 0 0;padding-left:18px;font-size:13px;line-height:1.45">{gap_list}</ul></details>
<div class="section" id="year-report">
<h2>Year · by quarter</h2>
<p class="volume-note">La-realtor-style cards: compact cover (≈160px wide), link, public likes / comments / views. {ig_miss + tt_miss} cards still use date tiles (no public image available). Organic TikTok is listed under each quarter—not in Ads.</p>
{year_filter_toolbar()}
{quarter_html}
</div>
{ads_placeholder_section()}
{competitor_watch_embed()}
<p class="foot">Dataset: <code>data/funboy-ig-year-oct2025-oct2026.json</code> · regenerated via <code>scripts/collect_funboy_ig_year.py</code>. Layout from la-reels ({LA_REELS_SOURCE}).</p>
{YEAR_FILTER_SCRIPT}"""
    return page_shell("FUNBOY · Year report", "year", body)


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


def _chart_axis_num(n: float) -> str:
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.0f}K"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K".replace(".0K", "K")
    return f"{int(round(n))}"


def _nice_y_ticks(max_val: int) -> list[int]:
    if max_val <= 6:
        return list(range(0, max_val + 1))
    step = max(1, math.ceil(max_val / 4))
    mag = 10 ** math.floor(math.log10(step)) if step >= 10 else 1
    step = max(mag, math.ceil(step / mag) * mag)
    top = int(math.ceil(max_val / step) * step)
    return list(range(0, top + 1, step))


def view_distribution_chart_svg(
    values: list[float],
    center: float,
    lo: float,
    hi: float,
    subject: float,
) -> str:
    """Log-spaced histogram + log-normal overlay (MULE-14 benchmarks)."""
    pos = [float(v) for v in values if v > 0]
    if not pos:
        return ""

    logs = [math.log(v) for v in pos]
    mu = sum(logs) / len(logs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in logs) / len(logs)) or 1e-6
    log_min = min(logs)
    log_max = max(logs)
    pad = max(0.08, (log_max - log_min) * 0.12)
    log_min -= pad
    log_max += pad
    span = log_max - log_min or 1.0

    n_bins = 6
    counts = [0] * n_bins
    edges = [log_min + span * i / n_bins for i in range(n_bins + 1)]
    for v in pos:
        lv = math.log(v)
        idx = min(n_bins - 1, max(0, int((lv - log_min) / span * n_bins)))
        counts[idx] += 1
    max_c = max(counts) or 1
    y_ticks = _nice_y_ticks(max_c)

    w, h = 680, 292
    x0, x1 = 52, 656
    y0, y1 = 36, 228
    plot_h = y1 - y0

    def lx(log_v: float) -> float:
        return x0 + (log_v - log_min) / span * (x1 - x0)

    def ly(count: float) -> float:
        return y1 - (count / y_ticks[-1]) * plot_h

    grid = ""
    y_labels = ""
    for tick in y_ticks:
        y = ly(tick)
        grid += f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e8e8e8" stroke-width="1"/>'
        if tick > 0:
            y_labels += (
                f'<text x="{x0 - 8}" y="{y + 3.5:.1f}" text-anchor="end" '
                f'font-size="10" fill="#666" font-variant-numeric="tabular-nums">{tick}</text>'
            )

    bars = ""
    x_labels = ""
    for i, c in enumerate(counts):
        x_left = lx(edges[i]) + 2
        x_right = lx(edges[i + 1]) - 2
        bw = max(4, x_right - x_left)
        top = ly(c)
        bar_h = y1 - top
        lo_v, hi_v = math.exp(edges[i]), math.exp(edges[i + 1])
        label = f"{_chart_axis_num(lo_v)}–{_chart_axis_num(hi_v)}"
        bars += (
            f'<rect x="{x_left:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bar_h:.1f}" '
            f'rx="3" fill="url(#barFill)" stroke="#2a7fc7" stroke-width="1"/>'
        )
        if c:
            bars += (
                f'<text x="{(x_left + x_right) / 2:.1f}" y="{top - 5:.1f}" text-anchor="middle" '
                f'font-size="10" font-weight="700" fill="#000">{c}</text>'
            )
        x_labels += (
            f'<text x="{(x_left + x_right) / 2:.1f}" y="{y1 + 14:.1f}" text-anchor="middle" '
            f'font-size="9" fill="#555">{label}</text>'
        )

    band_x0, band_x1 = lx(math.log(lo)), lx(math.log(hi))
    sigma_band = (
        f'<rect x="{band_x0:.1f}" y="{y0}" width="{band_x1 - band_x0:.1f}" height="{plot_h}" '
        f'fill="rgba(110,181,239,0.18)" stroke="none"/>'
    )

    pdf_pts: list[tuple[float, float]] = []
    steps = 120
    log_lo_plot = log_min
    log_hi_plot = log_max
    for i in range(steps + 1):
        lv = log_lo_plot + (log_hi_plot - log_lo_plot) * i / steps
        dens = math.exp(-0.5 * ((lv - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
        pdf_pts.append((lv, dens))
    max_d = max(p[1] for p in pdf_pts) or 1
    scale = max_c / max_d
    curve_path = []
    area_path = [f"M{lx(log_lo_plot):.1f},{y1:.1f}"]
    for i, (lv, dens) in enumerate(pdf_pts):
        sx = lx(lv)
        sy = ly(dens * scale)
        curve_path.append(f"{'M' if i == 0 else 'L'}{sx:.1f},{sy:.1f}")
        area_path.append(f"L{sx:.1f},{sy:.1f}")
    area_path.append(f"L{lx(log_hi_plot):.1f},{y1:.1f}Z")
    curve = f'<path d="{" ".join(curve_path)}" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round"/>'
    area = f'<path d="{"".join(area_path)}" fill="rgba(0,0,0,0.04)" stroke="none"/>'

    sub_x = lx(math.log(max(subject, 1)))
    subject_mark = (
        f'<line x1="{sub_x:.1f}" y1="{y0}" x2="{sub_x:.1f}" y2="{y1}" '
        f'stroke="#c73333" stroke-width="1.5" stroke-dasharray="5 4"/>'
        f'<text x="{sub_x:.1f}" y="{y0 - 8}" text-anchor="middle" font-size="10" fill="#c73333">'
        f"nearest median · {_chart_axis_num(subject)}</text>"
    )

    title = "View distribution · combined collected reels"
    meta = f"log-normal center {_chart_axis_num(center)} · 1σ {_chart_axis_num(lo)}–{_chart_axis_num(hi)}"
    caption = (
        f"Histogram uses log-spaced view bins ({len(pos)} reels). "
        f"Black curve is the fitted log-normal on log(view count), scaled to the tallest bin. "
        f"Shaded band is the 1σ view range."
    )

    return f"""<div class="chart-wrap">
<div class="chart-head"><h3>{title}</h3><span class="chart-meta">{meta}</span></div>
<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}. {meta}">
  <defs>
    <linearGradient id="barFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#c5e4fc"/>
      <stop offset="100%" stop-color="#6eb5ef"/>
    </linearGradient>
  </defs>
  {sigma_band}
  {grid}
  <line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#000" stroke-width="1.5"/>
  <line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#000" stroke-width="1.5"/>
  {y_labels}
  {bars}
  {area}
  {curve}
  {subject_mark}
  {x_labels}
  <text x="{(x0 + x1) / 2:.1f}" y="{h - 8}" text-anchor="middle" font-size="10" fill="#666">Public reel views (log-spaced bins)</text>
  <text x="18" y="{(y0 + y1) / 2:.1f}" text-anchor="middle" font-size="10" fill="#666" transform="rotate(-90 18 {(y0 + y1) / 2:.1f})"># reels</text>
</svg>
<p class="chart-caption">{caption}</p>
<div class="chart-legend">
  <span><i class="swatch bar"></i>Reel count</span>
  <span><i class="swatch curve"></i>Log-normal fit</span>
  <span><i class="swatch band"></i>1σ band</span>
  <span><i class="swatch subject"></i>Median-nearest reel</span>
</div>
</div>"""


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


def _volume_table_rows(rows: list[dict], *, total_label: str) -> tuple[str, str]:
    max_posts = max(r["posts"] for r in rows) or 1
    bars = ""
    table_rows = ""
    for row in rows:
        other = row["posts"] - row["reels"]
        h_reel = int(96 * row["reels"] / max_posts)
        h_other = int(96 * other / max_posts)
        short = row["month"][5:]
        bars += f"""<div class="volume-col"><b>{row['posts']}</b>
      <i class="reel" style="height:{max(h_reel, 2 if row['reels'] else 0)}px" title="{row['reels']} reels"></i>
      <i class="other" style="height:{max(h_other, 2 if other else 0)}px" title="{other} other formats"></i>
      {short}</div>"""
        note = row.get("note")
        month_cell = month_label(row["month"])
        if note:
            month_cell += f' <span class="who">({note})</span>'
        table_rows += (
            f"<tr><td>{month_cell}</td>"
            f"<td>{row['posts']}</td><td>{row['reels']}</td>"
            f"<td>{row['feed_posts']}</td><td>{row['carousels']}</td></tr>"
        )
    totals = fun_ig_year_totals(rows)
    table_rows += (
        f"<tr><th>{total_label}</th><th>{totals['posts']}</th><th>{totals['reels']}</th>"
        f"<th>{totals['feed_posts']}</th><th>{totals['carousels']}</th></tr>"
    )
    return bars, table_rows


def ig_volume_year_section() -> str:
    bars, rows = _volume_table_rows(FUN_IG_MONTHLY, total_label="Oct–Oct total")
    totals = fun_ig_year_totals()
    peak = max(FUN_IG_MONTHLY, key=lambda r: r["posts"])
    reel_share = totals["reels"] / totals["posts"] * 100 if totals["posts"] else 0
    prior_bars, prior_rows = _volume_table_rows(
        FUN_IG_MONTHLY_PRIOR, total_label="Nov 2024 – Sep 2025 subtotal"
    )
    return f"""<div class="section"><h2>Instagram posting volume</h2>
<p class="volume-note">Full-year circle: <b>{FUN_IG_YEAR_LABEL}</b> · @funboy main-feed assets (Reels, feed posts, carousels; excludes Tagged reposts and TikTok). Source: {FUN_IG_YEAR_SOURCE}. Peak month in this window: {month_label(peak['month'])} ({peak['posts']} assets, {peak['reels']} reels). Reel share across the year: {reel_share:.0f}%.</p>
<div class="volume-chart" aria-hidden="true">{bars}</div>
<p class="who" style="margin:-8px 0 12px">Bar stack: blue = reels · gray = other IG formats · labels = month (10 = Oct)</p>
<table class="data"><tr><th>Month</th><th>Total posts</th><th>Reels</th><th>Feed posts</th><th>Carousels</th></tr>
{rows}
</table>
<details class="volume-prior">
<summary>Earlier months (optional · Nov 2024 – Sep 2025)</summary>
<div class="volume-chart" aria-hidden="true">{prior_bars}</div>
<table class="data"><tr><th>Month</th><th>Total posts</th><th>Reels</th><th>Feed posts</th><th>Carousels</th></tr>
{prior_rows}
</table>
</details></div>"""


def build_benchmarks() -> str:
    pool = all_collected_reels()
    views = [float(p["views"]) for p in pool]
    avg = sum(views) / len(views)
    sd = pop_std(views)
    med = median(views)
    subject = min(pool, key=lambda p: abs(p["views"] - med))
    center, lo, hi = log_normal_band(views)

    body = f"""<p class="eyebrow">Benchmarks · MULE-14 math</p>
<h1>View benchmark</h1>
{ig_volume_year_section()}
{competitor_shelf_cards(show_covers=False)}
<div class="stat-strip">
  <div class="kpi"><b>{len(pool)}</b><span>Reels in Oct window pool</span></div>
  <div class="kpi"><b>{fmt(int(sum(views)))}</b><span>Total public views</span></div>
  <div class="kpi"><b>{avg:,.0f}</b><span>Average views</span></div>
  <div class="kpi"><b>{sd:,.0f}</b><span>Std. dev.</span></div>
  <div class="kpi"><b>{fmt(int(med))}</b><span>Median views</span></div>
  <div class="kpi"><b>{(sum((p['likes']+p['comments'])/p['views'] for p in pool)/len(pool)*100):.1f}%</b><span>Avg engagement</span></div>
</div>
{view_distribution_chart_svg(views, center, lo, hi, float(subject["views"]))}
<p class="foot">View math (MULE-14) uses public reels collected in the current October window ({COLLECTED}). Posting volume uses the Oct 2025–Oct 2026 year circle; earlier months are optional in the fold. Layout from la-reels.</p>"""
    return page_shell("FUNBOY · Benchmarks", "benchmarks", body)


def build_competitor() -> str:
    fun = funboy_window_stats()
    profiles = ""
    for c in COMPETITOR_SHELF:
        if c.get("brand"):
            continue
        profiles += competitor_profile_block(c, fun)

    body = f"""<p class="eyebrow">Competitor watch · mold 1</p>
<h1>Competitor watch</h1>
<p class="who">Side-by-side public Instagram reels · {WINDOW_LABEL} · engagement = (likes + comments) ÷ views</p>
<div class="section"><h2>Shelf comparison</h2>
{competitor_watch_table(fun)}
</div>
<div class="section"><h2>Reel-by-reel analysis</h2>
{profiles}
<p class="who" style="margin-top:8px">@bigshinyballs pinned outside window: {BSB_PINNED['date']} reel ({fmt(BSB_PINNED['views'])} public views) — excluded from Oct medians.</p>
</div>
<p class="foot">Competitor watch follows the DA Portal mold (MULE-15). Layout from la-reels ({LA_REELS_SOURCE}).</p>"""
    return page_shell("FUNBOY · Competitor watch", "competitor", body)


def build_all_reports() -> str:
    body = """<p class="eyebrow">Archive · mold 2</p>
<h1>All reports</h1>
<p class="lead">Earlier windows. Active home is the Instagram year report (index). October public window kept as a subpage.</p>
<div class="archive-list mold2">
  <a class="mold2-card" href="index.html"><span><strong>Instagram year report</strong><br><span class="who">Oct 2025 – Oct 2026 · quarterly cards</span></span><span class="pill">Active</span></a>
  <a class="mold2-card" href="october-report.html"><span><strong>October 2026 (public)</strong><br><span class="who">Oct 10–Nov 1 grid</span></span><span class="pill">Archive</span></a>
  <a class="mold2-card" href="september-2026-recap.html"><span><strong>September 2026</strong><br><span class="who">Full month · Instagram Insights + TikTok</span></span><span class="pill">Archive</span></a>
  <a class="mold2-card" href="august-2026-recap.html"><span><strong>August 2026</strong><br><span class="who">Full month · Instagram + TikTok</span></span><span class="pill">Archive</span></a>
</div>
<p class="foot">Card edge glow matches the Dream Aspect pricing selector animation. Return to the <a href="index.html">year report</a> for the active report.</p>"""
    return page_shell("FUNBOY · All reports", "all", body)


def patch_archives() -> None:
    shell = nav("all")
    note = """<link rel="stylesheet" href="portal-styles.css" />
<style>.report-nav{display:none!important}</style>
<p class="archive-note">Archived report — not the current window. Active report: <a href="index.html">Instagram year report</a> · <a href="all-reports.html">All reports</a></p>"""
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
        "october-report.html",
        "benchmarks.html",
        "competitor-watch.html",
        "competitor-research.html",
        "all-reports.html",
        "portal-styles.css",
        "august-2026-recap.html",
        "september-2026-recap.html",
    ):
        src = os.path.join(ROOT, fn)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dst, fn))
    shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(dst, "fonts"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "covers"), os.path.join(dst, "covers"), dirs_exist_ok=True)
    data_src = os.path.join(ROOT, "data", "funboy-ig-year-oct2025-oct2026.json")
    if os.path.isfile(data_src):
        data_dst = os.path.join(dst, "data")
        os.makedirs(data_dst, exist_ok=True)
        shutil.copy2(data_src, os.path.join(data_dst, "funboy-ig-year-oct2025-oct2026.json"))


def main() -> None:
    try:
        save_bsb_covers()
    except Exception:
        pass
    open(os.path.join(ROOT, "portal-styles.css"), "w", encoding="utf-8").write(CSS)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(build_year_report())
    open(os.path.join(ROOT, "october-report.html"), "w", encoding="utf-8").write(build_october())
    open(os.path.join(ROOT, "benchmarks.html"), "w", encoding="utf-8").write(build_benchmarks())
    comp_html = build_competitor()
    open(os.path.join(ROOT, "competitor-watch.html"), "w", encoding="utf-8").write(comp_html)
    open(os.path.join(ROOT, "competitor-research.html"), "w", encoding="utf-8").write(comp_html)
    open(os.path.join(ROOT, "all-reports.html"), "w", encoding="utf-8").write(build_all_reports())
    patch_archives()
    for obsolete in ("october-public-2026-recap.html",):
        p = os.path.join(ROOT, obsolete)
        if os.path.isfile(p):
            os.remove(p)
    sync_funboy_path()
    print("Built la-reels layout portal pages.")


if __name__ == "__main__":
    main()
