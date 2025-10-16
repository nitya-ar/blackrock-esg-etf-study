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




    # ---------------- Change Since 2017 ----------------
    with tab2:
        st.subheader("Change since 2017")
        st.caption("All years are evaluated using the 2025 classification.")

        # ---------- load ----------
        try:
            by_fund = load_exposures_by_fund_year()
            agg_tr  = load_aggregate_trends()
            scr_tr  = load_screen_trends()
            movers  = load_movers_by_yearpair()
        except Exception as e:
            st.error(f"Could not load Analysis 2 CSVs: {e}")
            st.stop()

        # ---------- helpers ----------
        def _pick(df, *keys):
            kl = [k.lower() for k in keys]
            for c in df.columns:
                lc = c.lower()
                if any(k in lc for k in kl):
                    return c
            return None

        # canonical columns
        etf_col   = _pick(by_fund, "etf_ticker", "etf ticker", "etf")
        clean_col = _pick(by_fund, "pct_clean", "clean200", "clean")
        ctr_col   = _pick(by_fund, "pct_controversial", "controversial", "contro")
        oth_col   = _pick(by_fund, "pct_other", "other")

        # derive other if missing
        if not oth_col and clean_col and ctr_col:
            by_fund["_other_derived"] = 100.0 \
                - pd.to_numeric(by_fund[clean_col], errors="coerce") \
                - pd.to_numeric(by_fund[ctr_col],   errors="coerce")
            oth_col = "_other_derived"

        # normalize years
        for df_ in (by_fund, agg_tr, scr_tr, movers):
            if df_ is not None and "year" in df_.columns:
                df_["year"] = pd.to_numeric(df_["year"], errors="coerce").astype("Int64")

        years = sorted([int(y) for y in by_fund.get("year", pd.Series(dtype="Int64")).dropna().unique().tolist()]) or list(range(2017, 2026))
        end_year = 2025 if 2025 in years else max(years)
        min_year = min(years)

        # try hard to detect AUM column
        aum_col = _pick(
            by_fund,
            "aum_usd","etf_aum_usd","fund_aum_usd","aum","net_assets","net_assets_usd",
            "tna","assets","total_aum","aum_musd","aum_bln"
        )

        # ---------- filters ----------
        f1, f2, f3 = st.columns([0.44, 0.28, 0.28])
        with f1:
            all_etfs = sorted(by_fund.get(etf_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) if etf_col else []
            sel_etfs = st.multiselect("ETF (default: all)", all_etfs, default=[])
        with f2:
            start_year = st.slider("Start Year", min_value=min_year, max_value=max(end_year-1, min_year), value=min_year)
        with f3:
            st.markdown(
                '<div class="chart-head"><div class="chart-title">Weighting</div>'
                '<div class="info-badge has-tip" data-tip="AUM-weighted averages ETFs by assets; Equal-weighted gives each ETF the same weight.">i</div></div>',
                unsafe_allow_html=True,
            )
            weighting = st.segmented_control("Weighting", ["AUM-weighted", "Equal-weighted"], default="AUM-weighted", label_visibility="collapsed")

        # apply ETF filter
        df = by_fund.copy()
        if sel_etfs and etf_col in df.columns:
            df = df[df[etf_col].astype(str).isin(sel_etfs)]

        # coverage
        yA, yZ = df[df["year"]==start_year], df[df["year"]==end_year]
        setA = set(yA.get(etf_col, pd.Series([], dtype=str)).astype(str)) if etf_col in yA.columns else set()
        setZ = set(yZ.get(etf_col, pd.Series([], dtype=str)).astype(str)) if etf_col in yZ.columns else set()
        covA, covZ, covI = len(setA), len(setZ), len(setA & setZ)

        # weighting for aggregate tables
        def _mask_weighting_agg(d: pd.DataFrame) -> pd.DataFrame:
            wt_col = _pick(d, "weight", "weighting")
            if wt_col and wt_col in d.columns:
                if weighting == "AUM-weighted":
                    return d[d[wt_col].astype(str).str.lower().str.contains("aum")]
                return d[d[wt_col].astype(str).str.lower().str.contains("equal|ew", regex=True)]
            return d

        # compute series from per-fund table using chosen weighting (fallback path)
        def _series_from_funds(col_name: str) -> pd.DataFrame:
            if not col_name or col_name not in df.columns or df.empty:
                return pd.DataFrame(columns=["year","value"])
            d = df[["year", col_name]].copy()
            d[col_name] = pd.to_numeric(d[col_name], errors="coerce")
            if weighting == "AUM-weighted" and aum_col in df.columns:
                tmp = df[["year", col_name, aum_col]].copy()
                tmp[aum_col] = pd.to_numeric(tmp[aum_col], errors="coerce").clip(lower=0)
                out = tmp.groupby("year").apply(
                    lambda g: (g[col_name]*g[aum_col]).sum()/g[aum_col].sum() if g[aum_col].sum()>0 else pd.NA
                ).reset_index(name="value")
            else:
                out = d.groupby("year")[col_name].mean().reset_index().rename(columns={col_name:"value"})
            return out[(out["year"]>=start_year) & (out["year"]<=end_year)]

        # preferred: aggregate exposure trends; else fallback to per-fund
        def _series(cat_key: str) -> pd.DataFrame:
            if agg_tr is not None and not agg_tr.empty:
                d = _mask_weighting_agg(agg_tr.copy())
                cat_col = _pick(d, "category", "classification", "label")
                val_col = _pick(d, "share", "exposure", "_pct")
                if cat_col and val_col:
                    want = {"clean200":"clean200","controversial":"controversial","other":"other"}[cat_key]
                    dd = d[d[cat_col].astype(str).str.lower()==want][["year", val_col]].rename(columns={val_col:"value"})
                    dd = dd[(dd["year"]>=start_year) & (dd["year"]<=end_year)]
                    if not dd.empty:
                        return dd
            fmap = {"clean200": clean_col, "controversial": ctr_col, "other": oth_col}
            return _series_from_funds(fmap.get(cat_key))

        def _val(s: pd.DataFrame, yr: int):
            v = pd.to_numeric(s.loc[s["year"]==yr, "value"], errors="coerce")
            return float(v.iloc[0]) if len(v) else float("nan")

        s_clean  = _series("clean200")
        s_contro = _series("controversial")

        # If AUM is missing and user picked AUM-weighted, warn once (explains equal vs aum won’t differ)
        if weighting == "AUM-weighted" and aum_col not in df.columns:
            st.info("AUM values aren’t available for the selected ETFs, so AUM-weighted and Equal-weighted will match.")

        cA, cZ = _val(s_clean, start_year),  _val(s_clean, end_year)
        kA, kZ = _val(s_contro, start_year), _val(s_contro, end_year)

        # more legible mini-slopes (taller, thicker, arrow at end, colored by direction)
        def mini_slope(s: pd.DataFrame, pos_color: str, neg_color: str):
            if s is None or s.empty:
                return None
            s2 = s[(s["year"]>=start_year) & (s["year"]<=end_year)].copy()
            if s2.empty: return None
            v0, v1 = _val(s2, start_year), _val(s2, end_year)
            if pd.isna(v0) or pd.isna(v1): return None
            up = (v1 - v0) >= 0
            col = pos_color if up else neg_color
            base = alt.Chart(s2).encode(x=alt.X("year:O", axis=alt.Axis(labels=False, ticks=False)))
            line = base.mark_line(strokeWidth=4, opacity=0.95, color=col).encode(
                y=alt.Y("value:Q", axis=alt.Axis(labels=False, ticks=False))
            )
            end  = base.transform_filter(alt.datum.year==end_year).mark_point(size=110, color=col)
            arrow = base.transform_filter(alt.datum.year==end_year).mark_text(
                text="↗" if up else "↘", dx=6, dy=-4, fontSize=16, color=col
            )
            return (line + end + arrow).properties(height=64)

        # ---------- KPIs ----------
        k1, k2, k3 = st.columns([0.32, 0.32, 0.36])
        with k1:
            delta_c = (cZ - cA) if (pd.notna(cZ) and pd.notna(cA)) else None
            kpi_card("Clean — change since start", f"{delta_c:.1f} pp" if delta_c is not None else "–",
                     tone="green" if (delta_c or 0) >= 0 else "red")
            chart = mini_slope(s_clean, COLORS["clean"], COLORS["contro"])
            if chart: st.altair_chart(chart, use_container_width=True)
        with k2:
            delta_k = (kZ - kA) if (pd.notna(kZ) and pd.notna(kA)) else None
            kpi_card("Controversial — change since start", f"{delta_k:.1f} pp" if delta_k is not None else "–",
                     tone="red" if (delta_k or 0) > 0 else "green")
            chart = mini_slope(s_contro, COLORS["contro"], COLORS["clean"])
            if chart: st.altair_chart(chart, use_container_width=True)
        with k3:
            kpi_card("ETFs — coverage", f"Start: {covA}  |  End: {covZ}  |  Present in both: {covI}", tone="neutral")

        gap(8)

        # ---------- Combined trend ----------
        st.markdown('<div class="chart-title">Combined trend — % Clean and % Controversial</div>', unsafe_allow_html=True)
        comb = pd.concat([
            s_clean.assign(category="Clean"),
            s_contro.assign(category="Controversial")
        ], ignore_index=True) if (not s_clean.empty or not s_contro.empty) else pd.DataFrame(columns=["year","value","category"])
        st.altair_chart(
            alt.Chart(comb).mark_line(point=True).encode(
                x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("value:Q", title="Exposure (%)", axis=alt.Axis(format=".1f")),
                color=alt.Color("category:N", title=None, scale=alt.Scale(domain=["Clean","Controversial"], range=[COLORS["clean"], COLORS["contro"]])),
                tooltip=[alt.Tooltip("category:N"), alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Exposure (%)", format=".1f")]
            ).properties(height=300),
            use_container_width=True
        )

        gap(8)

        # ---------- Screen trends + Composition ----------
        st.markdown('<div class="chart-title">Screen trends and portfolio composition</div>', unsafe_allow_html=True)
        left, right = st.columns([0.62, 0.38])

        with left:
            if scr_tr is not None and not scr_tr.empty:
                d = scr_tr.copy()
                screen_col = _pick(d, "screen_category", "screen", "tag", "category")  # broadened
                val_col    = _pick(d, "share_of_total_aum_pct", "exposure", "exposure_pct", "share", "_pct", "value")
                if screen_col and val_col:
                    d = _mask_weighting_agg(d)
                    alias = {
                        "clean200":"Clean200","prison":"Prisons","prisons":"Prisons",
                        "deforestation":"Deforestation",
                        "fossil fuel":"Fossil Fuel","fossil_fuel":"Fossil Fuel","fossil":"Fossil Fuel",
                        "weapons":"Weapons","tobacco":"Tobacco"
                    }
                    d["_screen"] = d[screen_col].astype(str).str.lower().map(lambda x: alias.get(x, x.title()))
                    keep = ["Clean200","Prisons","Deforestation","Fossil Fuel","Weapons","Tobacco"]
                    d = d[d["_screen"].isin(keep)]
                    d = d[(d["year"]>=start_year) & (d["year"]<=end_year)].rename(columns={val_col:"value"})
                    st.altair_chart(
                        alt.Chart(d).mark_line(point=True).encode(
                            x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                            y=alt.Y("value:Q", title="Exposure (%)", axis=alt.Axis(format=".1f")),
                            color=alt.Color("_screen:N", title=None),
                            tooltip=[alt.Tooltip("_screen:N"), alt.Tooltip("year:O"), alt.Tooltip("value:Q", title="Exposure (%)", format=".1f")]
                        ).properties(height=300),
                        use_container_width=True
                    )
                else:
                    st.info("Screen trends unavailable.")
            else:
                st.info("Screen trends unavailable.")

        with right:
            st.markdown('<div class="chart-title" style="margin-bottom:4px;">Composition — Year A vs 2025</div>', unsafe_allow_html=True)
            def _series_for(key):
                s = _series(key)
                if s.empty:
                    fmap = {"clean200": clean_col, "controversial": ctr_col, "other": oth_col}
                    s = _series_from_funds(fmap.get(key))
                return s
            comp_rows = []
            for label, key in [("Clean","clean200"), ("Controversial","controversial"), ("Other","other")]:
                s = _series_for(key)
                if s.empty: continue
                vA, vZ = _val(s, start_year), _val(s, end_year)
                if pd.notna(vA): comp_rows.append({"Year": str(start_year), "Category": label, "Value": vA})
                if pd.notna(vZ): comp_rows.append({"Year": str(end_year),   "Category": label, "Value": vZ})
            comp_df = pd.DataFrame(comp_rows)
            if not comp_df.empty:
                comp_df["Year"] = pd.Categorical(comp_df["Year"], categories=[str(start_year), str(end_year)], ordered=True)
                st.altair_chart(
                    alt.Chart(comp_df).mark_bar(opacity=0.92, stroke="#0A0B0D", strokeWidth=0.6).encode(
                        x=alt.X("Year:N", title=None),
                        y=alt.Y("Value:Q", stack="normalize", axis=alt.Axis(format="%"), title="Portfolio share"),
                        color=alt.Color("Category:N", title=None, scale=alt.Scale(domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])),
                        tooltip=[alt.Tooltip("Year:N"), alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", title="Share (%)", format=".1f")]
                    ).properties(height=220),
                    use_container_width=True
                )
            else:
                st.info("Composition compare unavailable for the selected filters.")

        gap(8)

        # ---------- Heatmap + Top movers ----------
        st.markdown('<div class="chart-title">Controversial exposure by ETF and Top 10 Movers (Holdings)</div>', unsafe_allow_html=True)
        hleft, hright = st.columns([0.64, 0.36])

        with hleft:
            if etf_col and ctr_col and not df.empty:
                hm = df[[etf_col, "year", ctr_col]].dropna()
                hm[ctr_col] = pd.to_numeric(hm[ctr_col], errors="coerce")
                etf_order = hm.groupby(etf_col)["year"].nunique().sort_values(ascending=False).index.tolist()
                hm[etf_col] = pd.Categorical(hm[etf_col].astype(str), categories=etf_order, ordered=True)
                # softer, more diffuse gradient
                vmin = float(hm[ctr_col].min()) if hm[ctr_col].notna().any() else 0.0
                vmax = float(hm[ctr_col].max()) if hm[ctr_col].notna().any() else 1.0
                st.altair_chart(
                    alt.Chart(hm).mark_rect().encode(
                        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y(f"{etf_col}:N", title=None, sort=etf_order),
                        color=alt.Color(
                            f"{ctr_col}:Q",
                            title="Controversial (%)",
                            scale=alt.Scale(
                                domain=[vmin, (vmin+vmax)/2, vmax],
                                range=["#0e1726", "#a16bfe", "#ff7a7a"]  # deep indigo → lavender → soft red
                            )
                        ),
                        tooltip=[alt.Tooltip(f"{etf_col}:N", title="ETF"),
                                 alt.Tooltip("year:O"),
                                 alt.Tooltip(f"{ctr_col}:Q", title="Controversial (%)", format=".1f")]
                    ).properties(height=min(26*max(1,len(etf_order)), 600)),
                    use_container_width=True
                )
            else:
                st.info("Heatmap unavailable (missing ETF or controversial column).")

        with hright:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Movers (Holdings)</div>', unsafe_allow_html=True)
            if movers is not None and not movers.empty:
                mv = movers.copy()
                m = {c.lower(): c for c in mv.columns}
                sy = m.get("year_a") or m.get("start_year") or m.get("startyear")
                ey = m.get("year_b") or m.get("end_year")   or m.get("endyear")
                ecol = m.get("etf_ticker") or etf_col
                hcol = m.get("holding_name") or m.get("holding") or m.get("name")
                scrc = m.get("screen") or m.get("classification")
                contrib = m.get("delta_contrib_pct_agg") or m.get("contribution_pp") or m.get("delta_pp")
                if all([sy, ey, hcol, contrib]):
                    mvv = mv[(mv[sy]==start_year) & (mv[ey]==end_year)].copy()
                    if sel_etfs and (ecol in mvv.columns):
                        mvv = mvv[mvv[ecol].astype(str).isin(sel_etfs)]
                    cols = []
                    if ecol in mvv.columns: cols.append(("ETF", ecol))
                    cols += [("Holding", hcol)]
                    if scrc in mvv.columns: cols.append(("Screen", scrc))
                    cols += [("Contribution (pp)", contrib)]
                    tbl = mvv[[c for _, c in cols]].rename(columns={c: lbl for lbl, c in cols}).copy()
                    # Capitalize display names for readability (doesn't change source data)
                    if "Holding" in tbl.columns:
                        tbl["Holding"] = tbl["Holding"].astype(str).str.title()
                    if "Screen" in tbl.columns:
                        tbl["Screen"] = tbl["Screen"].astype(str).str.title()
                    if "Contribution (pp)" in tbl.columns:
                        tbl["Contribution (pp)"] = pd.to_numeric(tbl["Contribution (pp)"], errors="coerce")
                        tbl["_abs"] = tbl["Contribution (pp)"].abs()
                        tbl = tbl.sort_values("_abs", ascending=False).drop(columns=["_abs"]).head(10)
                    st.dataframe(tbl, use_container_width=True, hide_index=True)
                else:
                    st.info("Movers columns not found for this view.")
            else:
                st.info("Movers table unavailable.")






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
