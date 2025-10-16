

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
        st.caption("Market value–weighted. Year A compares to 2025 (or last available).")

        # ---------- Load data (Analysis 2) ----------
        def _safe_read(fname):
            try:
                return load_csv(2, fname)
            except Exception:
                return pd.DataFrame()

        exp_fy = _safe_read("exposures_by_fund_year.csv")
        scr_tr = _safe_read("aggregate_screen_trends.csv")
        movers = _safe_read("movers_by_yearpair.csv")
        # optional / used for badges if present
        disp_stats = _safe_read("exposure_dispersion_stats.csv")
        yc_sum = _safe_read("year_compare_summary.csv")

        # ---------- Utils ----------
        def _nk(s: str) -> str:
            return str(s).strip().lower().replace("%","").replace("_","").replace(" ","")

        def pick(df, *names):
            if df is None or df.empty: return None
            m = {_nk(c): c for c in df.columns}
            for n in names:
                k = _nk(n)
                if k in m: return m[k]
                # loose contains
                for nk, orig in m.items():
                    if k in nk: return orig
            return None

        def to_num(s): return pd.to_numeric(s, errors="coerce")

        def pct_fmt(x):
            try: return f"{float(x):.1f}%"
            except: return "-"

        # ---------- Normalize exposures_by_fund_year (MV only) ----------
        if exp_fy.empty:
            st.error("exposures_by_fund_year.csv missing or empty.")
            st.stop()

        ef = exp_fy.copy()
        c_year = pick(ef,"year","yr")
        c_etf  = pick(ef,"etf_ticker","etf","ticker","fund")
        c_name = pick(ef,"etf_name","name")
        c_view = pick(ef,"view","weighting","method")

        c_clean = pick(ef,"pct_clean","clean_pct","clean")
        c_cont  = pick(ef,"pct_controversial","controversial_pct","controversial","contro")
        c_other = pick(ef,"pct_other","other_pct","other")

        ef = ef.rename(columns={c_year:"year", c_etf:"etf_ticker"})
        if c_name: ef["etf_name"] = ef[c_name]
        else:      ef["etf_name"] = ef["etf_ticker"]

        # view -> MV only
        if c_view:
            ef["_view"] = ef[c_view].astype(str).str.upper()
            ef = ef[ef["_view"].str.contains("AUM|MARKET|MKT|MV|VALUE", regex=True)]
        ef["year"] = to_num(ef["year"])

        if c_clean: ef = ef.rename(columns={c_clean:"pct_clean"})
        if c_cont:  ef = ef.rename(columns={c_cont :"pct_controversial"})
        if c_other: ef = ef.rename(columns={c_other:"pct_other"})

        for c in ["pct_clean","pct_controversial","pct_other"]:
            if c in ef.columns: ef[c] = to_num(ef[c])
        if "pct_other" not in ef.columns and {"pct_clean","pct_controversial"}.issubset(ef.columns):
            ef["pct_other"] = 100 - ef["pct_clean"].fillna(0) - ef["pct_controversial"].fillna(0)

        # years
        if ef["year"].dropna().empty:
            st.error("No year values found in exposures_by_fund_year.csv"); st.stop()
        y_min = int(ef["year"].min())
        y_last = 2025 if (ef["year"]==2025).any() else int(ef["year"].max())

        # ---------- Controls ----------
        cc1, cc2, cc3 = st.columns([0.46, 0.24, 0.30])
        with cc1:
            all_etfs = sorted(ef["etf_ticker"].dropna().unique().tolist())
            sel_etfs = st.multiselect("ETF(s)", options=all_etfs, placeholder="All ETFs")
        with cc2:
            coh_only = st.toggle("Consistent cohort (in both Year A & 2025)", value=True, help="Limits to ETFs with data in both endpoints.")
        with cc3:
            yearA = st.slider("Year A (compares to 2025)", min_value=y_min, max_value=max(y_min, y_last-1),
                              value=max(2017, y_min))
        view_change = st.toggle("Show change vs Year A (pp)", value=True)

        # filter by ETFs & cohort
        dfv = ef.copy()
        if sel_etfs:
            dfv = dfv[dfv["etf_ticker"].isin(sel_etfs)]

        if coh_only:
            have_A = set(dfv.loc[dfv["year"]==yearA, "etf_ticker"])
            have_Z = set(dfv.loc[dfv["year"]==y_last, "etf_ticker"])
            keep = list(have_A & have_Z)
            dfv = dfv[dfv["etf_ticker"].isin(keep)]

        # final year window
        dfv = dfv[(dfv["year"]>=yearA) & (dfv["year"]<=y_last)].copy()

        # coverage
        covA = dfv.loc[dfv["year"]==yearA, "etf_ticker"].nunique()
        covZ = dfv.loc[dfv["year"]==y_last, "etf_ticker"].nunique()

        # aggregated series (avg across selected ETFs)
        series = (dfv.groupby("year", as_index=False)[["pct_clean","pct_controversial","pct_other"]]
                    .mean(numeric_only=True).sort_values("year"))
        series["net_align"] = series["pct_clean"].fillna(0)-series["pct_controversial"].fillna(0)

        # helpers for Year A vs Last
        def _v(df, y, col):
            try: return float(df.loc[df["year"]==y, col].mean())
            except: return None

        clean_A, clean_Z = _v(series, yearA,"pct_clean"), _v(series, y_last,"pct_clean")
        cont_A,  cont_Z  = _v(series, yearA,"pct_controversial"), _v(series, y_last,"pct_controversial")
        net_A,   net_Z   = _v(series, yearA,"net_align"), _v(series, y_last,"net_align")
        d_clean = (clean_Z - clean_A) if clean_A is not None and clean_Z is not None else None
        d_cont  = (cont_Z  - cont_A)  if cont_A  is not None and cont_Z  is not None  else None
        d_net   = (net_Z   - net_A)   if net_A   is not None and net_Z   is not None   else None

        # change view dataframe
        def to_change(df, base_year):
            out = df.copy()
            for c in ["pct_clean","pct_controversial","pct_other","net_align"]:
                if c in out.columns:
                    base = _v(out, base_year, c)
                    if base is None: base = 0.0
                    out[c+"_pp"] = out[c] - base
            return out

        ser_chg = to_change(series, yearA)

        # ---------- KPI row with tall slope charts ----------
        k1,k2,k3,k4 = st.columns(4)

        def slope(df, col, color_hex):
            if df.empty or col not in df.columns: return None
            s = df[df["year"].isin([yearA, y_last])][["year", col]].dropna().sort_values("year")
            if s.empty: return None
            ax_title = "pp" if col.endswith("_pp") else "%"
            y_scale = alt.Scale(domain=(-5,5)) if col.endswith("_pp") else alt.Scale(domain=[0,100])
            area = alt.Chart(s).mark_area(opacity=0.12).encode(
                x=alt.X("year:O", title=None),
                y=alt.Y(f"{col}:Q", title=None, scale=y_scale)
            )
            line = alt.Chart(s).mark_line(point=True, strokeWidth=2.2, color=color_hex).encode(
                x=alt.X("year:O", title=None),
                y=alt.Y(f"{col}:Q", title=None, scale=y_scale),
                tooltip=[alt.Tooltip("year:O"), alt.Tooltip(f"{col}:Q", format=".1f")]
            )
            yaxis = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="#2A2F36") \
                .encode(y=alt.Y("y:Q", scale=y_scale)) if col.endswith("_pp") else None
            chart = (area + line) if yaxis is None else (area + line + yaxis)
            return chart.properties(height=120)

        # choose columns for slope based on view
        net_col   = "net_align_pp" if view_change else "net_align"
        clean_col = "pct_clean_pp" if view_change else "pct_clean"
        cont_col  = "pct_controversial_pp" if view_change else "pct_controversial"

        with k1:
            kpi_card("Δ Net alignment (Clean − Contro)", pct_fmt(d_net), tone="neutral")
            sp = slope(ser_chg if view_change else series, net_col, COLORS["other"])
            if sp: st.altair_chart(sp, use_container_width=True)

        with k2:
            kpi_card(f"% Clean — {yearA} → {y_last}",
                     f"{pct_fmt(clean_A)} → {pct_fmt(clean_Z)}",
                     tone=("green" if (d_clean or 0) > 0 else "red"))
            sp = slope(ser_chg if view_change else series, clean_col, COLORS["clean"])
            if sp: st.altair_chart(sp, use_container_width=True)

        with k3:
            kpi_card(f"% Controversial — {yearA} → {y_last}",
                     f"{pct_fmt(cont_A)} → {pct_fmt(cont_Z)}",
                     tone="red")
            sp = slope(ser_chg if view_change else series, cont_col, COLORS["contro"])
            if sp: st.altair_chart(sp, use_container_width=True)

        with k4:
            kpi_card("Coverage", f"{covA} funds in {yearA} • {covZ} in {y_last}", tone="neutral")

        gap(6)

        # ---------- Graph A (full width): Combined trend or change ----------
        st.markdown(
            """<div class="chart-head">
                   <div class="chart-title">Combined trend — % Clean / % Controversial (Year A → 2025)</div>
                   <div class="info-badge has-tip" data-tip="Toggle 'Show change' to view percentage-point deltas vs Year A.">i</div>
               </div>""",
            unsafe_allow_html=True,
        )
        plot_df = ser_chg if view_change else series
        value_col = "pct" if not view_change else "pp"
        # melt
        cm = plot_df.melt(id_vars="year",
                          value_vars=[clean_col, cont_col] if view_change else ["pct_clean","pct_controversial"],
                          var_name="class", value_name="val")
        cm["class"] = cm["class"].replace({
            "pct_clean":"Clean","pct_controversial":"Controversial",
            "pct_clean_pp":"Clean (pp)","pct_controversial_pp":"Controversial (pp)"
        })
        y_scale = alt.Scale(domain=(-5,5)) if view_change else alt.Scale(domain=[0,100])
        y_title = "Δ vs Year A (pp)" if view_change else "% of AUM"
        color_scale = alt.Scale(domain=[c for c in cm["class"].unique()],
                                range=[COLORS["clean"], COLORS["contro"]])
        lines = alt.Chart(cm).mark_line().encode(
            x=alt.X("year:O", title=None),
            y=alt.Y("val:Q", title=y_title, scale=y_scale, axis=alt.Axis(format=".1f")),
            color=alt.Color("class:N", scale=color_scale, title=None),
            tooltip=[alt.Tooltip("year:O"), alt.Tooltip("class:N"), alt.Tooltip("val:Q", format=".1f")]
        ).properties(height=320)
        if view_change:
            zero = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="#2A2F36").encode(y="y:Q")
            lines = zero + lines
        st.altair_chart(lines, use_container_width=True)

        gap(10)

        # ---------- Graphs B & C: screens + composition ----------
        colB, colC = st.columns([0.52, 0.48])

        # B) Screen trends — Clean200, Deforestation, Fossil Fuels, Prisons, Weapons
        with colB:
            st.markdown(
                """<div class="chart-head">
                       <div class="chart-title">Screen trends — aggregate shift (Year A → 2025)</div>
                       <div class="info-badge has-tip" data-tip="Clean200, Deforestation, Fossil Fuels, Prisons, Weapons.">i</div>
                   </div>""",
                unsafe_allow_html=True,
            )
            if not scr_tr.empty:
                sc = scr_tr.copy()
                cy  = pick(sc,"year","yr")
                cv  = pick(sc,"view","weighting")
                cat = pick(sc,"screen","category","screen_category")
                met = pick(sc,"pct","value","share","share_of_aum_pct")
                if cy: sc = sc.rename(columns={cy:"year"})
                if cv: sc = sc.rename(columns={cv:"view"})
                if cat: sc = sc.rename(columns={cat:"screen"})
                if met: sc = sc.rename(columns={met:"pct"})
                if "view" in sc.columns:
                    sc = sc[sc["view"].astype(str).str.upper().str.contains("AUM|MARKET|MKT|MV|VALUE")]
                sc = sc[(sc["year"]>=yearA) & (sc["year"]<=y_last)]
                sc["screen"] = sc.get("screen", pd.Series(dtype=str)).astype(str).str.strip().str.title()
                fix = {
                    "Clean 200":"Clean200","Clean200":"Clean200",
                    "Deforestation":"Deforestation",
                    "Fossil":"Fossil Fuels","Fossil Fuel":"Fossil Fuels","Fossil Fuels":"Fossil Fuels",
                    "Prison":"Prisons","Prisons":"Prisons",
                    "Weapons":"Weapons",
                }
                sc["screen"] = sc["screen"].map(lambda x: fix.get(x, x))
                keep = ["Clean200","Deforestation","Fossil Fuels","Prisons","Weapons"]
                sc = sc[sc["screen"].isin(keep)]
                sc["screen"] = pd.Categorical(sc["screen"], categories=keep, ordered=True)
                if view_change:
                    # convert to change vs Year A per screen
                    base = sc[sc["year"]==yearA].set_index("screen")["pct"].to_dict()
                    sc["pct"] = sc.apply(lambda r: (r["pct"] - base.get(r["screen"], 0.0)), axis=1)
                    ysc = alt.Scale(domain=(-5,5))
                    ytitle = "Δ vs Year A (pp)"
                    zero = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="#2A2F36").encode(y="y:Q")
                else:
                    ysc = alt.Scale(domain=[0,100])
                    ytitle = "% of AUM"
                    zero = None
                lines_sc = alt.Chart(sc).mark_line().encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y("pct:Q", title=ytitle, scale=ysc, axis=alt.Axis(format=".1f")),
                    color=alt.Color("screen:N", title=None),
                    tooltip=[alt.Tooltip("screen:N"), alt.Tooltip("year:O"), alt.Tooltip("pct:Q", format=".1f")]
                ).properties(height=300)
                st.altair_chart(lines_sc if zero is None else (zero + lines_sc), use_container_width=True)
            else:
                st.info("aggregate_screen_trends.csv missing/empty.")

        # C) Year A vs 2025 composition — vertical 100%
        with colC:
            st.markdown(
                f"""<div class="chart-head">
                        <div class="chart-title">Year {yearA} vs {y_last} — composition</div>
                        <div></div>
                    </div>""",
                unsafe_allow_html=True,
            )
            baseC = dfv.copy()
            compA = baseC[baseC["year"]==yearA][["pct_clean","pct_controversial","pct_other"]].mean(numeric_only=True)
            compZ = baseC[baseC["year"]==y_last][["pct_clean","pct_controversial","pct_other"]].mean(numeric_only=True)
            comp = pd.DataFrame({
                "year":[str(yearA), str(y_last)],
                "Clean":[compA.get("pct_clean",0.0)/100.0, compZ.get("pct_clean",0.0)/100.0],
                "Controversial":[compA.get("pct_controversial",0.0)/100.0, compZ.get("pct_controversial",0.0)/100.0],
                "Other":[compA.get("pct_other",0.0)/100.0, compZ.get("pct_other",0.0)/100.0],
            })
            comp_m = comp.melt(id_vars="year", var_name="class", value_name="share")
            color_scale = alt.Scale(domain=["Clean","Controversial","Other"],
                                    range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])
            bars_v = alt.Chart(comp_m).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                x=alt.X("year:N", title=None),
                y=alt.Y("share:Q", stack="normalize", axis=alt.Axis(format='%', title=None)),
                color=alt.Color("class:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
                tooltip=[alt.Tooltip("year:N"), alt.Tooltip("class:N"), alt.Tooltip("share:Q", format=".1%")]
            ).properties(height=300)
            st.altair_chart(bars_v, use_container_width=True)

        gap(10)

        # ---------- Movers + Distributions row ----------
        m1, m2, m3 = st.columns([0.44, 0.28, 0.28])

        # Movers scatter: ΔClean vs ΔControversial (Year A -> last)
        with m1:
            st.markdown('<div class="chart-title">Movers — ΔClean vs ΔControversial (pp)</div>', unsafe_allow_html=True)
            mv = movers.copy()
            y0 = pick(mv,"year_start","year_a","year0","yeara")
            y1 = pick(mv,"year_end","year_b","year1","yearz")
            et = pick(mv,"etf_ticker","etf","ticker")
            dc = pick(mv,"d_clean_pp","delta_clean_pp","clean_pp")
            dct= pick(mv,"d_contro_pp","d_controversial_pp","delta_contro_pp","contro_pp")
            if all([col is not None for col in [y0,y1,et,dc,dct]]):
                mv = mv.rename(columns={y0:"y0", y1:"y1", et:"ETF", dc:"d_clean_pp", dct:"d_contro_pp"})
                mv = mv[(mv["y0"]==yearA) & (mv["y1"]==y_last)]
                if sel_etfs: mv = mv[mv["ETF"].isin(sel_etfs)]
                if coh_only and mv.shape[0]:
                    mv = mv[mv["ETF"].isin(dfv["etf_ticker"].unique())]
                if not mv.empty:
                    zeroV = alt.Chart(pd.DataFrame({"x":[0],"y":[0]})).mark_rule(color="#2A2F36").encode(x="x:Q") + \
                            alt.Chart(pd.DataFrame({"x":[0],"y":[0]})).mark_rule(color="#2A2F36").encode(y="y:Q")
                    scat = alt.Chart(mv).mark_point(filled=True, size=85).encode(
                        x=alt.X("d_contro_pp:Q", title="Δ Controversial (pp)"),
                        y=alt.Y("d_clean_pp:Q", title="Δ Clean (pp)"),
                        color=alt.value(COLORS["primary"]),
                        tooltip=["ETF","d_clean_pp","d_contro_pp"]
                    ).properties(height=280)
                    st.altair_chart(zeroV + scat, use_container_width=True)
                else:
                    st.info("No movers available for the chosen Year A and selection.")
            else:
                st.info("movers_by_yearpair.csv missing expected columns — skipping scatter.")

        # Histograms: ΔControversial and ΔClean
        with m2:
            st.markdown('<div class="chart-title">Distribution — ΔControversial (pp)</div>', unsafe_allow_html=True)
            # derive quick deltas from dfv by ETF
            baseA = dfv[dfv["year"]==yearA].set_index("etf_ticker")
            baseZ = dfv[dfv["year"]==y_last].set_index("etf_ticker")
            joined = baseA[["pct_controversial"]].join(baseZ[["pct_controversial"]], lsuffix="_A", rsuffix="_Z", how="inner")
            joined["d_contro_pp"] = joined["pct_controversial_Z"] - joined["pct_controversial_A"]
            if not joined.empty:
                hist = alt.Chart(joined.reset_index()).mark_bar().encode(
                    x=alt.X("d_contro_pp:Q", bin=alt.Bin(step=0.5), title="pp"),
                    y=alt.Y("count()", title="ETFs")
                ).properties(height=180)
                st.altair_chart(hist, use_container_width=True)
            else:
                st.info("Not enough overlapping ETFs for histogram.")

        with m3:
            st.markdown('<div class="chart-title">Distribution — ΔClean (pp)</div>', unsafe_allow_html=True)
            joined2 = baseA[["pct_clean"]].join(baseZ[["pct_clean"]], lsuffix="_A", rsuffix="_Z", how="inner")
            joined2["d_clean_pp"] = joined2["pct_clean_Z"] - joined2["pct_clean_A"]
            if not joined2.empty:
                hist2 = alt.Chart(joined2.reset_index()).mark_bar().encode(
                    x=alt.X("d_clean_pp:Q", bin=alt.Bin(step=0.5), title="pp"),
                    y=alt.Y("count()", title="ETFs")
                ).properties(height=180)
                st.altair_chart(hist2, use_container_width=True)
            else:
                st.info("Not enough overlapping ETFs for histogram.")

        gap(8)

        # ---------- Screen attribution to change (Year A -> 2025) ----------
        st.markdown('<div class="chart-title">Attribution — which screens drove Δ (pp) since Year A</div>', unsafe_allow_html=True)
        if not scr_tr.empty:
            sc2 = scr_tr

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
