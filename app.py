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
        st.caption("How exposures evolved from Year A to 2025. AUM/EW toggle and cohort control affect all visuals below.")

        aet = load_aggregate_trends()
        eds = load_dispersion_stats()
        eby = load_exposures_by_fund_year()
        ycs = load_year_compare()
        ast = load_screen_trends()
        mv  = load_movers_by_yearpair()

        # normalize column names and values
        if "ETF ticker" in eby.columns and "etf_ticker" not in eby.columns:
            eby = eby.rename(columns={"ETF ticker": "etf_ticker"})

        # coerce and renormalize ETF x year rows to avoid >100% totals
        if {"year","pct_clean","pct_controversial","pct_other"}.issubset(eby.columns):
            for c in ["pct_clean","pct_controversial","pct_other"]:
                eby[c] = pd.to_numeric(eby[c], errors="coerce")
            sums = eby[["pct_clean","pct_controversial","pct_other"]].sum(axis=1)
            valid = sums.mask(~sums.gt(0), 1.0)
            eby["pct_clean"]         = (eby["pct_clean"] / valid).clip(0,1)*100
            eby["pct_controversial"] = (eby["pct_controversial"] / valid).clip(0,1)*100
            eby["pct_other"]         = (eby["pct_other"] / valid).clip(0,1)*100

        yrs_all = sorted(aet["year"].dropna().unique().tolist()) if "year" in aet.columns else sorted(eby["year"].dropna().unique().tolist())
        yrs_a_choices = [y for y in yrs_all if y != 2025] or [2017]

        # --- controls
        c_year, c_weight, c_cohort, c_metric = st.columns([0.22, 0.22, 0.22, 0.34])
        with c_year:
            year_a = st.selectbox("Year A", yrs_a_choices, index=0)
        with c_weight:
            weighting_choice = st.segmented_control(
                "Weighting", options=["AUM-weighted","Equal-weighted"], default="AUM-weighted",
                help="AUM uses ETF AUM; EW treats each ETF equally."
            )
            wmode = {"AUM-weighted":"AUM","Equal-weighted":"EW"}[weighting_choice]
        with c_cohort:
            cohort_only = st.toggle("Only ETFs present in both years", value=True)
        with c_metric:
            slope_metric = st.segmented_control("Slope metric", options=["% Clean","% Controversial"], default="% Clean")

        # helpers
        def get_agg(year, cls):
            if aet.empty: return None
            df = aet[(aet["year"]==year) & (aet["weighting_mode"]==wmode)]
            if df.empty: return None
            key = {"Clean":"pct_clean","Controversial":"pct_controversial","Other":"pct_other"}[cls]
            val = pd.to_numeric(df[key], errors="coerce").dropna()
            return float(val.iloc[0]) if len(val) else None

        # headline deltas (A -> 2025)
        clean_a, clean_b = get_agg(year_a, "Clean"), get_agg(2025, "Clean")
        contro_a, contro_b = get_agg(year_a, "Controversial"), get_agg(2025, "Controversial")
        other_a, other_b = get_agg(year_a, "Other"), get_agg(2025, "Other")

        k1, k2, k3, k4 = st.columns(4)
        d_clean  = (clean_b or 0)  - (clean_a or 0)   if (clean_a is not None and clean_b is not None) else None
        d_contro = (contro_b or 0) - (contro_a or 0)  if (contro_a is not None and contro_b is not None) else None
        with k1: kpi_card("Δ Clean (pp)", f"{d_clean:.1f}%" if d_clean is not None else "-", tone="green" if (d_clean or 0) >= 0 else "red")
        with k2: kpi_card("Δ Controversial (pp)", f"{d_contro:.1f}%" if d_contro is not None else "-", tone="red" if (d_contro or 0) > 0 else "green")

        if "aum_total_usd" in aet.columns:
            aum_2025 = aet[(aet["year"]==2025) & (aet["weighting_mode"]==wmode)]["aum_total_usd"]
            aum_disp = usd_fmt(aum_2025.dropna().iloc[0]) if len(aum_2025.dropna()) else "-"
        else:
            aum_disp = "-"
        with k3: kpi_card("Total AUM (2025)", aum_disp, tone="neutral")

        # cohort filter for ETF-level artifacts and counts
        def cohort_mask(df):
            if not cohort_only or "etf_ticker" not in df.columns:
                return pd.Series(True, index=df.index)
            a = set(df.loc[df["year"]==year_a, "etf_ticker"].dropna().unique())
            b = set(df.loc[df["year"]==2025,   "etf_ticker"].dropna().unique())
            keep = a.intersection(b)
            return df["etf_ticker"].isin(list(keep))

        if "etf_ticker" in eby.columns:
            eby_masked = eby.loc[cohort_mask(eby)].copy()
            if not eby_masked.empty:
                piv = eby_masked.pivot_table(index="etf_ticker", columns="year", values="pct_clean")
                num_cleaner = int((piv.get(2025) - piv.get(year_a)).dropna().gt(0).sum())
            else:
                num_cleaner = 0
        else:
            eby_masked, num_cleaner = eby, 0

        with k4: kpi_card("# ETFs cleaner", f"{num_cleaner}", tone="neutral")

        gap(6)
        c1, c2 = st.columns([0.55, 0.45])

        # --- Aggregate trend 2017–2025 (Clean / Contro / Other)
        with c1:
            st.markdown(
                '<div class="chart-head"><div class="chart-title">Aggregate trend (2017–2025) — Clean vs Controversial vs Other</div><div></div></div>',
                unsafe_allow_html=True
            )
            if not aet.empty:
                show = aet[aet["weighting_mode"]==wmode].copy()
                for c in ["pct_clean","pct_controversial","pct_other"]:
                    show[c] = pd.to_numeric(show[c], errors="coerce")
                show = show.melt(
                    id_vars=["year","weighting_mode"],
                    value_vars=["pct_clean","pct_controversial","pct_other"],
                    var_name="class", value_name="pct"
                )
                show["class"] = show["class"].map({"pct_clean":"Clean","pct_controversial":"Controversial","pct_other":"Other"})
                color_scale = alt.Scale(domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])
                line = alt.Chart(show).mark_line(point=True).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("pct:Q", title="Share of total (%)", scale=alt.Scale(domain=[0,100])),
                    color=alt.Color("class:N", scale=color_scale, title=None),
                    tooltip=[
                        alt.Tooltip("year:O",  title="Year"),
                        alt.Tooltip("class:N", title="Class"),
                        alt.Tooltip("pct:Q",   title="%", format=".1f"),
                    ],
                ).properties(height=260)
                st.altair_chart(line, use_container_width=True)
            else:
                st.info("aggregate_exposure_trends.csv is empty")

        # --- Dispersion fan (p10–p90 band + p50 line)
        with c2:
            st.markdown(
                '<div class="chart-head"><div class="chart-title">Dispersion fan — p10–p90 with median</div><div class="info-badge has-tip" data-tip="Distribution of ETF exposures by year; wider band = greater dispersion across funds.">i</div></div>',
                unsafe_allow_html=True
            )
            if not eds.empty:
                target = st.radio("Target", options=["Clean","Controversial"], horizontal=True, label_visibility="collapsed")
                e = eds[eds["target"].str.title()==target].copy()
                for c in ["p10","p50","p90"]:
                    e[c] = pd.to_numeric(e[c], errors="coerce")
                band = alt.Chart(e).mark_area(opacity=0.25).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("p10:Q",  title="%", scale=alt.Scale(domain=[0,100])),
                    y2="p90:Q",
                    tooltip=[
                        alt.Tooltip("year:O", title="Year"),
                        alt.Tooltip("p10:Q",  title="p10", format=".1f"),
                        alt.Tooltip("p50:Q",  title="p50", format=".1f"),
                        alt.Tooltip("p90:Q",  title="p90", format=".1f"),
                    ],
                )
                med = alt.Chart(e).mark_line().encode(x="year:O", y="p50:Q")
                st.altair_chart((band + med), use_container_width=True)
            else:
                st.info("exposure_dispersion_stats.csv is empty")

        gap(10)
        st.markdown(
            '<div class="chart-head"><div class="chart-title">ETF slopes — change from Year A to 2025</div><div class="info-badge has-tip" data-tip="Sorted by largest improvement; cohort filter applies.">i</div></div>',
            unsafe_allow_html=True
        )

        # --- ETF slopes (A -> 2025), facet-sorted by numeric delta (Altair v5-safe)
        if "etf_ticker" in eby_masked.columns:
            metric_col = "pct_clean" if slope_metric == "% Clean" else "pct_controversial"
            ef = eby_masked[eby_masked["year"].isin([year_a, 2025])][["etf_ticker","year",metric_col]].dropna()
            if not ef.empty:
                ef[metric_col] = pd.to_numeric(ef[metric_col], errors="coerce")
                ef["year"] = ef["year"].astype(str)  # two-point slope

                piv = (
                    eby_masked.pivot_table(index="etf_ticker", columns="year", values=metric_col)
                    .rename(columns={year_a: "A", 2025: "B"})
                )
                piv["delta"] = (piv["B"] - piv["A"])
                delta_map = piv["delta"].to_dict()
                ef["delta"] = ef["etf_ticker"].map(delta_map)

                base = alt.Chart(ef).encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y(f"{metric_col}:Q", title="%", scale=alt.Scale(domain=[0,100])),
                    tooltip=[
                        alt.Tooltip("etf_ticker:N",   title="ETF"),
                        alt.Tooltip("year:O",         title="Year"),
                        alt.Tooltip(f"{metric_col}:Q", title="%", format=".1f"),
                        alt.Tooltip("delta:Q",        title="Δ (A→2025)", format=".1f"),
                    ],
                )
                lines = base.mark_line().encode(detail="etf_ticker:N")
                pts   = base.mark_point(filled=True, size=35)

                chart = (lines + pts).facet(
                    facet=alt.Facet(
                        "etf_ticker:N",
                        sort=alt.SortField(field="delta", order="descending"),
                        title=None
                    ),
                    columns=6
                ).properties(height=120)

                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No ETF slope data after filters.")
        else:
            st.info("exposures_by_fund_year is missing etf_ticker.")

        gap(6)
        l1, r1 = st.columns([0.55, 0.45])

        # --- Year A vs 2025 composition bars (normalized)
        with l1:
            st.markdown('<div class="chart-head"><div class="chart-title">Year A vs 2025 — composition and deltas</div><div></div></div>', unsafe_allow_html=True)
            g = ycs.copy()
            if not g.empty:
                if "weighting_mode" in g.columns:
                    g = g[g["weighting_mode"]==wmode]
                if "classification" in g.columns:
                    g["classification"] = g["classification"].astype(str).str.title()
                g = g[g["year"].isin([year_a, 2025])]
                cats = ["Clean","Controversial","Other"]
                gg = g[g["classification"].isin(cats)].copy()
                gg["exposure_pct"] = pd.to_numeric(gg["exposure_pct"], errors="coerce")
                color_scale = alt.Scale(domain=cats, range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])
                bar = alt.Chart(gg).mark_bar().encode(
                    x=alt.X("year:O", title=None),
                    y=alt.Y("exposure_pct:Q", title="%", stack="normalize"),
                    color=alt.Color("classification:N", scale=color_scale, title=None),
                    tooltip=[
                        alt.Tooltip("classification:N", title="Class"),
                        alt.Tooltip("year:O",          title="Year"),
                        alt.Tooltip("exposure_pct:Q",  title="%", format=".1f"),
                    ],
                ).properties(height=220)
                st.altair_chart(bar, use_container_width=True)
            else:
                st.info("year_compare_summary.csv is empty")

        # --- Screen trends (if/when populated)
        with r1:
            st.markdown('<div class="chart-head"><div class="chart-title">By-screen trends (2017–2025)</div><div class="info-badge has-tip" data-tip="Clean200 and controversial screens; categories overlap.">i</div></div>', unsafe_allow_html=True)
            if not ast.empty:
                screens = sorted(ast["screen_category"].dropna().unique().tolist())
                pick = st.multiselect(
                    "Screens", screens,
                    default=[s for s in screens if s and s.lower() in ["clean200","fossil","weapons","tobacco","prisons","deforestation"]][:4]
                )
                aa = ast.copy()
                if pick:
                    aa = aa[aa["screen_category"].isin(pick)]
                if "weighting_mode" in aa.columns:
                    aa = aa[aa["weighting_mode"]==wmode]
                aa["exposure_pct"] = pd.to_numeric(aa["exposure_pct"], errors="coerce")
                ln = alt.Chart(aa).mark_line(point=True).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("exposure_pct:Q", title="Share of total (%)", scale=alt.Scale(domain=[0,100])),
                    color=alt.Color("screen_category:N", title=None),
                    tooltip=[
                        alt.Tooltip("screen_category:N", title="Screen"),
                        alt.Tooltip("year:O",            title="Year"),
                        alt.Tooltip("exposure_pct:Q",    title="%", format=".1f"),
                    ],
                ).properties(height=240)
                st.altair_chart(ln, use_container_width=True)
            else:
                st.info("aggregate_screen_trends.csv is empty — populate to enable screen-level trends.")

        gap(6)
        st.markdown('<div class="chart-head"><div class="chart-title">Movers — what drove the change (Year A → 2025)</div><div></div></div>', unsafe_allow_html=True)
        if not mv.empty and {"year_a","year_b"}.issubset(mv.columns):
            mv_pair = mv[(mv["year_a"]==year_a) & (mv["year_b"]==2025)].copy()

            # find best available delta/name columns across schemas
            delta_col = next((c for c in [
                "delta_contrib_pct_agg","delta_weight_pp","delta_contrib_pp","delta_pct_points","delta"
            ] if c in mv_pair.columns), None)
            name_cols = [c for c in ["holding_name","name","company_name"] if c in mv_pair.columns]
            tick_col = next((c for c in ["ticker","company_ticker"] if c in mv_pair.columns), None)
            tags_col = next((c for c in ["screen_tags","screens","tags"] if c in mv_pair.columns), None)
            appear_a = next((c for c in ["appear_in_n_funds_a","funds_a","n_funds_a"] if c in mv_pair.columns), None)
            appear_b = next((c for c in ["appear_in_n_funds_b","funds_b","n_funds_b"] if c in mv_pair.columns), None)

            if delta_col and name_cols:
                mv_pair[delta_col] = pd.to_numeric(mv_pair[delta_col], errors="coerce")
                top_adds = mv_pair.sort_values(delta_col, ascending=False).head(15)
                top_drops = mv_pair.sort_values(delta_col, ascending=True).head(15)

                def slim(df):
                    cols = [c for c in [tick_col, name_cols[0], delta_col, tags_col, appear_a, appear_b] if c]
                    out = df[cols].copy()
                    out[delta_col] = out[delta_col].map(lambda v: f"{v:.2f}")
                    # tidy column titles
                    rename = {}
                    if tick_col:   rename[tick_col] = "Ticker"
                    rename[name_cols[0]] = "Holding"
                    rename[delta_col] = "Δ contrib (pp)"
                    if tags_col:   rename[tags_col] = "Screen tags"
                    if appear_a:   rename[appear_a] = "#ETFs (A)"
                    if appear_b:   rename[appear_b] = "#ETFs (B)"
                    return out.rename(columns=rename)

                t1, t2 = st.columns(2)
                with t1:
                    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top Adds (↑ contribution)</div>', unsafe_allow_html=True)
                    st.dataframe(slim(top_adds), use_container_width=True, hide_index=True)
                with t2:
                    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top Drops (↓ contribution)</div>', unsafe_allow_html=True)
                    st.dataframe(slim(top_drops), use_container_width=True, hide_index=True)
            else:
                st.info("Movers file is present but the expected delta/name columns weren’t found.")
        else:
            st.info("movers_by_yearpair.csv is empty or missing year_a/year_b.")

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
