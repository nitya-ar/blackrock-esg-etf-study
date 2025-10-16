import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st
# ===================
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

        # NEW: one-click hard refresh so updated CSVs are reloaded
        btn_col, _sp = st.columns([0.18, 0.82])
        with btn_col:
            if st.button("Reload 2025 data", help="Clear cache and reload latest Analysis 1 CSVs"):
                st.cache_data.clear()
                st.rerun()

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
        st.caption("Using 2025 classifications retroactively. End year fixed at 2025; drag the start year.")

        # Reload button
        col_btn, _ = st.columns([0.25, 0.75])
        with col_btn:
            if st.button("Reload Analysis 2 data", help="Clear cache and reload latest Analysis 2 CSVs"):
                st.cache_data.clear()
                st.rerun()

        # Load data
        by_fund = load_exposures_by_fund_year()
        agg_tr  = load_aggregate_trends()
        scr_tr  = load_screen_trends()
        movers  = load_movers_by_yearpair()

        # --------- helpers & column detection ----------
        import re
        def _has(name, *tokens):
            s = re.sub(r"[^a-z0-9]+", " ", str(name).lower())
            return all(t in s for t in tokens)

        # ETF cols (handles "ETF ticker" with space)
        etf_col  = next((c for c in by_fund.columns if _has(c,"etf","ticker")), None) or ("ETF ticker" if "ETF ticker" in by_fund.columns else None)
        name_col = next((c for c in by_fund.columns if _has(c,"etf","name")), None)

        # Exposure cols (explicit first, then fuzzy)
        def _pick(df,*keys):
            return next((c for c in df.columns if any(k in c.lower() for k in keys)), None)
        col_clean  = "pct_clean"         if "pct_clean"         in by_fund.columns else _pick(by_fund,"clean200","clean")
        col_contro = "pct_controversial" if "pct_controversial" in by_fund.columns else _pick(by_fund,"contro","controversial")
        col_other  = "pct_other"         if "pct_other"         in by_fund.columns else _pick(by_fund,"other")
        if not col_other and col_clean and col_contro:
            by_fund["_other_derived"] = 100.0 - pd.to_numeric(by_fund[col_clean], errors="coerce") - pd.to_numeric(by_fund[col_contro], errors="coerce")
            col_other = "_other_derived"

        # Year as int
        for df in (by_fund, agg_tr, scr_tr, movers):
            if "year" in df.columns:
                df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

        years = sorted([int(y) for y in by_fund["year"].dropna().unique()]) if "year" in by_fund.columns else list(range(2017,2026))
        min_y, max_y = (min(years), max(years)) if years else (2017, 2025)
        end_year = 2025 if 2025 in years else max_y

        # ------------- FILTERS -------------
        f1, f2, f3 = st.columns([0.44, 0.28, 0.28])
        with f1:
            etf_all = sorted(by_fund.get(etf_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) if etf_col else []
            sel_etfs = st.multiselect("ETF (default: all)", etf_all, default=[])
        with f2:
            start_year = st.slider("Start Year", min_value=min_y, max_value=end_year-1, value=min_y, help="Drag to change the comparison start year. End year stays 2025.")
        with f3:
            # AUM/EW with info icon
            st.markdown(
                '<div class="chart-head"><div class="chart-title">Weighting</div>'
                f'<div class="info-badge has-tip" data-tip="AUM-weighted = each ETF weighted by its assets; Equal-weighted = every ETF counts the same.">i</div></div>',
                unsafe_allow_html=True,
            )
            weighting = st.segmented_control("Weighting", options=["AUM-weighted","Equal-weighted"], default="AUM-weighted", label_visibility="collapsed")

        # Apply ETF filter
        df = by_fund.copy()
        if sel_etfs and etf_col in df.columns:
            df = df[df[etf_col].astype(str).isin(sel_etfs)]

        # Cohorts for coverage
        yA = df[df["year"]==start_year]
        yZ = df[df["year"]==end_year]
        setA = set(yA[etf_col].astype(str)) if etf_col in yA.columns else set()
        setZ = set(yZ[etf_col].astype(str)) if etf_col in yZ.columns else set()
        intersect = setA & setZ if etf_col else set()
        covA = len(setA); covZ = len(setZ); covI = len(intersect)

        # ---------------- KPI CARDS ----------------
        # Build aggregate series for Clean/Contro (weighting-aware)
        def _agg_pick(df_src, cat):
            d = df_src.copy()
            # detect columns
            cat_col = next((c for c in d.columns if c.lower() in ("category","classification","label")), None)
            val_col = next((c for c in d.columns if "share" in c.lower() or "exposure" in c.lower() or c.lower().endswith("_pct")), None)
            wt_col  = next((c for c in d.columns if "weight" in c.lower() or "weighting" in c.lower()), None)
            if cat_col is None or val_col is None:
                return pd.DataFrame(columns=["year","value"])
            if wt_col in d.columns:
                if weighting == "AUM-weighted":
                    d = d[d[wt_col].astype(str).str.lower().str.contains("aum")]
                else:
                    d = d[d[wt_col].astype(str).str.lower().str.contains(r"(equal|ew)")]
            d["_cat"] = d[cat_col].astype(str).str.strip().str.lower()
            want = {"clean":"clean200","clean200":"clean200","controversial":"controversial"}[cat.lower()]
            d = d[d["_cat"]==want].rename(columns={val_col:"value"})
            return d[["year","value"]]

        # If aggregate file missing, fallback to simple mean across ETFs
        def _fallback_series(cat_col):
            if not cat_col: return pd.DataFrame(columns=["year","value"])
            x = df.groupby("year")[cat_col].mean(numeric_only=True).reset_index().rename(columns={cat_col:"value"})
            return x[["year","value"]]

        s_clean  = _agg_pick(agg_tr, "clean200")  if not agg_tr.empty else _fallback_series(col_clean)
        s_contro = _agg_pick(agg_tr, "controversial") if not agg_tr.empty else _fallback_series(col_contro)
        s_clean  = s_clean[(s_clean["year"]>=start_year) & (s_clean["year"]<=end_year)]
        s_contro = s_contro[(s_contro["year"]>=start_year) & (s_contro["year"]<=end_year)]

        def _val(series, year):
            v = pd.to_numeric(series.loc[series["year"]==year, "value"], errors="coerce")
            return float(v.iloc[0]) if len(v) else float("nan")

        cA = _val(s_clean, start_year); cZ = _val(s_clean, end_year)
        kA = _val(s_contro, start_year); kZ = _val(s_contro, end_year)

        kk1, kk2, kk3 = st.columns([0.32, 0.32, 0.36])
        with kk1:
            kpi_card("Clean — Δ since start", f"{(cZ - cA):.1f} pp" if pd.notna(cZ) and pd.notna(cA) else "–", tone="green" if (cZ-cA)>=0 else "red")
            # mini sparkline
            if not s_clean.empty:
                ch = alt.Chart(s_clean).mark_line(point=True).encode(
                    x=alt.X("year:O", axis=alt.Axis(labels=False, ticks=False)),
                    y=alt.Y("value:Q", axis=alt.Axis(labels=False, ticks=False)),
                    tooltip=[alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Clean (%)", format=".1f")],
                    color=alt.value(COLORS["clean"])
                ).properties(height=40)
                st.altair_chart(ch, use_container_width=True)
        with kk2:
            kpi_card("Controversial — Δ since start", f"{(kZ - kA):.1f} pp" if pd.notna(kZ) and pd.notna(kA) else "–", tone="red" if (kZ-kA)>0 else "green")
            if not s_contro.empty:
                ch2 = alt.Chart(s_contro).mark_line(point=True).encode(
                    x=alt.X("year:O", axis=alt.Axis(labels=False, ticks=False)),
                    y=alt.Y("value:Q", axis=alt.Axis(labels=False, ticks=False)),
                    tooltip=[alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Controversial (%)", format=".1f")],
                    color=alt.value(COLORS["contro"])
                ).properties(height=40)
                st.altair_chart(ch2, use_container_width=True)
        with kk3:
            kpi_card("Coverage (ETFs)", f"Year {start_year}: {covA} • 2025: {covZ} • Intersect: {covI}", tone="neutral")

        gap(8)

        # --------- Combined trend: Clean & Controversial (Year A → 2025) ----------
        st.markdown('<div class="chart-title">Combined trend — % Clean / % Controversial (Start → 2025)</div>', unsafe_allow_html=True)
        comb = []
        if not s_clean.empty:
            a = s_clean.assign(category="Clean")
            comb.append(a)
        if not s_contro.empty:
            b = s_contro.assign(category="Controversial")
            comb.append(b)
        comb_df = pd.concat(comb, ignore_index=True) if comb else pd.DataFrame(columns=["year","value","category"])
        color_scale = alt.Scale(domain=["Clean","Controversial"], range=[COLORS["clean"], COLORS["contro"]])
        line = alt.Chart(comb_df).mark_line(point=True).encode(
            x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("value:Q", title="Exposure (%)", axis=alt.Axis(format=".1f")),
            color=alt.Color("category:N", scale=color_scale, title=None),
            tooltip=[alt.Tooltip("category:N"), alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Exposure (%)", format=".1f")]
        ).properties(height=300)
        st.altair_chart(line, use_container_width=True)

        gap(8)

        # --------- Screen trends (Clean200, Prisons, Deforestation, Fossil Fuel, Weapons, Tobacco) ----------
        st.markdown('<div class="chart-title">Screen trends — Clean200 & controversial screens</div>', unsafe_allow_html=True)
        if not scr_tr.empty:
            d = scr_tr.copy()
            # expected columns: year, screen_category, value/exposure/share, weighting_mode
            cat_col = next((c for c in d.columns if "screen" in c.lower()), None)
            val_col = next((c for c in d.columns if ("exposure" in c.lower()) or ("share" in c.lower()) or c.lower().endswith("_pct")), None)
            wt_col  = next((c for c in d.columns if "weight" in c.lower() or "weighting" in c.lower()), None)
            if wt_col:
                d = d[d[wt_col].astype(str).str.lower().str.contains("aum")] if weighting=="AUM-weighted" else d[d[wt_col].astype(str).str.lower().str.contains(r"(equal|ew)")]
            if cat_col and val_col:
                alias = {
                    "clean200":"Clean200",
                    "prison":"Prisons", "prisons":"Prisons",
                    "deforestation":"Deforestation",
                    "fossil":"Fossil Fuel","fossil fuel":"Fossil Fuel","fossil_fuel":"Fossil Fuel",
                    "weapons":"Weapons",
                    "tobacco":"Tobacco",
                }
                d["_cat"] = d[cat_col].astype(str).str.lower().map(lambda x: alias.get(x, x.title()))
                keep = ["Clean200","Prisons","Deforestation","Fossil Fuel","Weapons","Tobacco"]
                d = d[d["_cat"].isin(keep)]
                d = d[(d["year"]>=start_year) & (d["year"]<=end_year)]
                d = d.rename(columns={val_col:"value"})
                sc = alt.Scale(domain=keep, range=[COLORS["clean"], COLORS["other"], COLORS["other"], COLORS["contro"], COLORS["contro"], COLORS["contro"]])
                ch = alt.Chart(d).mark_line(point=True).encode(
                    x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("value:Q", title="Exposure (%)", axis=alt.Axis(format=".1f")),
                    color=alt.Color("_cat:N", title=None, scale=sc),
                    tooltip=[alt.Tooltip("_cat:N"), alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Exposure (%)", format=".1f")]
                ).properties(height=300)
                st.altair_chart(ch, use_container_width=True)
            else:
                st.info("Screen trends: expected columns not found.")
        else:
            st.info("Screen trends: file empty or missing.")

        gap(8)

        # --------- Composition compare (Year A vs 2025) ----------
        st.markdown('<div class="chart-title">Overall composition — Year A vs 2025</div>', unsafe_allow_html=True)
        def _cat_series(cat_name):
            ds = _agg_pick(agg_tr, cat_name) if not agg_tr.empty else _fallback_series({"clean200":col_clean,"controversial":col_contro,"other":col_other}[cat_name])
            return ds

        comp_parts = []
        for label, key in [("Clean","clean200"),("Controversial","controversial"),("Other","other")]:
            s = _cat_series(key)
            if s.empty: continue
            rowA = {"Year": str(start_year), "Category": label, "Value": _val(s, start_year)}
            rowZ = {"Year": str(end_year),   "Category": label, "Value": _val(s, end_year)}
            comp_parts += [rowA, rowZ]
        comp_df = pd.DataFrame(comp_parts).dropna()
        comp_df["Year"] = pd.Categorical(comp_df["Year"], categories=[str(start_year), str(end_year)], ordered=True)
        color_all = alt.Scale(domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])
        bars = alt.Chart(comp_df).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
            x=alt.X("Year:N", title=None),
            y=alt.Y("Value:Q", stack="normalize", axis=alt.Axis(format='%'), title="Portfolio share"),
            color=alt.Color("Category:N", scale=color_all, title=None),
            tooltip=[alt.Tooltip("Year:N"), alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", title="Share (%)", format=".1f")]
        ).properties(height=180)
        st.altair_chart(bars, use_container_width=True)

        gap(8)

        # --------- Heatmap — Controversial by ETF × Year ----------
        st.markdown('<div class="chart-title">Heatmap — Controversial by ETF × Year</div>', unsafe_allow_html=True)
        if etf_col and col_contro:
            hm = df[[etf_col,"year",col_contro]].dropna()
            hm[col_contro] = pd.to_numeric(hm[col_contro], errors="coerce")
            etf_order = hm.groupby(etf_col)["year"].nunique().sort_values(ascending=False).index.tolist()
            hm[etf_col] = pd.Categorical(hm[etf_col].astype(str), categories=etf_order, ordered=True)
            heat = alt.Chart(hm).mark_rect().encode(
                x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y(f"{etf_col}:N", title=None, sort=etf_order),
                color=alt.Color(f"{col_contro}:Q", title="Controversial (%)", scale=alt.Scale(scheme="redyellowblue")),
                tooltip=[alt.Tooltip(f"{etf_col}:N", title="ETF"), alt.Tooltip("year:O"),
                         alt.Tooltip(f"{col_contro}:Q", title="Controversial (%)", format=".1f")]
            ).properties(height=min(26*max(1,len(etf_order)), 600))
            st.altair_chart(heat, use_container_width=True)
        else:
            st.info("Heatmap unavailable (missing ETF or controversial column).")

        gap(8)

        # --------- Biggest movers list ----------
        st.markdown('<div class="chart-title">Biggest movers — holdings driving change (Start → 2025)</div>', unsafe_allow_html=True)
        mv = movers.copy()
        mvcols = {c.lower(): c for c in mv.columns}
        sy = mvcols.get("year_a") or mvcols.get("start_year") or mvcols.get("startyear")
        ey = mvcols.get("year_b") or mvcols.get("end_year")   or mvcols.get("endyear")
        hcol = mvcols.get("holding_name") or mvcols.get("holding") or mvcols.get("name")
        ecol = mvcols.get("etf_ticker") or etf_col
        scrc = mvcols.get("screen") or mvcols.get("classification")
        contrib = mvcols.get("delta_contrib_pct_agg") or mvcols.get("contribution_pp") or mvcols.get("delta_pp")

        if sy and ey and hcol and contrib:
            mvv = mv[(mv[sy]==start_year) & (mv[ey]==end_year)].copy()
            if sel_etfs and ecol in mvv.columns:
                mvv = mvv[mvv[ecol].astype(str).isin(sel_etfs)]
            cols = []
            if ecol in mvv.columns: cols.append(("ETF", ecol))
            cols += [("Holding", hcol)]
            if scrc in mvv.columns: cols.append(("Screen", scrc))
            cols += [("Contribution (pp)", contrib)]
            table = mvv[[c for _,c in cols]].rename(columns={c:l for l,c in cols}).copy()
            table["Contribution (pp)"] = pd.to_numeric(table["Contribution (pp)"], errors="coerce")
            table["_abs"] = table["Contribution (pp)"].abs()
            table = table.sort_values("_abs", ascending=False).drop(columns=["_abs"]).head(50)
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.download_button("Download movers (CSV)", data=table.to_csv(index=False).encode("utf-8"),
                               file_name=f"movers_{start_year}_to_{end_year}.csv", mime="text/csv")
        else:
            st.info("Movers table unavailable (need year_a/year_b, holding_name, and contribution column).")




    # ---------------- Tradeoff Scenarios ----------------
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
