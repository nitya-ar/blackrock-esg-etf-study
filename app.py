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

/* ---------- GLOBAL TEXT & LINKS ---------- */
* {{ color: var(--text); }}
a {{ color: #73B4FF !important; }}
a:hover {{ color: #A3CFFF !important; }}

/* ---------- APP CONTAINERS ---------- */
section.main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
  background-color: var(--bg) !important;
  color: var(--text) !important;
  border: 0 !important;
}}
[data-testid="stToolbar"] {{ background: transparent !important; }}

/* ---------- CARDS / CHART WRAPPERS ---------- */
.blx-card, .kpi, .stPlotlyChart, .stAltairChart, .stVegaLiteChart, .stEChart {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
}}
.vega-embed, .vega-embed * {{ background: transparent !important; }}

/* ---------- DATAFRAMES / TABLES ---------- */
div[data-testid="stDataframe"] {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
div[data-testid="stDataframe"] thead tr th {{
  background: #0C0E13 !important;
  color: var(--text) !important;
  border-bottom: 1px solid var(--border) !important;
}}
div[data-testid="stDataframe"] tbody tr {{
  background: #0E1015 !important;
  color: var(--text) !important;
}}
div[data-testid="stDataframe"] ::-webkit-scrollbar-thumb {{
  background: #2A2F36 !important;
  border-radius: 6px;
}}
div[data-testid="stDataframe"] ::-webkit-scrollbar-track {{
  background: #0B0D12 !important;
}}

/* ---------- INPUTS: SELECT / MULTISELECT / TEXT INPUT ---------- */
[data-baseweb="select"], [data-baseweb="select"] * {{
  background-color: var(--card) !important;
  color: var(--text) !important;
}}
[data-baseweb="select"] {{ border: 1px solid var(--border) !important; border-radius: 10px; }}
[data-baseweb="select"] svg {{ fill: var(--muted) !important; }}
[data-baseweb="tag"] {{
  background: #10131A !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
[data-baseweb="input"] input, [data-baseweb="input"] textarea {{
  background: var(--card) !important;
  color: var(--text) !important;
}}
[data-baseweb="input"] {{ border: 1px solid var(--border) !important; border-radius: 10px; }}

/* Dropdown menu (the popover list) */
[data-baseweb="menu"] {{
  background: #0F1116 !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
[data-baseweb="menu"] li {{ color: var(--text) !important; }}
/* fixed missing '[' here ↓ */
[data-baseweb="menu"] li:hover {{ background: #12151C !important; }}

/* ---------- SLIDERS ---------- */
[data-baseweb="slider"] {{ color: var(--text) !important; }}
[data-baseweb="slider"] > div {{ background: transparent !important; }}
[data-baseweb="slider"] [role="slider"] {{
  background: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(0,163,255,0.18) !important;
}}
[data-baseweb="slider"] div[role="presentation"] {{ background: #1C2027 !important; }} /* track */
[data-baseweb="slider"] div[role="presentation"] > div {{ background: var(--primary) !important; }} /* filled */

/* ---------- CHECKBOX / RADIO ---------- */
[data-baseweb="checkbox"] label, [data-baseweb="radio"] label {{ color: var(--text) !important; }}
[data-baseweb="checkbox"] input, [data-baseweb="radio"] input {{ accent-color: var(--primary) !important; }}

/* ---------- SEGMENTED CONTROL ---------- */
div[data-testid="stSegmentedControl"] div[role="tablist"] {{
  background: #0E1015 !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
div[data-testid="stSegmentedControl"] button[role="tab"] {{
  background: transparent !important;
  color: var(--text) !important;
  border: none !important;
}}
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
  background: #12151C !important;
  color: var(--text) !important;
  box-shadow: inset 0 0 0 1px var(--border);
}}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"] {{
  background: #0E1015 !important;
  border-bottom: 1px solid var(--border) !important;
}}
.stTabs [data-baseweb="tab"] {{
  color: var(--muted) !important;
  background: transparent !important;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
  color: var(--text) !important;
  border-color: var(--primary) !important;
}}

/* ---------- BUTTONS (incl. download) ---------- */
.stDownloadButton > button, .stButton > button {{
  background: #12151C !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
.stDownloadButton > button:hover, .stButton > button:hover {{
  background: #151923 !important;
  border-color: #2A2F36 !important;
}}

/* ---------- TOOLTIP & LEGEND WRAPPERS ---------- */
.has-tip::after {{
  background: #0B0D12 !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
.vega-bindings, .vega-tooltip, .vega-tooltip * {{
  background: #0F1116 !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}}

/* ---------- FORMS / SMALL LABELS ---------- */
label, .st-emotion-cache-1cypcdb, .st-emotion-cache-1qg05tj {{
  color: var(--muted) !important;
}}

/* ---------- SCROLLBARS (GLOBAL) ---------- */
*::-webkit-scrollbar {{ width: 10px; height: 10px; }}
*::-webkit-scrollbar-thumb {{ background: #2A2F36; border-radius: 8px; }}
*::-webkit-scrollbar-track {{ background: #0B0D12; }}


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
def load_top_movers_with_names():       return load_csv(2, "top_movers_with_names.csv")

# Analysis 3 loaders (Tradeoff Scenarios)
@st.cache_data(show_spinner=False)
def load_scenario_metrics():        return load_csv(3, "scenario_portfolio_metrics.csv")

@st.cache_data(show_spinner=False)
def load_scenario_deltas():         return load_csv(3, "scenario_position_deltas.csv")

@st.cache_data(show_spinner=False)
def load_scenario_progress():       return load_csv(3, "scenario_progress.csv")

@st.cache_data(show_spinner=False)
def load_covariance_2025():         return load_csv(3, "covariance_2025.csv")

@st.cache_data(show_spinner=False)
def load_returns_top_per_etf_2025():return load_csv(3, "returns_top_per_etf_2025.csv")

@st.cache_data(show_spinner=False)
def load_universe_2025_xlsx():
    # Try local first
    lp = local_path(3, "universe_2025.xlsx")
    try:
        if lp and os.path.exists(lp):
            return pd.read_excel(lp)
    except: pass
    # GitHub raw fallback
    raw_url = github_raw_url(3, "universe_2025.xlsx")
    try:
        return pd.read_excel(raw_url)
    except Exception as e_raw:
        # GitHub API fallback (requires Accept header)
        api_url = github_api_url(3, "universe_2025.xlsx")
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        import io, requests
        r = requests.get(api_url, headers=headers, timeout=25)
        r.raise_for_status()
        return pd.read_excel(io.BytesIO(r.content))

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
                screen_range  = ["#5C6ACF","#C97F64","#EDE7DE","#B5A793","#2FA08A","#A99ABD"]

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

        # Filter to the selected year pair (Start → 2025) if possible
        if y0_col and y1_col:
            m = m[(m[y0_col] == start_year) & (m[y1_col] == end_year)]
        else:
            # If the file doesn't carry explicit year columns, assume it's for 2017→2025 only
            m = m.head(0)

        if d_col in (m.columns if m is not None else []) and not m.empty:
            # Sort by absolute change and take top 10
            m["_abs"] = pd.to_numeric(m[d_col], errors="coerce").abs()
            m = m.sort_values("_abs", ascending=False).head(10)

            # Choose best display name: Name_2025 if present, else base name
            if name25_col and name25_col in m.columns:
                holding_name = m[name25_col]
            elif base_name and base_name in m.columns:
                holding_name = m[base_name]
            else:
                holding_name = pd.Series(["—"] * len(m), index=m.index)

            # Build display table
            movers_view = pd.DataFrame({
                "Holding (2025)": holding_name,
                "Category": m[cat_col] if cat_col in m.columns else "—",
                "Δ exposure (pp)": pd.to_numeric(m[d_col], errors="coerce").map(lambda v: f"{v:+.4f}")
            })

    if movers_view.empty:
        st.info("No movers found for the selected start year.")
    else:
        st.dataframe(movers_view, use_container_width=True, hide_index=True)




# -------------------------
# RENDERER FOR TAB 3
# -------------------------
def render_tradeoffs():
    import re

    st.subheader("Tradeoff Scenarios")
    st.caption("Pick an ETF, choose a scenario, and inspect cleanliness vs tracking error, what changed, and where the weight moved.")

    # ===== Load data (Analysis 3) =====
    try:
        metr   = load_scenario_metrics()          # scenario_portfolio_metrics.csv
        deltas = load_scenario_deltas()           # scenario_position_deltas.csv
    except Exception as e:
        st.error(f"Could not load scenario metrics/deltas: {e}")
        st.stop()

    # Optional enrichers (best-effort)
    try:    prog = load_scenario_progress()
    except: prog = pd.DataFrame()
    try:    _ = load_universe_2025_xlsx()  # not strictly needed here
    except: pass

    # ===== Helpers =====
    def _pick(df, *keys):
        if df is None or df.empty: return None
        keys = [k.lower() for k in keys]
        for c in df.columns:
            lc = c.lower()
            if any(k in lc for k in keys):
                return c
        return None

    # Robust column resolver for scenario_portfolio_metrics.csv
    def resolve_metric_cols(df: pd.DataFrame):
        def simp(s): return re.sub(r"[^a-z0-9]+", "", str(s).lower())
        bysimp = {simp(c): c for c in df.columns}

        def pick(*synonyms, numeric=False, pct=False, allow_regex=None):
            # direct synonym match
            for s in synonyms:
                k = re.sub(r"[^a-z0-9]+", "", s.lower())
                if k in bysimp: 
                    return bysimp[k]
            # regex fallback
            if allow_regex:
                patt = re.compile(allow_regex, re.I)
                for c in df.columns:
                    if patt.search(c): 
                        return c
            # heuristic fallback: contains token
            token = re.sub(r"[^a-z0-9]+", "", synonyms[0].lower())
            for c in df.columns:
                if token in simp(c):
                    if numeric:
                        s = pd.to_numeric(df[c], errors="coerce")
                        if s.notna().sum() == 0: 
                            continue
                        if pct:
                            v = s.dropna()
                            ok = (
                                ((v >= 0) & (v <= 100)).mean() > 0.7 or
                                ((v >= 0) & (v <= 1)).mean()  > 0.7
                            )
                            if not ok: 
                                continue
                    return c
            return None

        scen   = pick("scenario", "scenario_id", "scenario_name", "name", allow_regex=r"^scenario")
        etf    = pick("etf_ticker", "etf", "fund", "ticker", "symbol", allow_regex=r"(etf|fund).*(tick|sym)")
        weight = pick("weighting", "mode", "weight_mode", allow_regex=r"weight.*(mode|ing)")
        clean  = pick("pct_clean", "clean_pct", "percent_clean", "clean", numeric=True, pct=True)
        te     = pick("tracking_error", "te", "te_ann", "te_pct", allow_regex=r"track.*err", numeric=True, pct=True)
        ctr    = pick("pct_controversial", "controversial_pct", "contro", "contro_pct", numeric=True, pct=True)
        oth    = pick("pct_other", "other_pct", numeric=True, pct=True)
        retc   = pick("ann_return", "return", "ret_ann", "annual_return", numeric=True, pct=True)
        volc   = pick("ann_vol", "vol", "volatility", "stdev", numeric=True, pct=True)

        # Convert 0–1 to % for numeric pct-like columns
        def ensure_pct(colname):
            if not colname or colname not in df.columns: return
            s = pd.to_numeric(df[colname], errors="coerce")
            if s.dropna().between(0, 1).mean() > 0.7:
                df[colname] = s * 100.0

        for c in [clean, te, ctr, oth, retc, volc]:
            ensure_pct(c)

        missing = [("scenario", scen), ("etf_ticker", etf), ("weighting", weight), ("pct_clean", clean), ("tracking_error", te)]
        if any(v is None for _, v in missing):
            st.error(
                "Your metrics file is missing required columns after fuzzy mapping.\n\n"
                "**Required (any case/fuzzy):** scenario, etf_ticker, weighting, pct_clean, tracking_error\n\n"
                f"**Found columns:** {list(df.columns)}"
            )
            st.stop()

        return dict(
            scen=scen, etf=etf, weight=weight,
            clean=clean, te=te, ctr=ctr, oth=oth,
            ret=retc, vol=volc,
        )

    # ===== Resolve columns and normalize scenarios =====
    col = resolve_metric_cols(metr)
    scen_col   = col["scen"]
    etf_col    = col["etf"]
    weight_col = col["weight"]
    clean_col  = col["clean"]
    te_col     = col["te"]
    ctr_col    = col["ctr"]
    oth_col    = col["oth"]
    ret_col    = col["ret"]
    vol_col    = col["vol"]

    metr = metr.copy()

    def _norm_scen(s: str) -> str:
        s = str(s or "")
        return "Baseline" if s.lower().startswith("baseline") else s

    def _pretty_name(s: str) -> str:
        s = str(s or "")
        if s.lower().startswith("baseline"): return "Baseline"
        # strip type_ and trailing timestamps like _20250101T171545
        s = re.sub(r"^\w+_", "", s)
        s = re.sub(r"_\d{8}t?\d{6,}$", "", s, flags=re.I)
        return (s.replace("_", " ").strip().title() or "Scenario")

    metr["_scen"]  = metr[scen_col].map(_norm_scen)
    metr["_label"] = metr[scen_col].map(_pretty_name)

    # ===== Controls =====
    topL, topM, topR = st.columns([0.34, 0.34, 0.32])

    with topL:
        etfs = sorted(metr[etf_col].dropna().astype(str).unique().tolist())
        sel_etf = st.selectbox("ETF", etfs, index=0 if etfs else None)

    with topM:
        wopts = sorted(metr[weight_col].dropna().astype(str).unique().tolist())
        default_idx = wopts.index("AUM") if "AUM" in wopts else 0
        sel_weight = st.selectbox("Weighting", wopts, index=default_idx)

    mview = metr[(metr[etf_col].astype(str).eq(sel_etf)) & (metr[weight_col].astype(str).eq(sel_weight))].copy()
    if mview.empty:
        st.info("No scenario rows for this ETF + weighting selection.")
        st.stop()

    # scenario cards for current ETF+weight
    cards = (
        mview[["_scen", "_label", clean_col, te_col, ctr_col, oth_col]]
        .dropna(subset=[clean_col, te_col], how="any")
        .drop_duplicates("_scen")
        .sort_values([te_col, clean_col], ascending=[True, False])
    )
    scen_order = (["Baseline"] if "Baseline" in cards["_scen"].values else []) + \
                 [s for s in cards["_scen"].values if s != "Baseline"]
    label_map = dict(zip(cards["_scen"], cards["_label"]))

    with topR:
        sel_scenario = st.segmented_control(
            "Scenario",
            options=scen_order,
            format_func=lambda s: label_map.get(s, s),
            default=("Baseline" if "Baseline" in scen_order else scen_order[0]),
            help="Pick which portfolio to visualize. Baseline is the original ETF."
        )

    # Optional targets (from scenario_progress if present)
    tgtL, tgtR = st.columns([0.5, 0.5])
    with tgtL:
        cw_col = _pick(prog, "clean_target", "clean_overweight", "clean tilt", "target_clean")
        cur_clean = float(pd.to_numeric(mview.loc[mview["_scen"]==sel_scenario, clean_col], errors="coerce").head(1).fillna(0).iloc[0] if sel_scenario in mview["_scen"].values else 0.0)
        if cw_col in (prog.columns if not prog.empty else []):
            vals = sorted(pd.to_numeric(prog[cw_col], errors="coerce").dropna().unique().tolist())
            t_clean = st.select_slider("Clean target (%)", options=vals, value=vals[0] if vals else cur_clean)
        else:
            t_clean = st.slider("Clean target (%)", min_value=0.0, max_value=max(30.0, cur_clean), value=cur_clean, step=0.1)
    with tgtR:
        tebud_col = _pick(prog, "te_budget", "te cap", "te_cap", "tracking_error_budget")
        cur_te = float(pd.to_numeric(mview.loc[mview["_scen"]==sel_scenario, te_col], errors="coerce").head(1).fillna(0).iloc[0] if sel_scenario in mview["_scen"].values else 0.0)
        if tebud_col in (prog.columns if not prog.empty else []):
            vals = sorted(pd.to_numeric(prog[tebud_col], errors="coerce").dropna().unique().tolist())
            t_te = st.select_slider("TE cap (ann. %)", options=vals, value=vals[0] if vals else max(cur_te, 0.5))
        else:
            t_te = st.slider("TE cap (ann. %)", min_value=0.0, max_value=max(2.0, cur_te*1.5 + 0.2), value=max(cur_te, 0.5), step=0.05)

    # Debug info
    with st.expander("Data health (debug)", expanded=False):
        st.write({
            "metrics_rows_for_selection": len(mview),
            "columns_in_metrics": list(metr.columns),
            "has_returns": ret_col in metr.columns if ret_col else False,
            "has_vol": vol_col in metr.columns if vol_col else False,
            "deltas_rows_all": (0 if deltas is None or deltas.empty else len(deltas)),
        })

    # Nearest row to target (if multiple points per scenario)
    def _nearest_by_targets(df: pd.DataFrame):
        df = df.copy()
        df["_d"] = (
            (pd.to_numeric(df[clean_col], errors="coerce") - float(t_clean))**2 +
            (pd.to_numeric(df[te_col],    errors="coerce") - float(t_te))**2
        )
        return df.sort_values("_d").head(1)

    base = mview[mview["_scen"] == "Baseline"]
    cur  = mview[mview["_scen"] == sel_scenario]
    base = _nearest_by_targets(base) if len(base) > 1 else base
    cur  = _nearest_by_targets(cur)  if len(cur)  > 1 else cur

    # Extract values
    def _get(df, col):
        try:    return float(pd.to_numeric(df[col], errors="coerce").iloc[0])
        except: return None

    b_clean = _get(base, clean_col); s_clean = _get(cur, clean_col)
    b_ctr   = _get(base, ctr_col);   s_ctr   = _get(cur, ctr_col)
    b_oth   = _get(base, oth_col);   s_oth   = _get(cur, oth_col)
    b_te    = _get(base, te_col);    s_te    = _get(cur, te_col)
    b_ret   = _get(base, ret_col) if ret_col else None
    s_ret   = _get(cur,  ret_col) if ret_col else None
    b_vol   = _get(base, vol_col) if vol_col else None
    s_vol   = _get(cur,  vol_col) if vol_col else None

    # ===== KPIs =====
    k1, k2, k3, k4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with k1:
        kpi_card("% Clean", f"{(s_clean if s_clean is not None else 0):.1f}%")
    with k2:
        kpi_card("Tracking Error", f"{(s_te if s_te is not None else 0):.2f}%")
    with k3:
        d_ret = None if (s_ret is None or b_ret is None) else (s_ret - b_ret)
        kpi_card("Return Δ (ann.)", "-" if d_ret is None else f"{d_ret:+.2f}%")
    with k4:
        d_vol = None if (s_vol is None or b_vol is None) else (s_vol - b_vol)
        kpi_card("Volatility Δ (ann.)", "-" if d_vol is None else f"{d_vol:+.2f}%")

    # ===== Frontier & Composition =====
    left, right = st.columns([0.52, 0.48])

    # Frontier: Clean% vs TE with target box
    with left:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Frontier — Clean% vs TE (points = scenarios)</div>', unsafe_allow_html=True)
        dfp = cards.rename(columns={clean_col:"CleanPct", te_col:"TE", "_scen":"Scenario"}).copy()
        if dfp.empty:
            st.info("No scenarios with both Clean% and TE for this ETF/weight.")
        else:
            y_max = max(5.0, float(dfp["CleanPct"].max() or 0) * 1.1)
            x_max = max(0.2, float(dfp["TE"].max() or 0) * 1.1)
            bg = pd.DataFrame({"x1":[0], "x2":[x_max], "y1":[t_clean], "y2":[y_max]})
            rect = alt.Chart(bg).mark_rect(opacity=0.08, stroke=COLORS["primary"], strokeWidth=1).encode(
                x=alt.X("x1:Q", scale=alt.Scale(domain=[0, x_max]), title="Tracking Error (ann. %)"),
                x2="x2:Q",
                y=alt.Y("y1:Q", scale=alt.Scale(domain=[0, y_max]), title="% Clean"),
                y2="y2:Q",
            )
            tgt_clean = alt.Chart(pd.DataFrame({"y":[t_clean]})).mark_rule(strokeDash=[4,4]).encode(
                y=alt.Y("y:Q", scale=alt.Scale(domain=[0, y_max]))
            )
            tgt_te = alt.Chart(pd.DataFrame({"x":[t_te]})).mark_rule(strokeDash=[4,4]).encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=[0, x_max]))
            )
            pts = alt.Chart(dfp).mark_circle(size=130).encode(
                x=alt.X("TE:Q", scale=alt.Scale(domain=[0, x_max]), title="Tracking Error (ann. %)"),
                y=alt.Y("CleanPct:Q", scale=alt.Scale(domain=[0, y_max]), title="% Clean"),
                color=alt.condition(alt.datum.Scenario == sel_scenario, alt.value(COLORS["primary"]), alt.value("#8A93A6")),
                tooltip=["Scenario:N", alt.Tooltip("CleanPct:Q", title="% Clean", format=".1f"), alt.Tooltip("TE:Q", title="TE", format=".2f")]
            ).interactive()
            st.altair_chart((rect + tgt_clean + tgt_te + pts).properties(height=360), use_container_width=True)

    # Composition: Baseline vs Selected
    with right:
        st.markdown(f'<div class="chart-title" style="margin-bottom:6px;">Composition — {label_map.get("Baseline","Baseline")} vs {label_map.get(sel_scenario, sel_scenario)}</div>', unsafe_allow_html=True)
        rows = []
        if b_clean is not None: rows.append({"View":"Baseline","Category":"Clean","Value":b_clean})
        if b_ctr   is not None: rows.append({"View":"Baseline","Category":"Controversial","Value":b_ctr})
        if b_oth   is not None: rows.append({"View":"Baseline","Category":"Other","Value":b_oth})
        if s_clean is not None: rows.append({"View":label_map.get(sel_scenario, sel_scenario),"Category":"Clean","Value":s_clean})
        if s_ctr   is not None: rows.append({"View":label_map.get(sel_scenario, sel_scenario),"Category":"Controversial","Value":s_ctr})
        if s_oth   is not None: rows.append({"View":label_map.get(sel_scenario, sel_scenario),"Category":"Other","Value":s_oth})
        comp = pd.DataFrame(rows)
        if not comp.empty:
            comp["View"] = pd.Categorical(comp["View"], categories=["Baseline", label_map.get(sel_scenario, sel_scenario)], ordered=True)
            ch = alt.Chart(comp).mark_bar(opacity=0.92).encode(
                x=alt.X("View:N", title=None),
                y=alt.Y("Value:Q", stack="normalize", axis=alt.Axis(format="%", title="Portfolio share")),
                color=alt.Color("Category:N", title=None, scale=alt.Scale(
                    domain=["Clean","Controversial","Other"], range=[COLORS["clean"], COLORS["contro"], COLORS["other"]]
                )),
                tooltip=[alt.Tooltip("View:N"), alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", title="Share (%)", format=".2f")]
            ).properties(height=320)
            st.altair_chart(ch, use_container_width=True)
        else:
            st.caption("Composition not available for this selection.")

    # ===== Movers (adds / drops) =====
    st.markdown('<div class="chart-title" style="margin-top:12px; margin-bottom:6px;">Top movers — scenario vs baseline</div>', unsafe_allow_html=True)
    movers_ok = False
    if deltas is not None and not deltas.empty:
        d_etf  = _pick(deltas, "etf_ticker","etf","fund") or etf_col
        d_scen = _pick(deltas, "scenario","name")         or scen_col
        aw_col = _pick(deltas, "active_weight", "delta_weight", "dw")
        name_c = _pick(deltas, "name", "holding_name", "security")
        tick_c = _pick(deltas, "ticker", "company_ticker")
        cls_c  = _pick(deltas, "classification", "class")
        sec_c  = _pick(deltas, "sector")
        reg_c  = _pick(deltas, "region")
        b_wt   = _pick(deltas, "baseline_weight")
        s_wt   = _pick(deltas, "scenario_weight")

        d = deltas[(deltas[d_etf].astype(str).eq(sel_etf)) & (deltas[d_scen].astype(str).eq(sel_scenario))].copy() \
            if (d_etf in deltas.columns and d_scen in deltas.columns) else pd.DataFrame()

        if not d.empty and aw_col in d.columns:
            d[aw_col] = pd.to_numeric(d[aw_col], errors="coerce")
            adds  = d.sort_values(aw_col, ascending=False).head(10)
            drops = d.sort_values(aw_col, ascending=True).head(10)

            def _fmt(df):
                return pd.DataFrame({
                    "Ticker": df.get(tick_c, pd.Series(["—"]*len(df))).astype(str),
                    "Holding": df.get(name_c, pd.Series(["—"]*len(df))).astype(str),
                    "Class": df.get(cls_c, pd.Series(["—"]*len(df))).astype(str),
                    "Sector": df.get(sec_c, pd.Series(["—"]*len(df))).astype(str) if sec_c in df.columns else "—",
                    "Region": df.get(reg_c, pd.Series(["—"]*len(df))).astype(str) if reg_c in df.columns else "—",
                    "Baseline Wt (%)": pd.to_numeric(df.get(b_wt, 0), errors="coerce").map(lambda v: f"{v:.3f}"),
                    "Scenario Wt (%)": pd.to_numeric(df.get(s_wt, 0), errors="coerce").map(lambda v: f"{v:.3f}"),
                    "Active Δ (pp)":   pd.to_numeric(df.get(aw_col, 0), errors="coerce").map(lambda v: f"{v:+.3f}")
                })

            cL, cR = st.columns([0.5, 0.5])
            with cL:
                st.markdown('<div class="blx-muted" style="margin-bottom:4px;">Adds / Overweights</div>', unsafe_allow_html=True)
                st.dataframe(_fmt(adds), use_container_width=True, hide_index=True)
            with cR:
                st.markdown('<div class="blx-muted" style="margin-bottom:4px;">Removals / Underweights</div>', unsafe_allow_html=True)
                st.dataframe(_fmt(drops), use_container_width=True, hide_index=True)
            movers_ok = True

    if not movers_ok:
        st.info("No movers for this selection.")

    # ===== Download filtered metrics =====
    gap(6)
    if not mview.empty:
        st.download_button(
            "Download scenario metrics (filtered)",
            data=mview.to_csv(index=False).encode("utf-8"),
            file_name=f"scenario_metrics_{sel_etf}_{sel_weight}.csv",
            mime="text/csv",
        )




# =========================
# BODY
# =========================
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Scenarios"])

    # ---------- 2025 OVERVIEW ----------
    with tab1:
        st.subheader("2025 Overview")

        # (RELOADER BUTTON REMOVED AS REQUESTED)

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
                st.dataframe(cont_disp, use_container_width=True, hide_index=True)
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
        render_change_since_2017()

    # ---------------- Tradeoff Scenarios ----------------
    with tab3:
        render_tradeoffs()

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
