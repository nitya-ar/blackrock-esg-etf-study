import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color:#E7EBF1; background:#0B0D11; }
      .block-container { padding-top: 28px; padding-bottom: 28px; max-width: 1200px; }
      .brandrow { display:flex; align-items:center; gap:14px; margin-bottom:4px; }
      .brandrow h1 { margin:0; font-size:28px; font-weight:800; letter-spacing:.2px; }
      .tagline { margin:8px 0 4px; color:#A8B3C2; font-size:14px; }
      .tabs-top { display:flex; gap:10px; margin:10px 0 14px; }
      .tablink { padding:7px 12px; border-radius:10px; background:#12151B; border:1px solid #2A313C; color:#DDE3EC; text-decoration:none; font-size:13px; }
      .tablink.active { background:#1A2029; border-color:#3A4554; font-weight:600; }
      .section-switch { display:flex; gap:8px; margin:6px 0 12px; }
      .switch-pill { padding:8px 14px; border-radius:999px; background:#12161D; border:1px solid #2B3441; color:#DADFE7; font-size:13px; }
      .switch-pill.sel { background:#1E2530; border-color:#3A4656; box-shadow: 0 0 0 2px rgba(81,133,255,.08) inset; font-weight:600; }
      .asof { font-size:12px; color:#95A2B3; text-align:right; }
      .muted-accent { background:#171C23; border:1px solid #2C3541; color:#CBD6E4; padding:6px 10px; border-radius:8px; display:inline-block; }
      .section-title { font-size:24px; font-weight:800; margin:12px 0 10px; }
      .kpi-wrap { display:grid; grid-template-columns: repeat(5, 1fr); gap:12px; margin:4px 0 8px; }
      .kcard { background:#12161D; border:1px solid #27303A; border-radius:14px; padding:14px 16px; }
      .klabel { font-size:11px; letter-spacing:.4px; color:#9FB0C4; text-transform:uppercase; }
      .kvalue { font-size:30px; font-weight:800; line-height:1.1; margin-top:2px; }
      .ksub { font-size:11px; color:#8FA0B4; margin-top:2px; }
      .kvalue.positive { color:#27A28C; }
      .kvalue.negative { color:#C36D6D; }
      .pairhead { display:flex; align-items:center; justify-content:space-between; margin:10px 0 6px; }
      .subhead { font-size:16px; font-weight:700; }
      .infopill { font-size:12px; color:#C9D9FF; background:#1A2437; border:1px solid #334A78; padding:2px 8px; border-radius:999px; cursor:help; }
      .footer { margin-top: 18px; padding-top: 14px; border-top:1px solid #26303A; display:flex; justify-content:space-between; align-items:center; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#12161C; border:1px solid #2B3441; font-size:12px; color:#9FB0C4; margin-right:8px; }
      .footer a { color:#E7EBF1; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1; text-decoration:underline; }
      .kpi-big { font-size:32px; }
      .head-main { font-size:30px; font-weight:800; }
      .subsection { font-size:20px; font-weight:800; margin:18px 0 8px; }
    </style>
    """,
    unsafe_allow_html=True
)

BASE = Path("Data") / "Data for Dashboard"
AN1 = BASE / "Analysis 1"
AN2 = BASE / "Analysis 2"

CTX_SUMMARY = AN1 / "context_summary_2025.csv"
CTX_BYSCREEN = AN1 / "context_breakdown_by_screen.csv"
TOP_SPOTLIGHT = AN1 / "top_holdings_spotlight.csv"

AGG_TRENDS = AN2 / "aggregate_exposure_trends.csv"
BY_FUND_YEAR = AN2 / "exposures_by_fund_year.csv"
YEAR_COMPARE = AN2 / "year_compare_summary.csv"
SCREEN_TRENDS = AN2 / "aggregate_screen_trends.csv"
MOVERS = AN2 / "movers_by_yearpair.csv"

CALM_GREEN = "#27A28C"
CALM_RED = "#C36D6D"
CALM_OTHER = "#5A6674"

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

def deltas_from_trends(df, weighting_key):
    ycol = pick(df, [lambda s: s == "year"])
    wcol = pick(df, [lambda s: s in ("weighting","agg_type","type")])
    clean_col = pick(df, [lambda s: ("clean" in s and "pct" in s) or s in ("pct_clean","clean_pct","clean_percent")])
    contro_col = pick(df, [lambda s: ("controversial" in s and "pct" in s) or s in ("pct_controversial","controversial_pct")])
    if not all([ycol, clean_col, contro_col]):
        return np.nan, np.nan
    filt = df if wcol is None else df[df[wcol].str.lower().str.contains(weighting_key)]
    y17 = filt.loc[filt[ycol] == 2017]
    y25 = filt.loc[filt[ycol] == 2025]
    d_clean = float(y25[clean_col].mean() - y17[clean_col].mean()) if len(y17) and len(y25) else np.nan
    d_contro = float(y25[contro_col].mean() - y17[contro_col].mean()) if len(y17) and len(y25) else np.nan
    return d_clean, d_contro

def ensure_0_1(series):
    s = pd.to_numeric(series, errors="coerce")
    return s/100.0 if s.dropna().max() and s.dropna().max() > 1.5 else s

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
    ).properties(height=150)

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
    ).properties(height=220)

def format_billions(n):
    if pd.isna(n): return "—"
    return f"${n/1_000_000_000:.1f}B" if n >= 1_000_000_000 else f"${n:,.0f}"

st.markdown(
    """
    <div class="brandrow">
      <img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/BlackRock_wordmark.svg" alt="BlackRock" style="height:28px; filter:brightness(0) invert(1);">
      <h1 class="head-main">ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="tagline">We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.</div>', unsafe_allow_html=True)

st.markdown('<div class="tabs-top"><span class="tablink active">Dashboard</span><span class="tablink">Report</span></div>', unsafe_allow_html=True)

ctx = read_csv(CTX_SUMMARY)
byscreen = read_csv(CTX_BYSCREEN)
top = read_csv(TOP_SPOTLIGHT)
agg = read_csv(AGG_TRENDS)

asof = get_asof(ctx) if ctx is not None else "2025"

c1, c2 = st.columns([0.65, 0.35])
with c1:
    st.markdown("<span class='muted-accent'>All ESG ETFs</span>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='asof'>As of: {asof}</div>", unsafe_allow_html=True)

switch_cols = st.columns([0.42,0.22,0.22,0.14])
with switch_cols[0]:
    st.markdown('<div class="section-switch"><span class="switch-pill sel">2025 Overview</span><span class="switch-pill">Change since 2017</span><span class="switch-pill">Tradeoffs</span></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">2025 Overview</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5, gap="small")
if ctx is not None:
    pct_con, pct_clean, total_aum = kpis_from_ctx(ctx)
    with k1:
        st.markdown(f"<div class='kcard'><div class='klabel'>% Controversial</div><div class='kvalue kpi-big'>{pct_con:.1f}%</div><div class='ksub'>share of total AUM</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='kcard'><div class='klabel'>% Clean</div><div class='kvalue kpi-big'>{pct_clean:.1f}%</div><div class='ksub'>share of total AUM</div></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='kcard'><div class='klabel'>Total AUM</div><div class='kvalue kpi-big'>{format_billions(total_aum)}</div><div class='ksub'>across selected ESG ETFs</div></div>", unsafe_allow_html=True)
else:
    for col in (k1,k2,k3): col.markdown("<div class='kcard'><div class='klabel'>&nbsp;</div><div class='kvalue kpi-big'>—</div></div>", unsafe_allow_html=True)

weighting_key = "aum"
if agg is not None:
    d_clean, d_contro = deltas_from_trends(agg, weighting_key)
    with k4:
        st.markdown(f"<div class='kcard'><div class='klabel'>Δ Clean since 2017</div><div class='kvalue kpi-big positive'>{d_clean:+.1f} pp</div><div class='ksub'>AUM-weighted</div></div>", unsafe_allow_html=True)
    with k5:
        color_class = "negative" if d_contro>0 else "positive"
        st.markdown(f"<div class='kcard'><div class='klabel'>Δ Controversial since 2017</div><div class='kvalue kpi-big {color_class}'>{d_contro:+.1f} pp</div><div class='ksub'>AUM-weighted</div></div>", unsafe_allow_html=True)
else:
    for col in (k4,k5): col.markdown("<div class='kcard'><div class='klabel'>&nbsp;</div><div class='kvalue kpi-big'>—</div></div>", unsafe_allow_html=True)

left, right = st.columns([0.48, 0.52], gap="small")
with left:
    st.markdown('<div class="pairhead"><div class="subhead">Composition & Screens (2025)</div></div>', unsafe_allow_html=True)
    if ctx is not None:
        st.altair_chart(chart_composition(ctx), use_container_width=True)
with right:
    st.markdown(
        "<div class='pairhead'><div class='subhead'>Top screens by share (2025)</div>"
        "<div><span class='infopill' title='Categories can overlap; totals won’t sum to overall controversial exposure.'>ⓘ</span></div></div>",
        unsafe_allow_html=True
    )
    if byscreen is not None:
        d = byscreen.copy()
        st.altair_chart(chart_by_screen(d), use_container_width=True)

s1, s2 = st.columns(2, gap="small")
if top is not None:
    cohort = pick(top, [lambda s: s == "cohort"])
    rank = pick(top, [lambda s: "rank" in s])
    name = pick(top, [lambda s: s in ("holding_name","name")])
    ticker = pick(top, [lambda s: s == "ticker"])
    share = pick(top, [lambda s: "share_of_total_aum_pct" in s or s == "share_pct"])
    etfsn = pick(top, [lambda s: s in ("num_etfs","#etfs","count_etfs")])
    tags = pick(top, [lambda s: "screen_categories" in s or s == "tags"])
    cols = [rank, ticker, name, share, etfsn, tags]
    rename_map = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}

    with s1:
        st.markdown('<div class="subsection">Top Controversial holdings</div>', unsafe_allow_html=True)
        tc = top[top[cohort].str.lower()=="controversial"][cols].rename(columns=rename_map).copy()
        tc["Share of AUM (%)"] = pd.to_numeric(tc["Share of AUM (%)"], errors="coerce").round(4)
        st.dataframe(tc.head(10), use_container_width=True, hide_index=True)
    with s2:
        st.markdown('<div class="subsection">Top Clean holdings</div>', unsafe_allow_html=True)
        tg = top[top[cohort].str.lower()=="clean"][cols].rename(columns=rename_map).copy()
        tg["Share of AUM (%)"] = pd.to_numeric(tg["Share of AUM (%)"], errors="coerce").round(4)
        st.dataframe(tg.head(10), use_container_width=True, hide_index=True)

st.markdown(
    """
    <div class="footer">
      <div>
        <span class="pill">Clean = Green</span>
        <span class="pill">Controversial = Red</span>
        <span class="pill">Other = Blue-grey</span>
      </div>
      <div>
        <a href="https://github.com/nitya-ar/blackrock-esg-etf-study" target="_blank">GitHub</a>
        <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a>
        <a href="https://forms.gle/1fFm9cXQfx9fbD2u5" target="_blank">Feedback</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
