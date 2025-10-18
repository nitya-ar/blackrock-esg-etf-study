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
    "muted": "#E7EBF0",
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
# RENDERER FOR TAB 3 (Simplified, visual-first)
# -------------------------
def render_tradeoffs_v2():
    import re
    import pandas as pd
    import altair as alt

    # (optional) Plotly for Sankey; skip if not installed
    try:
        import plotly.graph_objects as go
        _PLOTLY_OK = True
    except Exception:
        _PLOTLY_OK = False

    st.subheader("Tradeoff Scenarios")
    st.caption("Pick an ETF, click a scenario card, and see cleanliness vs tracking error, what changed, and where the weight moved.")

    # ---------- Load ----------
    try:
        metr   = load_scenario_metrics()
        deltas = load_scenario_deltas()
    except Exception as e:
        st.error(f"Could not load scenario metrics/deltas: {e}")
        st.stop()

    # ---------- Helpers ----------
    def _pick(df, *keys):
        if df is None or df.empty: return None
        keys = [k.lower() for k in keys]
        for c in df.columns:
            if any(k in str(c).lower() for k in keys): return c
        return None

    def _norm_scen(s):
        s = str(s or "")
        if s.lower().startswith("baseline"): return "Baseline"
        return re.sub(r"\s+", " ", s).strip()

    def _num(v):
        try: return float(v)
        except: return None

    def _pp(v, nd=1, blank="–"):
        try: return f"{float(v):.{nd}f}%"
        except: return blank

    # ---------- Column keys ----------
    scen_col   = _pick(metr, "scenario", "scenario_id", "scenario_name") or "scenario"
    etf_col    = _pick(metr, "etf_ticker", "etf", "fund") or "etf"
    weight_col = _pick(metr, "weighting", "mode") or "weighting"
    clean_col  = _pick(metr, "pct_clean", "clean") or "pct_clean"
    ctr_col    = _pick(metr, "pct_controversial", "contro") or "pct_controversial"
    oth_col    = _pick(metr, "pct_other", "other") or "pct_other"
    te_col     = _pick(metr, "tracking_error", "te") or "tracking_error"
    ret_col    = _pick(metr, "ann_return", "return") or "ann_return"
    vol_col    = _pick(metr, "ann_vol", "vol") or "ann_vol"

    # Backfills for missing cols
    for c, default in [(scen_col,"Baseline"), (etf_col,"ALL"), (weight_col,"AUM")]:
        if c not in metr.columns: metr[c] = default

    metr["_scen"] = metr[scen_col].map(_norm_scen)

    if deltas is None:
        deltas = pd.DataFrame()
    else:
        d_scen = _pick(deltas, "scenario", "scenario_name", "scenario_id") or "scenario"
        if d_scen not in deltas.columns: deltas[d_scen] = "Baseline"
        deltas["_scen"] = deltas[d_scen].map(_norm_scen)

    # ---------- Controls ----------
    topA, topB, topC, topD = st.columns([0.30, 0.20, 0.22, 0.28])
    with topA:
        etf_opts = [e for e in sorted(metr[etf_col].dropna().astype(str).unique()) if e.upper()!="ALL"] or ["ALL"]
        sel_etf = st.selectbox("ETF", etf_opts, index=0)
    with topB:
        w_opts = sorted(metr[weight_col].dropna().astype(str).unique()) or ["AUM","EW"]
        sel_weight = st.selectbox("Weighting", w_opts, index=0)
    mview = metr[(metr[etf_col].astype(str).eq(sel_etf)) & (metr[weight_col].astype(str).eq(sel_weight))].copy()
    with topC:
        nov_exp = st.segmented_control("Mode", ["Novice","Expert"], default="Novice", label_visibility="collapsed")
    with topD:
        # targets to guide the frontier chart
        max_clean = float(pd.to_numeric(mview[clean_col], errors="coerce").max() or 30)
        max_te    = float(pd.to_numeric(mview[te_col], errors="coerce").max() or 2)
        t_clean = st.slider("Clean target (%)", 0.0, max(40.0, round(max_clean+2,1)), value=min(30.0, max_clean))
        t_te    = st.slider("TE cap (ann. %)", 0.0, max(0.5, round(max_te+0.2,2)), step=0.05, value=min(1.0, max_te))

    if mview.empty:
        st.warning("No scenario rows for this ETF/weighting.")
        st.stop()

    # ---------- Scenario Gallery (segmented) ----------
    cards = (
        mview[[ "_scen", clean_col, te_col ]]
        .dropna(subset=[clean_col, te_col])
        .drop_duplicates("_scen")
        .sort_values([te_col, clean_col], ascending=[True, False])
    )
    # ensure baseline first if present
    order = (["Baseline"] if "Baseline" in cards["_scen"].values else []) + [s for s in cards["_scen"].values if s!="Baseline"]
    cards["_order"] = cards["_scen"].map({s:i for i,s in enumerate(order)})
    cards = cards.sort_values("_order")
    default_scen = "Baseline" if "Baseline" in cards["_scen"].values else cards["_scen"].iloc[0]
    sel_scenario = st.segmented_control("Scenario", options=order, default=default_scen, label_visibility="collapsed")

    # current rows
    base = mview[mview["_scen"]=="Baseline"].head(1)
    pick = mview[mview["_scen"]==sel_scenario].head(1)

    # ---------- Headline KPIs ----------
    k1,k2,k3,k4 = st.columns([0.25,0.25,0.25,0.25])
    b_clean = _num(base[clean_col].iloc[0]) if not base.empty else None
    s_clean = _num(pick[clean_col].iloc[0]) if not pick.empty else None
    s_te    = _num(pick[te_col].iloc[0]) if not pick.empty else None
    b_ret   = _num(base[ret_col].iloc[0]) if (not base.empty and ret_col in base.columns) else None
    s_ret   = _num(pick[ret_col].iloc[0]) if (not pick.empty and ret_col in pick.columns) else None
    b_vol   = _num(base[vol_col].iloc[0]) if (not base.empty and vol_col in base.columns) else None
    s_vol   = _num(pick[vol_col].iloc[0]) if (not pick.empty and vol_col in pick.columns) else None
    d_ret = None if (b_ret is None or s_ret is None) else (s_ret - b_ret)
    d_vol = None if (b_vol is None or s_vol is None) else (s_vol - b_vol)

    with k1: kpi_card("% Clean", _pp(s_clean), "green" if (s_clean or -1) >= (b_clean or -1) else "red")
    with k2: kpi_card("Tracking Error", _pp(s_te, nd=2), "red" if (s_te or 0) > t_te else "neutral")
    with k3: kpi_card("Return Δ (ann.)", (f"{d_ret:+.2f}%" if d_ret is not None else "–"),
                      "green" if (d_ret or 0) >= 0 else "red")
    with k4: kpi_card("Volatility Δ (ann.)", (f"{d_vol:+.2f}%" if d_vol is not None else "–"),
                      "red" if (d_vol or 0) > 0 else "green")

    gap(6)

    # ================= VISUALS =================
    left, right = st.columns([0.55, 0.45])

    # ---- A) Frontier (Clean vs TE) with targets & quadrant shading ----
    with left:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Frontier — Clean% vs TE (click a point)</div>', unsafe_allow_html=True)
        dfp = cards.rename(columns={clean_col:"CleanPct", te_col:"TE", "_scen":"Scenario"}).copy()
        if dfp.empty:
            st.info("No scenarios with both Clean% and TE for this ETF/weight.")
        else:
            # background shading (below TE cap & above Clean target)
            bg = pd.DataFrame({
                "x1":[0], "x2":[(dfp["TE"].max() or 2.0)*1.05],
                "y1":[t_clean], "y2":[(dfp["CleanPct"].max() or 30.0)*1.05]
            })
            rect = alt.Chart(bg).mark_rect(opacity=0.06, stroke=COLORS["primary"], strokeWidth=1).encode(
                x="x1:Q", x2="x2:Q", y="y1:Q", y2="y2:Q"
            )
            tgt_clean = alt.Chart(pd.DataFrame({"y":[t_clean]})).mark_rule(strokeDash=[4,4]).encode(y="y:Q")
            tgt_te    = alt.Chart(pd.DataFrame({"x":[t_te]})).mark_rule(strokeDash=[4,4]).encode(x="x:Q")
            pts = alt.Chart(dfp).mark_circle(size=130).encode(
                x=alt.X("TE:Q", title="Tracking Error (ann. %)"),
                y=alt.Y("CleanPct:Q", title="% Clean"),
                color=alt.condition(alt.datum.Scenario == sel_scenario, alt.value(COLORS["primary"]), alt.value("#8A93A6")),
                tooltip=["Scenario:N", alt.Tooltip("CleanPct:Q", format=".1f"), alt.Tooltip("TE:Q", format=".2f")]
            ).interactive()
            st.altair_chart((rect + tgt_clean + tgt_te + pts).properties(height=360), use_container_width=True)

    # ---- B) Waterfall: change in Clean% vs Baseline ----
    with right:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Waterfall — Clean% change vs baseline</div>', unsafe_allow_html=True)
        if base.empty or pick.empty or (b_clean is None) or (s_clean is None):
            st.info("Waterfall unavailable — need baseline & selected scenario Clean%.")
        else:
            wf = pd.DataFrame([
                {"Label":"Baseline", "Value": b_clean, "Type":"base"},
                {"Label": sel_scenario, "Value": s_clean - b_clean, "Type":"delta"},
                {"Label":"Scenario", "Value": s_clean, "Type":"total"},
            ])
            color_map = {"base":"#8892A6","delta":COLORS["clean"] if (s_clean or 0) >= (b_clean or 0) else COLORS["contro"], "total":COLORS["primary"]}
            bar = alt.Chart(wf).mark_bar().encode(
                x=alt.X("Label:N", title=None),
                y=alt.Y("Value:Q", title="% Clean"),
                color=alt.Color("Type:N", legend=None, scale=alt.Scale(domain=list(color_map), range=list(color_map.values()))),
                tooltip=[alt.Tooltip("Label:N"), alt.Tooltip("Value:Q", format=".1f")]
            ).properties(height=220)
            st.altair_chart(bar, use_container_width=True)

    gap(10)

    # ---- C) Sankey: weight flow Baseline → Scenario (bucketed) ----
    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Weight flow — Baseline → Scenario (Clean / Controversial / Other)</div>', unsafe_allow_html=True)
    if not _PLOTLY_OK:
        st.caption("Plotly not available; skipping flow chart.")
    elif deltas.empty:
        st.info("No deltas file; flow chart unavailable.")
    else:
        d_etf   = _pick(deltas, "etf_ticker", "etf", "fund") or etf_col
        d_class = _pick(deltas, "classification", "class") or "classification"
        base_w  = _pick(deltas, "baseline_weight", "weight_base_pct")
        scen_w  = _pick(deltas, "scenario_weight", "weight_scn_pct")
        if not all(c in deltas.columns for c in [d_etf, "_scen", d_class, base_w, scen_w]):
            st.info("Flow chart needs classification & baseline/scenario weights.")
        else:
            dv = deltas[(deltas[d_etf].astype(str).eq(sel_etf)) & (deltas["_scen"].astype(str).eq(sel_scenario))].copy()
            if dv.empty:
                st.info("No deltas for this selection.")
            else:
                def _bucket(x):
                    x = str(x).strip().lower()
                    if x == "clean": return "Clean"
                    if x == "controversial": return "Controversial"
                    return "Other"
                dv["_bucket"] = dv[d_class].map(_bucket)

                buckets = ["Clean","Controversial","Other"]
                base_b = dv.groupby("_bucket")[base_w].sum().reindex(buckets).fillna(0).to_dict()
                scen_b = dv.groupby("_bucket")[scen_w].sum().reindex(buckets).fillna(0).to_dict()

                sources = [f"Base {b}" for b in buckets]
                targets = [f"Scen {b}" for b in buckets]
                nodes = sources + targets
                node_index = {n:i for i,n in enumerate(nodes)}
                link = dict(
                    source=[node_index[f"Base {b}"] for b in buckets],
                    target=[node_index[f"Scen {b}"] for b in buckets],
                    value=[float(scen_b[b]) for b in buckets],
                )
                node = dict(label=nodes, pad=18, thickness=16)
                fig = go.Figure(go.Sankey(node=node, link=link))
                st.plotly_chart(fig, use_container_width=True, theme=None)

    # ---- D) Sector drift (lollipops) if present ----
    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Sector drift — Scenario vs Baseline (pp)</div>', unsafe_allow_html=True)
    if deltas.empty:
        st.caption("Sector breakdown not available.")
    else:
        d_etf  = _pick(deltas, "etf_ticker", "etf", "fund") or etf_col
        d_sect = _pick(deltas, "sector")
        base_w = _pick(deltas, "baseline_weight", "weight_base_pct")
        scen_w = _pick(deltas, "scenario_weight", "weight_scn_pct")
        if not all(c in deltas.columns for c in [d_etf, "_scen", d_sect, base_w, scen_w]):
            st.caption("Sector drift needs sector, baseline, and scenario weights.")
        else:
            dv = deltas[(deltas[d_etf].astype(str).eq(sel_etf)) & (deltas["_scen"].astype(str).eq(sel_scenario))].copy()
            if dv.empty:
                st.caption("No sector rows for this selection.")
            else:
                g = dv.groupby(d_sect)[[base_w, scen_w]].sum().reset_index()
                g["drift"] = pd.to_numeric(g[scen_w], errors="coerce") - pd.to_numeric(g[base_w], errors="coerce")
                g = g.sort_values("drift", key=lambda s: s.abs(), ascending=False).head(10)
                lol = alt.Chart(g).mark_circle(size=110).encode(
                    x=alt.X("drift:Q", title="Δ weight (pp)"),
                    y=alt.Y(f"{d_sect}:N", sort="-x", title=None),
                    color=alt.condition(alt.datum.drift > 0, alt.value(COLORS["clean"]), alt.value(COLORS["contro"])),
                    tooltip=[alt.Tooltip(d_sect, title="Sector"), alt.Tooltip("drift:Q", title="Δ (pp)", format="+.2f")]
                ).properties(height=260)
                st.altair_chart(lol, use_container_width=True)

    gap(8)

    # ---- E) Movers (compact bars, top 5 adds / drops) ----
    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top movers — adds & drops</div>', unsafe_allow_html=True)
    if deltas.empty:
        st.info("No position deltas file.")
    else:
        d_etf  = _pick(deltas, "etf_ticker", "etf", "fund") or etf_col
        aw_col = _pick(deltas, "active_weight", "delta_weight", "delta_weight_pct", "dw")
        name_c = _pick(deltas, "name", "holding_name", "security")
        tick_c = _pick(deltas, "ticker")
        cls_c  = _pick(deltas, "classification", "class")

        dv = deltas[(deltas[d_etf].astype(str).eq(sel_etf)) & (deltas["_scen"].astype(str).eq(sel_scenario))].copy()
        if dv.empty or (aw_col not in dv.columns) or (tick_c not in dv.columns) or (name_c not in dv.columns):
            st.info("No movers for this selection.")
        else:
            dv[aw_col] = pd.to_numeric(dv[aw_col], errors="coerce")
            adds  = dv.sort_values(aw_col, ascending=False).head(5).copy()
            drops = dv.sort_values(aw_col, ascending=True).head(5).copy()

            def _bars(df, color):
                df = df.copy()
                df["_label"] = df[[tick_c, name_c]].astype(str).agg(lambda r: f"{r[0]} — {r[1]}", axis=1)
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(f"{aw_col}:Q", title="Active Δ (pp)"),
                    y=alt.Y("_label:N", sort="-x", title=None),
                    color=alt.value(color),
                    tooltip=[alt.Tooltip(tick_c, title="Ticker"),
                             alt.Tooltip(name_c, title="Holding"),
                             alt.Tooltip(cls_c,  title="Class"),
                             alt.Tooltip(aw_col, title="Active Δ (pp)", format="+.3f")]
                ).properties(height=180)
                return chart

            c1, c2 = st.columns([0.5,0.5])
            with c1:
                st.caption("Adds / Overweights")
                st.altair_chart(_bars(adds, COLORS["clean"]), use_container_width=True)
            with c2:
                st.caption("Removals / Underweights")
                st.altair_chart(_bars(drops, COLORS["contro"]), use_container_width=True)

    # ---- Expert toggles (raw tables) ----
    if nov_exp == "Expert":
        with st.expander("Raw metrics (current ETF + weighting)"):
            st.dataframe(mview.drop(columns=["_scen"]), use_container_width=True, hide_index=True)
        if not deltas.empty:
            with st.expander("Raw deltas (current ETF + scenario)"):
                d_etf  = _pick(deltas, "etf_ticker", "etf", "fund") or etf_col
                sub = deltas[(deltas[d_etf].astype(str).eq(sel_etf)) & (deltas["_scen"].astype(str).eq(sel_scenario))]
                st.dataframe(sub, use_container_width=True, hide_index=True)

    # ---- Download ----
    gap(6)
    st.download_button("Download scenario metrics (filtered)",
                       data=mview.drop(columns=["_scen"]).to_csv(index=False).encode("utf-8"),
                       file_name=f"{sel_etf}_{sel_weight}_metrics.csv", mime="text/csv")


# Back-compat shim so existing call sites don't crash
def render_tradeoffs():
    return render_tradeoffs_v2()



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
