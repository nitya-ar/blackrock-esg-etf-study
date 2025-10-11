import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      html, body, [class*="css"] { font-family: Avenir, "Avenir Next", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color:#E6E9EF; background:#0B0C10; }
      .block-container { padding-top: 32px; padding-bottom: 32px; max-width: 1200px; }
      .brandrow { display:flex; align-items:center; gap:16px; margin-bottom:6px; }
      .brandrow h2 { margin:0; font-size:28px; font-weight:700; letter-spacing:.2px; }
      .footer { margin-top: 18px; padding-top: 14px; border-top:1px solid #2A2F36; display:flex; justify-content:space-between; align-items:center; }
      .footer a { color:#E6E9EF; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1; text-decoration:underline; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#121419; border:1px solid #2A2F36; font-size:12px; color:#9AA4B2; margin-right:8px; }
      .muted-accent { background:#191c22; border:1px solid #2A2F36; color:#C9D2DF; padding:6px 10px; border-radius:8px; display:inline-block; }
      .asof { font-size:12px; color:#9AA4B2; text-align:right; }
      div[data-testid="stMetric"] { padding: 0 4px; }
      div[data-testid="stMetricValue"] { font-size: 26px; }
      div[data-testid="stMetricLabel"] { font-size: 13px; color:#C9D2DF; }
      div[data-testid="stMetricDelta"] { font-size: 12px; }
      .section-2025 { font-size:34px; font-weight:800; margin:8px 0 6px 0; }
      .minor-h { font-size:18px; font-weight:700; margin:10px 0 6px 0; }
      .section-title { font-size:28px; font-weight:800; margin:26px 0 12px; }
      .infopill { font-size:12px; color:#C8DAFF; background:#1A2437; border:1px solid #334a78; padding:2px 8px; border-radius:999px; cursor:help; }
      .infopill:hover { filter:brightness(1.1); }
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

CLEAN_COLOR = "#0A6F56"
CONTRO_COLOR = "#8F3131"
OTHER_COLOR = "#414B55"

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
    colors = {"Clean": CLEAN_COLOR, "Controversial": CONTRO_COLOR, "Other": OTHER_COLOR}
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
    colors = {"Controversial": CONTRO_COLOR, "Clean": CLEAN_COLOR}
    return alt.Chart(d).mark_bar().encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=""),
        x=alt.X("_plot_share:Q", axis=alt.Axis(format="%", title="Share of total AUM")),
        color=alt.Color(f"{cls}:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip(cat, title="Screen"), alt.Tooltip(cls, title="Cohort"), alt.Tooltip(share, title="Share of total AUM (%)", format=".1f")]
    ).properties(height=230)

def chart_trend_agg(df, weighting_key):
    ycol = pick(df, [lambda s: s == "year"])
    wcol = pick(df, [lambda s: s in ("weighting","agg_type","type")])
    clean_col = pick(df, [lambda s: ("clean" in s and "pct" in s) or s in ("pct_clean","clean_pct","clean_percent")])
    contro_col = pick(df, [lambda s: ("controversial" in s and "pct" in s) or s in ("pct_controversial","controversial_pct")])
    other_col = pick(df, [lambda s: ("other" in s and "pct" in s) or s in ("pct_other","other_pct")])
    if not all([ycol, clean_col, contro_col, other_col]):
        return None
    d = df if wcol is None else df[df[wcol].str.lower().str.contains(weighting_key)]
    melt = d[[ycol, clean_col, contro_col, other_col]].rename(columns={clean_col:"Clean", contro_col:"Controversial", other_col:"Other"})
    melt = melt.melt(id_vars=[ycol], var_name="Cohort", value_name="pct")
    melt["_plot"] = ensure_0_1(melt["pct"])
    colors = {"Clean": CLEAN_COLOR, "Controversial": CONTRO_COLOR, "Other": OTHER_COLOR}
    return alt.Chart(melt).mark_line(point=False).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y("_plot:Q", axis=alt.Axis(format="%", title="Portfolio share")),
        color=alt.Color("Cohort:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title=""))
    ).properties(height=220)

def chart_year_vs_year(df, weighting_key, year_a, year_b):
    ycol = pick(df, [lambda s: s == "year"])
    wcol = pick(df, [lambda s: s in ("weighting","agg_type","type")])
    clean_col = pick(df, [lambda s: ("clean" in s and "pct" in s) or s in ("pct_clean","clean_pct","clean_percent")])
    contro_col = pick(df, [lambda s: ("controversial" in s and "pct" in s) or s in ("pct_controversial","controversial_pct")])
    other_col = pick(df, [lambda s: ("other" in s and "pct" in s) or s in ("pct_other","other_pct")])
    if not all([ycol, clean_col, contro_col, other_col]):
        return None
    d = df if wcol is None else df[df[wcol].str.lower().str.contains(weighting_key)]
    sub = d[d[ycol].isin([year_a, year_b])][[ycol, clean_col, contro_col, other_col]].rename(columns={clean_col:"Clean", contro_col:"Controversial", other_col:"Other"})
    m = sub.melt(id_vars=[ycol], var_name="Cohort", value_name="pct")
    m["_plot"] = ensure_0_1(m["pct"])
    colors = {"Clean": CLEAN_COLOR, "Controversial": CONTRO_COLOR, "Other": OTHER_COLOR}
    return alt.Chart(m).mark_bar().encode(
        x=alt.X(f"{ycol}:O", title=""),
        y=alt.Y("_plot:Q", stack="normalize", axis=alt.Axis(format="%", title="Portfolio share")),
        color=alt.Color("Cohort:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title=""))
    ).properties(height=220)

def chart_heatmap_by_fund_year(df):
    fund = pick(df, [lambda s: s in ("etf","etf_ticker","fund","ticker","etf_symbol")])
    ycol = pick(df, [lambda s: s == "year"])
    pctc = pick(df, [lambda s: ("controversial" in s and "pct" in s) or s in ("pct_controversial","controversial_pct")])
    if not all([fund, ycol, pctc]):
        return None
    d = df[[fund, ycol, pctc]].dropna()
    d["_plot"] = ensure_0_1(d[pctc])
    return alt.Chart(d).mark_rect().encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y(f"{fund}:N", title="ETF"),
        color=alt.Color("_plot:Q", scale=alt.Scale(scheme="reds"), legend=alt.Legend(title="% share", format="%"))
    ).properties(height=380, use_container_width=True)

def chart_screen_trends(df):
    ycol = pick(df, [lambda s: s == "year"])
    cat = pick(df, [lambda s: s in ("screen_category","screen","category")])
    share = pick(df, [lambda s: "pct" in s or "share" in s])
    if not all([ycol, cat, share]):
        return None
    d = df[[ycol, cat, share]].dropna().copy()
    d["_plot"] = ensure_0_1(d[share])
    return alt.Chart(d).mark_line().encode(
        x=alt.X(f"{ycol}:O", title=""),
        y=alt.Y("_plot:Q", axis=alt.Axis(format="%", title="AUM-weighted share")),
        facet=alt.Facet(f"{cat}:N", columns=1, title=None),
        color=alt.value(CONTRO_COLOR)
    ).properties(height=140)

def movers_tables(df, year_a, year_b):
    ya = pick(df, [lambda s: s in ("year_a","yeara","start_year","from_year")])
    yb = pick(df, [lambda s: s in ("year_b","yearb","end_year","to_year")])
    name = pick(df, [lambda s: s in ("holding_name","name")])
    ticker = pick(df, [lambda s: s == "ticker"])
    delta = pick(df, [lambda s: "delta" in s or "change" in s or "d_contribution" in s or "contribution_delta" in s])
    d = df.copy()
    if ya and yb:
        d = d[(d[ya] == year_a) & (d[yb] == year_b)]
    d[delta] = pd.to_numeric(d[delta], errors="coerce")
    inc = d.sort_values(delta, ascending=False).head(10)[[ticker, name, delta]].rename(columns={ticker:"Ticker", name:"Name", delta:"Δ contribution (pp)"})
    dec = d.sort_values(delta, ascending=True).head(10)[[ticker, name, delta]].rename(columns={ticker:"Ticker", name:"Name", delta:"Δ contribution (pp)"})
    return inc, dec

def render_top_exposures_block(top_df):
    if top_df is None or top_df.empty:
        return
    cohort = pick(top_df, [lambda s: s == "cohort"])
    rank   = pick(top_df, [lambda s: "rank" in s])
    name   = pick(top_df, [lambda s: s in ("holding_name","name")])
    ticker = pick(top_df, [lambda s: s == "ticker"])
    share  = pick(top_df, [lambda s: "share_of_total_aum_pct" in s or s == "share_pct"])
    etfsn  = pick(top_df, [lambda s: s in ("num_etfs","#etfs","count_etfs")])
    tags   = pick(top_df, [lambda s: "screen_categories" in s or s == "tags"])
    cols = [rank, ticker, name, share, etfsn, tags]
    ren  = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}
    st.markdown("<div class='section-title'>Top Exposures (2025)</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    with c1:
        h1, h2 = st.columns([0.65, 0.35])
        with h1:
            st.markdown("<div class='minor-h'>Top Controversial</div>", unsafe_allow_html=True)
        with h2:
            show_all_tc = st.toggle("Show full list", value=False, key="toggle_tc")
        tc = top_df[top_df[cohort].str.lower()=="controversial"][cols].rename(columns=ren).copy()
        tc["Share of AUM (%)"] = pd.to_numeric(tc["Share of AUM (%)"], errors="coerce").round(4)
        rows_tc = 10 if show_all_tc else 5
        st.dataframe(tc.head(rows_tc), use_container_width=True, hide_index=True, height=(rows_tc+1)*32 + 24)
    with c2:
        h3, h4 = st.columns([0.65, 0.35])
        with h3:
            st.markdown("<div class='minor-h'>Top Clean</div>", unsafe_allow_html=True)
        with h4:
            show_all_tg = st.toggle("Show full list", value=False, key="toggle_tg")
        tg = top_df[top_df[cohort].str.lower()=="clean"][cols].rename(columns=ren).copy()
        tg["Share of AUM (%)"] = pd.to_numeric(tg["Share of AUM (%)"], errors="coerce").round(4)
        rows_tg = 10 if show_all_tg else 5
        st.dataframe(tg.head(rows_tg), use_container_width=True, hide_index=True, height=(rows_tg+1)*32 + 24)

st.markdown(
    """
    <div class="brandrow">
      <img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/BlackRock_wordmark.svg" alt="BlackRock" style="height:32px; filter:brightness(0) invert(1);">
      <h2>ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.")

tab_dash, tab_report = st.tabs(["Dashboard","Report"])

with tab_dash:
    ctx = read_csv(CTX_SUMMARY)
    byscreen = read_csv(CTX_BYSCREEN)
    top = read_csv(TOP_SPOTLIGHT)
    agg = read_csv(AGG_TRENDS)
    byfy = read_csv(BY_FUND_YEAR)
    yearcmp = read_csv(YEAR_COMPARE)
    screentr = read_csv(SCREEN_TRENDS)
    movers = read_csv(MOVERS)

    asof = get_asof(ctx) if ctx is not None else "2025"

    c1, c2 = st.columns([0.65, 0.35])
    with c1:
        st.markdown("<span class='muted-accent'>All ESG ETFs</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='asof'>As of: {asof}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-2025'>2025 Overview</div>", unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns([0.18, 0.18, 0.26, 0.19, 0.19], gap="small")
    if ctx is not None:
        pct_con, pct_clean, total_aum = kpis_from_ctx(ctx)
        k1.metric("% Controversial", f"{pct_con:.1f}%")
        k2.metric("% Clean", f"{pct_clean:.1f}%")
        k3.metric("Total AUM", f"${total_aum:,.0f}" if pd.notna(total_aum) else "—")
    else:
        k1.metric("% Controversial", "—")
        k2.metric("% Clean", "—")
        k3.metric("Total AUM", "—")

    weighting_key = "aum"
    if agg is not None:
        d_clean, d_contro = deltas_from_trends(agg, weighting_key)
        k4.metric("Δ Clean since 2017", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
        k5.metric("Δ Controversial since 2017", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")
    else:
        k4.metric("Δ Clean since 2017", "—")
        k5.metric("Δ Controversial since 2017", "—")

    left, right = st.columns([0.48, 0.52], gap="small")
    with left:
        st.markdown("<div class='minor-h'>Composition & Screens (2025)</div>", unsafe_allow_html=True)
        if ctx is not None:
            st.altair_chart(chart_composition(ctx), use_container_width=True)
    with right:
        st.markdown(
            "<div style='display:flex; justify-content:flex-end; margin:2px 0 4px 0;'>"
            "<span class='infopill' title='Categories can overlap; totals won’t sum to overall controversial exposure.'>ⓘ</span>"
            "</div>",
            unsafe_allow_html=True
        )
        if byscreen is not None:
            st.altair_chart(chart_by_screen(byscreen), use_container_width=True)

    render_top_exposures_block(top)

    st.markdown("<div class='section-title'>Change since 2017</div>", unsafe_allow_html=True)

    cw1, cw2, cw3 = st.columns([0.25, 0.35, 0.4])
    with cw1:
        weighting = st.radio("Weighting", ["AUM-weighted", "Equal-weighted"], horizontal=True, index=0)
        key = "aum" if "AUM" in weighting else "equal"
    with cw2:
        years = sorted(agg["year"].unique().tolist()) if agg is not None and "year" in agg.columns else list(range(2017, 2025+1))
        year_a = st.selectbox("Year A", years, index=0)
    with cw3:
        year_b = st.selectbox("Year B", years, index=len(years)-1)

    kdc1, kdc2 = st.columns(2)
    if agg is not None:
        d_clean, d_contro = deltas_from_trends(agg, key)
        kdc1.metric("Δ Clean (2017 → 2025)", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
        kdc2.metric("Δ Controversial (2017 → 2025)", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")
    else:
        kdc1.metric("Δ Clean (2017 → 2025)", "—")
        kdc2.metric("Δ Controversial (2017 → 2025)", "—")

    tr1, tr2 = st.columns(2, gap="large")
    if agg is not None:
        trend = chart_trend_agg(agg, key)
        if trend is not None:
            tr1.altair_chart(trend, use_container_width=True)
        yvy = chart_year_vs_year(agg, key, year_a, year_b)
        if yvy is not None:
            tr2.altair_chart(yvy, use_container_width=True)

    st.markdown("<div class='minor-h'>Heatmap: % Controversial by ETF × Year</div>", unsafe_allow_html=True)
    if byfy is not None:
        hm = chart_heatmap_by_fund_year(byfy)
        if hm is not None:
            st.altair_chart(hm, use_container_width=True)

    with st.expander("Screen trends (AUM-weighted)"):
        if screentr is not None:
            st.altair_chart(chart_screen_trends(screentr), use_container_width=True)

    if movers is not None:
        inc, dec = movers_tables(movers, year_a, year_b)
        st.markdown("<div class='minor-h'>Top movers (Year A → Year B)</div>", unsafe_allow_html=True)
        mv1, mv2 = st.columns(2, gap="large")
        with mv1:
            st.subheader("Largest increases")
            st.dataframe(inc, use_container_width=True, hide_index=True)
        with mv2:
            st.subheader("Largest decreases")
            st.dataframe(dec, use_container_width=True, hide_index=True)

with tab_report:
    st.header("Report")
    st.markdown("Context, methods, results highlights, and notes will appear here.")

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
