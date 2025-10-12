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
    "clean": "#0E8F66",   # emerald
    "contro": "#C63C41",  # red
    "other": "#768397",   # blue-grey
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

      /* KPI cards */
      .kpi {{
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
      }}
      .kpi .label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
      .kpi .value {{ font-size: 30px; font-weight: 700; line-height: 1.05; }}

      /* KPI tone variants (subtle tinted gradients) */
      .kpi.kpi-red {{
        background: linear-gradient(180deg, rgba(198,60,65,0.16), rgba(255,255,255,0));
        border-color: rgba(198,60,65,0.45);
      }}
      .kpi.kpi-green {{
        background: linear-gradient(180deg, rgba(14,143,102,0.16), rgba(255,255,255,0));
        border-color: rgba(14,143,102,0.45);
      }}
      .kpi.kpi-neutral {{
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0));
        border-color: rgba(255,255,255,0.08);
      }}

      /* Tabs underline */
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-color: var(--primary) !important;
      }}

      /* Dataframe: denser rows, darker header */
      div[data-testid="stDataframe"] thead tr th {{
        background: #0C0E13 !important;
        color: var(--text) !important;
        border-bottom: 1px solid var(--border) !important;
      }}
      div[data-testid="stDataframe"] tbody tr {{ background: #0E1015 !important; }}
      div[data-testid="stDataframe"] * {{
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important;
        font-size: 13px !important;
      }}

      /* Chart titles row + tooltip badge */
      .chart-head {{
        display:flex; align-items:center; justify-content:space-between;
        margin: 4px 2px 8px 2px;
      }}
      .chart-title {{
        font-weight: 600; color: var(--text); letter-spacing:.1px;
      }}
      .info-badge {{
        display:inline-flex; align-items:center; justify-content:center;
        height: 24px; min-width: 24px; border-radius: 14px;
        border: 1px solid #2A2F36; color: #B6C0CC; font-weight: 700;
        font-size: 12px; user-select:none; cursor: default;
        background: #0B0D12; padding: 0 8px;
      }}
      /* pure CSS tooltip */
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

      /* Footer: right-aligned blue bold links */
      .footer-wrap {{
        display:flex; align-items:center; justify-content:space-between; width:100%;
      }}
      .footer-left {{ color: var(--muted); font-size: 13px; }}
      .footer-links {{ display:flex; gap:24px; align-items:center; justify-content:flex-end; width:100%; }}
      .footer-links a {{
        color: #4DA3FF !important;
        text-decoration: none;
        font-size: 15px;
        font-weight: 700;
      }}
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

# Analysis 2 loaders
@st.cache_data(show_spinner=False)
def load_exposures_by_fund_year():      return load_csv(2, "exposures_by_fund_year.csv")
@st.cache_data(show_spinner=False)
def load_agg_trends():                   return load_csv(2, "aggregate_exposure_trends.csv")
@st.cache_data(show_spinner=False)
def load_dispersion():                   return load_csv(2, "exposure_dispersion_stats.csv")
@st.cache_data(show_spinner=False)
def load_year_compare():                 return load_csv(2, "year_compare_summary.csv")
@st.cache_data(show_spinner=False)
def load_movers():                       return load_csv(2, "movers_by_yearpair.csv")
@st.cache_data(show_spinner=False)
def load_screen_trends():                return load_csv(2, "aggregate_screen_trends.csv")


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

# KPI helper (tinted variants)
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

        # 1) Composition — shaded bars (opacity + stroke)
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

        # 2) By-screen bars — shaded
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
                x=alt.X("share_of_total_aum_pct:Q", title="Share of total AUM (%)",
                        axis=alt.Axis(format=".1f")),
                y=alt.Y("screen_category:N", sort="-x", title=None),
                color=alt.Color("color:N", legend=None, scale=None),
                tooltip=[alt.Tooltip("screen_category:N", title="Category"),
                         alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")],
            ).properties(height=240)

            st.altair_chart(chart2, use_container_width=True)

        # Top 10 tables (no logos)
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

        # --- Holdings Explorer (always show all rows) ---
        gap(8)
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Holdings Explorer</div>', unsafe_allow_html=True)

        df_raw, df_disp, all_tags = load_explorer()

        fc1, fc2, fc3, fc4, fc5 = st.columns([0.22, 0.18, 0.24, 0.18, 0.18])
        with fc1:
            etfs = sorted(df_disp["ETF"].dropna().unique().tolist()) if "ETF" in df_disp.columns else []
            sel_etfs = st.multiselect("ETF", etfs, placeholder="All")
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
        if sel_etfs:   mask &= df_disp["ETF"].isin(sel_etfs)
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
        st.caption("Concise, one-screen read: where exposures went, which funds moved, and what drove it. (MV = total market value; not official AUM)")

        exp_fy  = load_exposures_by_fund_year()
        agg     = load_agg_trends()
        disp    = load_dispersion()
        ycomp   = load_year_compare()
        movers  = load_movers()
        scr_tr  = load_screen_trends()

        # --- robust column resolver ---
        def pick(df: pd.DataFrame, *cands):
            cols = list(df.columns)
            lower = {c.lower(): c for c in cols}
            for cand in cands:
                if cand in cols:
                    return cand
                if cand.lower() in lower:
                    return lower[cand.lower()]
            def norm(s): return "".join(ch for ch in s.lower() if ch.isalnum())
            norm_map = {norm(c): c for c in cols}
            for cand in cands:
                n = norm(cand)
                if n in norm_map:
                    return norm_map[n]
            for cand in cands:
                key = cand.lower()
                for c in cols:
                    if key in c.lower():
                        return c
            return None

        # Canonical column names (try lots of aliases)
        c_etf  = pick(exp_fy, "ETF_Ticker","ETF","Fund","etf","fund_ticker","fund")
        c_year = pick(exp_fy, "Year","year","report_year")
        c_pc   = pick(exp_fy, "pct_clean","clean_pct","pct_clean_pct","clean")
        c_pv   = pick(exp_fy, "pct_controversial","contro_pct","pct_contro","controversial")
        c_po   = pick(exp_fy, "pct_other","other_pct","other")
        c_mv   = pick(exp_fy, "market_total_value_usd","total_market_value_usd","aum_proxy_usd","total_mv_usd")

        missing = [("ETF",c_etf),("Year",c_year),("%Clean",c_pc),("%Contro",c_pv),("MV",c_mv)]
        missing = [k for k,v in missing if v is None]
        if missing:
            st.error(f"Missing expected columns in exposures_by_fund_year.csv: {', '.join(missing)}")
            st.caption(f"Found columns: {list(exp_fy.columns)}")
            st.stop()

        # ----- Filters (single thin row) -----
        all_years = sorted(exp_fy[c_year].dropna().unique().tolist())
        yrA, yrB = (min(all_years), max(all_years)) if all_years else (2017, 2025)

        left, mid, right = st.columns([0.44, 0.22, 0.34])
        with left:
            etf_list = sorted(exp_fy[c_etf].dropna().unique().tolist())
            sel_etf = st.multiselect("ETFs", etf_list, default=etf_list)
        with mid:
            weighting = st.segmented_control("Weighting", ["EW","MV"], default="MV", help="EW = equal-weighted across funds; MV = weighted by each fund’s total market value (sum of holdings).")
        with right:
            col1, col2 = st.columns(2)
            with col1:
                year_a = st.selectbox("Year A", all_years, index=all_years.index(yrA) if all_years else 0)
            with col2:
                year_b = st.selectbox("Year B", all_years, index=all_years.index(yrB) if all_years else 0)

        # Filter frame by ETF selection
        exp_sel = exp_fy[exp_fy[c_etf].isin(sel_etf)].copy()

        # ----- Helper: aggregate (EW or MV) by year -----
        def series_from_exp(df, col_pct):
            if weighting == "EW":
                s = df.groupby(c_year, as_index=False)[col_pct].mean()
                s.rename(columns={col_pct:"value"}, inplace=True)
                s["weighting"] = "EW"
            else:
                w = df[[c_year, col_pct, c_mv]].dropna()
                w["value"] = w[col_pct] * w[c_mv]
                s = w.groupby(c_year, as_index=False).agg(value=("value","sum"), mv=(c_mv,"sum"))
                s["value"] = s["value"] / s["mv"]
                s["weighting"] = "MV"
            return s[[c_year,"value","weighting"]]

        # Build compact aggregates (respect ETF filter)
        s_clean = series_from_exp(exp_sel, c_pc).rename(columns={"value":"clean"})
        s_contr = series_from_exp(exp_sel, c_pv).rename(columns={"value":"contro"})
        agg_now = s_clean.merge(s_contr, on=[c_year,"weighting"], how="outer").fillna(0)

        # KPI deltas (year_b - year_a)
        def pick_year_vals(df, y):
            row = df.loc[df[c_year]==y]
            return (row["clean"].values[0], row["contro"].values[0]) if not row.empty else (None, None)

        cA, vA = pick_year_vals(agg_now, year_a)
        cB, vB = pick_year_vals(agg_now, year_b)

        mv_by_year = exp_sel.groupby(c_year, as_index=False)[c_mv].sum()
        mvA = float(mv_by_year.loc[mv_by_year[c_year]==year_a, c_mv].sum()) if not mv_by_year.empty else None
        mvB = float(mv_by_year.loc[mv_by_year[c_year]==year_b, c_mv].sum()) if not mv_by_year.empty else None

        k1,k2,k3 = st.columns([0.2,0.2,0.6])
        with k1: kpi_card("Δ % Clean", f"{(cB - cA):.1f}%" if cA is not None and cB is not None else "-", tone="green" if (cB or 0) >= (cA or 0) else "red")
        with k2: kpi_card("Δ % Controversial", f"{(vB - vA):.1f}%" if vA is not None and vB is not None else "-", tone="red" if (vB or 0) > (vA or 0) else "green")
        with k3:
            if weighting=="MV" and (mvA is not None) and (mvB is not None):
                kpi_card("Δ Total Market Value", usd_fmt(mvB - mvA), tone="neutral")
            else:
                kpi_card("Δ Total Market Value", "-", tone="neutral")

        gap(6)

        # ===== Row 1: Trend snapshot (compact dual-line with optional ribbon) =====
        r1c1, r1c2 = st.columns([0.62, 0.38])

        with r1c1:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">2017–2025 Trend — % Clean vs % Controversial</div>', unsafe_allow_html=True)
            base = alt.Chart(agg_now).transform_fold(
                ["clean","contro"], as_=["series","value"]
            ).mark_line(point=False).encode(
                x=alt.X(f"{c_year}:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("value:Q", title="%", scale=alt.Scale(domain=[0,100])),
                color=alt.Color("series:N",
                                scale=alt.Scale(domain=["clean","contro"], range=[COLORS["clean"], COLORS["contro"]]),
                                legend=alt.Legend(title=None, orient="top", direction="horizontal")),
                tooltip=[alt.Tooltip(f"{c_year}:O", title="Year"),
                         alt.Tooltip("series:N", title="Metric"),
                         alt.Tooltip("value:Q", title="%", format=".1f")]
            ).properties(height=170)

            # Dispersion ribbon (compute from per-fund series to respect ETF filter)
            disp_in = exp_sel[[c_year, c_etf, c_pc, c_pv]].dropna()
            band = None
            if not disp_in.empty:
                dm = disp_in.groupby([c_year]).agg(
                    clean_p10=(c_pc, lambda x: pd.Series(x).quantile(0.10)),
                    clean_med=(c_pc, "median"),
                    clean_p90=(c_pc, lambda x: pd.Series(x).quantile(0.90)),
                ).reset_index()
                band = alt.Chart(dm).mark_area(opacity=0.15).encode(
                    x=alt.X(f"{c_year}:O", title=None),
                    y=alt.Y("clean_p10:Q", title="%"),
                    y2="clean_p90:Q",
                    color=alt.value(COLORS["clean"])
                )
            chart = (band + base) if band is not None else base
            st.altair_chart(chart, use_container_width=True)

        with r1c2:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">By Fund — % Controversial (toggle % Clean)</div>', unsafe_allow_html=True)
            metric = st.segmented_control("Metric", options=["% Controversial","% Clean"], default="% Controversial", label_visibility="collapsed")
            show_col = c_pv if metric.startswith("% Con") else c_pc

            hm = exp_sel[[c_etf, c_year, show_col]].copy()
            hm.rename(columns={show_col:"value"}, inplace=True)
            latest = hm[hm[c_year]==hm[c_year].max()].sort_values("value", ascending=False)[c_etf].tolist()
            heat = alt.Chart(hm).mark_rect().encode(
                x=alt.X(f"{c_year}:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y(f"{c_etf}:N", sort=latest, title=None),
                color=alt.Color("value:Q",
                                scale=alt.Scale(range=["(#172026)", COLORS["contro"] if metric.startswith("% Con") else COLORS["clean"]]),
                                legend=alt.Legend(title="%", orient="right")),
                tooltip=[alt.Tooltip(f"{c_etf}:N", title="ETF"),
                         alt.Tooltip(f"{c_year}:O", title="Year"),
                         alt.Tooltip("value:Q", title="%", format=".1f")]
            ).properties(height=min(320, 18*max(3,len(latest))))

            st.altair_chart(heat, use_container_width=True)

        # ===== Row 2: Year-vs-Year (stacked bars) + Top Movers =====
        r2c1, r2c2 = st.columns([0.52, 0.48])

        with r2c1:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Year-vs-Year Composition (100%)</div>', unsafe_allow_html=True)

            # Recompute composition for selected ETFs & weighting
            def comp_for_year(y):
                d = exp_sel[exp_sel[c_year]==y]
                if d.empty: return {"year":y, "Clean":0, "Controversial":0, "Other":0}
                if weighting=="EW":
                    vals = d[[c_pc,c_pv,c_po]].mean(numeric_only=True)
                else:
                    w = d[[c_pc,c_pv,c_po,c_mv]].dropna()
                    if w.empty:
                        vals = d[[c_pc,c_pv,c_po]].mean(numeric_only=True)
                    else:
                        vals = (w[[c_pc,c_pv,c_po]].multiply(w[c_mv], axis=0).sum()/w[c_mv].sum())
                return {"year":y, "Clean":float(vals[c_pc]), "Controversial":float(vals[c_pv]), "Other":float(vals[c_po])}

            comp_df = pd.DataFrame([comp_for_year(year_a), comp_for_year(year_b)])
            comp_m  = comp_df.melt(id_vars="year", var_name="class", value_name="pct")
            color_scale = alt.Scale(domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])

            bars = alt.Chart(comp_m).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                y=alt.Y("year:O", title=None),
                x=alt.X("pct:Q", stack="normalize", axis=alt.Axis(format='%', title=None)),
                color=alt.Color("class:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
                tooltip=[alt.Tooltip("year:O", title="Year"),
                         alt.Tooltip("class:N", title="Class"),
                         alt.Tooltip("pct:Q", title="%", format=".1f")]
            ).properties(height=120)
            st.altair_chart(bars, use_container_width=True)

        with r2c2:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top Movers (2017 → 2025)</div>', unsafe_allow_html=True)
            mv = movers.copy()
            etf_col = pick(mv, "etf_ticker","ETF")
            if etf_col and sel_etf:
                mv = mv[mv[etf_col].isin(sel_etf)]
            h_name = pick(mv, "holding_name","company_name","name")
            h_tic  = pick(mv, "ticker","symbol")
            h_dc   = pick(mv, "delta_contribution_pct","delta_pct","delta")
            h_scr  = pick(mv, "screen_categories","screens")

            mv_disp = mv[[x for x in [h_name, h_tic, h_dc, h_scr] if x]].copy()
            if h_dc in mv_disp.columns:
                mv_disp[h_dc] = pd.to_numeric(mv_disp[h_dc], errors="coerce")
                mv_up  = mv_disp.sort_values(h_dc, ascending=False).head(5)
                mv_dn  = mv_disp.sort_values(h_dc, ascending=True).head(5)
                tbl = pd.concat([mv_up, mv_dn], axis=0)
            else:
                tbl = mv_disp.head(10)

            rename = {}
            if h_name: rename[h_name] = "Holding"
            if h_tic:  rename[h_tic]  = "Ticker"
            if h_dc:   rename[h_dc]   = "Δ contrib (% of MV)"
            if h_scr:  rename[h_scr]  = "Screens"
            st.dataframe(tbl.rename(columns=rename), use_container_width=True, hide_index=True, height=220)

        # ===== Optional: Screen trends mini-multiples (compact) =====
        st.markdown('<div class="chart-title" style="margin:8px 0 6px;">Screen Trends (MV-weighted; categories overlap)</div>', unsafe_allow_html=True)

        if scr_tr is None or scr_tr.empty:
            st.caption("No screen trend data available.")
        else:
            sc_cat  = pick(scr_tr, "screen_category","category","screen","screen_cat")
            sc_year = pick(scr_tr, "year","report_year")
            sc_val  = pick(
                scr_tr,
                "share_of_total_mv_pct",
                "share_of_total_aum_pct",
                "share_of_total_market_value_pct",
                "share_pct",
                "value_pct",
                "pct_share",
                "pct"
            )
            if sc_val is None:
                numeric_cols = [c for c in scr_tr.columns if pd.api.types.is_numeric_dtype(scr_tr[c])]
                guess = [c for c in numeric_cols if ("pct" in c.lower() or "share" in c.lower())]
                sc_val = guess[0] if guess else None

            if sc_cat is None or sc_year is None or sc_val is None:
                st.caption(
                    f"Screen trend dataset has unexpected columns. "
                    f"Found: {list(scr_tr.columns)}. "
                    f"Expected category/year/value (%). Skipping chart."
                )
            else:
                keep = scr_tr[[sc_cat, sc_year, sc_val]].dropna()

                def normcat(x: str) -> str:
                    t = str(x).strip().lower().replace(" ", "").replace("-", "").replace("_", "")
                    mapping = {
                        "fossil": "FossilFuel",
                        "fossilfuel": "FossilFuel",
                        "fossilfuels": "FossilFuel",
                        "weapons": "Weapons",
                        "weapon": "Weapons",
                        "tobacco": "Tobacco",
                        "prisons": "Prisons",
                        "prison": "Prisons",
                        "deforestation": "Deforestation",
                    }
                    return mapping.get(t, str(x))

                keep[sc_cat] = keep[sc_cat].map(normcat)

                ordered = ["FossilFuel","Weapons","Tobacco","Prisons","Deforestation"]
                present = [c for c in ordered if c in keep[sc_cat].unique().tolist()]
                if not present:
                    st.caption("Screen trend categories not found (FossilFuel/Weapons/Tobacco/Prisons/Deforestation). Skipping chart.")
                else:
                    keep = keep[keep[sc_cat].isin(present)]

                    sm = alt.Chart(keep).mark_line().encode(
                        x=alt.X(f"{sc_year}:O", title=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y(f"{sc_val}:Q", title="%", scale=alt.Scale(zero=True)),
                        facet=alt.Facet(f"{sc_cat}:N", columns=len(present), title=None, sort=present),
                        tooltip=[
                            alt.Tooltip(f"{sc_year}:O", title="Year"),
                            alt.Tooltip(f"{sc_val}:Q", title="%", format=".1f"),
                            alt.Tooltip(f"{sc_cat}:N", title="Screen")
                        ]
                    ).properties(height=120)

                    st.altair_chart(sm, use_container_width=True)

        st.markdown(
            '<div class="blx-muted" style="margin-top:4px;">2025 classifications applied retroactively. MV = sum of holdings market values; screen categories overlap and do not sum to total controversial.</div>',
            unsafe_allow_html=True
        )

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
      .footer-wrap {
        display:flex; align-items:center; justify-content:space-between; width:100%;
      }
      .footer-left {
        color: var(--muted); font-size: 14px; white-space: nowrap;
      }
      .footer-links {
        display:flex; gap:28px; align-items:center; justify-content:flex-end;
      }
      .footer-links a {
        color: {text} !important;        /* no blue */
        text-decoration: none;
        font-size: 15.5px;                      /* slightly larger */
        font-weight: 500;                     /* not bold by default */
        opacity: .9;
      }
      .footer-links a:hover { opacity: 1; text-decoration: underline; }
    </style>

    <div class="footer-wrap">
      <div class="footer-left">Built by <strong>Nitya Arya</strong></div>
      <div class="footer-links">
        <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a>
        <a href="https://github.com/nitya-ar" target="_blank">GitHub</a>
        <a href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank"><strong>Send Feedback</strong></a>
      </div>
    </div>
    """.format(text=COLORS["text"]),
    unsafe_allow_html=True,
)
