import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
import re

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      html, body, [class*="css"] {
        font-family: Avenir, "Avenir Next", -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, "Helvetica Neue", Arial, sans-serif;
        color:#E6E9EF; background:#0B0C10;
      }
      .block-container { padding-top: 32px; padding-bottom: 32px; max-width: 1200px; }

      .brandrow { display:flex; align-items:center; gap:16px; margin-bottom:6px; }
      .brandrow h2 { margin:0; font-size:28px; font-weight:700; letter-spacing:.2px; }

      .footer { margin-top: 18px; padding-top: 14px; border-top:1px solid #2A2F36;
                display:flex; justify-content:space-between; align-items:center; }
      .footer a { color:#E6E9EF; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1; text-decoration:underline; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#121419;
              border:1px solid #2A2F36; font-size:12px; color:#9AA4B2; margin-right:8px; }
      .muted-accent { background:#191c22; border:1px solid #2A2F36; color:#C9D2DF;
                      padding:6px 10px; border-radius:8px; display:inline-block; }
      .asof { font-size:12px; color:#9AA4B2; text-align:right; }

      div[data-testid="stMetric"] { padding: 0 4px; }
      div[data-testid="stMetricValue"] { font-size: 26px; }
      div[data-testid="stMetricLabel"] { font-size: 13px; color:#C9D2DF; }
      div[data-testid="stMetricDelta"] { font-size: 12px; }

      .section-2025 { font-size:34px; font-weight:800; margin:8px 0 14px 0; }
      .section-2017 { font-size:30px; font-weight:800; margin:22px 0 10px 0; }
      .minor-h { font-size:18px; font-weight:700; margin:10px 0 6px 0; }
      .pairhead { display:flex; align-items:center; justify-content:space-between; margin:8px 0 4px 0; }

      .infopill { font-size:12px; color:#C8DAFF; background:#1A2437;
                  border:1px solid #334a78; padding:2px 8px; border-radius:999px; cursor:help; }
      .infopill:hover { filter:brightness(1.1); }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------ Paths ------------------------
BASE = Path("Data") / "Data for Dashboard"
AN1 = BASE / "Analysis 1"
AN2 = BASE / "Analysis 2"

# Analysis 1
CTX_SUMMARY = AN1 / "context_summary_2025.csv"
CTX_BYSCREEN = AN1 / "context_breakdown_by_screen.csv"
TOP_SPOTLIGHT = AN1 / "top_holdings_spotlight.csv"

# Analysis 2
AGG_TRENDS = AN2 / "aggregate_exposure_trends.csv"
YEAR_COMPARE = AN2 / "year_compare_summary.csv"
DISPERSION = AN2 / "exposure_dispersion_stats.csv"
BY_FUND_YEAR = AN2 / "exposures_by_fund_year.csv"
SCREEN_TRENDS = AN2 / "aggregate_screen_trends.csv"
MOVERS = AN2 / "movers_by_yearpair.csv"

# ------------------------ Colors ------------------------
CLEAN_COLOR = "#0A6F56"
CONTRO_COLOR = "#8F3131"
OTHER_COLOR = "#414B55"
SERIES_COLORS = {"Clean": CLEAN_COLOR, "Controversial": CONTRO_COLOR, "Other": OTHER_COLOR}

# ------------------------ Utils ------------------------
@st.cache_data
def read_csv(p: Path):
    return pd.read_csv(p) if p.exists() else None

def pick(df: pd.DataFrame, *patterns, contains_all=None):
    """
    Robust column picker:
    - patterns: substrings to be present (case-insensitive). Any of these can match.
    - contains_all: list of substrings that ALL must be present.
    Returns the first best match or None.
    """
    cols = list(df.columns)
    low = {c.lower(): c for c in cols}
    # build candidate list
    cands = []
    for lc, orig in low.items():
        ok_any = (not patterns) or any(p.lower() in lc for p in patterns)
        ok_all = True
        if contains_all:
            ok_all = all(s.lower() in lc for s in contains_all)
        if ok_any and ok_all:
            cands.append(orig)
    return cands[0] if cands else None

def first_existing(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def get_asof(df):
    c = pick(df, "as_of") or first_existing(df, ["as_of_date","as-of date"])
    return df[c].iloc[0] if c else "2025"

# ------------------------ A1 helpers ------------------------
def kpis_from_ctx(df):
    cls = pick(df, "classif") or "classification"
    share = pick(df, "share", "pct") or "share_of_total_aum_pct"
    aum_col = pick(df, "total_aum") or first_existing(df, ["total_aum_usd","aum_usd"])
    pct_con = float(df.loc[df[cls].str.lower()=="controversial", share].sum())
    pct_clean = float(df.loc[df[cls].str.lower()=="clean", share].sum())
    total_aum = float(df[aum_col].iloc[0]) if aum_col else np.nan
    return pct_con, pct_clean, total_aum

def chart_composition(df):
    cls = pick(df, "classif") or "classification"
    share = pick(df, "share", "pct") or "share_of_total_aum_pct"
    m = df[[cls, share]].groupby(cls, as_index=False).sum()
    order = pd.Categorical(m[cls], categories=["Clean","Controversial","Other"], ordered=True)
    m = m.assign(order=order).sort_values("order")
    colors = {"Clean":CLEAN_COLOR,"Controversial":CONTRO_COLOR,"Other":OTHER_COLOR}
    return alt.Chart(m).mark_bar().encode(
        x=alt.X(f"{share}:Q", stack="normalize", axis=alt.Axis(format="%", title="Share of total AUM")),
        color=alt.Color(cls, scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None),
        tooltip=[alt.Tooltip(cls, title="Category"), alt.Tooltip(share, title="Share of total AUM (%)", format=".1f")]
    ).properties(height=160)

def chart_by_screen(df):
    cat = pick(df, "screen", "category")
    cls = pick(df, "classif") or "classification"
    share = pick(df, "share", "pct") or "share_of_total_aum_pct"
    d = df[[cat, cls, share]].groupby([cat, cls], as_index=False)[share].sum()
    colors = {"Controversial":CONTRO_COLOR,"Clean":CLEAN_COLOR}
    return alt.Chart(d).mark_bar().encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=""),
        x=alt.X(f"{share}:Q", axis=alt.Axis(format="%", title="Share of total AUM")),
        color=alt.Color(f"{cls}:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip(cat, title="Screen"), alt.Tooltip(cls, title="Cohort"), alt.Tooltip(share, title="Share of total AUM (%)", format=".1f")]
    ).properties(height=230)

# ------------------------ A2 helpers ------------------------
def line_trends(df, weighting):
    wcol = pick(df, "weighting", "agg", "type", "view")
    ycol = pick(df, "year") or "year"
    clean = pick(df, "clean", contains_all=["pct"])
    contro = pick(df, "contro", contains_all=["pct"])
    other = pick(df, "other", contains_all=["pct"])
    d = df.copy()
    if wcol is not None and d[wcol].dtype == "O":
        key = "aum" if "AUM" in weighting.upper() else "ew"
        d = d[d[wcol].str.lower().str.contains(key, na=False)]
    tidy = pd.melt(
        d[[ycol, clean, contro, other]].rename(columns={clean:"Clean", contro:"Controversial", other:"Other"}),
        id_vars=ycol, var_name="Series", value_name="pct"
    )
    return alt.Chart(tidy).mark_line(point=True).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y("pct:Q", axis=alt.Axis(format="%", title="Portfolio share")),
        color=alt.Color("Series:N", scale=alt.Scale(domain=list(SERIES_COLORS.keys()), range=list(SERIES_COLORS.values())), legend=alt.Legend(title="")),
        tooltip=[ycol, "Series", alt.Tooltip("pct:Q", title="Share (%)", format=".1f")]
    ).properties(height=260)

def ribbon_from_dispersion(df, weighting):
    wcol = pick(df, "weighting", "agg", "type", "view")
    ycol = pick(df, "year") or "year"
    med = pick(df, "contro", "median") or pick(df, contains_all=["contro","p50"])
    p10 = pick(df, "contro", "p10")
    p90 = pick(df, "contro", "p90")
    if not all([ycol, med, p10, p90]):
        return None
    d = df.copy()
    if wcol is not None and d[wcol].dtype == "O":
        key = "aum" if "AUM" in weighting.upper() else "ew"
        d = d[d[wcol].str.lower().str.contains(key, na=False)]
    d = d[[ycol, med, p10, p90]].rename(columns={med:"median", p10:"p10", p90:"p90"})
    area = alt.Chart(d).mark_area(opacity=0.2, color=CONTRO_COLOR).encode(
        x=alt.X(f"{ycol}:O", title="Year"), y="p10:Q", y2="p90:Q"
    )
    line = alt.Chart(d).mark_line(color=CONTRO_COLOR).encode(
        x=alt.X(f"{ycol}:O"),
        y=alt.Y("median:Q", axis=alt.Axis(format="%", title="Controversial share")),
        tooltip=[ycol, alt.Tooltip("median:Q", title="Median (%)", format=".1f"),
                 alt.Tooltip("p10:Q", title="p10 (%)", format=".1f"),
                 alt.Tooltip("p90:Q", title="p90 (%)", format=".1f")]
    )
    return area + line

def heatmap_by_fund_year(df, metric="controversial"):
    ycol = pick(df, "year") or "year"
    fund = pick(df, "etf_ticker", "etf", "fund", "etf_name")
    # Try many metric name variants
    metric_patterns = [
        ("contro", "pct"), ("contro", "share"), ("contro", "percent"),
        ("clean", "pct"), ("clean", "share"), ("clean", "percent")
    ]
    mcol = None
    for p in metric_patterns:
        c = pick(df, *p)
        if c and ((metric.startswith("contro") and "clean" not in c.lower()) or
                  (metric.startswith("clean") and "clean" in c.lower())):
            mcol = c
            break
    if metric.startswith("contro") and mcol is None:
        # last resort exacts that appear in some exports
        mcol = first_existing(df, ["pct_controversial","controversial_pct","controversial_percent"])
    if metric.startswith("clean") and mcol is None:
        mcol = first_existing(df, ["pct_clean","clean_pct","clean_percent"])

    # If we still don't have what we need, gracefully skip
    if not all([fund, ycol, mcol]) or any(c not in df.columns for c in [fund, ycol, mcol]):
        st.info("Heatmap skipped: required columns not found in exposures_by_fund_year.csv.")
        return None

    d = df[[fund, ycol, mcol]].rename(columns={mcol:"pct"})
    latest_year = d[ycol].max()
    latest_order = d[d[ycol]==latest_year].sort_values("pct", ascending=False)[fund].tolist()
    d[fund] = pd.Categorical(d[fund], categories=latest_order, ordered=True)

    return alt.Chart(d).mark_rect().encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y(f"{fund}:O", title="ETF"),
        color=alt.Color("pct:Q",
                        scale=alt.Scale(scheme="reds" if metric.startswith("contro") else "greens"),
                        legend=alt.Legend(title="% share", format="%")),
        tooltip=[fund, ycol, alt.Tooltip("pct:Q", title="Share (%)", format=".1f")]
    ).properties(height=420)

def stacked_year_compare(df, weighting, year_a, year_b):
    wcol = pick(df, "weighting", "agg", "type", "view")
    ycol = pick(df, "year") or "year"
    cohort = pick(df, "cohort", "classif", "bucket") or "cohort"
    pct = pick(df, "pct", "share")
    d = df.copy()
    if wcol is not None and d[wcol].dtype == "O":
        key = "aum" if "AUM" in weighting.upper() else "ew"
        d = d[d[wcol].str.lower().str.contains(key, na=False)]
    d = d[d[ycol].isin([year_a, year_b])]
    d[cohort] = pd.Categorical(d[cohort], categories=["Clean","Controversial","Other"], ordered=True)
    return alt.Chart(d).mark_bar().encode(
        x=alt.X(f"{ycol}:O", title="", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{pct}:Q", axis=alt.Axis(format="%", title="Portfolio share"), stack="normalize"),
        color=alt.Color(f"{cohort}:N",
                        scale=alt.Scale(domain=["Clean","Controversial","Other"],
                                        range=[CLEAN_COLOR, CONTRO_COLOR, OTHER_COLOR]),
                        legend=alt.Legend(title="")),
        tooltip=[ycol, cohort, alt.Tooltip(pct, title="Share (%)", format=".1f")]
    ).properties(height=220)

def screen_small_multiples(df, weighting):
    wcol = pick(df, "weighting", "agg", "type", "view")
    ycol = pick(df, "year") or "year"
    cat = pick(df, "screen_category", "category")
    pct = pick(df, "pct", "share")
    d = df.copy()
    if wcol is not None and d[wcol].dtype == "O":
        key = "aum" if "AUM" in weighting.upper() else "ew"
        d = d[d[wcol].str.lower().str.contains(key, na=False)]
    screens = d[cat].unique().tolist()
    base = alt.Chart(d).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y(f"{pct}:Q", axis=alt.Axis(format="%", title="AUM-weighted share")),
        tooltip=[ycol, alt.Tooltip(pct, title="Share (%)", format=".1f")]
    )
    charts = []
    for s in screens:
        c = base.transform_filter(alt.datum[cat] == s).mark_line(
            color=CONTRO_COLOR if s!="Clean200" else CLEAN_COLOR
        ).properties(title=s, height=110)
        charts.append(c)
    return alt.vconcat(*charts).resolve_scale(y='independent')

# ------------------------ Header ------------------------
st.markdown(
    """
    <div class="brandrow">
      <img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/BlackRock_wordmark.svg"
           alt="BlackRock" style="height:32px; filter:brightness(0) invert(1);">
      <h2>ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.")

tab_dash, tab_report = st.tabs(["Dashboard","Report"])

# =======================================================
# Dashboard
# =======================================================
with tab_dash:
    # ---------- A1: 2025 Overview ----------
    ctx = read_csv(CTX_SUMMARY)
    agg_a2 = read_csv(AGG_TRENDS)
    asof = get_asof(ctx) if ctx is not None else "2025"

    c1, c2 = st.columns([0.65, 0.35])
    with c1:
        st.markdown("<span class='muted-accent'>All ESG ETFs</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='asof'>As of: {asof}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-2025'>2025 Overview</div>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns([0.18,0.18,0.26,0.19,0.19], gap="small")
    if ctx is not None:
        pct_con, pct_clean, total_aum = kpis_from_ctx(ctx)
        k1.metric("% Controversial", f"{pct_con:.1f}%")
        k2.metric("% Clean", f"{pct_clean:.1f}%")
        k3.metric("Total AUM", f"${total_aum:,.0f}" if pd.notna(total_aum) else "—")
    else:
        k1.metric("% Controversial", "—"); k2.metric("% Clean", "—"); k3.metric("Total AUM", "—")

    if agg_a2 is not None:
        # simple AUM-weighted deltas across all funds
        ycol = pick(agg_a2, "year") or "year"
        clean_col = pick(agg_a2, "clean", contains_all=["pct"])
        contro_col = pick(agg_a2, "contro", contains_all=["pct"])
        y17 = agg_a2[agg_a2[ycol]==2017]; y25 = agg_a2[agg_a2[ycol]==2025]
        d_clean = (y25[clean_col].mean() - y17[clean_col].mean()) if len(y17) and len(y25) else np.nan
        d_contro = (y25[contro_col].mean() - y17[contro_col].mean()) if len(y17) and len(y25) else np.nan
        k4.metric("Δ Clean since 2017", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
        k5.metric("Δ Controversial since 2017", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")
    else:
        k4.metric("Δ Clean since 2017", "—"); k5.metric("Δ Controversial since 2017", "—")

    # Composition & Screens — adjust widths (narrow left, wider right)
    left, right = st.columns([0.44,0.56], gap="small")
    with left:
        st.markdown("<div class='minor-h'>Composition & Screens (2025)</div>", unsafe_allow_html=True)
        if ctx is not None:
            st.altair_chart(chart_composition(ctx), use_container_width=True)
    with right:
        st.markdown(
            "<div style='display:flex; justify-content:flex-end; margin:2px 0 4px 0;'>"
            "<span class='infopill' title='Categories can overlap; totals won’t sum to overall controversial exposure.'>ⓘ</span>"
            "</div>", unsafe_allow_html=True
        )
        byscreen = read_csv(CTX_BYSCREEN)
        if byscreen is not None:
            st.altair_chart(chart_by_screen(byscreen), use_container_width=True)

    # Spotlight: show 5, expandable to full 10
    s1, s2 = st.columns(2, gap="small")
    top = read_csv(TOP_SPOTLIGHT)
    if top is not None:
        cohort = pick(top, "cohort") or "cohort"
        rank = pick(top, "rank") or first_existing(top, ["rank_within_cohort"])
        name = pick(top, "holding_name") or "holding_name"
        ticker = pick(top, "ticker") or "ticker"
        share = pick(top, "share", "pct") or "share_of_total_aum_pct"
        etfsn = pick(top, "num_etfs", "#etfs", "fund") or "num_etfs"
        tags = pick(top, "screen_categories", "tags") or "screen_categories"
        cols = [rank, ticker, name, share, etfsn, tags]
        rename_map = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}

        with s1:
            st.markdown("<div class='minor-h'>Top Controversial</div>", unsafe_allow_html=True)
            tc = top[top[cohort].str.lower()=="controversial"][cols].rename(columns=rename_map).copy()
            tc["Share of AUM (%)"] = pd.to_numeric(tc["Share of AUM (%)"], errors="coerce").round(4)
            st.dataframe(tc.head(5), use_container_width=True, hide_index=True)
            with st.expander("Show full list"):
                st.dataframe(tc.head(10), use_container_width=True, hide_index=True)

        with s2:
            st.markdown("<div class='minor-h'>Top Clean</div>", unsafe_allow_html=True)
            tg = top[top[cohort].str.lower()=="clean"][cols].rename(columns=rename_map).copy()
            tg["Share of AUM (%)"] = pd.to_numeric(tg["Share of AUM (%)"], errors="coerce").round(4)
            st.dataframe(tg.head(5), use_container_width=True, hide_index=True)
            with st.expander("Show full list"):
                st.dataframe(tg.head(10), use_container_width=True, hide_index=True)

    # ---------- A2: Change since 2017 ----------
    st.markdown("<div class='section-2017'>Change since 2017</div>", unsafe_allow_html=True)

    colL, colR = st.columns([0.55, 0.45])
    with colL:
        weighting = st.radio("Weighting", ["AUM-weighted", "Equal-weighted"], horizontal=True, index=0)
    with colR:
        yc = read_csv(YEAR_COMPARE)
        if yc is not None:
            ycol = pick(yc, "year") or "year"
            years = sorted(yc[ycol].unique().tolist())
        else:
            years = list(range(2017, 2026))
        cA, cB = st.columns(2)
        with cA:
            year_a = st.selectbox("Year A", years, index=0)
        with cB:
            year_b = st.selectbox("Year B", years, index=len(years)-1)

    agg = read_csv(AGG_TRENDS)
    if agg is not None:
        wcol = pick(agg, "weighting", "agg", "type", "view")
        ycol = pick(agg, "year") or "year"
        clean = pick(agg, "clean", contains_all=["pct"])
        contro = pick(agg, "contro", contains_all=["pct"])

        if wcol is not None and agg[wcol].dtype == "O":
            key = "aum" if "AUM" in weighting.upper() else "ew"
            filt = agg[agg[wcol].str.lower().str.contains(key, na=False)]
        else:
            filt = agg.copy()

        y_min = int(np.nanmin(filt[ycol])) if ycol else 2017
        y_max = int(np.nanmax(filt[ycol])) if ycol else 2025
        y17 = filt[filt[ycol] == y_min] if ycol else pd.DataFrame()
        y25 = filt[filt[ycol] == y_max] if ycol else pd.DataFrame()
        d_clean = (y25[clean].mean() - y17[clean].mean()) if (clean and len(y17) and len(y25)) else np.nan
        d_contro = (y25[contro].mean() - y17[contro].mean()) if (contro and len(y17) and len(y25)) else np.nan
    else:
        d_clean = d_contro = np.nan

    m1, m2 = st.columns(2)
    m1.metric("Δ Clean (2017 → 2025)", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
    m2.metric("Δ Controversial (2017 → 2025)", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")

    left2, right2 = st.columns([0.58, 0.42], gap="small")
    with left2:
        st.markdown("<div class='minor-h'>Trend (Clean / Controversial / Other)</div>", unsafe_allow_html=True)
        if agg is not None:
            st.altair_chart(line_trends(agg, weighting), use_container_width=True)
    with right2:
        disp = read_csv(DISPERSION)
        st.markdown("<div class='minor-h'>Cross-fund dispersion (Controversial)</div>", unsafe_allow_html=True)
        if disp is not None:
            rib = ribbon_from_dispersion(disp, weighting)
            if rib is not None:
                st.altair_chart(rib, use_container_width=True)

    st.markdown("<div class='minor-h'>Heatmap: % Controversial by ETF × Year</div>", unsafe_allow_html=True)
    byfy = read_csv(BY_FUND_YEAR)
    if byfy is not None:
        hm = heatmap_by_fund_year(byfy, metric="controversial")
        if hm is not None:
            st.altair_chart(hm, use_container_width=True)

    st.markdown("<div class='minor-h'>Year vs Year (stacked share)</div>", unsafe_allow_html=True)
    yc2 = read_csv(YEAR_COMPARE)
    if yc2 is not None:
        st.altair_chart(stacked_year_compare(yc2, weighting, year_a, year_b), use_container_width=True)

    st.markdown(
        "<div class='pairhead'>"
        "<div class='minor-h'>Screen trends (AUM-weighted)</div>"
        "<span class='infopill' title='Screen categories can overlap; their series are not meant to sum to overall controversial exposure.'>ⓘ</span>"
        "</div>", unsafe_allow_html=True
    )
    scr = read_csv(SCREEN_TRENDS)
    if scr is not None:
        st.altair_chart(screen_small_multiples(scr, "AUM" if "AUM" in weighting.upper() else "EW"), use_container_width=True)

    st.markdown("<div class='minor-h'>Top movers (Year A → Year B)</div>", unsafe_allow_html=True)
    mov = read_csv(MOVERS)
    if mov is not None:
        ya = pick(mov, "year_a", "from_year")
        yb = pick(mov, "year_b", "to_year")
        if ya and yb:
            mov = mov[(mov[ya]==year_a) & (mov[yb]==year_b)]
        name = pick(mov, "holding_name", "name")
        tic = pick(mov, "ticker")
        delta = pick(mov, "delta", "change")
        num = pick(mov, "num_etfs", "fund_count", "#etfs")
        cols = [tic, name, delta, num]
        cols = [c for c in cols if c in mov.columns]
        if cols:
            tidy = mov[cols].rename(columns={tic:"Ticker", name:"Name",
                                             delta:"Δ contribution (pp)", num:"#ETFs"}).copy()
            if "Δ contribution (pp)" in tidy.columns:
                tidy["Δ contribution (pp)"] = pd.to_numeric(tidy["Δ contribution (pp)"], errors="coerce")
                up = tidy.sort_values("Δ contribution (pp)", ascending=False).head(10).reset_index(drop=True)
                dn = tidy.sort_values("Δ contribution (pp)", ascending=True).head(10).reset_index(drop=True)
            else:
                up = tidy.head(10); dn = tidy.head(10)
            t1, t2 = st.columns(2)
            with t1:
                st.subheader("Largest increases", divider=False)
                st.dataframe(up, use_container_width=True, hide_index=True)
            with t2:
                st.subheader("Largest decreases", divider=False)
                st.dataframe(dn, use_container_width=True, hide_index=True)

# =======================================================
# Report tab
# =======================================================
with tab_report:
    st.header("Report")
    st.markdown("Context, methods, results highlights, and notes will appear here.")

# ------------------------ Footer ------------------------
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
