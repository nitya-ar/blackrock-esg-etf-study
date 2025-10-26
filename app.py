import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st

# ===============
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

# -------------------------
# Analysis 3 loaders
# -------------------------
@st.cache_data(show_spinner=False)
def load_scenario_specs():
    return load_csv(3, "scenario_specs.csv")

@st.cache_data(show_spinner=False)
def load_scenario_metrics():
    # Expected columns (any reasonable header casing is fine in render):
    # scenario, ETF_Ticker, %Clean (or pct_clean_scn), %Controversial (or pct_contro_scn),
    # TE_annual (or est_te_annual_pct), #names
    return load_csv(3, "scenario_portfolio_metrics.csv")

@st.cache_data(show_spinner=False)
def load_scenario_deltas():
    # Expected: [scenario, ETF_Ticker, company_ticker, company_name, Sector, Location, w_base, w_new, delta]
    return load_csv(3, "scenario_position_deltas.csv")

@st.cache_data(show_spinner=False)
def load_returns_top():
    # Daily single-name returns for top names per ETF (used later for financial-impact charts)
    return load_csv(3, "returns_top_per_etf_2025.csv")

@st.cache_data(show_spinner=False)
def load_covariance_daily():
    return load_csv(3, "covariance_2025.csv")

@st.cache_data(show_spinner=False)
def load_etf_aum_2025():
    # Simple helper so we don’t rely on Analysis 2 if you want a direct AUM table.
    # Expected columns: ETF_Ticker, AUM_USD (names can vary; render will map flexibly)
    return load_csv(3, "etf_aum_2025.csv")





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
        This project analyzes 20 BlackRock ETFs positioned as sustainable to evaluate how their holdings align with core sustainability themes from 2017 to 2025. It applies a consistent classification framework for 2025 that distinguishes companies considered clean from those associated with five controversial categories: fossil fuels, weapons, tobacco, prisons, and deforestation. The dashboard brings this analysis to life through three views: the 2025 Overview, which outlines current exposure to clean and controversial holdings; Change since 2017, which traces how these exposures have evolved; and Tradeoff Scenarios, which model cleaner portfolio versions to illustrate the relationship between sustainability alignment and investment performance.
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
        movers_df = load_top_movers_with_names()       # Holding deltas for specific year-pairs
        
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

    # KPI 1: Net improvement (level slope: Clean−Contro @ start vs end; fixed −10..10)
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
            st.altair_chart(slope_chart(tp_net, [-20, 0], "#8A93A6"), use_container_width=True)

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

    # KPI 4: Coverage — big number, smaller caption with bolded years
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

        # Shaded middle band with a clean, customized tooltip
        band_df = pd.concat([band_clean, band_contro], ignore_index=True)
        band_tooltip = [
            alt.Tooltip(f"{year_col}:O", title="Year"),
            alt.Tooltip("qlo:Q",        title="Middle 35–65% — low",  format=".1f"),
            alt.Tooltip("qhi:Q",        title="Middle 35–65% — high", format=".1f"),
            alt.Tooltip("category:N",   title="Category"),
        ]
        band_layer = (
            alt.Chart(band_df)
            .mark_area(opacity=0.10)
            .encode(
                x=alt.X(
                    f"{year_col}:O",
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelPadding=10, labelFlush=False, labelOverlap=True),
                ),
                y=alt.Y("qlo:Q", title="Exposure (%)", scale=alt.Scale(domain=[0, 30])),
                y2="qhi:Q",
                color=alt.Color(
                    "category:N",
                    legend=None,
                    scale=alt.Scale(domain=["Clean", "Controversial"], range=[COLORS["clean"], COLORS["contro"]]),
                ),
                tooltip=band_tooltip,  # Custom tooltip; no _category_sort_index; friendlier labels
            )
        )
        layers.append(band_layer)

        # Lines with a minimal, clear tooltip (Year, Exposure, Category only)
        line_layer = (
            alt.Chart(comb)
            .mark_line(point=True, clip=True)
            .encode(
                x=alt.X(
                    f"{year_col}:O",
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelPadding=10, labelFlush=False, labelOverlap=True),
                ),
                y=alt.Y("value:Q", title="Exposure (%)", scale=alt.Scale(domain=[0, 30]), axis=alt.Axis(format=".1f")),
                color=alt.Color(
                    "category:N",
                    title=None,
                    scale=alt.Scale(domain=["Clean", "Controversial"], range=[COLORS["clean"], COLORS["contro"]]),
                ),
                tooltip=[
                    alt.Tooltip(f"{year_col}:O", title="Year"),
                    alt.Tooltip("value:Q",       title="Exposure (%)", format=".1f"),
                    alt.Tooltip("category:N",    title="Category"),
                ],
            )
        )
        layers.append(line_layer)

        st.altair_chart(
            alt.layer(*layers).properties(height=300, padding={"left": 8, "right": 8}),
            use_container_width=True,
        )

    gap(8)



    
    # ===== Screen trends & Composition — aligned headings, side-by-side =====
    h_left, h_right = st.columns([0.5, 0.5])
    with h_left:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Screen trends and portfolio composition</div>', unsafe_allow_html=True)
    with h_right:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Composition — Year A vs 2025</div>', unsafe_allow_html=True)

    left, right = st.columns([0.5, 0.5])

    with left:
        if scr_tr is not None and not scr_tr.empty:
            d = scr_tr.copy()
            if "weighting_mode" in d.columns:
                mode_name = "AUM_TRUE" if weighting == "AUM-weighted" else "EW"
                d = d[d["weighting_mode"].astype(str) == mode_name]

            d = d.rename(columns={"exposure_pct": "value"})
            if {"screen_category", "value", year_col}.issubset(d.columns):
                keep = ["Clean200", "Prisons", "Deforestation", "Fossil Fuel", "Weapons", "Tobacco"]
                d["Category"] = (
                    d["screen_category"].astype(str).str.strip().str.title()
                    .replace({"Prison":"Prisons","Fossil_fuel":"Fossil Fuel"})
                )
                d = d[d["Category"].isin(keep)]
                d = d[(d[year_col] >= start_year) & (d[year_col] <= end_year)]

                screen_domain = keep
                screen_range  = ["#2FA08A","#C97F64","#EDE7DE","#B5A793","#5C6ACF","#A99ABD"]

                chart = alt.Chart(d).mark_line(
                    strokeWidth=2, opacity=0.95,
                    point=alt.OverlayMarkDef(size=36, opacity=0.95)
                ).encode(
                    x=alt.X(f"{year_col}:O", title=None, axis=alt.Axis(labelAngle=0, labelPadding=10)),
                    y=alt.Y("value:Q", title="Exposure (%)",
                            axis=alt.Axis(format=".1f"),
                            scale=alt.Scale(domain=[0, 15])),
                    color=alt.Color("Category:N", title=None,
                                    scale=alt.Scale(domain=screen_domain, range=screen_range)),
                    tooltip=[
                        alt.Tooltip("Category:N", title="Category"),
                        alt.Tooltip(f"{year_col}:O", title="Year"),
                        alt.Tooltip("value:Q", title="Exposure (%)", format=".1f"),
                    ],
                ).properties(height=300, padding={"top": 4, "left": 4, "right": 4, "bottom": 4})
                st.altair_chart(chart, use_container_width=True)
        else:
            st.empty()

    with right:
        comp_rows = []

        def _val_series(col):
            s = _series_from_funds(col)
            if s.empty: return None, None
            vA = s.loc[s[year_col] == start_year, "value"]
            vZ = s.loc[s[year_col] == end_year,   "value"]
            return (float(vA.iloc[0]) if len(vA) else None,
                    float(vZ.iloc[0]) if len(vZ) else None)

        for label, col in [("Clean", clean_col), ("Controversial", ctr_col), ("Other", oth_col)]:
            vA, vZ = _val_series(col)
            if vA is not None: comp_rows.append({"Year": str(start_year), "Category": label, "Value": vA})
            if vZ is not None: comp_rows.append({"Year": str(end_year),   "Category": label, "Value": vZ})

        comp_df = pd.DataFrame(comp_rows)
        if not comp_df.empty:
            comp_df["Year"] = pd.Categorical(comp_df["Year"], categories=[str(start_year), str(end_year)], ordered=True)
            comp_chart = alt.Chart(comp_df).mark_bar(opacity=0.92, stroke="#0A0B0D", strokeWidth=0.6).encode(
                x=alt.X("Year:N", title=None),
                y=alt.Y("Value:Q", stack="normalize",
                        axis=alt.Axis(format="%", grid=True),
                        title="Portfolio share"),
                color=alt.Color("Category:N", title=None,
                                scale=alt.Scale(domain=["Clean","Controversial","Other"],
                                                range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])),
                tooltip=[alt.Tooltip("Year:N", title="Year"),
                         alt.Tooltip("Category:N", title="Category"),
                         alt.Tooltip("Value:Q", title="Share (%)", format=".1f")]
            ).properties(height=300, padding={"top": 4, "left": 4, "right": 4, "bottom": 4})
            st.altair_chart(comp_chart, use_container_width=True)
        else:
            st.empty()

    gap(10)

          # ---------- Top movers (no filters) ----------
    st.markdown(
        '<div class="chart-head">'
        '<div class="chart-title">Top movers — holdings (Year A → 2025)</div>'
        '<div class="info-badge has-tip" '
        'data-tip="Precomputed holding-level exposure changes from the selected start year to 2025; not affected by the AUM vs Equal-weighted toggle.">'
        'i</div>'
        '</div>',
        unsafe_allow_html=True,
    )







# ---------------------------
# TAB 3: Tradeoff Scenarios
# ---------------------------
def render_tradeoff_scenarios():
    import numpy as np
    import pandas as pd
    import streamlit as st
    import base64
    import altair as alt

    # ---------- helpers ----------
    def _need(df: pd.DataFrame, name: str) -> str:
        if name in df.columns: return name
        low = {c.lower(): c for c in df.columns}
        if name.lower() in low: return low[name.lower()]
        raise KeyError(f"Missing required column: '{name}'")

    def _fmt_pct(v):
        try: return f"{float(v):.1f}%"
        except: return "–"

    def _fmt_te_from_fraction(v):
        try: return f"{100.0 * float(v):.2f}%"
        except: return "–"

    def _fmt_int(v):
        try: return f"{int(round(float(v))):,}"
        except: return "–"

    def _is_zero_display(v) -> bool:
        try: return abs(float(v)) < 0.05
        except: return False

    # palette fallbacks (if a global COLORS dict isn't present)
    try:
        _ = COLORS  # noqa: F821
    except Exception:
        globals()["COLORS"] = {
            "clean":  "#24A27B",
            "contro": "#D35E5E",
            "other":  "#9AA3B2",
        }

    COLOR_PT = "#C77DBB"  # Pragmatic Tilt
    COLOR_SE = "#A47ADC"  # Strict Exclusion

    # ---------- load: metrics ----------
    M = load_scenario_metrics().copy()

    scen_col  = _need(M, "scenario")
    etf_col   = _need(M, "ETF_Ticker")
    clean_col = _need(M, "%Clean")
    ctr_col   = _need(M, "%Controversial")
    te_col    = _need(M, "TE_annual")
    n_col     = _need(M, "#names")

    # optional columns
    as_col    = "ActiveShare_%" if "ActiveShare_%" in M.columns else None
    aum_in_M  = "ETF_AUM_USD" if "ETF_AUM_USD" in M.columns else None

    for c in [clean_col, ctr_col, te_col, n_col] + ([as_col] if as_col else []) + ([aum_in_M] if aum_in_M else []):
        if c: M[c] = pd.to_numeric(M[c], errors="coerce")

    scen_map = {"baseline":"Baseline","pragmatic tilt":"Pragmatic Tilt","strict exclusion":"Strict Exclusion"}
    M["Scenario"] = M[scen_col].astype(str).str.strip().map(lambda s: scen_map.get(s.lower(), s))

    # ---------- header ----------
    st.subheader("Tradeoff Scenarios")
    st.write(
        "This section analyzes three portfolio versions for each fund: the current 2025 portfolio and two cleaner alternatives "
        "that increase the weight of clean holdings and reduce exposure to controversial areas such as fossil fuels, weapons, "
        "tobacco, prisons, and deforestation. The analysis highlights how progressive improvements in portfolio cleanliness affect "
        "diversification, risk, and financial performance, providing a clear view of the tradeoff between sustainability alignment "
        "and portfolio stability."
    )

    # ---------- scoped styles ----------
    st.markdown("""
    <style>
      .t3-scn-card{background:var(--card);border:1px solid var(--border);border-radius:14px;
                   padding:12px 14px;height:160px;display:flex;flex-direction:column;justify-content:space-between;}
      .t3-scn-card h4{margin:0 0 8px 0;font-size:13.5px;font-weight:600;}
      .t3-scn-card .desc{color:var(--muted);font-size:12px;line-height:1.35;}
      .t3-rowtitle{font-size:14px;font-weight:700;margin:6px 0 6px 0;}
      .kpi.t3{padding:10px 14px !important;border-radius:16px !important;min-height:78px !important;
              display:flex;flex-direction:column;justify-content:center;}
      .kpi.t3 .label{font-size:11px !important;color:var(--muted) !important;margin:0 0 6px 0;}
      .kpi.t3 .value{font-size:22px !important;font-weight:800 !important;line-height:1.0;}
      .t3-dl-inline-wrap{ text-align:center; margin-top:10px; margin-bottom:12px; }
      .t3-dl-inline-text{ color:var(--muted); font-size:13px; }
      .t3-dl-inline-link{ display:inline-block; width:12px; height:12px; margin-left:6px; color:var(--muted);
                          text-decoration:none; vertical-align:baseline; transition: transform .12s ease, color .12s ease; }
      .t3-dl-inline-link:hover{ color:var(--text); transform: translateY(-1px); }
      .t3-dl-inline-link svg{ width:12px; height:12px; display:block; }
      .chart-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}
      .chart-title{font-weight:700;}
      @media (max-width: 992px){ .t3-scn-card{height:auto;} }
    </style>
    """, unsafe_allow_html=True)

    # ---------- scenario cards ----------
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown("""
        <div class="t3-scn-card">
          <div>
            <h4>Baseline</h4>
            <div class="desc">Reflects each fund’s actual 2025 portfolio and serves as the reference point.</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="t3-scn-card">
          <div>
            <h4>Pragmatic Tilt</h4>
            <div class="desc">Moderate tilt to cleaner holdings while keeping sector balance and name caps to control risk.</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="t3-scn-card">
          <div>
            <h4>Strict Exclusion</h4>
            <div class="desc">Removes controversial exposures entirely and rebalances to stay close to baseline profile.</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

    # ---------- ETF filter & AUM map ----------
    etfs = sorted(M[etf_col].dropna().astype(str).unique().tolist())
    sel_etf = st.selectbox("ETF filter", ["All"] + etfs, index=0)

    aum_map = {}
    try:
        A = load_etf_aum_2025()
        f = "ETF_Ticker" if "ETF_Ticker" in A.columns else "etf_ticker"
        v = "ETF_AUM_USD" if "ETF_AUM_USD" in A.columns else ("AUM_USD" if "AUM_USD" in A.columns else None)
        if f and v and f in A.columns and v in A.columns:
            aum_map = A[[f, v]].dropna().groupby(f)[v].first().astype(float).to_dict()
    except Exception:
        pass
    if not aum_map and aum_in_M:
        try:
            aum_map = M[[etf_col, aum_in_M]].dropna().groupby(etf_col)[aum_in_M].first().astype(float).to_dict()
        except Exception:
            pass

    def _aum(etf):
        try: return float(aum_map.get(str(etf)))
        except: return np.nan

    X = M.copy()
    if sel_etf != "All":
        X = X[X[etf_col].astype(str) == sel_etf]
    X["__aum__"] = X[etf_col].astype(str).map(_aum)

    scen_order = ["Baseline", "Pragmatic Tilt", "Strict Exclusion"]
    rows = []
    for s in scen_order:
        d = X[X["Scenario"] == s].copy()
        if d.empty:
            rows.append({"Scenario": s, "clean": np.nan, "contro": np.nan, "te": np.nan, "n": np.nan, "as": np.nan})
            continue
        use_weights = (sel_etf == "All" and d["__aum__"].notna().any() and d["__aum__"].sum() > 0)
        w = d["__aum__"].clip(lower=0).values if use_weights else np.ones(len(d))
        rows.append({
            "Scenario": s,
            "clean":  np.average(pd.to_numeric(d[clean_col], errors="coerce"), weights=w),
            "contro": np.average(pd.to_numeric(d[ctr_col],   errors="coerce"), weights=w),
            "te":     np.average(pd.to_numeric(d[te_col],    errors="coerce"), weights=w),
            "n":      float(pd.to_numeric(d[n_col], errors="coerce").mean()),
            "as":     np.average(pd.to_numeric(d[as_col],    errors="coerce"), weights=w) if as_col else np.nan,
        })
    KP = pd.DataFrame(rows).set_index("Scenario").reindex(scen_order).reset_index()

    # ---------- KPI tiles ----------
    st.markdown("**Scenario Summary**")
    for _, r in KP.iterrows():
        st.markdown(f"<div class='t3-rowtitle'>{r['Scenario']}</div>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            tone_cls = "kpi t3" if _is_zero_display(r["clean"]) else "kpi kpi-green t3"
            st.markdown(f"<div class='{tone_cls}'><div class='label'>% Clean</div><div class='value'>{_fmt_pct(r['clean'])}</div></div>", unsafe_allow_html=True)
        with k2:
            tone_cls = "kpi t3" if _is_zero_display(r["contro"]) else "kpi kpi-red t3"
            st.markdown(f"<div class='{tone_cls}'><div class='label'>% Controversial</div><div class='value'>{_fmt_pct(r['contro'])}</div></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi kpi-neutral t3'><div class='label'>TE (ann.)</div><div class='value'>{_fmt_te_from_fraction(r['te'])}</div></div>", unsafe_allow_html=True)
        with k4:
            lbl = "# Holdings" if sel_etf != "All" else "# Holdings (avg)"
            st.markdown(f"<div class='kpi kpi-neutral t3'><div class='label'>{lbl}</div><div class='value'>{_fmt_int(r['n'])}</div></div>", unsafe_allow_html=True)
        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ---------- download (per-ETF metrics) ----------
    show = (
        M[[etf_col, "Scenario", clean_col, ctr_col, te_col, n_col] + ([as_col] if as_col else [])]
        .rename(columns={
            etf_col:"ETF", clean_col:"% Clean", ctr_col:"% Controversial",
            te_col:"TE_annual", n_col:"Holdings", **({"ActiveShare_%":"ActiveShare %"} if as_col else {})
        })
        .copy()
    )
    show["__ord__"] = show["Scenario"].map({"Baseline":0,"Pragmatic Tilt":1,"Strict Exclusion":2}).fillna(99)
    show = show.sort_values(["ETF","__ord__"]).drop(columns="__ord__")
    csv_b64 = base64.b64encode(show.to_csv(index=False).encode("utf-8")).decode("ascii")
    csv_href = f"data:text/csv;base64,{csv_b64}"

    st.markdown(
        f"""
        <div class="t3-dl-inline-wrap">
          <span class="t3-dl-inline-text">
            Download CSV of per-ETF metrics across all three scenarios: % Clean, % Controversial,
            annualized Tracking Error (fraction), # Holdings{", and Active Share (%)" if as_col else ""}.
          </span>
          <a class="t3-dl-inline-link" href="{csv_href}"
             download="per_etf_metrics_all_scenarios.csv"
             title="Download CSV" aria-label="Download CSV">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    # =========================
    # VISUALS (compact, two-per-row)
    # =========================

    # ---- Row 1: Composition | Uplift vs TE
    r1_left, r1_right = st.columns([0.56, 0.44], gap="large")

    # (1) Scenario composition
    with r1_left:
        st.markdown('<div class="chart-head"><div class="chart-title">Scenario composition</div><div></div></div>', unsafe_allow_html=True)

        comp_rows = []
        for _, r in KP.iterrows():
            clean  = float(r["clean"])  if pd.notna(r["clean"])  else float("nan")
            contro = float(r["contro"]) if pd.notna(r["contro"]) else float("nan")
            other  = 100.0 - (clean + contro) if (pd.notna(clean) and pd.notna(contro)) else float("nan")
            comp_rows += [
                {"Scenario": r["Scenario"], "Category": "Clean",         "Value": clean},
                {"Scenario": r["Scenario"], "Category": "Controversial", "Value": contro},
                {"Scenario": r["Scenario"], "Category": "Other",         "Value": other},
            ]
        comp_df = pd.DataFrame(comp_rows)

        if not comp_df.empty and comp_df["Value"].notna().any():
            comp_df["Scenario"] = pd.Categorical(comp_df["Scenario"], categories=["Baseline","Pragmatic Tilt","Strict Exclusion"], ordered=True)
            comp_df["Category"] = pd.Categorical(comp_df["Category"], categories=["Clean","Controversial","Other"], ordered=True)

            color_scale = alt.Scale(
                domain=["Clean","Controversial","Other"],
                range=[COLORS["clean"], COLORS["contro"], COLORS["other"]]
            )
            comp_chart = (
                alt.Chart(comp_df)
                .mark_bar(stroke='#0A0B0D', strokeWidth=0.6)
                .encode(
                    x=alt.X("Scenario:N", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Value:Q", stack="normalize", axis=alt.Axis(format="%", title="Portfolio share")),
                    color=alt.Color("Category:N", title=None, scale=color_scale),
                    tooltip=[alt.Tooltip("Scenario:N"), alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", title="Share (%)", format=".1f")],
                )
                .properties(height=280, padding={"left": 6, "right": 6, "top": 4, "bottom": 4})
            )
            st.altair_chart(comp_chart, use_container_width=True)
        else:
            st.info("Composition not available for the current selection.")

    # (2) Cleanliness Uplift vs Tracking Error
    with r1_right:
        st.markdown('<div class="chart-head"><div class="chart-title">Cleanliness Uplift vs Tracking Error</div><div></div></div>', unsafe_allow_html=True)

        A = X.copy()
        base = (A[A["Scenario"]=="Baseline"][[etf_col, clean_col, te_col, "__aum__"]]
                .rename(columns={clean_col:"clean_base", te_col:"te_base"}))
        alts = (A[A["Scenario"].isin(["Pragmatic Tilt","Strict Exclusion"])]
                [[etf_col, "Scenario", clean_col, te_col, "__aum__"]]
                .rename(columns={clean_col:"clean_alt", te_col:"te_alt", "__aum__":"__aum__alt"}))

        if not base.empty and not alts.empty:
            J = pd.merge(alts, base, on=etf_col, how="left")
            aum_cols = [c for c in J.columns if c.startswith("__aum__")]
            J["AUM"] = J[aum_cols].apply(pd.to_numeric, errors="coerce").max(axis=1).fillna(0.0)
            J["delta_clean_pp"] = pd.to_numeric(J["clean_alt"], errors="coerce") - pd.to_numeric(J["clean_base"], errors="coerce")
            J["TE %"] = pd.to_numeric(J["te_alt"], errors="coerce") * 100.0

            if sel_etf == "All" and J["AUM"].sum() > 0:
                def _aw(df, val):
                    w = pd.to_numeric(df["AUM"], errors="coerce").clip(lower=0)
                    x = pd.to_numeric(df[val], errors="coerce")
                    return np.average(x, weights=w) if w.sum() > 0 else np.nan
                pts = (J.groupby("Scenario")
                         .apply(lambda d: pd.Series({"delta_clean_pp": _aw(d,"delta_clean_pp"),
                                                     "TE %": _aw(d,"TE %"),
                                                     "AUM": d["AUM"].sum()}))
                         .reset_index())
            else:
                pts = J.groupby("Scenario", as_index=False)[["delta_clean_pp","TE %","AUM"]].first()

            if not pts.empty and pts[["delta_clean_pp","TE %"]].notna().any(axis=None):
                pts["Scenario"] = pd.Categorical(pts["Scenario"], categories=["Pragmatic Tilt","Strict Exclusion"], ordered=True)
                color_scale = alt.Scale(domain=["Pragmatic Tilt","Strict Exclusion"], range=[COLOR_PT, COLOR_SE])
                bubble = (
                    alt.Chart(pts)
                    .mark_point(filled=True, opacity=0.9)
                    .encode(
                        x=alt.X("delta_clean_pp:Q", title="Δ % Clean vs Baseline (pp)", axis=alt.Axis(format=".1f")),
                        y=alt.Y("TE %:Q", title="Tracking Error (ann. %)", axis=alt.Axis(format=".2f")),
                        color=alt.Color("Scenario:N", scale=color_scale, title=None, legend=alt.Legend(orient="right")),
                        size=alt.Size("AUM:Q", title="ETF AUM ($)", scale=alt.Scale(range=[14, 80])),
                        tooltip=[alt.Tooltip("Scenario:N"),
                                 alt.Tooltip("delta_clean_pp:Q", title="Δ % Clean (pp)", format=".2f"),
                                 alt.Tooltip("TE %:Q", title="TE (ann. %)", format=".2f"),
                                 alt.Tooltip("AUM:Q", title="AUM ($)", format=",.0f")],
                    )
                    .properties(height=280, padding={"left": 6, "right": 6, "top": 4, "bottom": 4})
                )
                st.altair_chart(bubble, use_container_width=True)
            else:
                st.info("Not enough data to compute uplift vs tracking error.")
        else:
            st.info("Not enough rows to compare scenarios against the baseline for the selected ETF(s).")

    # ---- Row 2: Turnover & Cost | Active Share vs % Clean
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    r2_left, r2_right = st.columns([0.56, 0.44], gap="large")

    # (3) Turnover & Cost
    with r2_left:
        st.markdown('<div class="chart-head"><div class="chart-title">Turnover & Cost</div><div></div></div>', unsafe_allow_html=True)
        rtc = st.slider("Assumed round-trip cost (bps)", min_value=5, max_value=50, value=20, step=1, key="t3_rtc")

        deltas = None
        for fn in ("load_scenario_position_deltas", "load_scenario_deltas"):
            try:
                deltas = globals()[fn]().copy()
                break
            except Exception:
                continue
        if deltas is None:
            try:
                deltas = load_data_file("scenario_position_deltas.csv").copy()  # type: ignore
            except Exception:
                deltas = None

        if deltas is not None:
            try:
                s_col = _need(deltas, "scenario")
                e_col = _need(deltas, "ETF_Ticker")
                d_col = _need(deltas, "delta")
            except KeyError:
                st.info("Turnover cannot be computed: required columns 'scenario', 'ETF_Ticker', and 'delta' not found.")
                deltas = None

        if deltas is not None:
            use = deltas.copy()
            use["Scenario"] = use[s_col].astype(str).str.strip().map(lambda s: scen_map.get(s.lower(), s))
            use = use[use["Scenario"].isin(["Pragmatic Tilt","Strict Exclusion"])]
            if sel_etf != "All":
                use = use[use[e_col].astype(str) == sel_etf]

            if not use.empty:
                agg = (use.assign(abs_delta = pd.to_numeric(use[d_col], errors="coerce").abs())
                          .groupby("Scenario", as_index=False)["abs_delta"].sum())
                agg["Turnover %"] = 0.5 * agg["abs_delta"] * 100.0
                agg["Cost (bps)"]   = agg["Turnover %"] * rtc

                long = agg.melt(id_vars="Scenario", value_vars=["Turnover %","Cost (bps)"],
                                var_name="Metric", value_name="Value")

                color_scale = alt.Scale(domain=["Pragmatic Tilt","Strict Exclusion"], range=[COLOR_PT, COLOR_SE])
                bars = (
                    alt.Chart(long)
                    .mark_bar(stroke='#0A0B0D', strokeWidth=0.6)
                    .encode(
                        x=alt.X("Metric:N", title=None, axis=alt.Axis(labelAngle=0)),
                        xOffset=alt.X("Scenario:N", title=None),
                        y=alt.Y("Value:Q", title=None, axis=alt.Axis(format=".1f")),
                        color=alt.Color("Scenario:N", scale=color_scale, title=None, legend=alt.Legend(orient="right")),
                        tooltip=[alt.Tooltip("Scenario:N"), alt.Tooltip("Metric:N"), alt.Tooltip("Value:Q", format=".2f")],
                    )
                    .properties(height=240, padding={"left": 6, "right": 6, "top": 4, "bottom": 4})
                )
                st.altair_chart(bars, use_container_width=True)
            else:
                st.info("No position deltas available for the current selection.")
        else:
            st.info("Turnover data not available (no position-deltas file detected).")

    # (4) Active Share vs % Clean
    with r2_right:
        st.markdown('<div class="chart-head"><div class="chart-title">Active Share vs % Clean</div><div></div></div>', unsafe_allow_html=True)

        if as_col:
            A2 = X[X["Scenario"].isin(["Pragmatic Tilt","Strict Exclusion"])].copy()
            if not A2.empty:
                if sel_etf == "All" and A2["__aum__"].notna().any() and A2["__aum__"].sum() > 0:
                    def _aw2(df, col):
                        w = pd.to_numeric(df["__aum__"], errors="coerce").clip(lower=0)
                        x = pd.to_numeric(df[col], errors="coerce")
                        return np.average(x, weights=w) if w.sum() > 0 else np.nan
                    S = (A2.groupby("Scenario")
                           .apply(lambda d: pd.Series({"ActiveShare_%": _aw2(d, as_col),
                                                       "%Clean": _aw2(d, clean_col),
                                                       "AUM": d["__aum__"].sum()}))
                           .reset_index())
                else:
                    S = (A2.groupby("Scenario", as_index=False)
                           .agg({"__aum__":"first", as_col:"first", clean_col:"first"})
                           .rename(columns={"__aum__":"AUM", as_col:"ActiveShare_%", clean_col:"%Clean"}))

                if not S.empty and S[["ActiveShare_%","%Clean"]].notna().any(axis=None):
                    S["Scenario"] = pd.Categorical(S["Scenario"], categories=["Pragmatic Tilt","Strict Exclusion"], ordered=True)
                    color_scale = alt.Scale(domain=["Pragmatic Tilt","Strict Exclusion"], range=[COLOR_PT, COLOR_SE])
                    scatter = (
                        alt.Chart(S)
                        .mark_point(filled=True, opacity=0.9)
                        .encode(
                            x=alt.X("ActiveShare_%:Q", title="Active Share (%)", axis=alt.Axis(format=".1f")),
                            y=alt.Y("%Clean:Q", title="% Clean (scenario)", axis=alt.Axis(format=".1f")),
                            color=alt.Color("Scenario:N", scale=color_scale, title=None, legend=alt.Legend(orient="right")),
                            size=alt.Size("AUM:Q", title="ETF AUM ($)", scale=alt.Scale(range=[14, 80])),
                            tooltip=[alt.Tooltip("Scenario:N"),
                                     alt.Tooltip("ActiveShare_%:Q", title="Active Share (%)", format=".2f"),
                                     alt.Tooltip("%Clean:Q", title="% Clean", format=".2f"),
                                     alt.Tooltip("AUM:Q", title="AUM ($)", format=",.0f")],
                        )
                        .properties(height=280, padding={"left": 6, "right": 6, "top": 4, "bottom": 4})
                    )
                    st.altair_chart(scatter, use_container_width=True)
                else:
                    st.info("Active Share data not available for the current selection.")
            else:
                st.info("No rows for alternative scenarios to plot Active Share.")
        else:
            st.info("Column 'ActiveShare_%' not found in scenario_portfolio_metrics; cannot draw this chart.")

    # ---- Row 3: Sector Drift Heatmap | Top Added / Removed
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    r3_left, r3_right = st.columns([0.56, 0.44], gap="large")

    # (5) Sector Drift Heatmap (vs Baseline)
    with r3_left:
        st.markdown('<div class="chart-head"><div class="chart-title">Sector drift vs Baseline</div><div></div></div>', unsafe_allow_html=True)

        sector_cols = [c for c in M.columns if c.startswith("sector_dev__")]
        if sector_cols:
            mm = X[X["Scenario"].isin(["Pragmatic Tilt", "Strict Exclusion"])].copy()

            def _pretty_sector(s: str) -> str:
                return (s.replace("sector_dev__", "")
                         .replace("_and/or_", " & ")
                         .replace("_", " ")
                         .title())

            if sel_etf == "All" and mm["__aum__"].notna().any() and mm["__aum__"].sum() > 0:
                w = pd.to_numeric(mm["__aum__"], errors="coerce").clip(lower=0).fillna(0.0)
                num = (mm[sector_cols].apply(pd.to_numeric, errors="coerce").mul(w, axis=0)
                       .groupby(mm["Scenario"]).sum())
                den = mm.groupby("Scenario")["__aum__"].apply(lambda s: pd.to_numeric(s, errors="coerce").clip(lower=0).sum())
                avg = (num.div(den, axis=0)).reset_index()
                heat_df = avg.melt(id_vars="Scenario", value_vars=sector_cols,
                                   var_name="Sector", value_name="Drift_pp")
            else:
                take = (mm.groupby("Scenario", as_index=False)[sector_cols].first())
                heat_df = take.melt(id_vars="Scenario", value_vars=sector_cols,
                                    var_name="Sector", value_name="Drift_pp")

            heat_df["Sector"] = heat_df["Sector"].map(_pretty_sector)
            heat_df["Drift_pp"] = pd.to_numeric(heat_df["Drift_pp"], errors="coerce")

            if heat_df["Drift_pp"].notna().any():
                # symmetric domain for clearer colors
                domain_max = float(np.nanmax(np.abs(heat_df["Drift_pp"].values)))
                domain_max = 0.1 if not np.isfinite(domain_max) or domain_max == 0 else domain_max

                heat = (
                    alt.Chart(heat_df)
                    .mark_rect()
                    .encode(
                        x=alt.X("Sector:N", title=None, axis=alt.Axis(labelAngle=-25)),
                        y=alt.Y("Scenario:N", title=None, sort=["Pragmatic Tilt","Strict Exclusion"]),
                        color=alt.Color(
                            "Drift_pp:Q",
                            title="Drift (pp)",
                            scale=alt.Scale(domain=[-domain_max, 0, domain_max], range=["#d9776f", "#1f2937", "#60a5fa"]),
                            legend=alt.Legend(orient="right"),
                        ),
                        tooltip=[alt.Tooltip("Scenario:N"),
                                 alt.Tooltip("Sector:N"),
                                 alt.Tooltip("Drift_pp:Q", title="Drift (pp)", format=".2f")],
                    )
                    .properties(height=220, padding={"left": 6, "right": 6, "top": 4, "bottom": 4})
                )
                st.altair_chart(heat, use_container_width=True)
            else:
                st.info("No sector drift values available for the current selection.")
        else:
            st.info("Sector drift columns not found in metrics (expected prefix 'sector_dev__').")

    # (6) Top Added / Top Removed (tables)
    with r3_right:
        st.markdown('<div class="chart-head"><div class="chart-title">Top Added / Top Removed</div><div></div></div>', unsafe_allow_html=True)

        sel_scn_changes = st.radio("Scenario", options=["Pragmatic Tilt", "Strict Exclusion"], horizontal=True, key="t3_changes_scn")

        # load deltas (same logic as turnover)
        deltas2 = None
        for fn in ("load_scenario_position_deltas", "load_scenario_deltas"):
            try:
                deltas2 = globals()[fn]().copy()
                break
            except Exception:
                continue
        if deltas2 is None:
            try:
                deltas2 = load_data_file("scenario_position_deltas.csv").copy()  # type: ignore
            except Exception:
                deltas2 = None

        if deltas2 is None:
            st.info("Position deltas file not found; cannot compute changes.")
        else:
            try:
                s_col  = _need(deltas2, "scenario")
                e_col  = _need(deltas2, "ETF_Ticker")
                nm_col = _need(deltas2, "company_name")
                tk_col = _need(deltas2, "company_ticker")
                sec_col= _need(deltas2, "Sector")
                d_col  = _need(deltas2, "delta")
            except KeyError as err:
                st.info(f"Missing column in deltas: {err}")
                deltas2 = None

        if deltas2 is not None:
            use = deltas2.copy()
            use["Scenario"] = use[s_col].astype(str).str.strip().map(lambda s: scen_map.get(s.lower(), s))
            use = use[use["Scenario"] == sel_scn_changes]
            if sel_etf != "All":
                use = use[use[e_col].astype(str) == sel_etf]

            if use.empty:
                st.info("No position changes for the current selection.")
            else:
                # optional AUM weighting if “All”
                if sel_etf == "All":
                    try:
                        AUM = load_etf_aum_2025()
                        f = "ETF_Ticker" if "ETF_Ticker" in AUM.columns else "etf_ticker"
                        v = "ETF_AUM_USD" if "ETF_AUM_USD" in AUM.columns else ("AUM_USD" if "AUM_USD" in AUM.columns else None)
                        AUM = AUM[[f, v]].rename(columns={f: "ETF_Ticker", v: "ETF_AUM_USD"})
                        use = use.merge(AUM, on="ETF_Ticker", how="left")
                        w = pd.to_numeric(use["ETF_AUM_USD"], errors="coerce").fillna(1.0).clip(lower=0)
                    except Exception:
                        w = pd.Series(1.0, index=use.index)
                else:
                    w = pd.Series(1.0, index=use.index)

                use["delta_num"] = pd.to_numeric(use[d_col], errors="coerce").fillna(0.0) * w
                grp = use.groupby([tk_col, nm_col, sec_col], as_index=False)["delta_num"].sum()
                grp["Δ weight (pp)"] = grp["delta_num"] * 100.0
                grp = grp.rename(columns={tk_col:"Ticker", nm_col:"Company", sec_col:"Sector"})

                top_added   = grp.sort_values("Δ weight (pp)", ascending=False).head(12)
                top_removed = grp.sort_values("Δ weight (pp)", ascending=True).head(12)

                def _fmt_table(df):
                    out = df[["Company","Ticker","Sector","Δ weight (pp)"]].copy()
                    out["Δ weight (pp)"] = out["Δ weight (pp)"].map(lambda x: f"{x:.2f}")
                    return out.reset_index(drop=True)

                ca, cr = st.columns(2)
                with ca:
                    st.caption("Top Added (Δ weight, pp)")
                    st.dataframe(_fmt_table(top_added), use_container_width=True, hide_index=True, height=360)
                with cr:
                    st.caption("Top Removed (Δ weight, pp)")
                    st.dataframe(_fmt_table(top_removed), use_container_width=True, hide_index=True, height=360)








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
