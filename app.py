import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st

# ===============
# CONFIG
# ===============
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

# ---- Altair dark theme to soften axes/grid/labels/legend ----
def _alt_dark():
    return {
        "config": {
            "background": "transparent",
            "view": {"fill": "transparent", "stroke": COLORS["border"]},
            "axis": {
                "labelColor": COLORS["text"],
                "titleColor": COLORS["muted"],
                "domainColor": "#2A2F36",
                "tickColor":   "#2A2F36",
                "grid": True,
                "gridColor": "#222831",
                "gridOpacity": 0.45
            },
            "legend": {"labelColor": COLORS["text"], "titleColor": COLORS["muted"]},
            "title": {"color": COLORS["text"]},
        }
    }

alt.themes.register("custom_dark", _alt_dark)
alt.themes.enable("custom_dark")


# =========================
# STYLES (final — cross-browser dark, fixed tooltips/contrast/controls)
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
        --muted: {COLORS.get('muted','#A9B4C2')};     /* brighter for readability */
        --primary: {COLORS['primary']};
        --clean: {COLORS.get('clean','#0E8F66')};
        --contro:{COLORS.get('contro','#C63C41')};
        --other: {COLORS.get('other','#4062FF')};
        --accent:#C63C41;                              /* red for active & slider */
      }}

      /* ---------- Base ---------- */
      html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }}
      h1, h2, h3, h4, h5 {{ color: var(--text); letter-spacing: .1px; }}
      .blx-divider {{ border-top: 1px solid var(--border); margin: 10px 0 24px 0; }}
      .blx-muted {{ color: var(--muted); }}

      /* ---------- Cards ---------- */
      .blx-card {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px; padding: 14px 16px;
      }}
      .kpi {{
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
        border: 1px solid var(--border); border-radius: 16px; padding: 18px 20px;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
      }}
      .kpi .label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
      .kpi .value {{ font-size: 30px; font-weight: 700; line-height: 1.05; }}
      .kpi.kpi-red {{ background: linear-gradient(180deg, rgba(198,60,65,0.16), rgba(255,255,255,0)); border-color: rgba(198,60,65,0.45); }}
      .kpi.kpi-green {{ background: linear-gradient(180deg, rgba(14,143,102,0.16), rgba(255,255,255,0)); border-color: rgba(14,143,102,0.45); }}
      .kpi.kpi-neutral {{ background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0)); border-color: rgba(255,255,255,0.08); }}

      /* ---------- Charts / tooltips ---------- */
      .stAltairChart, .stVegaLiteChart, .stPlotlyChart {{ background: var(--card) !important; border: 1px solid var(--border) !important; }}
      .vega-embed, .stAltairChart {{ background: transparent !important; }}
      .vega-tooltip, .vega-tooltip * {{ background:#0F1116 !important; color:var(--text) !important; border-color:var(--border) !important; }}

    /* ---------- Info badges (red OUTLINE, right-aligned, with tooltip) ---------- */
.info-badge {{
  display:inline-flex; align-items:center; justify-content:center;
  width:22px; height:22px; min-width:22px; border-radius:50%;
  background: transparent !important;               /* no fill */
  color: var(--texted) !important;                  /* red “i” */
  border: 2px solid var(--texted) !important;       /* red outline */
  font-weight:700; font-size:12px;
  margin-left:8px; vertical-align:text-bottom;
}}
.chart-head {{ display:flex; align-items:center; }}
.chart-head .chart-title {{ flex:1 1 auto; }}
.chart-head .info-badge {{ margin-left:auto; }}        /* push to right end */

/* optional: subtle hover focus ring */
.info-badge:hover, .info-badge:focus {{
  box-shadow: 0 0 0 3px rgba(198,60,65,0.22);
  outline: none;
}}

/* Tooltip stays the same */
.has-tip {{ position:relative; }}
.has-tip::after {{
  content: attr(data-tip);
  position:absolute; right:0; top:calc(100% + 8px);
  background:#0B0D12; color:var(--text); border:1px solid var(--border);
  padding:6px 10px; border-radius:8px; white-space:nowrap;
  opacity:0; transform:translateY(6px); pointer-events:none;
  transition:opacity .15s ease, transform .15s ease;
  box-shadow:0 10px 24px rgba(0,0,0,.45); z-index:99999;
}}
.has-tip:hover::after, .has-tip:focus::after {{ opacity:1; transform:translateY(0); }}


      /* ---------- DataFrames & Tables (no white headers/rows) ---------- */
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) {{
        background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="grid"] {{ background: var(--card) !important; }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"],
      div[data-testid="stDataframe"] thead tr th {{
        background:#11151C !important; color:var(--text) !important; border-bottom:1px solid #2A2F36 !important;
      }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="row"] [role="gridcell"],
      div[data-testid="stDataframe"] tbody tr td {{
        background:#0E1015 !important; color:var(--text) !important; border-top:1px solid #12151C !important;
      }}
      div[data-testid="stDataframe"] tbody tr:first-child td {{ background:#10131A !important; }}

      :where([data-testid="stTable"]) table {{ background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }}
      :where([data-testid="stTable"]) thead th {{ background:#11151C !important; color:var(--text) !important; border-bottom:1px solid #2A2F36 !important; }}
      :where([data-testid="stTable"]) tbody td {{ background:#0E1015 !important; color:var(--text) !important; border-top:1px solid #12151C !important; }}

      /* ---------- Inputs (Select/Text) — dark + consistent placeholders ---------- */
      [data-baseweb="select"], [data-baseweb="input"] {{
        border: 1px solid var(--border) !important; border-radius: 10px !important; background:#0F1116 !important;
      }}
      [data-baseweb="select"] > div, [data-baseweb="input"] > div {{
        background: var(--card) !important; border-radius:10px !important; box-shadow:none !important; border:none !important;
      }}
      [data-baseweb="select"] > div *, [data-baseweb="input"] > div * {{ background:transparent !important; color:var(--text) !important; }}
      [data-baseweb="select"] > div:focus-within, [data-baseweb="input"] > div:focus-within {{
        outline:none !important; border:1px solid var(--accent) !important;
        box-shadow:0 0 0 3px rgba(198,60,65,0.28) !important;
      }}
      /* placeholders: match “Any” muted tone */
      [data-baseweb="input"] input::placeholder {{ color: var(--muted) !important; opacity:1 !important; }}
      [data-baseweb="menu"] {{
        background:#10131A !important; color:var(--text) !important; border:1px solid var(--border) !important; border-radius:12px !important;
      }}
      [data-baseweb="menu"] li {{ color:var(--text) !important; }}
      [data-baseweb="menu"] li:hover {{ background:#161A22 !important; }}

      /* ---------- Slider (thumb not blue) ---------- */
      [data-baseweb="slider"] > div {{ background:transparent !important; }}
      [data-baseweb="slider"] div[role="presentation"] {{ background:#1C2027 !important; }}
      [data-baseweb="slider"] div[role="presentation"] > div {{ background:var(--accent) !important; }}
      [data-baseweb="slider"] [role="slider"] {{
        background:var(--accent) !important;
        box-shadow:0 0 0 3px rgba(198,60,65,0.18) !important; border:0 !important;
      }}
      [data-baseweb="slider"] * {{ color:var(--text) !important; }}

      /* ---------- Segmented controls (Dashboard/Report & AUM/EW) ---------- */
      div[data-testid="stSegmentedControl"] div[role="tablist"] {{
        background:#0E1015 !important; border:1px solid var(--border) !important; border-radius:12px !important;
      }}
      /* force dark on button and nested wrappers (Safari/Private) */
      div[data-testid="stSegmentedControl"] button[role="tab"],
      div[data-testid="stSegmentedControl"] button[role="tab"] > *,
      div[data-testid="stSegmentedControl"] button[role="tab"] > * > * {{
        background:#0E1015 !important; color:var(--muted) !important; border:none !important; box-shadow:none !important;
      }}
      div[data-testid="stSegmentedControl"] button[aria-selected="true"],
      div[data-testid="stSegmentedControl"] button[aria-selected="true"] > *,
      div[data-testid="stSegmentedControl"] button[aria-selected="true"] > * > * {{
        background:#12151C !important; color:var(--text) !important;
        border:none !important; box-shadow: inset 0 0 0 1px var(--accent) !important;
      }}
      div[data-testid="stSegmentedControl"] button[disabled],
      div[data-testid="stSegmentedControl"] button[aria-disabled="true"],
      div[data-testid="stSegmentedControl"] button[disabled] > *,
      div[data-testid="stSegmentedControl"] button[aria-disabled="true"] > * {{
        background:#151923 !important; color:#7E8A98 !important; border:none !important; box-shadow:none !important; opacity:1 !important;
      }}

      /* ---------- Tabs ---------- */
      .stTabs [data-baseweb="tab-list"] {{ background:#0E1015 !important; border-bottom:1px solid var(--border) !important; }}
      .stTabs [data-baseweb="tab"] {{ background:transparent !important; color:var(--muted) !important; border-color:transparent !important; box-shadow:none !important; }}
      .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color:var(--text) !important; border-color:transparent !important; box-shadow: inset 0 -2px 0 var(--accent) !important; }}

      /* ---------- Buttons ---------- */
      .stDownloadButton > button, .stButton > button {{
        background:#12151C !important; color:var(--text) !important; border:1px solid var(--border) !important; border-radius:12px !important;
      }}
      .stDownloadButton > button:hover, .stButton > button:hover {{ background:#151923 !important; border-color:#2A2F36 !important; }}

      /* ---------- Labels (ETF / Weighting / Start Year) & scrollbars ---------- */
      label, .st-emotion-cache-1cypcdb, .st-emotion-cache-1qg05tj {{
        color: var(--muted) !important; font-size:13px !important; letter-spacing:.2px;
      }}
      *::-webkit-scrollbar {{ width: 10px; height: 10px; }}
      *::-webkit-scrollbar-thumb {{ background:#2A2F36; border-radius: 8px; }}
      *::-webkit-scrollbar-track {{ background:#0B0D12; }}
    </style>
    """,
    unsafe_allow_html=True,
)

def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

def gap(px=6):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

# Dark styler for tables inside iframe
def style_dark_df(df: pd.DataFrame):
    bg, hdr, txt, bdr = "#0E1015", "#0C0E13", "#E7EBF0", "#1C2027"
    return (
        df.style
          .set_table_styles([
              {"selector": "table",             "props": [("background-color", bg),  ("color", txt), ("border-collapse", "collapse"), ("border", f"1px solid {bdr}")]},
              {"selector": "thead th",          "props": [("background-color", hdr), ("color", txt), ("border-bottom", f"1px solid {bdr}"), ("padding", "6px 8px")]},
              {"selector": "tbody td",          "props": [("background-color", bg),  ("color", txt), ("border-top",     f"1px solid {bdr}"), ("padding", "6px 8px")]},
              {"selector": "tbody tr:hover td", "props": [("background-color", "#12151C")]},
          ])
          .set_properties(**{"background-color": bg, "color": txt, "border-color": bdr})
    )

def grid(df: pd.DataFrame):
    st.dataframe(style_dark_df(df), use_container_width=True, hide_index=True)


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

# Analysis 2 loaders (Change since 2017)
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
def load_top_movers_with_names():    return load_csv(2, "top_movers_with_names.csv")

# -------- Analysis 3 loaders (Tradeoff Scenarios) --------
@st.cache_data(show_spinner=False)
def load_scenario_specs():
    # expected cols (from your generator): scenario, type, te_budget_annual, sector_neutrality_pct,
    # region_neutrality_pct, single_name_cap_pct, single_name_cap_mult, hard_screens
    return load_csv(3, "scenario_specs.csv")

@st.cache_data(show_spinner=False)
def load_scenario_metrics():
    # available (per your banner): 
    # [scenario_id, scope, ETF_Ticker, pct_clean_base, pct_contro_base, pct_other_base,
    #  pct_clean_scn, pct_contro_scn, pct_other_scn, active_share_pct, est_te_annual_pct,
    #  factor_drift_sector_pct, factor_drift_region_pct, liquidity_status, notes,
    #  rule_te_budget_annual_pct, rule_sector_band, rule_region_band, rule_cap_abs_pct,
    #  rule_cap_x_baseline, rule_clean_tilt_target_pp, rule_excl_fossil, rule_excl_tobacco,
    #  rule_excl_weapons, rule_excl_prisons, rule_excl_deforestation]
    return load_csv(3, "scenario_portfolio_metrics.csv")

@st.cache_data(show_spinner=False)
def load_scenario_deltas():
    # preferred cols (from your generator): 
    # [scenario, ETF_Ticker, company_ticker, company_name, Sector, Location, w_base, w_new, delta]
    # but we defensively handle if w_new is missing.
    return load_csv(3, "scenario_position_deltas.csv")

@st.cache_data(show_spinner=False)
def load_returns_top():
    return load_csv(3, "returns_top_per_etf_2025.csv")

@st.cache_data(show_spinner=False)
def load_covariance_daily():
    return load_csv(3, "covariance_2025.csv")



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

# -------------------------
# RENDERER FOR TAB 2
# -------------------------
def render_change_since_2017():
    st.subheader("Change since 2017")
    st.caption("All years are evaluated using the 2025 classification.")

    # ---- Load data
    try:
        by_fund   = load_exposures_by_fund_year()   # ETF-level exposures per year
        scr_tr    = load_screen_trends()            # Aggregate screen trends (may be empty)
        movers_df = load_top_movers_with_names()    # Holding deltas for specific year-pairs
    except Exception as e:
        st.error(f"Could not load Analysis 2 CSVs: {e}")
        st.stop()

    # ---- Helpers & canonical columns
    def _pick(df, *keys):
        keys = [k.lower() for k in keys]
        for c in df.columns:
            if any(k in c.lower() for k in keys):
                return c
        return None

    year_col  = "year"
    etf_col   = _pick(by_fund, "etf_ticker", "etf ticker", "etf")
    clean_col = _pick(by_fund, "pct_clean", "clean")
    ctr_col   = _pick(by_fund, "pct_controversial", "controversial", "contro")
    oth_col   = _pick(by_fund, "pct_other", "other")
    aum_col   = _pick(by_fund, "market_total_value_usd", "aum", "net_assets")

    if year_col in by_fund.columns:
        by_fund[year_col] = pd.to_numeric(by_fund[year_col], errors="coerce").astype("Int64")

    years    = sorted([int(y) for y in by_fund[year_col].dropna().unique().tolist()]) if year_col in by_fund.columns else list(range(2017, 2026))
    end_year = 2025 if 2025 in years else (max(years) if years else 2025)
    min_year = min(years) if years else 2017

    df_all = by_fund.copy()

    # ---- Controls row
    topA, topB, topC = st.columns([0.44, 0.28, 0.28])
    with topB:
        start_year = st.slider("Start Year", min_value=min_year, max_value=max(end_year-1, min_year), value=min_year)

    # Intersection cohort (ETFs present in both years)
    setA = set(df_all.loc[df_all[year_col] == start_year, etf_col].astype(str)) if etf_col in df_all.columns else set()
    setZ = set(df_all.loc[df_all[year_col] == end_year,   etf_col].astype(str)) if etf_col in df_all.columns else set()
    overlap = sorted(list(setA & setZ))

    with topA:
        sel_etfs = st.multiselect("ETF", overlap, default=[])

    with topC:
        st.markdown(
            '<div class="chart-head"><div class="chart-title">Weighting</div>'
            '<div class="info-badge has-tip" data-tip="AUM-weighted averages ETFs by assets; Equal-weighted gives each ETF the same weight.">i</div></div>',
            unsafe_allow_html=True,
        )
        weighting = st.segmented_control(
            "Weighting", ["AUM-weighted", "Equal-weighted"],
            default="AUM-weighted", label_visibility="collapsed"
        )

    # ---- Active cohort df (intersection + optional user subset)
    cohort = overlap if not sel_etfs else sel_etfs
    df = df_all[df_all[etf_col].astype(str).isin(cohort)].copy() if etf_col in df_all.columns else df_all.copy()
    df = df[(df[year_col] >= start_year) & (df[year_col] <= end_year)]
    covI = len(cohort)

    # ---- Weighted series (respects ETF selection + weighting)
    def _series_from_funds(col_name: str) -> pd.DataFrame:
        if not col_name or col_name not in df.columns or df.empty:
            return pd.DataFrame(columns=[year_col, "value"])
        d = df[[year_col, col_name] + ([aum_col] if aum_col in df.columns else [])].copy()
        d[col_name] = pd.to_numeric(d[col_name], errors="coerce")
        if weighting == "AUM-weighted" and aum_col in d.columns and d[aum_col].notna().any():
            d[aum_col] = pd.to_numeric(d[aum_col], errors="coerce").clip(lower=0)
            out = d.groupby(year_col).apply(
                lambda g: (g[col_name] * g[aum_col]).sum() / g[aum_col].sum() if g[aum_col].sum() > 0 else float("nan")
            ).reset_index(name="value")
        else:
            out = d.groupby(year_col)[col_name].mean().reset_index().rename(columns={col_name: "value"})
        return out.sort_values(year_col)

    s_clean  = _series_from_funds(clean_col)
    s_contro = _series_from_funds(ctr_col)

    if weighting == "AUM-weighted" and (aum_col not in df.columns or not df[aum_col].notna().any()):
        st.info("AUM values are unavailable for the current selection; Equal-weighted and AUM-weighted will be identical.")

    def _val(s: pd.DataFrame, yr: int):
        v = pd.to_numeric(s.loc[s[year_col] == yr, "value"], errors="coerce")
        return float(v.iloc[0]) if len(v) else float("nan")

    cA, cZ = _val(s_clean, start_year),  _val(s_clean, end_year)
    kA, kZ = _val(s_contro, start_year), _val(s_contro, end_year)

    # ---- Net series (level = %Clean − %Controversial)
    s_net = None
    if not s_clean.empty and not s_contro.empty:
        s_net = pd.merge(s_clean, s_contro, on=year_col, how="inner", suffixes=("_clean", "_contro"))
        s_net["value"] = s_net["value_clean"] - s_net["value_contro"]
        s_net = s_net[[year_col, "value"]].sort_values(year_col)

    net_start = _val(s_net, start_year) if s_net is not None else float("nan")
    net_end   = _val(s_net, end_year)   if s_net is not None else float("nan")
    net_delta = (net_end - net_start) if (pd.notna(net_end) and pd.notna(net_start)) else None

    # ---------- KPI slope helpers ----------
    def _two_points_from_series(s: pd.DataFrame):
        if s is None or s.empty: return None
        t = s[s[year_col].isin([start_year, end_year])][[year_col, "value"]].copy()
        return t if len(t) == 2 else None

    def slope_chart(two_point_df: pd.DataFrame, y_domain, color):
        two = two_point_df.copy()
        two["Year"] = two[year_col].astype(str)
        base = alt.Chart(two).encode(
            x=alt.X("Year:N", title="year", sort=[str(start_year), str(end_year)]),
            y=alt.Y("value:Q", title="value", axis=alt.Axis(format=".1f"),
                    scale=alt.Scale(domain=y_domain))
        )
        return (base.mark_line(color=color, strokeWidth=3) + base.mark_point(color=color, size=110)).properties(height=160)

    # ---------- KPI cards ----------
    k1, k2, k3, k4 = st.columns([0.25, 0.25, 0.25, 0.25])

    # KPI 1: Net improvement (Clean−Contro @ start vs end)
    with k1:
        st.markdown(
            f"""
            <div class="kpi kpi-neutral" style="background:linear-gradient(180deg, rgba(231,235,240,0.06), rgba(255,255,255,0));">
              <div class="label">Net improvement (Clean − Controversial)</div>
              <div class="value">{(net_delta if net_delta is not None else 0):+,.1f} pp</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tp_net = _two_points_from_series(s_net)
        if tp_net is not None:
            st.altair_chart(slope_chart(tp_net, [-20, 10], "#8A93A6"), use_container_width=True)

    # KPI 2: Clean
    with k2:
        d_clean = (cZ - cA) if (pd.notna(cZ) and pd.notna(cA)) else None
        kpi_card("Clean — change since start", f"{d_clean:.1f} pp" if d_clean is not None else "–",
                 tone="green" if (d_clean or 0) >= 0 else "red")
        tp = _two_points_from_series(s_clean)
        if tp is not None:
            st.altair_chart(slope_chart(tp, [0, 30], COLORS["clean"]), use_container_width=True)

    # KPI 3: Controversial
    with k3:
        d_ctr = (kZ - kA) if (pd.notna(kZ) and pd.notna(kA)) else None
        kpi_card("Controversial — change since start", f"{d_ctr:.1f} pp" if d_ctr is not None else "–",
                 tone="red" if (d_ctr or 0) > 0 else "green")
        tp = _two_points_from_series(s_contro)
        if tp is not None:
            st.altair_chart(slope_chart(tp, [0, 30], COLORS["contro"]), use_container_width=True)

    # KPI 4: Coverage
    with k4:
        st.markdown(
            f"""
            <div class="kpi kpi-neutral" style="display:flex;align-items:center;gap:14px;">
              <div style="font-size:44px; font-weight:800; line-height:1;">{covI}</div>
              <div><div class="label" style="margin:0;">ETFs appear in both <b>{start_year}</b> and <b>{end_year}</b></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    gap(8)

    # ---------- Combined trend with fixed middle dispersion band (35–65%) ----------
    st.markdown(
        '<div class="chart-head">'
        '<div class="chart-title">Combined trend — % Clean and % Controversial</div>'
        '<div class="info-badge has-tip" '
        'data-tip="The shaded band shows how much ETF exposures vary each year — it covers the typical middle range (35th to 65th percentile) for Clean and Controversial exposures. The lines show the average exposure across ETFs based on your selected weighting.">'
        'i</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Helper to compute a percentile band for a given column
    def _band_quantiles(df_in: pd.DataFrame, col: str, q_low: float = 0.35, q_high: float = 0.65) -> pd.DataFrame:
        if col not in df_in.columns or df_in.empty:
            return pd.DataFrame(columns=[year_col, "qlo", "qhi", "category"])
        dd = df_in[[year_col, col]].copy()
        dd[col] = pd.to_numeric(dd[col], errors="coerce")
        q = dd.groupby(year_col)[col].quantile([q_low, q_high]).unstack().reset_index()
        q.columns = [year_col, "qlo", "qhi"]
        q["category"] = "Clean" if col == clean_col else "Controversial"
        return q

    # Build the 35–65% band for Clean and Controversial
    band_clean  = _band_quantiles(df, clean_col, 0.35, 0.65)
    band_contro = _band_quantiles(df, ctr_col,   0.35, 0.65)

    # Mean lines dataframe
    comb = (
        pd.concat(
            [s_clean.assign(category="Clean"), s_contro.assign(category="Controversial")],
            ignore_index=True,
        )
        if (not s_clean.empty or not s_contro.empty)
        else pd.DataFrame(columns=[year_col, "value", "category"])
    )

    if not comb.empty:
        layers = []

        # Shaded middle band
        band_df = pd.concat([band_clean, band_contro], ignore_index=True)
        band_layer = (
            alt.Chart(band_df)
            .mark_area(opacity=0.10)
            .encode(
                x=alt.X(f"{year_col}:O", title=None, axis=alt.Axis(labelAngle=0, labelPadding=10, labelFlush=False, labelOverlap=True)),
                y=alt.Y("qlo:Q", title="Exposure (%)", scale=alt.Scale(domain=[0, 30])),
                y2="qhi:Q",
                color=alt.Color("category:N", legend=None, scale=alt.Scale(domain=["Clean", "Controversial"], range=[COLORS["clean"], COLORS["contro"]])),
                tooltip=[
                    alt.Tooltip(f"{year_col}:O", title="Year"),
                    alt.Tooltip("qlo:Q", title="Middle 35–65% — low",  format=".1f"),
                    alt.Tooltip("qhi:Q", title="Middle 35–65% — high", format=".1f"),
                    alt.Tooltip("category:N", title="Category"),
                ],
            )
        )
        layers.append(band_layer)

        # Mean lines
        line_layer = (
            alt.Chart(comb)
            .mark_line(point=True, clip=True)
            .encode(
                x=alt.X(f"{year_col}:O", title=None, axis=alt.Axis(labelAngle=0, labelPadding=10, labelFlush=False, labelOverlap=True)),
                y=alt.Y("value:Q", title="Exposure (%)", scale=alt.Scale(domain=[0, 30]), axis=alt.Axis(format=".1f")),
                color=alt.Color("category:N", title=None, scale=alt.Scale(domain=["Clean", "Controversial"], range=[COLORS["clean"], COLORS["contro"]])),
                tooltip=[
                    alt.Tooltip(f"{year_col}:O", title="Year"),
                    alt.Tooltip("value:Q",       title="Exposure (%)", format=".1f"),
                    alt.Tooltip("category:N",    title="Category"),
                ],
            )
        )
        layers.append(line_layer)

        st.altair_chart(alt.layer(*layers).properties(height=300, padding={"left": 8, "right": 8}), use_container_width=True)

    gap(8)

    # ---------- Top movers (no filters) ----------
    st.markdown(
        '<div class="chart-head">'
        '<div class="chart-title">Top movers — holdings (Year A → 2025)</div>'
        '<div class="info-badge has-tip" data-tip="Precomputed holding-level exposure changes from the selected start year to 2025; not affected by the AUM vs Equal-weighted toggle.">i</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Try to use the richer file with 2025 names; fallback to movers_df if not available
    try:
        topm_df = load_csv(2, "top_movers_with_names.csv")
    except Exception:
        topm_df = movers_df.copy() if (movers_df is not None and not movers_df.empty) else pd.DataFrame()

    movers_view = pd.DataFrame()
    if topm_df is not None and not topm_df.empty:
        # Auto-detect columns (be resilient to naming)
        name25_col = _pick(topm_df, "name_2025", "holding_2025", "security_name_2025")
        base_name  = _pick(topm_df, "holding", "name", "security_name")
        cat_col    = _pick(topm_df, "category", "class")
        y0_col     = _pick(topm_df, "start_year", "year_a", "year0")
        y1_col     = _pick(topm_df, "end_year", "year_b", "year1")
        d_col      = _pick(topm_df, "delta", "delta_pp", "pp", "change")

        m = topm_df.copy()
        if y0_col and y1_col:
            m = m[(m[y0_col] == start_year) & (m[y1_col] == end_year)]
        else:
            m = m.head(0)

        if d_col in (m.columns if m is not None else []) and not m.empty:
            m["_abs"] = pd.to_numeric(m[d_col], errors="coerce").abs()
            m = m.sort_values("_abs", ascending=False).head(10)

            if name25_col and name25_col in m.columns:
                holding_name = m[name25_col]
            elif base_name and base_name in m.columns:
                holding_name = m[base_name]
            else:
                holding_name = pd.Series(["—"] * len(m), index=m.index)

            movers_view = pd.DataFrame({
                "Holding (2025)": holding_name,
                "Category": m[cat_col] if cat_col in m.columns else "—",
                "Δ exposure (pp)": pd.to_numeric(m[d_col], errors="coerce").map(lambda v: f"{v:+.4f}")
            })

    if movers_view.empty:
        st.info("No movers found for the selected start year.")
    else:
        grid(movers_view)



# =========================
# TAB 3 — TRADEOFF SCENARIOS (full, robust)
# =========================

# ---------- Fuzzy helpers ----------
import re
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower()) if s is not None else ""

def _pick_col(cols, *candidates):
    low = { _norm(c): c for c in cols }
    for cand in candidates:
        if _norm(cand) in low: 
            return low[_norm(cand)]
    # fallback: contains
    for c in cols:
        cc = _norm(c)
        for cand in candidates:
            if _norm(cand) and _norm(cand) in cc:
                return c
    return None

# ---------- Loaders (robust to header variants) ----------
@st.cache_data(show_spinner=False)
def _load_specs():
    try:
        df = load_csv(3, "scenario_specs.csv").copy()
    except Exception as e:
        st.warning(f"scenario_specs.csv not found or unreadable: {e}")
        return pd.DataFrame()
    # normalize expected columns
    map_try = {
        "scenario": ["scenario","name","scenario_name","label"],
        "type": ["type","kind","scenario_type"],
        "te_budget_annual": ["te_budget_annual","tebudget","te_budget","te_limit"],
        "single_name_cap_pct": ["single_name_cap_pct","cap","singlecap","single_name_cap"],
        "single_name_cap_mult": ["single_name_cap_mult","cap_mult","multiplier"],
        "sector_neutrality_pct": ["sector_neutrality_pct","sector_neutrality"],
        "region_neutrality_pct": ["region_neutrality_pct","region_neutrality"],
        "hard_screens": ["hard_screens","screens","exclusions"]
    }
    ren = {}
    for target, cands in map_try.items():
        col = _pick_col(df.columns, *cands)
        if col and col != target: ren[col] = target
    if ren: df = df.rename(columns=ren)
    # sanify
    if "scenario" in df.columns:
        df["scenario"] = df["scenario"].astype(str)
    if "hard_screens" in df.columns:
        df["hard_screens"] = df["hard_screens"].fillna("").astype(str)
    return df

@st.cache_data(show_spinner=False)
def _load_deltas():
    try:
        d = load_csv(3, "scenario_position_deltas.csv").copy()
    except Exception as e:
        st.warning(f"scenario_position_deltas.csv not found or unreadable: {e}")
        return pd.DataFrame()

    # normalize
    ren = {}
    etf_col = _pick_col(d.columns, "ETF_Ticker","ETF Ticker","etf","fund")
    if etf_col and etf_col != "ETF_Ticker": ren[etf_col] = "ETF_Ticker"
    sc_col = _pick_col(d.columns, "scenario","Scenario","scenario_name")
    if sc_col and sc_col != "scenario": ren[sc_col] = "scenario"
    tic_col = _pick_col(d.columns, "company_ticker","ticker","symbol")
    if tic_col and tic_col != "company_ticker": ren[tic_col] = "company_ticker"
    name_col = _pick_col(d.columns, "company_name","name","holding","security_name")
    if name_col and name_col != "company_name": ren[name_col] = "company_name"
    w_base = _pick_col(d.columns, "w_base","weight_base","base_weight","wbase")
    if w_base and w_base != "w_base": ren[w_base] = "w_base"
    w_new  = _pick_col(d.columns, "w_new","new_weight","weight_new","wnew")
    if w_new and w_new != "w_new": ren[w_new] = "w_new"
    delta  = _pick_col(d.columns, "delta","dw","change")
    if delta and delta != "delta": ren[delta] = "delta"
    sec    = _pick_col(d.columns, "Sector","sector")
    if sec and sec != "Sector": ren[sec] = "Sector"

    if ren: d = d.rename(columns=ren)

    # reconstruct w_new if missing
    if "w_new" not in d.columns and {"w_base","delta"}.issubset(d.columns):
        d["w_new"] = pd.to_numeric(d["w_base"], errors="coerce") + pd.to_numeric(d["delta"], errors="coerce")

    # types
    for c in ["w_base","w_new","delta"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "scenario" in d.columns:
        d["scenario"] = d["scenario"].astype(str)
    if "ETF_Ticker" in d.columns:
        d["ETF_Ticker"] = d["ETF_Ticker"].astype(str)
    return d

@st.cache_data(show_spinner=False)
def _load_returns_top():
    try:
        r = load_csv(3, "returns_top_per_etf_2025.csv").copy()
    except Exception as e:
        st.warning(f"returns_top_per_etf_2025.csv not found or unreadable: {e}")
        return pd.DataFrame()

    # normalize
    ren = {}
    date = _pick_col(r.columns, "date","Date")
    if date and date != "date": ren[date] = "date"
    tic  = _pick_col(r.columns, "ticker","company_ticker","symbol")
    if tic and tic != "ticker": ren[tic] = "ticker"
    ret  = _pick_col(r.columns, "ret","return","daily_return")
    if ret and ret != "ret": ren[ret] = "ret"
    etfs = _pick_col(r.columns, "etfs","funds")
    if etfs and etfs != "etfs": ren[etfs] = "etfs"
    ysym = _pick_col(r.columns, "yahoo_symbol","ticker_yahoo")
    if ysym and ysym != "yahoo_symbol": ren[ysym] = "yahoo_symbol"
    if ren: r = r.rename(columns=ren)

    # types
    if "date" in r.columns:
        r["date"] = pd.to_datetime(r["date"], errors="coerce")
    if "ret" in r.columns:
        r["ret"] = pd.to_numeric(r["ret"], errors="coerce")
    for c in ["ticker","etfs","yahoo_symbol"]:
        if c in r.columns: r[c] = r[c].astype(str)
    return r

@st.cache_data(show_spinner=False)
def _load_metrics():
    df = load_csv(3, "scenario_portfolio_metrics.csv").copy()

    # fuzzy rename to canonical set
    want = {
        "scenario":        ["scenario","scenarioname","name"],
        "ETF_Ticker":      ["etfticker","fundticker","etf","fund","etf_ticker","ETF Ticker"],
        "TE_annual":       ["teannual","trackingerrorannual","te","trackingerror","te_ann","teann","tracking_error"],
        "%Clean":          ["pctclean","cleanpct","cleanpercent","clean","clean_%","% clean"],
        "%Controversial":  ["pctcontroversial","pctcontro","controversialpct","controversial","contro_%","% controversial"],
        "%Other":          ["pctother","otherpct","otherpercentage","other","other_%","% other"],
        "#names":          ["names","nnames","countnames","numsecurities","nsecurities","holdingscount",
                            "nholdings","#names","num_names","n_names"]
    }
    cur = { _norm(c): c for c in df.columns }
    ren = {}
    missing = []
    for target, cands in want.items():
        found = None
        for cand in cands:
            if _norm(cand) in cur:
                found = cur[_norm(cand)]
                break
        if found and found != target: ren[found] = target
        if not found: missing.append(target)
    if ren: df = df.rename(columns=ren)

    # If #names missing, try to reconstruct from deltas
    if "#names" in missing:
        try:
            d = _load_deltas()
            if not d.empty and {"ETF_Ticker","scenario","w_new"}.issubset(d.columns):
                tmp = d.copy()
                tmp["w_new"] = pd.to_numeric(tmp["w_new"], errors="coerce").fillna(0.0)
                nn = (tmp["w_new"] > 0).groupby([tmp["ETF_Ticker"], tmp["scenario"]]).sum().reset_index(name="#names")
                if {"ETF_Ticker","scenario"}.issubset(df.columns):
                    df = df.merge(nn, on=["ETF_Ticker","scenario"], how="left")
                    missing = [m for m in missing if m != "#names"]
        except Exception:
            pass

    # final presence check with helpful message
    required = {"scenario","ETF_Ticker","TE_annual","%Clean","%Controversial","%Other","#names"}
    still = [c for c in required if c not in df.columns]
    if still:
        have = ", ".join(df.columns)
        raise ValueError(f"scenario_portfolio_metrics.csv is missing: {still}. Available columns: [{have}]")

    # types
    for c in ["TE_annual","%Clean","%Controversial","%Other"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "#names" in df.columns:
        df["#names"] = pd.to_numeric(df["#names"], errors="coerce").fillna(0).astype(int)
    for c in ["scenario","ETF_Ticker"]:
        if c in df.columns: df[c] = df[c].astype(str)
    return df

# ---------- Financial impact helper (build daily portfolio series) ----------
def _portfolio_series_for_etf(etf: str, deltas: pd.DataFrame, returns_df: pd.DataFrame):
    """
    Returns a DataFrame with columns: date, scenario, ret
    Using constant weights (w_base / w_new) applied to daily single-name returns for tickers
    that have data in returns_top_per_etf_2025.csv.
    """
    if deltas.empty or returns_df.empty:
        return pd.DataFrame(columns=["date","scenario","ret"])
    d = deltas[deltas["ETF_Ticker"] == etf].copy()
    if d.empty: 
        return pd.DataFrame(columns=["date","scenario","ret"])

    # Decide which tickers belong to ETF in returns table
    r = returns_df.copy()
    if "etfs" in r.columns:
        r["_has"] = r["etfs"].astype(str).apply(lambda s: etf in [x.strip() for x in str(s).split(";") if x])
        r = r[r["_has"]].drop(columns=["_has"])
    # minimal required
    if not {"date","ticker","ret"}.issubset(r.columns):
        return pd.DataFrame(columns=["date","scenario","ret"])

    out_frames = []
    scenarios = sorted(d["scenario"].unique().tolist())
    for scn in scenarios:
        g = d[d["scenario"] == scn][["company_ticker","w_base","w_new"]].copy()
        g = g.rename(columns={"company_ticker":"ticker"})
        # choose which weight to use for portfolio
        if _norm(scn) in ("baseline","base","original"):
            g["w_use"] = pd.to_numeric(g["w_base"], errors="coerce")
        else:
            g["w_use"] = pd.to_numeric(g["w_new"], errors="coerce")
        g = g[["ticker","w_use"]].dropna()
        g = g[g["w_use"] > 0]
        if g.empty: 
            continue

        # keep only tickers we actually have returns for
        avail = set(r["ticker"].unique().tolist())
        g = g[g["ticker"].isin(avail)]
        if g.empty: 
            continue

        # renormalize weights over the covered subuniverse
        total = float(g["w_use"].sum())
        if total <= 0:
            continue
        g["w_use"] = g["w_use"] / total

        # merge with returns and aggregate per day
        rr = r.merge(g, on="ticker", how="inner")
        rr["wret"] = rr["ret"] * rr["w_use"]
        ser = rr.groupby("date", as_index=False)["wret"].sum().rename(columns={"wret":"ret"})
        ser["scenario"] = scn
        out_frames.append(ser)

    if not out_frames:
        return pd.DataFrame(columns=["date","scenario","ret"])
    return pd.concat(out_frames, ignore_index=True).sort_values(["scenario","date"])



# =============== TAB 3: TRADEOFF SCENARIOS (SIMPLIFIED FIRST PASS) ===============
def render_tradeoff_scenarios():
    import re
    import numpy as np
    import pandas as pd
    import streamlit as st
    import altair as alt

    # ---------- tiny utils ----------
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", str(s).lower()) if s is not None else ""

    def _pick(df: pd.DataFrame, *cands):
        # exact then case-insensitive
        for c in cands:
            if c in df.columns: return c
        low = {c.lower(): c for c in df.columns}
        for c in cands:
            if c.lower() in low: return low[c.lower()]
        # contains fall-back
        for c in df.columns:
            if any(cc.lower() in c.lower() for cc in cands):
                return c
        return None

    def _fmt_pct_auto(x):
        try:
            val = float(x)
            # If values look like fractions (<= 1.5), show as %
            if -1.5 <= val <= 1.5:
                return f"{val*100:.1f}%"
            return f"{val:.1f}%"
        except:
            return "–"

    def _kpi_card(label, value, tone="neutral"):
        tone_class = {"green": "kpi-green", "red": "kpi-red"}.get(tone, "kpi-neutral")
        st.markdown(
            f"""
            <div class="kpi {tone_class}">
              <div class="label">{label}</div>
              <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- load ----------
    specs   = load_scenario_specs()
    metrics = load_scenario_metrics()

    # ---------- scenario id / labels ----------
    # Canonical ids: baseline, tilt, exclude
    scen_col  = _pick(metrics, "scenario_id", "scenario")
    etf_col   = _pick(metrics, "ETF_Ticker", "etf", "fund_ticker")
    clean_col = _pick(metrics, "pct_clean_scn", "pct_clean", "%Clean")
    ctr_col   = _pick(metrics, "pct_contro_scn", "pct_controversial", "%Controversial")
    oth_col   = _pick(metrics, "pct_other_scn", "pct_other", "%Other")
    te_col    = _pick(metrics, "est_te_annual_pct", "te_annual", "tracking_error", "TE_annual")
    n_col     = _pick(metrics, "#names", "n_holdings", "holdings", "num_names")

    if scen_col is None or etf_col is None or clean_col is None or ctr_col is None or te_col is None:
        st.error("scenario_portfolio_metrics.csv is missing required columns.")
        return

    # normalize scenario id text
    scen_map_in = {
        "baseline": "baseline",
        "pragmatictilt": "tilt",
        "tilt": "tilt",
        "strictexclusion": "exclude",
        "exclude": "exclude",
    }
    metrics = metrics.copy()
    metrics["scenario_id"] = (
        metrics[scen_col].astype(str).apply(_norm).map(scen_map_in).fillna(metrics[scen_col].astype(str))
    )

    # pretty labels
    scen_label = {"baseline": "Baseline", "tilt": "Pragmatic Tilt", "exclude": "Strict Exclusion"}
    metrics["scenario_label"] = metrics["scenario_id"].map(lambda s: scen_label.get(s, str(s).title()))

    # ---------- 1) Scenario overview (simple copy — no data dependency) ----------
    st.subheader("Tradeoff Scenarios")

    # very short, plain-English explainer boxes
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Baseline**")
        st.caption("2025 current portfolio — unchanged holdings and weights.")
        st.markdown("- Single-name cap: 5.0%")
    with c2:
        st.markdown("**Pragmatic Tilt**")
        st.caption("Light tilt away from controversial exposure under a TE budget.")
        st.markdown("- Target: ~2 pp cleaner (typical), within TE cap")
    with c3:
        st.markdown("**Strict Exclusion**")
        st.caption("Exclude controversial names, reweight within sectors, keep single-name cap.")
        st.markdown("- Hard screens on controversial categories")

    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

    # ---------- 2) Filters ----------
    etf_list = sorted(metrics[etf_col].dropna().astype(str).unique().tolist())
    f1, f2 = st.columns([0.62, 0.38])
    with f1:
        sel_etf = st.selectbox("ETF filter", ["All"] + etf_list, index=0)
    with f2:
        view_mode = st.segmented_control("View", options=["All ETFs (mean)", "Per ETF"], default="All ETFs (mean)")

    M = metrics.copy()
    if sel_etf != "All":
        M = M[M[etf_col].astype(str) == sel_etf]

    # ---------- 3) KPI cards (% Clean, % Controversial, TE ann., # Holdings)
    # We color **by change vs Baseline**:
    # - % Clean: delta > 0 => green, < 0 => red
    # - % Controversial: delta > 0 => red, < 0 => green
    # - Tracking Error: delta > 0 (higher TE) => red, < 0 => green
    # - # Holdings: neutral (display only)
    # Aggregate by scenario (mean across selected ETFs)
    agg = (
        M.groupby(["scenario_id", "scenario_label"], dropna=False)
         .agg(
             clean=(clean_col, "mean"),
             contro=(ctr_col, "mean"),
             te=(te_col, "mean"),
             n=(n_col, "mean") if n_col in M.columns else (clean_col, "size")
         )
         .reset_index()
    )

    # align baseline row and compute deltas
    base_row = agg[agg["scenario_id"] == "baseline"].copy()
    if base_row.empty:
        # if no baseline present after filtering, use overall baseline as reference
        base_row = (
            metrics.groupby("scenario_id").agg(clean=(clean_col, "mean"),
                                               contro=(ctr_col, "mean"),
                                               te=(te_col, "mean")).reset_index()
        )
        base_row = base_row[base_row["scenario_id"] == "baseline"]

    b_clean = float(base_row["clean"].iloc[0]) if len(base_row) else np.nan
    b_contro = float(base_row["contro"].iloc[0]) if len(base_row) else np.nan
    b_te = float(base_row["te"].iloc[0]) if len(base_row) else np.nan

    # scenario order
    order = ["baseline", "tilt", "exclude"]
    agg["__o__"] = agg["scenario_id"].map({s: i for i, s in enumerate(order)})
    agg = agg.sort_values(["__o__", "scenario_label"])

    st.markdown("**Key metrics**")
    # One row: show each scenario block with four KPI boxes
    cols = st.columns(3)
    for i, (_, row) in enumerate(agg.iterrows()):
        with cols[i % 3]:
            st.markdown(f"**{row['scenario_label']}**")
            k1, k2 = st.columns(2)
            # % Clean — color by (clean - baseline)
            d_clean = row["clean"] - b_clean if pd.notna(b_clean) else 0.0
            tone_clean = "green" if d_clean > 1e-12 else ("red" if d_clean < -1e-12 else "neutral")
            with k1:
                _kpi_card("% Clean", _fmt_pct_auto(row["clean"]), tone_clean)

            # % Controversial — color by inverse sign
            d_ctr = row["contro"] - b_contro if pd.notna(b_contro) else 0.0
            tone_ctr = "red" if d_ctr > 1e-12 else ("green" if d_ctr < -1e-12 else "neutral")
            with k2:
                _kpi_card("% Controversial", _fmt_pct_auto(row["contro"]), tone_ctr)

            k3, k4 = st.columns(2)
            # TE — lower is better
            d_te = row["te"] - b_te if pd.notna(b_te) else 0.0
            tone_te = "red" if d_te > 1e-12 else ("green" if d_te < -1e-12 else "neutral")
            with k3:
                _kpi_card("TE (ann.)", _fmt_pct_auto(row["te"]), tone_te)

            with k4:
                val_n = f"{int(round(row['n'])):,}" if pd.notna(row["n"]) else "–"
                _kpi_card("# Holdings", val_n, "neutral")

    # Nothing else for now — visuals come next iteration.






# =========================
# BODY
# =========================
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Scenarios"])

    # ---------- 2025 OVERVIEW ----------
    with tab1:
        st.subheader("2025 Overview")

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
                comp["Group"] = "All"   # <-- fix: single stacked bar anchor

                color_scale = alt.Scale(domain=["Clean","Controversial","Other"],
                                        range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])

                chart = alt.Chart(comp).mark_bar(opacity=0.92, stroke='#0A0B0D', strokeWidth=0.6).encode(
                    x=alt.X("sum(share):Q", stack="normalize",
                            axis=alt.Axis(format='%', title=None, ticks=False, labels=False)),
                    y=alt.Y("Group:N", title=None, axis=None),
                    color=alt.Color("classification:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
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
            spot = load_spotlight()
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
                grid(cont_disp)
        with s2:
            st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Clean Holdings</div>', unsafe_allow_html=True)
            spot = load_spotlight()
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
                grid(clean_disp)

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

        df_view = df_f.copy()
        for c in ("Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)"):
            if c in df_view.columns:
                df_view[c] = pd.to_numeric(df_view[c], errors="coerce")
        grid(df_view)

        csv_bytes = df_f.to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered rows (CSV)", data=csv_bytes, file_name="holdings_explorer_filtered.csv", mime="text/csv")

    # ---------- CHANGE SINCE 2017 ----------
    with tab2:
        render_change_since_2017()
        # ---------- TRADEOFF SCENARIOS ----------
    with tab3:
        render_tradeoff_scenarios()


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
