import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; color:#E6E9EF; background:#0B0C10; }
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
      h1,h2,h3 { letter-spacing:0.2px; }
      .subtle { color:#9AA4B2; }
      .footer { margin-top: 28px; padding-top: 14px; border-top:1px solid #2A2F36; display:flex; justify-content:space-between; align-items:center; }
      .footer a { color:#E6E9EF; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1.0; text-decoration:underline; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#121419; border:1px solid #2A2F36; font-size:12px; color:#9AA4B2; margin-right:8px; }
      .asof { font-size:12px; color:#9AA4B2; text-align:right; }
      .muted-accent { background:#191c22; border:1px solid #2A2F36; color:#C9D2DF; padding:6px 10px; border-radius:8px; display:inline-block; }
      .stTabs [data-baseweb="tab-list"] { gap: 18px; }
      .stTabs [data-baseweb="tab-list"] button { font-weight:600; color:#E6E9EF; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color:#63A4E9; border-bottom:3px solid #63A4E9; }
      .tight { margin-top:-8px; }
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
HOLDINGS_EXPLORER = AN1 / "holdings_explorer_2025.csv"
AGG_TRENDS = AN2 / "aggregate_exposure_trends.csv"

CLEAN_COLOR = "#0A8F6A"
CONTRO_COLOR = "#B63C3C"
OTHER_COLOR = "#4B5865"

@st.cache_data
def read_csv(p: Path):
    return pd.read_csv(p) if p.exists() else None

def pick(df, fns):
    low = {c.lower(): c for c in df.columns}
    for fn in fns:
        for k,v in low.items():
            if fn(k):
                return v
    return None

def get_asof(df):
    c = pick(df, [lambda s: s in ("as_of_date","as-of date","asof","as_of")])
    return df[c].iloc[0] if c else "2025"

def kpis_from_ctx(df):
    cls = pick(df, [lambda s: s=="classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s=="share_pct" or s=="share"])
    aum_col = pick(df, [lambda s: "total_aum_usd" in s or s=="aum_usd" or s=="total_aum"])
    pct_con = float(df.loc[df[cls].str.lower()=="controversial", share].sum())
    pct_clean = float(df.loc[df[cls].str.lower()=="clean", share].sum())
    total_aum = float(df[aum_col].iloc[0]) if aum_col else np.nan
    return pct_con, pct_clean, total_aum

def deltas_from_trends(df):
    ycol = pick(df, [lambda s: s=="year"])
    clean_col = pick(df, [lambda s: ("clean" in s and "pct" in s) or s in ("pct_clean","clean_pct","clean_percent")])
    contro_col = pick(df, [lambda s: ("controversial" in s and "pct" in s) or s in ("pct_controversial","controversial_pct")])
    d = df
    y17 = d.loc[d[ycol]==2017]
    y25 = d.loc[d[ycol]==2025]
    dc = float(y25[clean_col].mean() - y17[clean_col].mean()) if len(y17) and len(y25) else np.nan
    dv = float(y25[contro_col].mean() - y17[contro_col].mean()) if contro_col and len(y17) and len(y25) else np.nan
    return dc, dv

def chart_composition(df):
    cls = pick(df, [lambda s: s=="classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s=="share_pct" or s=="share"])
    m = df[[cls, share]].groupby(cls, as_index=False).sum()
    order = pd.Categorical(m[cls], categories=["Clean","Controversial","Other"], ordered=True)
    m = m.assign(order=order).sort_values("order")
    colors = {"Clean":CLEAN_COLOR,"Controversial":CONTRO_COLOR,"Other":OTHER_COLOR}
    return alt.Chart(m).mark_bar().encode(
        x=alt.X(f"{share}:Q", stack="normalize", axis=alt.Axis(format="%")),
        color=alt.Color(cls, scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None),
        tooltip=[alt.Tooltip(cls, title="Category"), alt.Tooltip(share, title="Share of AUM", format=".1f")]
    ).properties(height=140)

def chart_by_screen(df):
    cat = pick(df, [lambda s: s in ("screen_category","screen_categories","category")])
    cls = pick(df, [lambda s: s=="classification"])
    share = pick(df, [lambda s: "share_of_total_aum_pct" in s or s=="share_pct" or s=="share"])
    d = df[[cat, cls, share]].copy()
    d[cat] = d[cat].astype(str)
    d = d.groupby([cat, cls], as_index=False)[share].sum()
    colors = {"Controversial":CONTRO_COLOR,"Clean":CLEAN_COLOR}
    return alt.Chart(d).mark_bar().encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=""),
        x=alt.X(f"{share}:Q", axis=alt.Axis(format="%")),
        color=alt.Color(f"{cls}:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip(cat, title="Screen"), alt.Tooltip(cls, title="Cohort"), alt.Tooltip(share, title="Share of AUM", format=".1f")]
    ).properties(height=200)

st.markdown("## BlackRock ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)")
st.caption("We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.")

tab_dash, tab_report = st.tabs(["Dashboard","Report"])

with tab_dash:
    ctx = read_csv(CTX_SUMMARY)
    agg = read_csv(AGG_TRENDS)
    asof = get_asof(ctx) if ctx is not None else "2025"

    c1,c2 = st.columns([0.7,0.3])
    with c1:
        st.markdown("<span class='muted-accent'>All ESG ETFs</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='asof'>As of: {asof}</div>", unsafe_allow_html=True)

    st.markdown("### Overview")
    k1,k2,k3,k4,k5 = st.columns(5)
    if ctx is not None:
        pct_con, pct_clean, total_aum = kpis_from_ctx(ctx)
        k1.metric("% Controversial", f"{pct_con:.1f}%")
        k2.metric("% Clean", f"{pct_clean:.1f}%")
        k3.metric("Total AUM", f"${total_aum:,.0f}" if pd.notna(total_aum) else "—")
    else:
        k1.metric("% Controversial", "—")
        k2.metric("% Clean", "—")
        k3.metric("Total AUM", "—")
    if agg is not None:
        d_clean, d_contro = deltas_from_trends(agg)
        k4.metric("Δ Clean since 2017", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
        k5.metric("Δ Controversial since 2017", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")
    else:
        k4.metric("Δ Clean since 2017", "—")
        k5.metric("Δ Controversial since 2017", "—")

    st.markdown("### 2025 Composition")
    cA, cB = st.columns([0.55,0.45])
    with cA:
        if ctx is not None:
            st.altair_chart(chart_composition(ctx), use_container_width=True)
        else:
            st.empty()
    with cB:
        byscreen = read_csv(CTX_BYSCREEN)
        if byscreen is not None:
            st.altair_chart(chart_by_screen(byscreen), use_container_width=True)
            st.caption("Categories can overlap; totals won’t sum to overall controversial exposure.")
        else:
            st.empty()

    st.markdown("### Spotlight", help="Largest contributors to total AUM exposure")
    s1,s2 = st.columns(2)
    top = read_csv(TOP_SPOTLIGHT)
    if top is not None:
        cohort = pick(top, [lambda s: s=="cohort"])
        rank = pick(top, [lambda s: "rank" in s])
        name = pick(top, [lambda s: s in ("holding_name","name")])
        ticker = pick(top, [lambda s: s=="ticker"])
        share = pick(top, [lambda s: "share_of_total_aum_pct" in s or "share_pct"==s])
        etfsn = pick(top, [lambda s: s in ("num_etfs","#etfs","count_etfs")])
        tags = pick(top, [lambda s: "screen_categories" in s or s=="tags"])
        top_c = top[top[cohort].str.lower()=="controversial"].copy()
        top_g = top[top[cohort].str.lower()=="clean"].copy()
        cols = [rank, ticker, name, share, etfsn, tags]
        rename_map = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}
        with s1:
            st.subheader("Top Controversial")
            if not top_c.empty:
                dfv = top_c[cols].rename(columns=rename_map)
                dfv["Share of AUM (%)"] = dfv["Share of AUM (%)"].map(lambda x: round(float(x),4))
                st.dataframe(dfv, use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame(), use_container_width=True)
        with s2:
            st.subheader("Top Clean")
            if not top_g.empty:
                dfv = top_g[cols].rename(columns=rename_map)
                dfv["Share of AUM (%)"] = dfv["Share of AUM (%)"].map(lambda x: round(float(x),4))
                st.dataframe(dfv, use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame(), use_container_width=True)
    else:
        with s1: st.dataframe(pd.DataFrame(), use_container_width=True)
        with s2: st.dataframe(pd.DataFrame(), use_container_width=True)

    st.markdown("### Downloads")
    d1, d2, d3, d4 = st.columns(4)
    if CTX_SUMMARY.exists():
        with d1:
            st.download_button("context_summary_2025.csv", data=CTX_SUMMARY.read_bytes(), file_name="context_summary_2025.csv")
    if CTX_BYSCREEN.exists():
        with d2:
            st.download_button("context_breakdown_by_screen.csv", data=CTX_BYSCREEN.read_bytes(), file_name="context_breakdown_by_screen.csv")
    if TOP_SPOTLIGHT.exists():
        with d3:
            st.download_button("top_holdings_spotlight.csv", data=TOP_SPOTLIGHT.read_bytes(), file_name="top_holdings_spotlight.csv")
    if HOLDINGS_EXPLORER.exists():
        with d4:
            st.download_button("holdings_explorer_2025.csv", data=HOLDINGS_EXPLORER.read_bytes(), file_name="holdings_explorer_2025.csv")

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
