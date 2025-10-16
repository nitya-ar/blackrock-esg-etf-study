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
        st.caption("Track how exposures evolved using today’s (2025) classification, applied to past portfolios.")

        btn_col, _sp = st.columns([0.25, 0.75])
        with btn_col:
            if st.button("Reload Analysis 2 data", help="Clear cache and reload latest Analysis 2 CSVs"):
                st.cache_data.clear()
                st.rerun()

        try:
            by_fund = load_exposures_by_fund_year()
            agg_tr  = load_aggregate_trends()
            disp    = load_dispersion_stats()
            screens = load_screen_trends()
            ycs     = load_year_compare()
            movers  = load_movers_by_yearpair()
        except Exception as e:
            st.error(f"Could not load Analysis 2 CSVs: {e}")
            st.stop()

        for df in [by_fund, agg_tr, disp, screens, ycs, movers]:
            if "year" in df.columns:
                df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

        def _find_col(cands):
            for c in by_fund.columns:
                if any(k in c.lower() for k in cands):
                    return c
            return None

        col_map = {
            "contro": _find_col(["contro", "controversial"]),
            "clean":  _find_col(["clean200", "clean"]),
            "other":  _find_col(["other"])
        }
        if not col_map["other"] and col_map["clean"] and col_map["contro"]:
            by_fund["_other_derived"] = 100.0 - pd.to_numeric(by_fund[col_map["clean"]], errors="coerce") - pd.to_numeric(by_fund[col_map["contro"]], errors="coerce")
            col_map["other"] = "_other_derived"

        etf_ticker_col = next((c for c in by_fund.columns if c.lower() in ("etf_ticker","etf","ticker_etf","etfcode")), None)
        etf_name_col   = next((c for c in by_fund.columns if "name" in c.lower() and "etf" in c.lower()), None)

        if etf_ticker_col is None:
            st.warning("Could not find ETF ticker column (expected like 'ETF_TICKER'). Some charts may not render.")
        if col_map["contro"] is None or col_map["clean"] is None:
            st.warning("Missing exposure columns (controversial/clean). Check 'exposures_by_fund_year.csv'.")

        years_avail = sorted(pd.to_numeric(by_fund["year"].dropna().unique(), errors="coerce"))
        min_year, max_year = (min(years_avail), max(years_avail)) if years_avail else (2017, 2025)

        c1, c2, c3, c4 = st.columns([0.22, 0.22, 0.26, 0.30])
        with c1:
            yr_range = st.slider("Year Range", min_value=int(min_year), max_value=int(max_year), value=(int(min_year), int(max_year)))
        with c2:
            start_year = st.selectbox("Start Year", options=[y for y in years_avail if yr_range[0] <= y <= yr_range[1]], index=0)
        with c3:
            end_year = st.selectbox("End Year", options=[y for y in years_avail if yr_range[0] <= y <= yr_range[1]], index=len([y for y in years_avail if yr_range[0] <= y <= yr_range[1]])-1)
        with c4:
            weighting = st.segmented_control("Weighting", options=["AUM-weighted","Equal-weighted"], default="AUM-weighted", help="AUM-weighted = ETF weighted by net assets; Equal-weighted = every ETF counts the same.")

        cA, cB, cC = st.columns([0.22, 0.22, 0.56])
        with cA:
            cohort_mode = st.segmented_control("Cohort", options=["Intersect","All per year"], default="Intersect", help="Intersect compares ETFs present in both endpoints; All per year uses each year’s available ETFs.")
        with cB:
            category = st.segmented_control("Category", options=["Controversial","Clean200","Other"], default="Controversial")
        with cC:
            all_etfs = sorted(by_fund.get(etf_ticker_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) if etf_ticker_col in by_fund.columns else []
            sel_etfs = st.multiselect("ETFs (optional)", all_etfs, default=[])

        df_fy = by_fund[(by_fund["year"] >= yr_range[0]) & (by_fund["year"] <= yr_range[1])].copy()
        if sel_etfs and etf_ticker_col in df_fy.columns:
            df_fy = df_fy[df_fy[etf_ticker_col].astype(str).isin(sel_etfs)]

        if etf_ticker_col in df_fy.columns:
            start_set = set(df_fy.loc[df_fy["year"] == start_year, etf_ticker_col].dropna().astype(str))
            end_set   = set(df_fy.loc[df_fy["year"] == end_year,   etf_ticker_col].dropna().astype(str))
            keep = (start_set & end_set) if cohort_mode == "Intersect" else (start_set | end_set)
            df_endpoints = df_fy[df_fy[etf_ticker_col].astype(str).isin(keep)].copy()
        else:
            df_endpoints = df_fy.copy()

        k1, k2, k3, k4, k5 = st.columns(5)

        def _agg_pick(df, cat, wt):
            if df is None or df.empty:
                return None
            d = df.copy()
            cat_col = next((c for c in d.columns if c.lower() in ("category","classification","cohort","label")), None)
            val_col = next((c for c in d.columns if "share" in c.lower() or "exposure" in c.lower() or c.lower().endswith("_pct")), None)
            wt_col  = next((c for c in d.columns if "weight" in c.lower()), None)
            if cat_col is None or val_col is None:
                return None
            if wt and wt_col in d.columns:
                mask = (d[wt_col].astype(str).str.lower().str.contains("aum") if wt == "AUM-weighted" else d[wt_col].astype(str).str.lower().str.contains(("equal","ew")))
                d = d[mask]
            d["_cat"] = d[cat_col].astype(str).str.strip().str.lower().replace({"controversial":"controversial","contro":"controversial","clean200":"clean200","clean":"clean200","other":"other"})
            want = {"Controversial":"controversial","Clean200":"clean200","Other":"other"}[cat]
            ds = d[(d["year"] >= yr_range[0]) & (d["year"] <= yr_range[1])]
            ds = ds[ds["_cat"] == want]
            return ds, val_col

        def _kpi_vals(cat):
            if not ycs.empty:
                d = ycs.copy()
                cat_col = next((c for c in d.columns if c.lower() in ("category","classification","cohort","label")), None)
                sy = next((c for c in d.columns if "start" in c.lower() and "year" in c.lower()), None)
                ey = next((c for c in d.columns if "end" in c.lower() and "year" in c.lower()), None)
                sv = next((c for c in d.columns if "start" in c.lower() and ("pct" in c.lower() or "share" in c.lower() or "exposure" in c.lower())), None)
                ev = next((c for c in d.columns if "end" in c.lower() and ("pct" in c.lower() or "share" in c.lower() or "exposure" in c.lower())), None)
                wt = next((c for c in d.columns if "weight" in c.lower()), None)
                if all(x is not None for x in [cat_col, sy, ey, sv, ev]):
                    dd = d[(d[sy]==start_year) & (d[ey]==end_year)]
                    if wt in dd.columns:
                        mask = (dd[wt].astype(str).str.lower().str.contains("aum") if weighting=="AUM-weighted" else dd[wt].astype(str).str.lower().str.contains(("equal","ew")))
                        dd = dd[mask]
                    dd["_cat"] = d[cat_col].astype(str).str.strip().str.lower().replace({"controversial":"controversial","contro":"controversial","clean200":"clean200","clean":"clean200","other":"other"})
                    want = {"Controversial":"controversial","Clean200":"clean200","Other":"other"}[cat]
                    row = dd[dd["_cat"]==want]
                    if not row.empty:
                        s_val = float(pd.to_numeric(row[sv], errors="coerce").iloc[0])
                        e_val = float(pd.to_numeric(row[ev], errors="coerce").iloc[0])
                        return s_val, e_val, e_val - s_val
            picked = _agg_pick(agg_tr, cat, weighting)
            if picked is None:
                return None, None, None
            ds, val_col = picked
            if ds.empty:
                return None, None, None
            s_val = float(pd.to_numeric(ds.loc[ds["year"]==start_year, val_col], errors="coerce").mean())
            e_val = float(pd.to_numeric(ds.loc[ds["year"]==end_year,   val_col], errors="coerce").mean())
            return s_val, e_val, e_val - s_val

        s_c, e_c, d_c = _kpi_vals("Controversial")
        s_l, e_l, d_l = _kpi_vals("Clean200")
        s_o, e_o, d_o = _kpi_vals("Other")

        with k1: kpi_card("Controversial (End)", pct_fmt(e_c if e_c is not None else float("nan")), tone="red")
        with k2: kpi_card("Δ Controversial (pp)", f"{(d_c if d_c is not None else float('nan')):.1f} pp", tone="red" if (d_c or 0)>0 else "green")
        with k3: kpi_card("Clean200 (End)", pct_fmt(e_l if e_l is not None else float("nan")), tone="green")
        with k4: kpi_card("Other (End)", pct_fmt(e_o if e_o is not None else float("nan")), tone="neutral")

        if etf_ticker_col and col_map["contro"]:
            d0 = df_endpoints[df_endpoints["year"].isin([start_year, end_year])][[etf_ticker_col, "year", col_map["contro"]]].copy()
            d0[col_map["contro"]] = pd.to_numeric(d0[col_map["contro"]], errors="coerce")
            wide = d0.pivot_table(index=etf_ticker_col, columns="year", values=col_map["contro"])
            if start_year in wide.columns and end_year in wide.columns:
                delta = (wide[end_year] - wide[start_year]).dropna()
                n_down = int((delta < 0).sum())
                n_up   = int((delta > 0).sum())
                with k5:
                    kpi_card("ETFs ↓contro / ↑contro", f"{n_down} / {n_up}", tone="neutral")

        st.markdown(
            f"""<div class="chart-head">
                   <div class="chart-title">Aggregate trend — Clean vs Controversial vs Other ({weighting}; {cohort_mode.lower()} cohort)</div>
                   <div class="info-badge has-tip" data-tip="2025 classifications applied to historical holdings. Headline categories partition the portfolio; sub-screens may overlap.">i</div>
               </div>""",
            unsafe_allow_html=True,
        )

        def build_agg_series():
            if not agg_tr.empty:
                d = agg_tr.copy()
                cat_col = next((c for c in d.columns if c.lower() in ("category","classification","label")), None)
                val_col = next((c for c in d.columns if "share" in c.lower() or "exposure" in c.lower() or c.lower().endswith("_pct")), None)
                wt_col  = next((c for c in d.columns if "weight" in c.lower()), None)
                if cat_col and val_col:
                    if wt_col in d.columns:
                        mask = (d[wt_col].astype(str).str.lower().str.contains("aum") if weighting=="AUM-weighted" else d[wt_col].astype(str).str.lower().str.contains(("equal","ew")))
                        d = d[mask]
                    d["_cat"] = d[cat_col].astype(str).str.strip().str.lower().replace({"controversial":"Controversial","contro":"Controversial","clean200":"Clean200","clean":"Clean200","other":"Other"})
                    d = d[(d["year"] >= yr_range[0]) & (d["year"] <= yr_range[1])]
                    d = d.rename(columns={val_col:"value"})
                    return d[["year","_cat","value"]]
            t = []
            for lab, col in [("Controversial", col_map["contro"]), ("Clean200", col_map["clean"]), ("Other", col_map["other"])]:
                if col:
                    g = df_fy.groupby("year")[col].mean().reset_index()
                    g["_cat"] = lab
                    g = g.rename(columns={col:"value"})
                    t.append(g)
            return pd.concat(t, ignore_index=True) if t else pd.DataFrame(columns=["year","_cat","value"])

        agg_series = build_agg_series()

        ribbon = None
        if not disp.empty:
            d = disp.copy()
            cat_col = next((c for c in d.columns if c.lower() in ("category","classification","label")), None)
            p25 = next((c for c in d.columns if "25" in c.lower() or "p25" in c.lower()), None)
            p50 = next((c for c in d.columns if "50" in c.lower() or "median" in c.lower() or "p50" in c.lower()), None)
            p75 = next((c for c in d.columns if "75" in c.lower() or "p75" in c.lower()), None)
            if all([cat_col, p25, p50, p75]):
                d["_cat"] = d[cat_col].astype(str).str.strip().str.lower().replace({"controversial":"Controversial","contro":"Controversial","clean200":"Clean200","clean":"Clean200","other":"Other"})
                d = d[(d["year"] >= yr_range[0]) & (d["year"] <= yr_range[1])]
                d = d.rename(columns={p25:"p25", p50:"p50", p75:"p75"})
                ribbon = d

        color_scale = alt.Scale(domain=["Clean200","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])

        base = alt.Chart(agg_series).encode(x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)))
        lines = base.mark_line(point=True).encode(
            y=alt.Y("value:Q", title="Exposure (%)", axis=alt.Axis(format=".1f")),
            color=alt.Color("_cat:N", scale=color_scale, title=None),
            tooltip=[alt.Tooltip("_cat:N", title="Category"), alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Exposure (%)", format=".1f")]
        )
        if ribbon is not None:
            rib = alt.Chart(ribbon).mark_area(opacity=0.18).encode(
                x="year:O", y="p25:Q", y2="p75:Q",
                color=alt.Color("_cat:N", scale=color_scale, title=None, legend=None),
                tooltip=[alt.Tooltip("_cat:N"), alt.Tooltip("year:O"), alt.Tooltip("p25:Q", format=".1f"), alt.Tooltip("p50:Q", format=".1f"), alt.Tooltip("p75:Q", format=".1f")]
            )
            st.altair_chart((rib + lines).properties(height=300), use_container_width=True)
        else:
            st.altair_chart(lines.properties(height=300), use_container_width=True)

        sA, sB = st.columns([0.55, 0.45])
        cat_to_col = {"Controversial": col_map["contro"], "Clean200": col_map["clean"], "Other": col_map["other"]}
        cat_col_sel = cat_to_col.get(category)

        with sA:
            st.markdown(f'<div class="chart-title">Per-ETF change — {category}: {start_year} → {end_year}</div>', unsafe_allow_html=True)
            if etf_ticker_col and cat_col_sel and start_year != end_year:
                d0 = df_endpoints[df_endpoints["year"].isin([start_year, end_year])][[etf_ticker_col, "year", cat_col_sel]].copy()
                d0[cat_col_sel] = pd.to_numeric(d0[cat_col_sel], errors="coerce")
                wide = d0.pivot_table(index=etf_ticker_col, columns="year", values=cat_col_sel)
                wide = wide.dropna(subset=[start_year, end_year], how="any")
                slope = wide.reset_index().melt(id_vars=etf_ticker_col, var_name="Year", value_name="Value")
                order = (wide[end_year] - wide[start_year]).abs().sort_values(ascending=False).index.tolist()
                slope["ETF_Order"] = pd.Categorical(slope[etf_ticker_col].astype(str), categories=order, ordered=True)
                chart = alt.Chart(slope).mark_line(opacity=0.9).encode(
                    x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Value:Q", title=f"{category} (%)", axis=alt.Axis(format=".1f")),
                    detail=alt.Detail(f"{etf_ticker_col}:N"),
                    order="Year:O",
                    tooltip=[alt.Tooltip(f"{etf_ticker_col}:N", title="ETF"), alt.Tooltip("Year:O"), alt.Tooltip("Value:Q", title=f"{category} (%)", format=".1f")],
                    color=alt.Color(f"{etf_ticker_col}:N", legend=None)
                ).properties(height=360)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Slope graph unavailable (missing ETF or category columns, or identical start/end years).")

        with sB:
            st.markdown(f'<div class="chart-title">Distribution across ETFs — {category}</div>', unsafe_allow_html=True)
            if etf_ticker_col and cat_col_sel:
                d1 = df_fy[[etf_ticker_col,"year",cat_col_sel]].copy()
                d1[cat_col_sel] = pd.to_numeric(d1[cat_col_sel], errors="coerce")
                box = alt.Chart(d1).mark_boxplot(extent="min-max").encode(
                    x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y(f"{cat_col_sel}:Q", title=f"{category} (%)", axis=alt.Axis(format=".1f")),
                    tooltip=[alt.Tooltip("year:O"), alt.Tooltip(f"{cat_col_sel}:Q", title=f"{category} (%)", format=".1f")]
                ).properties(height=300)
                st.altair_chart(box, use_container_width=True)
            else:
                st.warning("Distribution chart unavailable.")

        st.markdown(f'<div class="chart-title">Heatmap — {category} by ETF × Year</div>', unsafe_allow_html=True)
        if etf_ticker_col and cat_col_sel:
            d2 = df_fy[[etf_ticker_col,"year",cat_col_sel]].copy()
            d2[cat_col_sel] = pd.to_numeric(d2[cat_col_sel], errors="coerce")
            etf_counts = d2.groupby(etf_ticker_col)["year"].nunique()
            keep_etfs = etf_counts.sort_values(ascending=False).index.tolist()
            d2[etf_ticker_col] = pd.Categorical(d2[etf_ticker_col].astype(str), categories=keep_etfs, ordered=True)
            heat = alt.Chart(d2).mark_rect().encode(
                x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y(f"{etf_ticker_col}:N", title=None, sort=keep_etfs),
                color=alt.Color(f"{cat_col_sel}:Q", title=f"{category} (%)", scale=alt.Scale(scheme="blueorange")),
                tooltip=[alt.Tooltip(f"{etf_ticker_col}:N", title="ETF"), alt.Tooltip("year:O"), alt.Tooltip(f"{cat_col_sel}:Q", title=f"{category} (%)", format=".1f")]
            ).properties(height=min(26*max(1,len(keep_etfs)), 600))
            st.altair_chart(heat, use_container_width=True)
        else:
            st.warning("Heatmap unavailable.")

        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Biggest movers between selected years (holdings-level)</div>', unsafe_allow_html=True)
        mv = movers.copy()
        mvcols = {c.lower(): c for c in mv.columns}
        mv_sy = next((mvcols[k] for k in mvcols if "start" in k and "year" in k), None)
        mv_ey = next((mvcols[k] for k in mvcols if "end" in k and "year" in k), None)
        mv_etf = next((mvcols[k] for k in mvcols if "etf" in k and "ticker" in k), None) or etf_ticker_col
        mv_hold = next((mvcols[k] for k in mvcols if "holding" in k or "name" in k), None)
        mv_tag = next((mvcols[k] for k in mvcols if "screen" in k), None)
        mv_dpp = next((mvcols[k] for k in mvcols if "delta" in k and ("pp" in k or "pct" in k)), None)
        mv_contr = next((mvcols[k] for k in mvcols if "contribution" in k and ("pp" in k or "pct" in k)), None)
        mv_sw = next((mvcols[k] for k in mvcols if "start" in k and ("weight" in k or "pct" in k)), None)
        mv_ew = next((mvcols[k] for k in mvcols if "end" in k and ("weight" in k or "pct" in k)), None)

        if mv_sy and mv_ey and mv_hold:
            mview = mv[(mv[mv_sy]==start_year) & (mv[mv_ey]==end_year)].copy()
            if sel_etfs and mv_etf in mview.columns:
                mview = mview[mview[mv_etf].astype(str).isin(sel_etfs)]
            disp_cols = []
            if mv_etf in mview.columns: disp_cols.append(("ETF", mv_etf))
            disp_cols += [("Holding", mv_hold)]
            if mv_tag in mview.columns: disp_cols.append(("Screen", mv_tag))
            if mv_dpp in mview.columns: disp_cols.append(("Δ Weight (pp)", mv_dpp))
            if mv_contr in mview.columns: disp_cols.append(("Contribution (pp)", mv_contr))
            if mv_sw in mview.columns: disp_cols.append(("Start Weight (%)", mv_sw))
            if mv_ew in mview.columns: disp_cols.append(("End Weight (%)", mv_ew))
            df_mv = mview[[c for _, c in disp_cols]].copy()
            rename = {c: lbl for lbl, c in disp_cols}
            df_mv = df_mv.rename(columns=rename)
            sort_col = "Contribution (pp)" if "Contribution (pp)" in df_mv.columns else ("Δ Weight (pp)" if "Δ Weight (pp)" in df_mv.columns else None)
            if sort_col:
                df_mv["_abs_sort"] = df_mv[sort_col].apply(lambda x: abs(float(x)) if pd.notna(x) else 0.0)
                df_mv = df_mv.sort_values("_abs_sort", ascending=False).drop(columns=["_abs_sort"])
            st.dataframe(df_mv.head(50), use_container_width=True, hide_index=True)
            csv_bytes = df_mv.to_csv(index=False).encode("utf-8")
            st.download_button("Download movers (CSV)", data=csv_bytes, file_name=f"movers_{start_year}_{end_year}.csv", mime="text/csv")
        else:
            st.info("Movers table unavailable (expected movers_by_yearpair columns not found).")

        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Data table — Per-ETF exposures (filtered)</div>', unsafe_allow_html=True)
        show_cols = []
        for c in [etf_ticker_col, etf_name_col, "year", col_map["contro"], col_map["clean"], col_map["other"]]:
            if c and c in df_fy.columns and c not in show_cols:
                show_cols.append(c)
        df_show = df_fy[show_cols].copy() if show_cols else df_fy.copy()
        rename_disp = {}
        if col_map["contro"] in df_show.columns: rename_disp[col_map["contro"]] = "Controversial (%)"
        if col_map["clean"]  in df_show.columns: rename_disp[col_map["clean"]]  = "Clean200 (%)"
        if col_map["other"]  in df_show.columns: rename_disp[col_map["other"]]  = "Other (%)"
        if etf_ticker_col in df_show.columns:    rename_disp[etf_ticker_col]    = "ETF"
        if etf_name_col in df_show.columns:      rename_disp[etf_name_col]      = "ETF Name"
        df_show = df_show.rename(columns=rename_disp)
        st.dataframe(df_show.sort_values(["year","ETF"] if "ETF" in df_show.columns else ["year"]), use_container_width=True, hide_index=True)
        csv_slice = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered per-ETF exposures (CSV)", data=csv_slice, file_name="exposures_by_fund_year_filtered.csv", mime="text/csv")


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
