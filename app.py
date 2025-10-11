import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

# ---------- PAGE ----------
st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

# ---------- THEME / STYLES ----------
st.markdown(
    """
    <style>
      /* Typeface */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
      html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color:#E9EDF3; background:#0A0C10;
      }

      .block-container { padding-top: 28px; padding-bottom: 28px; max-width: 1200px; }

      /* Header */
      .brandrow { display:flex; align-items:flex-end; gap:14px; margin:0 0 8px 0; }
      .brandrow h1 { margin:0; font-size:32px; font-weight:800; letter-spacing:.2px; line-height:1.15; }
      .contextline { color:#A5B2C3; font-size:14px; margin:2px 0 10px; max-width:1000px; }

      /* Top-level nav */
      .topnav { display:flex; gap:8px; margin:8px 0 6px; }
      .topnav .pill { padding:8px 14px; border-radius:12px; background:#12161D; border:1px solid #283241; font-size:13px; color:#DDE4ED; }
      .topnav .pill.active { background:#1A2130; border-color:#3B475A; font-weight:600; box-shadow:0 0 0 2px rgba(92,130,255,.08) inset; }

      /* Dashboard subnav */
      .subnav { display:flex; gap:8px; margin:6px 0 2px; }
      .subnav .sp { padding:8px 14px; border-radius:999px; background:#11161D; border:1px solid #273141; font-size:13px; color:#DCE3EC; }
      .subnav .sp.active { background:#1B2230; border-color:#3A4658; font-weight:600; }

      .asof { font-size:12px; color:#94A1B1; text-align:right; margin-top:4px; }

      /* Section title */
      .section-title { font-size:22px; font-weight:800; margin:16px 0 10px; }

      /* KPI cards */
      .kpi-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap:12px; }
      .kcard { background:#11161D; border:1px solid #273140; border-radius:16px; padding:14px 16px; }
      .klabel { font-size:11px; letter-spacing:.35px; color:#9FB0C4; text-transform:uppercase; }
      .kvalue { font-size:30px; font-weight:800; line-height:1.1; margin-top:4px; }
      .ksub { font-size:11px; color:#8EA0B6; margin-top:4px; }

      /* Dark & punchy accents for the numbers only */
      .accent-green { color:#2EE2B4; }   /* bright teal-green on dark */
      .accent-red   { color:#FF7C90; }   /* bright coral-red on dark */

      /* Pair headings above charts */
      .pairhead { display:flex; align-items:center; justify-content:space-between; margin:10px 0 6px; }
      .subhead { font-size:16px; font-weight:700; }
      .infopill { font-size:12px; color:#C9D8FF; background:#1A2437; border:1px solid #334A78; padding:2px 8px; border-radius:999px; cursor:help; }

      /* Subsection headers for tables */
      .subsection { font-size:18px; font-weight:800; margin:18px 0 8px; }

      /* Footer */
      .footer { margin-top: 22px; padding-top: 16px; border-top:1px solid #26303A; display:flex; justify-content:flex-end; gap:22px; }
      .footer a { color:#E9EDF3; text-decoration:none; font-size:15px; }
      .footer a:hover { text-decoration:underline; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- PATHS ----------
BASE = Path("Data") / "Data for Dashboard"
AN1 = BASE / "Analysis 1"

CTX_SUMMARY   = AN1 / "context_summary_2025.csv"
CTX_BYSCREEN  = AN1 / "context_breakdown_by_screen.csv"
TOP_SPOTLIGHT = AN1 / "top_holdings_spotlight.csv"

# ---------- COLORS ----------
CALM_GREEN = "#2EE2B4"  # punchy on dark
CALM_RED   = "#FF7C90"
CALM_OTHER = "#6B7786"

# ---------- HELPERS ----------
@st.cache_data
def read_csv(p: Path):
    return pd.read_csv(p) if p.exists() else None

def pick(df, fns):
    low = {c.lower(): c for c in df.columns}
    for fn in fns:
        for k, v in low.items():
            if fn(k):
                return v
    return None

def get_asof(df):
    c = pick(df, [lambda s: s in ("as_of_date","as-of date","asof","as_of")])
    return df[c].iloc[0] if c else "2025"

def kpis_from_ctx(df):
    cls = pick(df, [lambda s: s == "classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s in ("share_pct","share")])
    aum_col = pick(df, [lambda s: s in ("total_aum_usd","total_aum","aum_usd")])
    df[share] = pd.to_numeric(df[share], errors="coerce")
    if aum_col:
        df[aum_col] = pd.to_numeric(df[aum_col], errors="coerce")
    pct_con = float(df.loc[df[cls].str.lower()=="controversial", share].sum())
    pct_clean = float(df.loc[df[cls].str.lower()=="clean", share].sum())
    total_aum = float(df[aum_col].iloc[0]) if aum_col else np.nan
    return pct_con, pct_clean, total_aum

def ensure_0_1(series):
    s = pd.to_numeric(series, errors="coerce")
    return s/100.0 if s.dropna().max() and s.dropna().max() > 1.5 else s

def format_billions(n):
    if pd.isna(n): return "—"
    return f"${n/1_000_000_000:.1f}B" if n >= 1_000_000_000 else f"${n:,.0f}"

# ---------- CHARTS ----------
def chart_composition(df):
    cls = pick(df, [lambda s: s == "classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s in ("share_pct","share")])
    m = df[[cls, share]].groupby(cls, as_index=False).sum()
    order = pd.Categorical(m[cls], categories=["Clean","Controversial","Other"], ordered=True)
    m = m.assign(order=order).sort_values("order")
    colors = {"Clean": CALM_GREEN, "Controversial": CALM_RED, "Other": CALM_OTHER}
    m["_plot_share"] = ensure_0_1(m[share])

    return alt.Chart(m).mark_bar().encode(
        x=alt.X("_plot_share:Q", stack="normalize", axis=alt.Axis(format="%", title="Share of total AUM")),
        color=alt.Color(cls, scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None),
        tooltip=[alt.Tooltip(cls, title="Category"), alt.Tooltip(share, title="Share of total AUM (%)", format=".1f")]
    ).properties(height=160)

def chart_by_screen(df):
    cat = pick(df, [lambda s: s in ("screen_category","screen_categories","category")])
    cls = pick(df, [lambda s: s == "classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s in ("share_pct","share")])

    d = df[[cat, cls, share]].groupby([cat, cls], as_index=False)[share].sum()
    d["_plot_share"] = ensure_0_1(d[share])
    colors = {"Controversial": CALM_RED, "Clean": CALM_GREEN}

    return alt.Chart(d).mark_bar().encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=""),
        x=alt.X(f"_plot_share:Q", axis=alt.Axis(format="%", title="Share of total AUM")),
        color=alt.Color(f"{cls}:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip(cat, title="Screen"), alt.Tooltip(cls, title="Cohort"), alt.Tooltip(share, title="Share of total AUM (%)", format=".1f")]
    ).properties(height=230)

# ---------- HEADER ----------
st.markdown(
    """
    <div class="brandrow">
      <img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/BlackRock_wordmark.svg"
           alt="BlackRock" style="height:28px; filter:brightness(0) invert(1);">
      <h1>ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# clear, one-line context (what/why)
st.markdown(
    """
    <div class="contextline">
      A concise look at BlackRock’s ESG-labelled ETFs through today’s (2025) ESG framework:
      where portfolios stand now, how exposures split across Clean / Controversial / Other,
      and which screens dominate—using AUM-aware shares throughout.
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- NAV ----------
st.markdown(
    """
    <div class="topnav">
      <span class="pill active">Dashboard</span>
      <span class="pill">Report</span>
    </div>
    <div class="subnav">
      <span class="sp active">2025 Overview</span>
      <span class="sp">Change since 2017</span>
      <span class="sp">Tradeoff experiment</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- DATA ----------
ctx       = read_csv(CTX_SUMMARY)
byscreen  = read_csv(CTX_BYSCREEN)
top       = read_csv(TOP_SPOTLIGHT)
asof      = get_asof(ctx) if ctx is not None else "2025"

# Right-aligned as-of date (no “All ESG ETFs” chip)
st.markdown(f"<div class='asof'>As of: {asof}</div>", unsafe_allow_html=True)

# ---------- 2025 OVERVIEW ----------
st.markdown('<div class="section-title">2025 Overview</div>', unsafe_allow_html=True)

# KPI cards (bigger numbers; dark but bright accents)
kcols = st.columns(5, gap="small")
if ctx is not None:
    pct_con, pct_clean, total_aum = kpis_from_ctx(ctx)

    with kcols[0]:
        st.markdown(
            f"<div class='kcard'>"
            f"<div class='klabel'>% Controversial</div>"
            f"<div class='kvalue accent-red'>{pct_con:.1f}%</div>"
            f"<div class='ksub'>share of total AUM</div></div>",
            unsafe_allow_html=True,
        )
    with kcols[1]:
        st.markdown(
            f"<div class='kcard'>"
            f"<div class='klabel'>% Clean</div>"
            f"<div class='kvalue accent-green'>{pct_clean:.1f}%</div>"
            f"<div class='ksub'>share of total AUM</div></div>",
            unsafe_allow_html=True,
        )
    with kcols[2]:
        st.markdown(
            f"<div class='kcard'>"
            f"<div class='klabel'>Total AUM</div>"
            f"<div class='kvalue'>{format_billions(total_aum)}</div>"
            f"<div class='ksub'>across selected ESG ETFs</div></div>",
            unsafe_allow_html=True,
        )
else:
    for c in kcols[:3]:
        c.markdown("<div class='kcard'><div class='klabel'>&nbsp;</div><div class='kvalue'>—</div></div>", unsafe_allow_html=True)

# If you later want deltas here, you can add two more cards; for now we keep the 3 key stats.

# Charts row
cL, cR = st.columns([0.48, 0.52], gap="small")
with cL:
    st.markdown('<div class="pairhead"><div class="subhead">Composition & Screens (2025)</div></div>', unsafe_allow_html=True)
    if ctx is not None:
        st.altair_chart(chart_composition(ctx), use_container_width=True)

with cR:
    st.markdown(
        "<div class='pairhead'><div class='subhead'>Top screens by share (2025)</div>"
        "<div><span class='infopill' title='Categories can overlap; totals won’t sum to overall controversial exposure.'>ⓘ</span></div></div>",
        unsafe_allow_html=True
    )
    if byscreen is not None:
        st.altair_chart(chart_by_screen(byscreen), use_container_width=True)

# Holdings tables (10 rows each; no extra “Top Exposures” header)
t1, t2 = st.columns(2, gap="small")
if top is not None:
    cohort = pick(top, [lambda s: s == "cohort"])
    rank   = pick(top, [lambda s: "rank" in s])
    name   = pick(top, [lambda s: s in ("holding_name","name")])
    ticker = pick(top, [lambda s: s == "ticker"])
    share  = pick(top, [lambda s: "share_of_total_aum_pct" in s or s == "share_pct"])
    etfsn  = pick(top, [lambda s: s in ("num_etfs","#etfs","count_etfs")])
    tags   = pick(top, [lambda s: "screen_categories" in s or s == "tags"])

    cols = [rank, ticker, name, share, etfsn, tags]
    rename_map = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}

    with t1:
        st.markdown('<div class="subsection">Top Controversial holdings</div>', unsafe_allow_html=True)
        tc = top[top[cohort].str.lower()=="controversial"][cols].rename(columns=rename_map).copy()
        tc["Share of AUM (%)"] = pd.to_numeric(tc["Share of AUM (%)"], errors="coerce").round(4)
        st.dataframe(tc.head(10), use_container_width=True, hide_index=True)

    with t2:
        st.markdown('<div class="subsection">Top Clean holdings</div>', unsafe_allow_html=True)
        tg = top[top[cohort].str.lower()=="clean"][cols].rename(columns=rename_map).copy()
        tg["Share of AUM (%)"] = pd.to_numeric(tg["Share of AUM (%)"], errors="coerce").round(4)
        st.dataframe(tg.head(10), use_container_width=True, hide_index=True)

# ---------- FOOTER ----------
st.markdown(
    """
    <div class="footer">
      <a href="https://github.com/nitya-ar/blackrock-esg-etf-study" target="_blank">GitHub</a>
      <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a>
      <a href="https://forms.gle/1fFm9cXQfx9fbD2u5" target="_blank">Feedback</a>
    </div>
    """,
    unsafe_allow_html=True
)
