# app.py — BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
# Logos removed. Subtle shaded bar charts. Original footer (right-aligned, bold blue links).

import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st

# ====================
# CONFIG
# ====================
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution, Tradeoffs",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

GITHUB_USER_REPO = st.secrets.get("ESG_REPO", os.getenv("ESG_REPO", "nitya-ar/blackrock-esg-etf-study"))
GITHUB_BRANCH    = st.secrets.get("ESG_BRANCH", os.getenv("ESG_BRANCH", "main"))
DASH_BASE_PATH   = st.secrets.get("ESG_DASH_PATH", os.getenv("ESG_DASH_PATH", "Data/Data for Dashboard"))
LOCAL_BASE       = st.secrets.get("ESG_LOCAL_BASE", os.getenv("ESG_LOCAL_BASE", ""))  # optional
GITHUB_TOKEN     = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))      # optional
ANALYSIS_DIRS = {1: "Analysis 1", 2: "Analysis 2", 3: "Analysis 3"}

# Dark-but-bright palette
COLORS = {
    "bg": "#0A0B0D",
    "card": "#0F1116",
    "border": "#1C2027",
    "text": "#E7EBF0",
    "muted": "#97A2B0",
    "primary": "#00A3FF",
    "clean": "#0E8F66",
    "contro": "#C63C41",
    "other": "#768397",
}

# =========================
# STYLES
# =========================
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

      :root {{
        --bg: {COLORS['bg']};
        --card: {COLORS['card']};
        --border: {COLORS['border']};
        --text: {COLORS['text']};
        --muted: {COLORS['muted']};
        --primary: {COLORS['primary']};
        --clean: {COLORS['clean']};
        --contro: {COLORS['contro']};
        --other: {COLORS['other']};
      }}

      html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }}

      h1, h2, h3, h4, h5 {{ color: var(--text); letter-spacing: .1px; }}
      .blx-divider {{ border-top: 1px solid var(--border); margin: 10px 0 24px 0; }}
      .blx-muted {{ color: var(--muted); }}

      .blx-card {{
        background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 16px;
      }}

      .kpi {{
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
      }}
      .kpi .label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
      .kpi .value {{ font-size: 30px; font-weight: 700; line-height: 1.05; }}

      .kpi.kpi-red {{ background: linear-gradient(180deg, rgba(198,60,65,0.16), rgba(255,255,255,0)); border-color: rgba(198,60,65,0.45); }}
      .kpi.kpi-green {{ background: linear-gradient(180deg, rgba(14,143,102,0.16), rgba(255,255,255,0)); border-color: rgba(14,143,102,0.45); }}
      .kpi.kpi-neutral {{ background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0)); border-color: rgba(255,255,255,0.08); }}

      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{ border-color: var(--primary) !important; }}

      div[data-testid="stDataframe"] thead tr th {{ background: #0C0E13 !important; color: var(--text) !important; border-bottom: 1px solid var(--border) !important; }}
      div[data-testid="stDataframe"] tbody tr {{ background: #0E1015 !important; }}
      div[data-testid="stDataframe"] * {{ font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important; font-size: 13px !important; }}

      .chart-head {{ display:flex; align-items:center; justify-content:space-between; margin: 4px 2px 8px 2px; }}
      .chart-title {{ font-weight: 600; color: var(--text); letter-spacing:.1px; }}
      .info-badge {{
        display:inline-flex; align-items:center; justify-content:center;
        height: 24px; min-width: 24px; border-radius: 14px;
        border: 1px solid #2A2F36; color: #B6C0CC; font-weight: 700;
        font-size: 12px; user-select:none; cursor: default;
        background: #0B0D12; padding: 0 8px;
      }}
      .has-tip {{ position: relative; }}
      .has-tip::after {{
        content: attr(data-tip);
        position: absolute; right: 0; top: calc(100% + 8px);
        background: #0B0D12; color: var(--text);
        border: 1px solid var(--border);
        padding: 6px 10px; border-radius: 8px;
        white-space: nowrap; opacity: 0; transform: translateY(6px);
        pointer-events: none; transition: opacity .15s ease, transform .15s ease;
        box-shadow: 0 10px 24px rgba(0,0,0,.45); z-index: 9999;
      }}
      .has-tip:hover::after {{ opacity: 1; transform: translateY(0); }}

      .footer-wrap {{ display:flex; align-items:center; justify-content:space-between; width:100%; }}
      .footer-left {{ color: var(--muted); font-size: 13px; }}
      .footer-links {{ display:flex; gap:24px; align-items:center; justify-content:flex-end; width:100%; }}
      .footer-links a {{ color: #4DA3FF !important; text-decoration: none; font-size: 15px; font-weight: 700; }}
      .footer-links a:hover {{ text-decoration: underline; }}
    </style>
    """,
    unsafe_allow_html=True,
)

def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

def gap(px=6):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

# =========================
# DATA LOADER
# =========================
def _url_join(*parts: str) -> str:
    path = "/".join(p.strip("/").replace("\\", "/") for p in parts if p)
    return "/".join(urllib.parse.quote(s, safe=":/") for s in path.split("/"))

def github_raw_url(analysis: int, filename: str) -> str:
    rel = _url_join(DASH_BASE_PATH, ANALYSIS_DIRS[analysis], filename)
    return f"https://raw.githubusercontent.com/{GITHUB_USER_REPO}/{GITHUB_BRANCH}/{rel}"

def github_api_url(analysis: int, filename: str) -> str:
    rel = _url_join(DASH_BASE_PATH, ANALYSIS_DIRS[analysis], filename)
    return f"https://api.github.com/repos/{GITHUB_USER_REPO}/contents/{rel}?ref={GITHUB_BRANCH}"

def local_path(analysis: int, filename: str) -> str:
    if not LOCAL_BASE:
        return ""
    return os.path.join(LOCAL_BASE, ANALYSIS_DIRS[analysis], filename)

@st.cache_data(show_spinner=False)
def load_csv(analysis: int, filename: str) -> pd.DataFrame:
    lp = local_path(analysis, filename)
    if lp and os.path.exists(lp):
        return pd.read_csv(lp)
    raw_url = github_raw_url(analysis, filename)
    try:
        return pd.read_csv(raw_url)
    except Exception as e_raw:
        api_url = github_api_url(analysis, filename)
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        try:
            r = requests.get(api_url, headers=headers, timeout=25)
            r.raise_for_status()
            return pd.read_csv(StringIO(r.text))
        except Exception as e_api:
            raise FileNotFoundError(
                f"Failed to load {filename}. Tried local, public raw, and API.\nraw={e_raw}; api={e_api}"
            )

# Analysis 1 loaders
@st.cache_data(show_spinner=False)
def load_context_summary():   return load_csv(1, "context_summary_2025.csv")
@st.cache_data(show_spinner=False)
def load_by_screen():         return load_csv(1, "context_breakdown_by_screen.csv")
@st.cache_data(show_spinner=False)
def load_spotlight():         return load_csv(1, "top_holdings_spotlight.csv")
@st.cache_data(show_spinner=False)
def load_explorer():
    df = load_csv(1, "holdings_explorer_2025.csv")
    for col in ["classification","sector","region","screen_categories"]:
        if col in df.columns: df[col] = df[col].fillna("")
    if "screen_categories" in df.columns:
        scn = (
            df["screen_categories"].astype(str)
            .str.split(r"\s*\|\s*")
            .apply(lambda xs: [x.strip() for x in xs if x and x.lower() != "nan"])
        )
    else:
        scn = [[] for _ in range(len(df))]
    df["_screen_categories_norm"] = scn

    rename_map = {
        "etf_ticker":"ETF","etf_name":"ETF Name","ticker":"Ticker","holding_name":"Holding",
        "sector":"Sector","region":"Region","classification":"Class","screen_categories":"Screens",
        "weight_pct_in_etf":"Weight % in ETF","aum_usd":"ETF AUM (USD)","weight_usd_in_agg":"$ Contribution (Agg)",
        "as_of_date":"As-of",
    }
    df_disp = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})
    ordered = [c for c in [
        "ETF","ETF Name","Ticker","Holding","Sector","Region","Class","Screens",
        "Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)","As-of"
    ] if c in df_disp.columns]
    df_disp = df_disp[ordered]
    tags = sorted({t for xs in scn for t in xs if t})
    return df, df_disp, tags

# Analysis 2 loaders (for Change since 2017)
@st.cache_data(show_spinner=False)
def load_exposures_by_fund_year():   return load_csv(2, "exposures_by_fund_year.csv")
@st.cache_data(show_spinner=False)
def load_aggregate_trends():         return load_csv(2, "aggregate_exposure_trends.csv")
@st.cache_data(show_spinner=False)
def load_dispersion_stats():         return load_csv(2, "exposure_dispersion_stats.csv")
@st.cache_data(show_spinner=False)
def load_screen_trends():            return load_csv(2, "aggregate_screen_trends.csv")
@st.cache_data(show_spinner=False)
def load_year_compare():             return load_csv(2, "year_compare_summary.csv")
@st.cache_data(show_spinner=False)
def load_movers_by_yearpair():       return load_csv(2, "movers_by_yearpair.csv")

# =========================
# HEADER
# =========================
st.markdown(
    """
    <div style="display:flex; flex-direction:column; gap:8px;">
      <h2 style="margin:0; font-weight:800; letter-spacing:0.1px;">
        BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
      </h2>
      <div class="blx-muted" style="max-width:1400px; text-align:justify; text-justify:inter-word;">
        This project analyzes 20 BlackRock ESG-labelled ETFs to examine how their holdings align with key ESG themes from 2017 to 2025. Using a unified 2025 ESG classification map that combines the Clean200 and five controversial screens covering fossil fuels, weapons, tobacco, prisons, and deforestation, each fund’s holdings were classified and compared over time. The dashboard presents three perspectives: a 2025 Overview of current exposures, Change since 2017 showing how those exposures evolved, and Tradeoff Scenarios that simulate cleaner portfolio versions to explore the balance between ESG alignment and performance.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# KPI helpers
def kpi_card(label: str, value: str, tone: str = "neutral"):
    tone_class = {"red":"kpi-red","green":"kpi-green","neutral":"kpi-neutral"}.get(tone, "kpi-neutral")
    st.markdown(f"""
        <div class="kpi {tone_class}">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def pct_fmt(x):
    try: return f"{float(x):.1f}%"
    except: return "-"

def usd_fmt(x):
    try:
        x = float(x)
        if abs(x) >= 1e9: return f"${x/1e9:.1f}B"
        if abs(x) >= 1e6: return f"${x/1e6:.1f}M"
        return f"${x:,.0f}"
    except: return "-"

divider()

# =========================
# VIEW SWITCH
# =========================
mode = st.segmented_control(
    "View",
    options=["Dashboard", "Report"],
    default="Dashboard",
    label_visibility="collapsed",
    help="Switch between the interactive dashboard and a short report",
)

divider()

# =========================
# BODY
# =========================
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Scenarios"])

    # ---------- 2025 OVERVIEW ----------
    with tab1:
        st.subheader("2025 Overview")
        st.caption("Today’s composition and the names/screens that drive it.")

        ctx = load_context_summary()
        scr = load_by_screen()
        spot = load_spotlight()

        # KPIs (tinted)
        k1, k2, k3, k4 = st.columns(4)
        if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
            clean_pct  = ctx.loc[ctx["classification"].str.lower()=="clean","share_of_total_aum_pct"].sum()
            contro_pct = ctx.loc[ctx["classification"].str.lower()=="controversial","share_of_total_aum_pct"].sum()
        else:
            clean_pct = contro_pct = None
        total_aum = ctx.get("total_aum_usd")
        total_aum = float(total_aum.dropna().iloc[0]) if total_aum is not None and len(total_aum.dropna()) else None
        num_etfs = int(ctx["num_etfs_in_scope"].dropna().iloc[0]) if "num_etfs_in_scope" in ctx.columns and len(ctx["num_etfs_in_scope"].dropna()) else None

        with k1: kpi_card("% Controversial", pct_fmt(contro_pct), tone="red")
        with k2: kpi_card("% Clean",         pct_fmt(clean_pct),  tone="green")
        with k3: kpi_card("Total AUM",       usd_fmt(total_aum),  tone="neutral")
        with k4: kpi_card("ETFs in scope",   f"{num_etfs:,}" if num_etfs is not None else "-", tone="neutral")

        gap(6)

        # Charts row
        c1, c2 = st.columns([0.5, 0.5])

        with c1:
            st.markdown(
                """<div class="chart-head">
                      <div class="chart-title">2025 Composition — Clean vs Controversial vs Other</div>
                      <div></div>
                   </div>""",
                unsafe_allow_html=True,
            )

            if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
                comp = ctx[ctx["classification"].str.lower().isin(["clean","controversial","other"])].copy()
                comp["classification"] = comp["classification"].map({
                    "Clean":"Clean","Controversial":"Controversial","Other":"Other",
                    "clean":"Clean","controversial":"Controversial","other":"Other"
                })
                comp = comp.groupby("classification", as_index=False)["share_of_total_aum_pct"].sum()
                comp["share"] = comp["share_of_total_aum_pct"]/comp["share_of_total_aum_pct"].sum()

                color_scale = alt.Scale(
                    domain=["Clean","Controversial","Other"],
                    range=[COLORS["clean"], COLORS["contro"], COLORS["other"]]
                )

                chart = alt.Chart(comp).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                    x=alt.X("sum(share):Q", stack="normalize",
                            axis=alt.Axis(format='%', title=None, ticks=False, labels=False)),
                    y=alt.Y("o:O", title=None, axis=None),
                    color=alt.Color("classification:N", scale=color_scale,
                                    legend=alt.Legend(orient="top", title=None)),
                    tooltip=[alt.Tooltip("classification:N"),
                             alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")]
                ).properties(height=120)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("composition columns missing in context_summary_2025.csv")

        with c2:
            st.markdown(
                """<div class="chart-head">
                      <div class="chart-title">By-screen exposures — share of total AUM</div>
                      <div class="info-badge has-tip" data-tip="Categories can overlap; not intended to sum to overall controversial exposure.">i</div>
                   </div>""",
                unsafe_allow_html=True,
            )

            parts = []
            clean200 = 0.0
            if {"screen_category","classification","share_of_total_aum_pct"}.issubset(scr.columns):
                s2 = scr.copy()
                s2["classification"] = s2["classification"].str.title()
                s_con = s2[s2["classification"]=="Controversial"].groupby(
                    "screen_category", as_index=False
                )["share_of_total_aum_pct"].sum()
                parts.append(s_con)
                c2_row = scr.loc[
                    scr["screen_category"].astype(str).str.strip().str.lower()=="clean200",
                    "share_of_total_aum_pct"
                ].sum()
                clean200 = float(c2_row) if pd.notna(c2_row) else 0.0

            parts.append(pd.DataFrame({"screen_category":["Clean200"], "share_of_total_aum_pct":[clean200]}))

            scr_all = pd.concat(parts, ignore_index=True)
            scr_all = scr_all.groupby("screen_category", as_index=False)["share_of_total_aum_pct"].sum()
            scr_all = scr_all.sort_values("share_of_total_aum_pct", ascending=True)
            scr_all["color"] = scr_all["screen_category"].apply(
                lambda x: COLORS["clean"] if str(x).strip().lower()=="clean200" else COLORS["contro"]
            )

            chart2 = alt.Chart(scr_all).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                x=alt.X("share_of_total_aum_pct:Q", title="Share of total AUM (%)", axis=alt.Axis(format=".1f")),
                y=alt.Y("screen_category:N", sort="-x", title=None),
                color=alt.Color("color:N", legend=None, scale=None),
                tooltip=[alt.Tooltip("screen_category:N", title="Category"),
                         alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")],
            ).properties(height=240)
            st.altair_chart(chart2, use_container_width=True)

        s1, s2 = st.columns([0.5, 0.5])
        with s1:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Controversial Holdings</div>', unsafe_allow_html=True)
            if "cohort" in spot.columns:
                cont = spot[spot["cohort"].str.lower()=="controversial"].copy()
                if "rank_within_cohort" in cont.columns:
                    cont = cont.sort_values("rank_within_cohort").head(10)
                cont_disp = cont.rename(columns={
                    "rank_within_cohort":"Rank","ticker":"Ticker","holding_name":"Holding",
                    "share_of_total_aum_pct":"Share of AUM (%)","num_etfs":"#ETFs","screen_categories":"Screens"
                })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
                if "Share of AUM (%)" in cont_disp.columns:
                    cont_disp["Share of AUM (%)"] = pd.to_numeric(cont_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
                st.dataframe(cont_disp, use_container_width=True, hide_index=True)
        with s2:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Clean Holdings</div>', unsafe_allow_html=True)
            if "cohort" in spot.columns:
                clean = spot[spot["cohort"].str.lower()=="clean"].copy()
                if "rank_within_cohort" in clean.columns:
                    clean = clean.sort_values("rank_within_cohort").head(10)
                clean_disp = clean.rename(columns={
                    "rank_within_cohort":"Rank","ticker":"Ticker","holding_name":"Holding",
                    "share_of_total_aum_pct":"Share of AUM (%)","num_etfs":"#ETFs","screen_categories":"Screens"
                })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
                if "Share of AUM (%)" in clean_disp.columns:
                    clean_disp["Share of AUM (%)"] = pd.to_numeric(clean_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
                st.dataframe(clean_disp, use_container_width=True, hide_index=True)

        gap(8)
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Holdings Explorer</div>', unsafe_allow_html=True)

        df_raw, df_disp, all_tags = load_explorer()
        fc1, fc2, fc3, fc4, fc5 = st.columns([0.22, 0.18, 0.24, 0.18, 0.18])
        with fc1:
            etfs = sorted(df_disp["ETF"].dropna().unique().tolist()) if "ETF" in df_disp.columns else []
            sel_etfs_explorer = st.multiselect("ETF", etfs, placeholder="All")
        with fc2:
            classes = ["Clean","Controversial","Other"]
            sel_class = st.multiselect("Classification", classes, default=[], placeholder="Any")
        with fc3:
            sel_tags = st.multiselect("Screen tags", all_tags, default=[], placeholder="Any")
        with fc4:
            sectors = sorted([s for s in df_disp.get("Sector", pd.Series()).dropna().unique().tolist() if s])
            sel_sector = st.multiselect("Sector", sectors, default=[], placeholder="Any")
        with fc5:
            regions = sorted([r for r in df_disp.get("Region", pd.Series()).dropna().unique().tolist() if r])
            sel_region = st.multiselect("Region", regions, default=[], placeholder="Any")

        q = st.text_input("Search ticker or name", "", placeholder="Type to filter…").strip().lower()

        mask = pd.Series(True, index=df_raw.index)
        if sel_etfs_explorer:   mask &= df_disp["ETF"].isin(sel_etfs_explorer)
        if sel_class:  mask &= df_disp["Class"].isin(sel_class)
        if sel_sector: mask &= df_disp["Sector"].isin(sel_sector)
        if sel_region: mask &= df_disp["Region"].isin(sel_region)
        if sel_tags:   mask &= df_raw["_screen_categories_norm"].apply(lambda xs: all(t in xs for t in sel_tags))
        if q:
            qcols = [c for c in ["Ticker","Holding","ETF Name"] if c in df_disp.columns]
            if qcols:
                qmask = False
                for c in qcols:
                    qmask |= df_disp[c].astype(str).str.lower().str.contains(q, na=False)
                mask &= qmask

        df_f = df_disp.loc[mask].copy()
        default_sort = "$ Contribution (Agg)" if "$ Contribution (Agg)" in df_f.columns else ("Weight % in ETF" if "Weight % in ETF" in df_f.columns else None)
        if default_sort:
            df_f = df_f.sort_values(by=default_sort, ascending=False)

        df_view = df_f
        for c in ("Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)"):
            if c in df_view.columns:
                df_view[c] = pd.to_numeric(df_view[c], errors="coerce")
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        csv_bytes = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered rows (CSV)",
            data=csv_bytes,
            file_name="holdings_explorer_filtered.csv",
            mime="text/csv",
        )

    # ---------- CHANGE SINCE 2017 ----------
    with tab2:
        st.subheader("Change since 2017")
        st.caption("Clear, minimal controls. Scope drives everything. Note: some ETFs launched after 2017; early years may be blank.")

        # Load files
        exp_fy  = load_exposures_by_fund_year()
        agg_tr  = load_aggregate_trends()
        disp    = load_dispersion_stats()
        scr_tr  = load_screen_trends()
        yearcmp = load_year_compare()

        # ---------- Helpers: tolerant column access ----------
        def _norm_key(s: str) -> str:
            return str(s).strip().lower().replace(" ", "").replace("%", "").replace("-", "").replace("_", "")

        def colpick(df, *cands):
            if df is None or df.empty:
                return None
            m = { _norm_key(c): c for c in df.columns }
            for c in cands:
                k = _norm_key(c)
                if k in m: return m[k]
                # substring fallback
                for nk, orig in m.items():
                    if k in nk: return orig
            return None

        def numify(x):
            return pd.to_numeric(x, errors="coerce")

        # ---------- Normalize exposures file ----------
        if exp_fy is None or exp_fy.empty:
            st.error("exposures_by_fund_year.csv is empty or missing.")
            st.stop()

        ef = exp_fy.copy()
        c_year  = colpick(ef, "year", "yr")
        c_view  = colpick(ef, "view", "weighting")
        c_etf   = colpick(ef, "etf_ticker", "ticker", "etf", "fund", "symbol")
        c_name  = colpick(ef, "etf_name", "name", "fundname")
        c_clean = colpick(ef, "pct_clean", "cleanpct", "clean")
        c_cont  = colpick(ef, "pct_controversial", "controversialpct", "controversial", "contro")
        c_other = colpick(ef, "pct_other", "otherpct", "other")

        if c_year is None or c_etf is None:
            st.error("Could not find Year or ETF columns in exposures_by_fund_year.csv.")
            st.stop()

        ef = ef.rename(columns={c_year:"year", c_etf:"etf_ticker"})
        ef["etf_name"] = ef[c_name] if c_name else ef["etf_ticker"]
        ef["view"] = ef[c_view] if c_view else "AUM"

        if c_clean: ef = ef.rename(columns={c_clean:"pct_clean"})
        if c_cont:  ef = ef.rename(columns={c_cont:"pct_controversial"})
        if c_other: ef = ef.rename(columns={c_other:"pct_other"})

        ef["year"] = numify(ef["year"])
        for c in ["pct_clean","pct_controversial","pct_other"]:
            if c in ef.columns: ef[c] = numify(ef[c])

        if "pct_other" not in ef.columns:
            if {"pct_clean","pct_controversial"}.issubset(ef.columns):
                ef["pct_other"] = 100 - ef["pct_clean"].fillna(0) - ef["pct_controversial"].fillna(0)
            else:
                ef["pct_other"] = pd.NA

        year_min = int(ef["year"].dropna().min())
        year_max = int(ef["year"].dropna().max())

        # ---------- Controls (simple & global) ----------
        cc1, cc2, cc3, cc4 = st.columns([0.28, 0.18, 0.24, 0.30])
        with cc1:
            scope = st.segmented_control("Scope", options=["All funds", "Selected funds"], default="All funds")
            etf_options = sorted(ef["etf_ticker"].dropna().unique().tolist())
            sel_etfs = st.multiselect("ETF(s) — used only when 'Selected funds'", options=etf_options) if scope=="Selected funds" else []
        with cc2:
            sel_view = st.selectbox("View", ["AUM-weighted", "Equal-weighted"], index=0)
        with cc3:
            metric_map = {"% Controversial": "pct_controversial", "% Clean": "pct_clean"}
            sel_metric_label = st.selectbox("Metric", list(metric_map.keys()), index=0)
            sel_metric = metric_map[sel_metric_label]
        with cc4:
            sel_years = st.slider("Years (applies to all visuals)", min_value=year_min, max_value=year_max, value=(year_min, year_max))

        view_key = "AUM" if "AUM" in sel_view else "EW"
        dfv = ef[ef["view"].astype(str).str.upper().str.contains(view_key)].copy()
        dfv = dfv[(dfv["year"]>=sel_years[0]) & (dfv["year"]<=sel_years[1])]
        if scope == "Selected funds" and sel_etfs:
            dfv = dfv[dfv["etf_ticker"].isin(sel_etfs)]

        # ---------- Aggregation helper ----------
        def aggregate_series(detail_df, col):
            if scope == "All funds" and agg_tr is not None and not agg_tr.empty:
                a = agg_tr.copy()
                ay = colpick(a, "year", "yr"); av = colpick(a, "view", "weighting")
                cm = colpick(a, col, col.replace("pct_", ""), "clean" if "clean" in col else "controversial")
                if ay: a = a.rename(columns={ay:"year"})
                if av: a = a.rename(columns={av:"view"})
                if cm: a = a.rename(columns={cm:col})
                if col not in a.columns:
                    return detail_df.groupby("year", as_index=False)[col].mean()
                if "view" in a.columns:
                    a = a[a["view"].astype(str).str.upper().str.contains(view_key)]
                out = a[["year", col]].copy()
                out["year"] = numify(out["year"])
                out = out.groupby("year", as_index=False)[col].mean().sort_values("year")
                out = out[(out["year"]>=sel_years[0]) & (out["year"]<=sel_years[1])]
                return out
            # fallback: mean of funds in scope
            if detail_df.empty or col not in detail_df.columns:
                return pd.DataFrame({"year": [], col: []})
            return detail_df.groupby("year", as_index=False)[col].mean().sort_values("year")

        # ---------- KPI row ----------
        def kpi_vals(col):
            s = aggregate_series(dfv, col).dropna(subset=[col]).sort_values("year")
            if s.empty: return None, None, None
            return float(s[col].iloc[0]), float(s[col].iloc[-1]), float(s[col].iloc[-1]-s[col].iloc[0])

        k1, k2, k3, k4 = st.columns(4)
        v0, v1, dv = kpi_vals(sel_metric)
        tone = (
            "green" if sel_metric=="pct_clean" and (dv or 0)>0 else
            "green" if sel_metric=="pct_controversial" and (dv or 0)<0 else
            "red"   if sel_metric=="pct_clean" and (dv or 0)<0 else
            "red"   if sel_metric=="pct_controversial" and (dv or 0)>0 else
            "neutral"
        )
        with k1: kpi_card("Δ since first available", pct_fmt(dv) if dv is not None else "-", tone=tone)
        with k2: kpi_card("Level — first available",  pct_fmt(v0) if v0 is not None else "-", tone="neutral")
        with k3: kpi_card("Level — last year",       pct_fmt(v1) if v1 is not None else "-", tone="neutral")
        with k4:
            starts = dfv.groupby("etf_ticker")["year"].min().reset_index(name="first_year") if not dfv.empty else pd.DataFrame(columns=["first_year"])
            txt = f"{(starts['first_year']<=sel_years[0]).sum()} had data in {sel_years[0]}" if not starts.empty else "—"
            kpi_card("Coverage", txt, tone="neutral")

        gap(6)

        # ---------- Trend & First-vs-Last ----------
        lc, rc = st.columns([0.58, 0.42])

        with lc:
            st.markdown(
                f"""<div class="chart-head">
                        <div class="chart-title">Trend — {sel_metric_label} over time ({'AUM' if view_key=='AUM' else 'EW'})</div>
                        <div class="info-badge has-tip" data-tip="Scope + View + Years apply here.">i</div>
                    </div>""",
                unsafe_allow_html=True
            )
            tdf = aggregate_series(dfv, sel_metric)
            if tdf.empty:
                st.info("No data to plot for the selected settings.")
            else:
                base = alt.Chart(tdf).mark_line().encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y(f"{sel_metric}:Q", title=sel_metric_label, axis=alt.Axis(format=".1f")),
                    tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip(f"{sel_metric}:Q", title=sel_metric_label, format=".1f")]
                ).properties(height=260)
                # Optional dispersion only when All funds
                if scope == "All funds" and disp is not None and not disp.empty:
                    d = disp.copy()
                    dy = colpick(d, "year", "yr")
                    dv = colpick(d, "view", "weighting")
                    c_p10 = colpick(d, "p10"); c_p90 = colpick(d, "p90"); c_med = colpick(d, "median", "p50")
                    dm = colpick(d, sel_metric, sel_metric.replace("pct_", ""), "clean" if "clean" in sel_metric else "controversial")
                    if dy: d = d.rename(columns={dy:"year"})
                    if dv: d = d.rename(columns={dv:"view"})
                    if dm: d = d.rename(columns={dm:"metric"})
                    if c_p10 and c_p90:
                        d = d.rename(columns={c_p10:"p10", c_p90:"p90"})
                        if "view" in d.columns:
                            d = d[d["view"].astype(str).str.upper().str.contains(view_key)]
                        d["year"] = numify(d["year"])
                        d = d[(d["year"]>=sel_years[0]) & (d["year"]<=sel_years[1])]
                        band = alt.Chart(d).mark_area(opacity=0.2).encode(
                            x=alt.X("year:O", title=None), y=alt.Y("p10:Q", title=None), y2="p90:Q"
                        )
                        chart = band + base
                        if c_med and c_med in disp.columns:
                            d = d.rename(columns={c_med:"median"})
                            med = alt.Chart(d).mark_line(opacity=0.6).encode(x="year:O", y="median:Q")
                            chart = band + base + med
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.altair_chart(base, use_container_width=True)
                else:
                    st.altair_chart(base, use_container_width=True)

        with rc:
            st.markdown(
                f"""<div class="chart-head">
                        <div class="chart-title">First vs Last — Composition (Clean/Controversial/Other)</div>
                        <div class="info-badge has-tip" data-tip="Uses the first and last available year in the selected range.">i</div>
                    </div>""",
                unsafe_allow_html=True
            )

            base = dfv.copy()
            # Aggregate option shows portfolio-average composition
            agg_first = base.groupby("year", as_index=False)[["pct_clean","pct_controversial","pct_other"]].mean(numeric_only=True)
            if not agg_first.empty:
                y0 = int(agg_first["year"].min()); y1 = int(agg_first["year"].max())
                comp = pd.DataFrame({
                    "year":[str(y0), str(y1)],
                    "Clean":[agg_first.loc[agg_first["year"]==y0,"pct_clean"].mean(), agg_first.loc[agg_first["year"]==y1,"pct_clean"].mean()],
                    "Controversial":[agg_first.loc[agg_first["year"]==y0,"pct_controversial"].mean(), agg_first.loc[agg_first["year"]==y1,"pct_controversial"].mean()],
                    "Other":[agg_first.loc[agg_first["year"]==y0,"pct_other"].mean(), agg_first.loc[agg_first["year"]==y1,"pct_other"].mean()],
                })
                comp_m = comp.melt(id_vars="year", var_name="class", value_name="pct")
                color_scale = alt.Scale(domain=["Clean","Controversial","Other"],
                                        range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])
                bars = alt.Chart(comp_m).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                    x=alt.X("pct:Q", stack="normalize", axis=alt.Axis(format='%', title=None, labels=False, ticks=False)),
                    y=alt.Y("year:N", title=None),
                    color=alt.Color("class:N", scale=color_scale, legend=alt.Legend(title=None, orient="top")),
                    tooltip=[alt.Tooltip("year:N"), alt.Tooltip("class:N"), alt.Tooltip("pct:Q", format=".1f")]
                ).properties(height=140)

                target = "Clean" if sel_metric=="pct_clean" else "Controversial"
                slope_df = comp[["year", target]].rename(columns={target:"value"})
                slope = alt.Chart(slope_df).mark_line(point=True).encode(
                    x=alt.X("year:N", title=None),
                    y=alt.Y("value:Q", title=sel_metric_label, axis=alt.Axis(format=".1f")),
                    tooltip=[alt.Tooltip("year:N"), alt.Tooltip("value:Q", title=sel_metric_label, format=".1f")]
                ).properties(height=120)

                st.altair_chart((bars & slope).resolve_scale(y="independent"), use_container_width=True)
                st.caption(f"First available: {y0} → Last: {y1}")

        gap(8)

        # ---------- Heatmap & Movers ----------
        hcol, rcol = st.columns([0.58, 0.42])

        with hcol:
            st.markdown(
                f"""<div class="chart-head">
                        <div class="chart-title">Heatmap — {sel_metric_label} by Fund × Year</div>
                        <div class="info-badge has-tip" data-tip="Scope + Years apply. Blank = pre-launch/no data.">i</div>
                    </div>""",
                unsafe_allow_html=True
            )
            heat_df = dfv.copy()
            if heat_df.empty:
                st.info("No data for the selected filters.")
            else:
                tickers = sorted(heat_df["etf_ticker"].dropna().unique().tolist())
                years = list(range(int(sel_years[0]), int(sel_years[1]) + 1))
                grid = pd.DataFrame([(t, y) for t in tickers for y in years], columns=["etf_ticker", "year"])
                heat_df = grid.merge(heat_df[["etf_ticker","year",sel_metric]], on=["etf_ticker","year"], how="left")
                names = ef[["etf_ticker","etf_name"]].drop_duplicates()
                heat_df = heat_df.merge(names, on="etf_ticker", how="left")
                heat_df["etf_label"] = heat_df["etf_name"].fillna(heat_df["etf_ticker"])

                hm = alt.Chart(heat_df).mark_rect(stroke=COLORS["bg"], strokeWidth=0.3).encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y("etf_label:N", title=None),
                    color=alt.Color(f"{sel_metric}:Q",
                                    scale=alt.Scale(scheme="blues") if sel_metric!="pct_controversial"
                                          else alt.Scale(range=["#1A2027","#2A3A46","#3F5667","#5E7E95","#8BB1C8"]),
                                    legend=alt.Legend(title=sel_metric_label)),
                    tooltip=[alt.Tooltip("etf_label:N", title="ETF"),
                             alt.Tooltip("year:O", title="Year"),
                             alt.Tooltip(f"{sel_metric}:Q", title=sel_metric_label, format=".1f")]
                ).properties(height=max(220, 18*len(heat_df['etf_label'].unique())))
                st.altair_chart(hm, use_container_width=True)

        with rcol:
            st.markdown(
                f"""<div class="chart-head">
                        <div class="chart-title">Top Movers — {sel_metric_label} (first → last)</div>
                        <div class="info-badge has-tip" data-tip="Computed from first/last year available within your range.">i</div>
                    </div>""",
                unsafe_allow_html=True
            )
            base = dfv.copy()
            rows = []
            for k, d in base.groupby("etf_ticker"):
                d = d.sort_values("year")
                if d.empty or sel_metric not in d.columns: continue
                v0 = d.iloc[0][sel_metric]
                v1 = d.iloc[-1][sel_metric]
                rows.append({"ETF": k, "First %": v0, "Last %": v1, "Δ (ppt)": (v1 - v0) if pd.notna(v0) and pd.notna(v1) else pd.NA})
            movers = pd.DataFrame(rows)
            if not movers.empty:
                mv = movers.sort_values("Δ (ppt)", ascending=(sel_metric!="pct_clean")).head(10).copy()
                for c in ["First %","Last %","Δ (ppt)"]:
                    mv[c] = pd.to_numeric(mv[c], errors="coerce").map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
                st.dataframe(mv, use_container_width=True, hide_index=True, height=290)
            else:
                st.info("No movers for the selected settings.")

        gap(8)

        # ---------- Screen Trends (aggregate only) ----------
        st.markdown(
            f"""<div class="chart-head">
                    <div class="chart-title">Screen Trends — Aggregate over time</div>
                    <div class="info-badge has-tip" data-tip="Always shown for All funds. Categories overlap.">i</div>
                </div>""",
            unsafe_allow_html=True
        )
        if scr_tr is not None and not scr_tr.empty:
            sc = scr_tr.copy()
            cy = colpick(sc, "year", "yr"); cv = colpick(sc, "view", "weighting")
            cat = colpick(sc, "screen", "category"); met = colpick(sc, "pct", "value", "share")
            if cy: sc = sc.rename(columns={cy:"year"})
            if cv: sc = sc.rename(columns={cv:"view"})
            if cat: sc = sc.rename(columns={cat:"screen"})
            if met: sc = sc.rename(columns={met:"pct"})
            if "view" in sc.columns:
                sc = sc[sc["view"].astype(str).str.upper().str.contains(view_key)]
            sc = sc[(sc["year"]>=sel_years[0]) & (sc["year"]<=sel_years[1])]
            sc["screen"] = sc.get("screen", pd.Series(dtype=str)).astype(str).replace({
                "fossil":"Fossil Fuels","fossil fuels":"Fossil Fuels","clean200":"Clean200",
                "weapons":"Weapons","tobacco":"Tobacco","prisons":"Prisons","deforestation":"Deforestation"
            })
            order = ["Fossil Fuels","Tobacco","Weapons","Prisons","Deforestation","Clean200"]
            sc["screen"] = pd.Categorical(sc["screen"], categories=order, ordered=True)
            if {"year","pct","screen"}.issubset(sc.columns):
                small = alt.Chart(sc).mark_line().encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y("pct:Q", title="%", axis=alt.Axis(format=".1f")),
                    facet=alt.Facet("screen:N", columns=6),
                    tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("pct:Q", title="%", format=".1f")]
                ).properties(height=130)
                st.altair_chart(small, use_container_width=True)

        # ---------- Downloads ----------
        dl1, dl2 = st.columns([0.5, 0.5])
        with dl1:
            ts = aggregate_series(dfv, sel_metric)
            st.download_button("Download trend series (CSV)", data=ts.to_csv(index=False).encode("utf-8"),
                               file_name="trend_series.csv", mime="text/csv")
        with dl2:
            # Heatmap dataset
            try:
                heat_out = heat_df.copy()
            except Exception:
                heat_out = dfv.copy()
            st.download_button("Download heatmap dataset (CSV)", data=heat_out.to_csv(index=False).encode("utf-8"),
                               file_name="heatmap_dataset.csv", mime="text/csv")

    # ---------- TRADEOFF LAB ----------
    with tab3:
        st.subheader("Tradeoff Scenarios")
        st.caption("Baseline vs cleaner scenarios, measuring cost (TE) vs benefit (% Clean).")
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Scenario KPIs — % Clean, % Controversial, TE, Active Share, Drift</div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Charts coming</div>', unsafe_allow_html=True)
            gap(10)
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Baseline vs Scenario — Composition (100% bars)</div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Charts coming</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Mini frontier — x: TE, y: % Clean (point = ETF)</div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Charts coming</div>', unsafe_allow_html=True)
            gap(10)
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Movers — adds/drops/ups/downs vs baseline</div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Table coming</div>', unsafe_allow_html=True)

else:
    # ---------------- REPORT ----------------
    st.subheader("Project Overview (Short Report)")
    st.markdown(
        """
**Purpose**  
Assess how BlackRock’s ESG-labelled ETFs align with a consistent 2025 ESG classification, how that alignment **changed from 2017 to 2025**, and what it **costs to push portfolios cleaner**.

**Method (high level)**  
1) Standardize 2025 holdings for 20 ETFs; tag Clean200 and controversial screens.  
2) Apply the same map retroactively to 2017–2025 holdings to measure change.  
3) Simulate cleaner portfolios (tilt and exclusion) and estimate tracking error with a covariance matrix.

**How to read this app**  
Use the three tabs on the **Dashboard**: *2025 Overview*, *Change since 2017*, and *Tradeoff Scenarios*.
        """
    )

# =========================
# FOOTER (replacement)
# =========================
gap(28)
divider()
st.markdown(
    """
    <style>
      .footer-wrap { display:flex; align-items:center; justify-content:space-between; width:100%; }
      .footer-left { color: var(--muted); font-size: 14px; white-space: nowrap; }
    </style>
    <div class="footer-wrap">
      <div class="footer-left">Built by <strong>Nitya Arya</strong></div>
      <div class="footer-links" style="display:flex; gap:28px; align-items:center; justify-content:flex-end;">
        <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank" style="color: var(--text); text-decoration:none; font-size:15.5px; font-weight:500; opacity:.9;">LinkedIn</a>
        <a href="https://github.com/nitya-ar" target="_blank" style="color: var(--text); text-decoration:none; font-size:15.5px; font-weight:500; opacity:.9;">GitHub</a>
        <a href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank" style="color: var(--text); text-decoration:none; font-size:15.5px; font-weight:500;"><strong>Send Feedback</strong></a>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
