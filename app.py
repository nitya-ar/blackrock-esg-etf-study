import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st

# =================
# CONFIG
# =================
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

# Analysis 3 loaders (Tradeoff Scenarios)
@st.cache_data(show_spinner=False)
def load_scenario_metrics():         return load_csv(3, "scenario_portfolio_metrics.csv")

@st.cache_data(show_spinner=False)
def load_scenario_deltas():          return load_csv(3, "scenario_position_deltas.csv")

@st.cache_data(show_spinner=False)
def load_returns_vector():           return load_csv(3, "returns_top_per_etf_2025.csv")

@st.cache_data(show_spinner=False)
def load_covariance_matrix():        return load_csv(3, "covariance_2025.csv")

@st.cache_data(show_spinner=False)
def load_scenario_progress():        return load_csv(3, "scenario_progress.csv")

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

# -------------------------
# RENDERER FOR TAB 3
# -------------------------
def render_tradeoff_scenarios():
    st.subheader("Tradeoff Scenarios")
    st.caption("Three simulated portfolios side-by-side. Baseline highlighted; Pragmatic Tilt (TE budget ~2%); Strict Exclusion (hard screens).")

    with st.spinner("Computing scenario metrics, expected return, volatility, and tracking error…"):
        try:
            met   = load_scenario_metrics()     # scenario-level KPIs & composition
            deltas= load_scenario_deltas()      # position changes & classifications
            rets  = load_returns_vector()       # (optional) exp return inputs
            cov   = load_covariance_matrix()    # (optional) if needed later
        except Exception as e:
            st.error(f"Could not load Analysis 3 CSVs: {e}")
            st.stop()

    # ---- Helpers ----
    def _pick(df, *keys):
        keys = [k.lower() for k in keys]
        for c in df.columns:
            lc = c.lower()
            if any(k in lc for k in keys):
                return c
        return None

    # Canonical columns for scenario metrics
    scen_col  = _pick(met, "scenario", "name")
    clean_col = _pick(met, "pct_clean", "clean")
    ctr_col   = _pick(met, "pct_controversial", "contro")
    oth_col   = _pick(met, "pct_other", "other")
    te_col    = _pick(met, "tracking_error", "te")
    er_col    = _pick(met, "expected_return", "exp_return")
    vol_col   = _pick(met, "volatility", "risk", "sigma")
    shr_col   = _pick(met, "sharpe")
    to_col    = _pick(met, "turnover")
    aw_col    = _pick(met, "active_weight")

    # Scenario order & colors
    # We’ll map fuzzy names to canonical order; unseen names will appear at the end.
    order_map = {
        "baseline": "Baseline",
        "pragmatic": "Pragmatic Tilt",
        "pragmatic tilt": "Pragmatic Tilt",
        "strict": "Strict Exclusion",
        "strict exclusion": "Strict Exclusion",
    }
    color_map = {
        "Baseline": COLORS["primary"],
        "Pragmatic Tilt": COLORS["clean"],
        "Strict Exclusion": "#D08A00",  # warm amber
    }

    # Normalize scenario names into a tidy frame
    def _norm_scen_name(x: str) -> str:
        if not isinstance(x, str): return str(x)
        k = x.strip().lower()
        return order_map.get(k, x.strip())

    met = met.copy()
    met["_Scenario"] = met[scen_col].apply(_norm_scen_name) if scen_col in met.columns else met.index.astype(str)
    # Stable order: Baseline, Pragmatic Tilt, Strict Exclusion, then anything else
    preferred = ["Baseline", "Pragmatic Tilt", "Strict Exclusion"]
    others = [s for s in met["_Scenario"].unique().tolist() if s not in preferred]
    scen_order = preferred + others

    # =========================
    # 1) KEY CARDS (3 per scenario)
    # =========================
    st.markdown(
        '<div class="chart-head"><div class="chart-title">Key metrics by scenario</div>'
        '<div class="info-badge has-tip" data-tip="Tracking Error is estimated vs. the benchmark using a covariance model.">'
        'i</div></div>', unsafe_allow_html=True
    )

    # Make a tidy block we can loop
    def _num(x):
        try: return float(x)
        except: return None

    row = st.columns(3)
    for i, scen in enumerate(scen_order[:3]):  # show top three
        sub = met.loc[met["_Scenario"] == scen].head(1)
        if sub.empty:
            continue
        with row[i]:
            c = _num(sub[clean_col].iloc[0]) if clean_col in sub.columns else None
            k = _num(sub[ctr_col].iloc[0])   if ctr_col in sub.columns   else None
            t = _num(sub[te_col].iloc[0])    if te_col in sub.columns    else None

            tone_clean  = "green" if (c is not None and c >= 0) else "neutral"
            tone_contro = "red"   if (k is not None and k > 0)  else "neutral"

            st.markdown(f"<h4 style='margin:4px 0 8px 0; color:{color_map.get(scen, COLORS['text'])};'>{scen}</h4>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: kpi_card("% Clean",  f"{c:.1f}%" if c is not None else "–", tone=tone_clean)
            with c2: kpi_card("% Contro", f"{k:.1f}%" if k is not None else "–", tone=tone_contro)
            with c3: kpi_card("TE (ann.)", f"{t:.2f}%" if t is not None else "–", tone="neutral")

    gap(8)

    # =========================
    # 2) COMPOSITION COMPARISON (stacked inside clusters)
    # =========================
    st.markdown(
        '<div class="chart-head"><div class="chart-title">Portfolio Composition — Clean vs Controversial vs Other</div>'
        '<div class="info-badge has-tip" data-tip="Shares of each scenario’s target portfolio weights.">'
        'i</div></div>', unsafe_allow_html=True
    )

    comp = []
    for scen in scen_order:
        m = met.loc[met["_Scenario"] == scen].head(1)
        if m.empty: continue
        comp.append({"Scenario": scen, "Category": "Clean",          "Value": _num(m[clean_col].iloc[0]) if clean_col in m.columns else None})
        comp.append({"Scenario": scen, "Category": "Controversial",  "Value": _num(m[ctr_col].iloc[0])   if ctr_col   in m.columns else None})
        if oth_col and oth_col in m.columns:
            comp.append({"Scenario": scen, "Category": "Other",      "Value": _num(m[oth_col].iloc[0])})
        else:
            # compute Other if missing
            c = _num(m[clean_col].iloc[0]) if clean_col in m.columns else 0
            k = _num(m[ctr_col].iloc[0])   if ctr_col   in m.columns else 0
            comp.append({"Scenario": scen, "Category": "Other", "Value": max(0.0, 100.0 - (c or 0) - (k or 0))})

    comp_df = pd.DataFrame(comp).dropna(subset=["Value"])
    color_scale = alt.Scale(
        domain=["Clean", "Controversial", "Other"],
        range=[COLORS["clean"], COLORS["contro"], COLORS["other"]]
    )

    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar(opacity=0.94)
        .encode(
            x=alt.X("sum(Value):Q", stack="normalize", axis=alt.Axis(title=None, format="%", ticks=False, labels=False)),
            y=alt.Y("Scenario:N", sort=scen_order, title=None),
            color=alt.Color("Category:N", scale=color_scale, title=None, legend=alt.Legend(orient="top", direction="horizontal")),
            tooltip=[
                alt.Tooltip("Scenario:N"),
                alt.Tooltip("Category:N"),
                alt.Tooltip("Value:Q", title="Share (%)", format=".1f"),
            ],
        )
        .properties(height=150)
    )
    st.altair_chart(comp_chart, use_container_width=True)

    gap(10)

    # =========================
    # 3) FINANCIAL COMPARISON (expected return & risk-return bubble)
    # =========================
    st.markdown('<div class="chart-head"><div class="chart-title">Expected performance</div></div>', unsafe_allow_html=True)

    # A) Expected Return bars
    er_df = met[["_Scenario", er_col]].rename(columns={er_col:"Expected Return"}).dropna() if er_col in met.columns else pd.DataFrame()
    if not er_df.empty:
        er_df["Color"] = er_df["_Scenario"].map(lambda s: color_map.get(s, COLORS["text"]))
        er_chart = (
            alt.Chart(er_df)
            .mark_bar(opacity=0.94)
            .encode(
                x=alt.X("Expected Return:Q", title="Annualized expected return (%)", axis=alt.Axis(format=".2f")),
                y=alt.Y("_Scenario:N", sort=scen_order, title=None),
                color=alt.Color("Color:N", scale=None, legend=None),
                tooltip=[alt.Tooltip("_Scenario:N", title="Scenario"), alt.Tooltip("Expected Return:Q", format=".2f")]
            )
            .properties(height=150)
        )
        st.altair_chart(er_chart, use_container_width=True)
    else:
        st.info("Expected return not found in scenario metrics.")

    # B) Risk vs Return bubble (X=Vol, Y=ExpRet, size=TE)
    if (vol_col in met.columns) and (er_col in met.columns) and (te_col in met.columns):
        rr = met[["_Scenario", vol_col, er_col, te_col]].dropna().rename(
            columns={vol_col:"Volatility", er_col:"Expected Return", te_col:"Tracking Error"}
        )
        rr["Color"] = rr["_Scenario"].map(lambda s: color_map.get(s, COLORS["text"]))
        rr_chart = (
            alt.Chart(rr)
            .mark_circle(opacity=0.9)
            .encode(
                x=alt.X("Volatility:Q", title="Volatility (ann. %)", axis=alt.Axis(format=".2f")),
                y=alt.Y("Expected Return:Q", title="Expected Return (ann. %)", axis=alt.Axis(format=".2f")),
                size=alt.Size("Tracking Error:Q", title="TE (%)", legend=alt.Legend(orient="right")),
                color=alt.Color("Color:N", scale=None, legend=None),
                tooltip=[
                    alt.Tooltip("_Scenario:N", title="Scenario"),
                    alt.Tooltip("Expected Return:Q", format=".2f"),
                    alt.Tooltip("Volatility:Q", format=".2f"),
                    alt.Tooltip("Tracking Error:Q", format=".2f"),
                ],
            )
            .properties(height=300)
        )
        st.altair_chart(rr_chart, use_container_width=True)

    gap(10)

    # =========================
    # 4) TRACKING ERROR LENS (Top active bets)
    # =========================
    st.markdown(
        '<div class="chart-head"><div class="chart-title">Top active bets — over/underweights vs benchmark</div>'
        '<div class="info-badge has-tip" data-tip="Active weight = portfolio weight − benchmark weight. Shows where TE lives.">'
        'i</div></div>', unsafe_allow_html=True
    )

    # We’ll look for a reasonable active weight column in deltas
    name_col   = _pick(deltas, "holding", "name", "security")
    scen_d_col = _pick(deltas, "scenario", "name")
    aw_name    = _pick(deltas, "active_weight", "active_wt", "delta_w", "delta_weight", "weight_delta", "w_minus_bench")

    if name_col and scen_d_col and aw_name and not deltas.empty:
        # Build a small multiples chart (3 scenarios) of top ± over/underweights
        tabs = st.tabs([s for s in scen_order[:3]])
        for tab, scen in zip(tabs, scen_order[:3]):
            with tab:
                d = deltas.loc[deltas[scen_d_col].apply(_norm_scen_name) == scen].copy()
                d["_aw"] = pd.to_numeric(d[aw_name], errors="coerce")
                d = d.dropna(subset=["_aw"])
                # pick symmetric top 8 over & under
                over = d.nlargest(8, "_aw")
                under= d.nsmallest(8, "_aw")
                view = pd.concat([under, over], ignore_index=True)
                view["_dir"] = view["_aw"].apply(lambda v: "Overweight" if v > 0 else "Underweight")
                view = view.rename(columns={name_col:"Holding"})

                if view.empty:
                    st.info("No active bets detected for this scenario.")
                else:
                    chart = (
                        alt.Chart(view)
                        .transform_calculate(abs_aw="abs(datum._aw)")
                        .mark_bar()
                        .encode(
                            x=alt.X("_aw:Q", title="Active weight (pp)"),
                            y=alt.Y("Holding:N", sort=alt.SortField(field="abs_aw", order="descending"), title=None),
                            color=alt.Color("_dir:N", title=None, scale=alt.Scale(domain=["Underweight","Overweight"], range=[COLORS["contro"], COLORS["clean"]])),
                            tooltip=[alt.Tooltip("Holding:N"), alt.Tooltip("_aw:Q", title="Active weight (pp)", format="+.3f")],
                        )
                        .properties(height=340)
                    )
                    st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Active weights not available in scenario_position_deltas.csv to build the bets view.")

    gap(10)

    # =========================
    # 5) POSITION DELTAS MIX (what moved to get cleaner)
    # =========================
    st.markdown(
        '<div class="chart-head"><div class="chart-title">How the portfolio moved — adds/trims/exits/entries</div>'
        '<div class="info-badge has-tip" data-tip="Split of portfolio changes by action and classification (Clean / Controversial / Other).">'
        'i</div></div>', unsafe_allow_html=True
    )

    act_col   = _pick(deltas, "action", "change_type")
    cls_col   = _pick(deltas, "classification", "class")
    wpp_col   = _pick(deltas, "weight_delta_pp", "delta_pp", "pp_change", "weight_pp", "delta_weight_pp")

    if all([scen_d_col, act_col, cls_col, wpp_col]):
        d2 = deltas.copy()
        d2["_Scenario"] = d2[scen_d_col].apply(_norm_scen_name)
        d2["_Action"]   = d2[act_col].astype(str).str.title()
        d2["_Class"]    = d2[cls_col].astype(str).str.title().replace({"Controversial":"Controversial", "Clean":"Clean", "Other":"Other"})
        d2["_PP"]       = pd.to_numeric(d2[wpp_col], errors="coerce").fillna(0.0)

        agg = (d2.groupby(["_Scenario","_Action","_Class"], as_index=False)["_PP"].sum())
        agg = agg[agg["_Scenario"].isin(scen_order[:3])]

        stack_color = alt.Scale(domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])

        deltas_chart = (
            alt.Chart(agg)
            .mark_bar(opacity=0.94)
            .encode(
                x=alt.X("sum(_PP):Q", stack="normalize", axis=alt.Axis(title="Share of total |Δweight|", format="%")),
                y=alt.Y("_Scenario:N", sort=scen_order[:3], title=None),
                color=alt.Color("_Class:N", scale=stack_color, title=None, legend=alt.Legend(orient="top")),
                column=alt.Column("_Action:N", title=None, spacing=18),
                tooltip=[
                    alt.Tooltip("_Scenario:N", title="Scenario"),
                    alt.Tooltip("_Action:N", title="Action"),
                    alt.Tooltip("_Class:N", title="Class"),
                    alt.Tooltip("sum(_PP):Q", title="Weight change (pp, signed)", format="+.3f"),
                ],
            )
            .resolve_scale(y="independent")
            .properties(height=160)
        )
        st.altair_chart(deltas_chart, use_container_width=True)
    else:
        st.info("Could not detect action/class/Δweight columns for the position deltas visualization.")

    gap(10)

    # =========================
    # 6) Scenario story strip (short narrative)
    # =========================
    st.markdown(
        """
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:12px;">
          <div class="blx-card"><b style="color:var(--text);">Baseline</b><br><span class="blx-muted">Closest to benchmark; moderate controversial exposure remains.</span></div>
          <div class="blx-card"><b style="color:var(--text);">Pragmatic Tilt</b><br><span class="blx-muted">Uses small TE budget (~2%) to reduce controversial exposure while preserving balance.</span></div>
          <div class="blx-card"><b style="color:var(--text);">Strict Exclusion</b><br><span class="blx-muted">Hard screens remove targeted areas; highest TE and largest active bets.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    gap(6)
    # Optional downloads (kept subtle)
    cdl1, cdl2, cdl3 = st.columns([0.3,0.3,0.4])
    with cdl1:
        try:
            st.download_button("Download scenario metrics (CSV)", met.to_csv(index=False).encode("utf-8"),
                               file_name="scenario_portfolio_metrics.csv", mime="text/csv")
        except: pass
    with cdl2:
        try:
            st.download_button("Download position deltas (CSV)", deltas.to_csv(index=False).encode("utf-8"),
                               file_name="scenario_position_deltas.csv", mime="text/csv")
        except: pass

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
