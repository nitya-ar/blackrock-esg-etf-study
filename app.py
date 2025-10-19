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
      .blx-card, .stPlotlyChart, .stAltairChart, .stVegaLiteChart, .stEChart {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
      }}
      .vega-embed, .vega-embed * {{ background: transparent !important; }}

      /* ===== Dataframes & Tables – dark mode ===== */
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
      }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="grid"] {{ background: var(--card) !important; }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="row"] {{ background: #0E1015 !important; }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"] {{
        background: #0C0E13 !important; color: var(--text) !important; border-bottom: 1px solid var(--border) !important;
      }}
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="gridcell"] {{
        background: #0E1015 !important; color: var(--text) !important;
      }}

      :where([data-testid="stTable"]) table {{
        background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      :where([data-testid="stTable"]) thead th {{
        background: #0C0E13 !important; color: var(--text) !important; border-bottom: 1px solid var(--border) !important;
      }}
      :where([data-testid="stTable"]) tbody td {{
        background: #0E1015 !important; color: var(--text) !important; border-top: 1px solid #12151C !important;
      }}

      /* ---------- INPUTS ---------- */
      [data-baseweb="select"], [data-baseweb="select"] * {{ background-color: var(--card) !important; color: var(--text) !important; }}
      [data-baseweb="select"] {{ border: 1px solid var(--border) !important; border-radius: 10px; }}
      [data-baseweb="select"] svg {{ fill: var(--muted) !important; }}
      [data-baseweb="tag"] {{ background: #10131A !important; color: var(--text) !important; border: 1px solid var(--border) !important; }}
      [data-baseweb="input"] input, [data-baseweb="input"] textarea {{ background: var(--card) !important; color: var(--text) !important; }}
      [data-baseweb="input"] {{ border: 1px solid var(--border) !important; border-radius: 10px; }}

      [data-baseweb="menu"] {{
        background: #0F1116 !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      [data-baseweb="menu"] li {{ color: var(--text) !important; }}
      [data-baseweb="menu"] li:hover {{ background: #12151C !important; }}

      /* ---------- SLIDERS ---------- */
      [data-baseweb="slider"] {{ color: var(--text) !important; }}
      [data-baseweb="slider"] > div {{ background: transparent !important; }}
      [data-baseweb="slider"] [role="slider"] {{ background: var(--primary) !important; box-shadow: 0 0 0 3px rgba(0,163,255,0.18) !important; }}
      [data-baseweb="slider"] div[role="presentation"] {{ background: #1C2027 !important; }}
      [data-baseweb="slider"] div[role="presentation"] > div {{ background: var(--primary) !important; }}

      /* ---------- CHECKBOX / RADIO ---------- */
      [data-baseweb="checkbox"] label, [data-baseweb="radio"] label {{ color: var(--text) !important; }}
      [data-baseweb="checkbox"] input, [data-baseweb="radio"] input {{ accent-color: var(--primary) !important; }}

      /* ---------- SEGMENTED CONTROL (base) ---------- */
      div[data-testid="stSegmentedControl"] div[role="tablist"] {{
        background: #0E1015 !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      div[data-testid="stSegmentedControl"] button[role="tab"] {{
        background: transparent !important; color: var(--muted) !important; border: 1px solid transparent !important;
      }}
      div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
        background: #12151C !important; color: var(--text) !important; border: 1px solid #C63C41 !important; box-shadow: inset 0 0 0 1px #C63C41 !important;
      }}

      /* ---------- TABS ---------- */
      .stTabs [data-baseweb="tab-list"] {{ background: #0E1015 !important; border-bottom: 1px solid var(--border) !important; }}
      .stTabs [data-baseweb="tab"] {{ color: var(--muted) !important; background: transparent !important; }}
      .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: var(--text) !important; border-color: var(--primary) !important; }}

      /* ---------- BUTTONS ---------- */
      .stDownloadButton > button, .stButton > button {{
        background: #12151C !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      .stDownloadButton > button:hover, .stButton > button:hover {{ background: #151923 !important; border-color: #2A2F36 !important; }}

      /* ---------- TOOLTIP & LEGEND ---------- */
      .has-tip::after {{ background: #0B0D12 !important; color: var(--text) !important; border: 1px solid var(--border) !important; }}
      .vega-bindings, .vega-tooltip, .vega-tooltip * {{ background: #0F1116 !important; color: var(--text) !important; border-color: var(--border) !important; }}

      /* ---------- FORMS / SMALL LABELS ---------- */
      label, .st-emotion-cache-1cypcdb, .st-emotion-cache-1qg05tj {{ color: var(--muted) !important; }}

      /* ---------- SCROLLBARS ---------- */
      *::-webkit-scrollbar {{ width: 10px; height: 10px; }}
      *::-webkit-scrollbar-thumb {{ background: #2A2F36; border-radius: 8px; }}
      *::-webkit-scrollbar-track {{ background: #0B0D12; }}

      /* Vega container — no white behind charts */
      .vega-embed, .stAltairChart {{ background: transparent !important; }}

      /* =========================================================
         ADD-ONS FOR YOUR THREE REQUESTS
         ========================================================= */

      /* 1) TABLE HEADER ROW — very subtle grey, no white */
      /* st.dataframe */
      [data-testid="stDataframe"] thead,
      [data-testid="stDataframe"] thead tr,
      [data-testid="stDataframe"] thead th {{
        background: #11151C !important;
        color: var(--text) !important;
        border-bottom: 1px solid #2A2F36 !important;
      }}
      /* st.table */
      :where([data-testid="stTable"]) thead,
      :where([data-testid="stTable"]) thead tr,
      :where([data-testid="stTable"]) thead th {{
        background: #11151C !important;
        color: var(--text) !important;
        border-bottom: 1px solid #2A2F36 !important;
      }}
      /* st.data_editor header (glide-data-grid uses role=columnheader) */
      :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"] {{
        background: #11151C !important;
        color: var(--text) !important;
        border-bottom: 1px solid #2A2F36 !important;
      }}

      /* 2) SELECTS / INPUTS — red outline on focus, no white interiors */
      [data-baseweb="select"],
      [data-baseweb="input"] {{
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        background: #0F1116 !important;
      }}
      /* kill the inner white containers some themes add */
      [data-baseweb="select"] *, [data-baseweb="input"] * {{
        background: transparent !important;
      }}
      /* focus ring */
      [data-baseweb="select"]:focus-within,
      [data-baseweb="input"]:focus-within {{
        border-color: #C63C41 !important;
        box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important;
      }}
      /* placeholder color */
      [data-baseweb="input"] input::placeholder {{ color: var(--muted) !important; }}

      /* 3) SEGMENTED CONTROLS — no white for unselected/disabled */
      div[data-testid="stSegmentedControl"] div[role="tablist"] {{
        background: #0E1015 !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
      }}
      /* unselected */
      div[data-testid="stSegmentedControl"] button[role="tab"][aria-selected="false"] {{
        background: transparent !important; color: var(--muted) !important; border: 1px solid transparent !important;
      }}
      /* selected */
      div[data-testid="stSegmentedControl"] button[role="tab"][aria-selected="true"] {{
        background: #12151C !important; color: var(--text) !important; border: 1px solid #C63C41 !important; box-shadow: inset 0 0 0 1px #C63C41 !important;
      }}
      /* disabled (e.g., Equal-weighted when AUM-weighted selected) */
      div[data-testid="stSegmentedControl"] button[role="tab"][disabled] {{
        background: #151923 !important; color: #7E8A98 !important; border-color: #2A2F36 !important; opacity: 1 !important;
      }}

      /* Top-level tabs “Dashboard / Report” — remove any white fill */
      .stTabs [data-baseweb="tab-list"] {{ background: #0E1015 !important; border-bottom: 1px solid var(--border) !important; }}
      .stTabs [data-baseweb="tab"] {{ background: transparent !important; color: var(--muted) !important; border-color: transparent !important; box-shadow: none !important; }}
      .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: var(--text) !important; border-color: transparent !important; box-shadow: inset 0 -2px 0 #C63C41 !important; }}
      <style>
/* ===============================
   A) TABLE HEADERS — subtle grey
   =============================== */
div[data-testid="stDataframe"] thead tr th,
:where([data-testid="stTable"]) thead th,
:where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"] {{
  background: #11151C !important;      /* very subtle grey */
  color: var(--text) !important;
  border-bottom: 1px solid #2A2F36 !important;
}}

/* ===============================================
   B) FILTERS & "CHOOSE OPTIONS" — red outline
   Target the INNER BaseWeb wrapper (first child)
   =============================================== */

/* SELECT / MULTISELECT (ETF / Classification / Any …) */
[data-baseweb="select"] > div {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
[data-baseweb="select"] > div:hover {{
  border-color: #2A2F36 !important;
}}
[data-baseweb="select"] > div:focus-within {{
  border-color: #C63C41 !important;                       /* red border */
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important;  /* red focus ring */
}}
/* Clear inner sub-wrappers that sometimes inject white */
[data-baseweb="select"] > div * {{
  background: transparent !important;
}}

/* TEXT INPUT (Search “Type to filter…”) */
[data-baseweb="input"] > div {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
[data-baseweb="input"] > div:focus-within {{
  border-color: #C63C41 !important;
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important;
}}
[data-baseweb="input"] input::placeholder {{ color: var(--muted) !important; }}

/* ==========================================================
   C) SEGMENTED CONTROLS — no white pills anywhere
      (Dashboard/Report + AUM-weighted/Equal-weighted)
   ========================================================== */
div[data-testid="stSegmentedControl"] div[role="tablist"] {{
  background: #0E1015 !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
div[data-testid="stSegmentedControl"] button[role="tab"] {{
  background: #0E1015 !important;               /* remove white */
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;   /* subtle outline */
  box-shadow: none !important;
}}
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
  background: #12151C !important;
  color: var(--text) !important;
  border-color: #C63C41 !important;             /* red active */
  box-shadow: inset 0 0 0 1px #C63C41 !important;
}}
div[data-testid="stSegmentedControl"] button[aria-disabled="true"] {{
  background: #151923 !important;               /* keep dark, not white */
  color: #6B7280 !important;                    /* muted text */
  border-color: var(--border) !important;
  opacity: 1 !important;                        /* avoid BaseWeb fade + white */
  box-shadow: none !important;
}}
div[data-testid="stSegmentedControl"] button[role="tab"]:focus-visible {{
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important; /* keyboard focus */
}}

/* ===============================
   A) TABLE HEADERS — subtle grey
   =============================== */
div[data-testid="stDataframe"] thead tr th,
:where([data-testid="stTable"]) thead th,
:where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"] {{
  background: #11151C !important;      /* very subtle grey */
  color: var(--text) !important;
  border-bottom: 1px solid #2A2F36 !important;
}}

/* ===============================================
   B) FILTERS & "CHOOSE OPTIONS" — red outline
   Target the INNER BaseWeb wrapper (first child)
   =============================================== */

/* SELECT / MULTISELECT (ETF / Classification / Any …) */
[data-baseweb="select"] > div {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
[data-baseweb="select"] > div:hover {{
  border-color: #2A2F36 !important;
}}
[data-baseweb="select"] > div:focus-within {{
  border-color: #C63C41 !important;                       /* red border */
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important;  /* red focus ring */
}}
/* Clear inner sub-wrappers that sometimes inject white */
[data-baseweb="select"] > div * {{
  background: transparent !important;
}}

/* TEXT INPUT (Search “Type to filter…”) */
[data-baseweb="input"] > div {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
[data-baseweb="input"] > div:focus-within {{
  border-color: #C63C41 !important;
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important;
}}
[data-baseweb="input"] input::placeholder {{ color: var(--muted) !important; }}

/* ==========================================================
   C) SEGMENTED CONTROLS — no white pills anywhere
      (Dashboard/Report + AUM-weighted/Equal-weighted)
   ========================================================== */
div[data-testid="stSegmentedControl"] div[role="tablist"] {{
  background: #0E1015 !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}
div[data-testid="stSegmentedControl"] button[role="tab"] {{
  background: #0E1015 !important;               /* remove white */
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;   /* subtle outline */
  box-shadow: none !important;
}}
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
  background: #12151C !important;
  color: var(--text) !important;
  border-color: #C63C41 !important;             /* red active */
  box-shadow: inset 0 0 0 1px #C63C41 !important;
}}
div[data-testid="stSegmentedControl"] button[aria-disabled="true"] {{
  background: #151923 !important;               /* keep dark, not white */
  color: #6B7280 !important;                    /* muted text */
  border-color: var(--border) !important;
  opacity: 1 !important;                        /* avoid BaseWeb fade + white */
  box-shadow: none !important;
}}
div[data-testid="stSegmentedControl"] button[role="tab"]:focus-visible {{
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(198,60,65,0.28) !important; /* keyboard focus */
}}

</style>

    </style>
    """,
    unsafe_allow_html=True,
)


def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

def gap(px=6):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

# ---------- NEW: Dark styler for tables inside the iframe ----------
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

# Read-only, theme-aware grid helper (replaces st.dataframe)
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
def load_scenario_progress():        return load_csv(3, "scenario_progress.csv")
@st.cache_data(show_spinner=False)
def load_covariance_2025():          return load_csv(3, "covariance_2025.csv")
@st.cache_data(show_spinner=False)
def load_returns_top_per_etf_2025(): return load_csv(3, "returns_top_per_etf_2025.csv")

@st.cache_data(show_spinner=False)
def load_universe_2025_xlsx():
    # Try local first
    lp = local_path(3, "universe_2025.xlsx")
    try:
        if lp and os.path.exists(lp):
            return pd.read_excel(lp)
    except:
        pass
    # GitHub raw fallback
    raw_url = github_raw_url(3, "universe_2025.xlsx")
    try:
        return pd.read_excel(raw_url)
    except Exception:
        # GitHub API fallback (requires Accept header)
        api_url = github_api_url(3, "universe_2025.xlsx")
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        import io
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
# RENDERER FOR TAB 3 (Tradeoff Scenarios) — clean, visual-first
# -------------------------
def render_tradeoffs():
    import numpy as np
    import pandas as pd
    import altair as alt
    import streamlit as st

    st.subheader("Tradeoff Scenarios")
    st.caption("Pick an ETF and compare three scenarios side-by-side: "
               "portfolio composition, performance, and tracking error. Baseline is highlighted.")

    # ---------- Load data ----------
    try:
        metr = load_scenario_metrics()
    except Exception as e:
        st.error(f"Could not load scenario_portfolio_metrics.csv: {e}")
        st.stop()

    if metr is None or metr.empty:
        st.warning("Scenario metrics file is empty.")
        st.stop()

    # ---------- Helpers ----------
    def pick(df, *cands):
        """Fuzzy pick a column: returns the first column whose lowercase name contains any candidate."""
        cand_l = [c.lower() for c in cands]
        for col in df.columns:
            lc = col.lower()
            if any(c in lc for c in cand_l):
                return col
        return None

    # Flexible schema (works with your current file)
    scen_col  = pick(metr, "scenario_id", "scenario", "name")
    etf_col   = pick(metr, "etf_ticker", "etf")
    wt_col    = pick(metr, "weighting", "scope", "mode")  # we’ll show whatever exists
    te_col    = pick(metr, "tracking_error", "te")
    r_col     = pick(metr, "ann_return", "return")
    v_col     = pick(metr, "ann_vol", "vol")

    c_base    = pick(metr, "pct_clean_base")
    k_base    = pick(metr, "pct_contro_base", "pct_controversial_base")
    o_base    = pick(metr, "pct_other_base")

    c_scn     = pick(metr, "pct_clean_scn")
    k_scn     = pick(metr, "pct_contro_scn", "pct_controversial_scn")
    o_scn     = pick(metr, "pct_other_scn")

    # Minimum fields we need to draw core charts
    needed = [scen_col, etf_col, wt_col, c_base, c_scn]
    if any(x is None for x in needed):
        st.error("scenario_portfolio_metrics.csv is missing required columns. "
                 "Needed (fuzzy): scenario, etf, weighting/scope, pct_clean_base, pct_clean_scn.")
        # Quick data-health peek so you can map/rename externally if needed
        with st.expander("Data health (debug)"):
            st.write("Columns:", list(metr.columns))
        st.stop()

    # Normalize numbers
    def num(s):
        return pd.to_numeric(s, errors="coerce")

    # Detect Baseline rows
    def is_baseline(series):
        return series.astype(str).str.lower().str.startswith("baseline")

    metr = metr.copy()
    metr["_is_baseline"] = is_baseline(metr[scen_col])

    # ---------- Controls ----------
    etfs = sorted(metr[etf_col].dropna().astype(str).unique())
    sel_etf = st.selectbox("ETF", etfs, index=0)

    wts_raw = metr[wt_col].dropna().astype(str).unique().tolist()
    # Keep the selector even if there’s only one — it explains the scope clearly
    sel_wt = st.selectbox("Weighting", sorted(wts_raw), index=0,
                          help="Whatever is in your data (e.g., 'etf', 'aggregate', 'AUM', 'EW').")

    # Filter by ETF + weighting/scope
    m = metr[(metr[etf_col].astype(str) == str(sel_etf)) & (metr[wt_col].astype(str) == str(sel_wt))].copy()

    if m.empty:
        st.warning("No rows for this ETF/weighting.")
        st.stop()

    # Scenario dropdown: choose up to TWO scenarios to compare with Baseline
    av_scen = m[scen_col].dropna().astype(str).unique().tolist()
    base_name = next((s for s in av_scen if s.lower().startswith("baseline")), None)
    non_base = [s for s in av_scen if s != base_name]

    # sensible defaults: 2 scenarios if available
    default_choices = non_base[:2] if len(non_base) >= 2 else non_base[:1]
    sel_scenarios = st.multiselect("Scenarios", non_base, default=default_choices,
                                   help="Pick up to two scenarios to compare against Baseline.")
    sel_scenarios = sel_scenarios[:2]  # hard cap at 2

    # ---------- Color & style ----------
    color_baseline = "#8C93A6"   # muted steel (highlight via stroke & label)
    color_s1       = "#0E8F66"   # clean green
    color_s2       = "#C63C41"   # contro red
    stack_colors   = ["#0E8F66", "#C63C41", "#768397"]  # Clean / Contro / Other

    # ---------- Build tidy data for charts ----------
    # One row in m per (scenario, ETF, weighting). Use *_base for baseline, *_scn for scenarios.
    # Composition long frame: columns -> ['view','category','value']
    comp_rows = []

    def add_comp_row(view_label, clean, contro, other):
        comp_rows.extend([
            {"view": view_label, "category": "Clean",         "value": clean},
            {"view": view_label, "category": "Controversial", "value": contro if contro is not None else 0.0},
            {"view": view_label, "category": "Other",         "value": other if other is not None else 0.0},
        ])

    # Baseline row(s) (usually one)
    mb = m[m["_is_baseline"]].copy()
    if not mb.empty:
        # If multiple baselines exist (e.g., param sweeps), take the first
        b = mb.iloc[0]
        add_comp_row("Baseline", num(b[c_base]), num(b[k_base]) if k_base else 0.0, num(b[o_base]) if o_base else 0.0)

    # Selected scenarios
    scen_te_rows = []   # for TE bar chart
    perf_rows = []      # for return/vol (if present)
    labels = []         # ordering for charts

    labels.append("Baseline")
    for i, s in enumerate(sel_scenarios):
        ms = m[m[scen_col].astype(str) == s]
        if ms.empty:
            continue
        r = ms.iloc[0]
        label = str(s)
        labels.append(label)
        add_comp_row(label, num(r[c_scn]), num(r[k_scn]) if k_scn else 0.0, num(r[o_scn]) if o_scn else 0.0)

        scen_te_rows.append({"Scenario": label, "TE": float(num(r[te_col]).fillna(0).iloc[0]) if te_col in m.columns else 0.0})

        if r_col in m.columns or v_col in m.columns:
            perf_rows.append({
                "Scenario": label,
                "Return": float(num(r[r_col]).fillna(np.nan).iloc[0]) if r_col in m.columns else np.nan,
                "Vol":    float(num(r[v_col]).fillna(np.nan).iloc[0]) if v_col in m.columns else np.nan,
            })

    # TE for baseline is 0 by definition
    scen_te_rows.insert(0, {"Scenario": "Baseline", "TE": 0.0})

    comp_df = pd.DataFrame(comp_rows)
    te_df   = pd.DataFrame(scen_te_rows)
    perf_df = pd.DataFrame(perf_rows)

    # Ensure view ordering
    comp_df["view"] = pd.Categorical(comp_df["view"], categories=labels, ordered=True)
    te_df["Scenario"] = pd.Categorical(te_df["Scenario"], categories=labels, ordered=True)
    if not perf_df.empty:
        perf_df["Scenario"] = pd.Categorical(perf_df["Scenario"], categories=labels, ordered=True)

    # ---------- KPI Row (Clean %) ----------
    k1, k2, k3, k4 = st.columns([0.25, 0.25, 0.25, 0.25])
    def big_kpi(container, title, value, tone="neutral"):
        tone_class = {"green":"kpi-green","red":"kpi-red","neutral":"kpi-neutral"}.get(tone, "kpi-neutral")
        container.markdown(
            f"""
            <div class="kpi {tone_class}">
              <div class="label">{title}</div>
              <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Extract clean% for KPIs
    def clean_from_view(v):
        s = comp_df[(comp_df["view"] == v) & (comp_df["category"] == "Clean")]["value"]
        return float(s.iloc[0]) if len(s) else np.nan

    base_clean = clean_from_view("Baseline")
    big_kpi(k1, "% Clean — Baseline", f"{base_clean:.1f}%" if pd.notna(base_clean) else "–", "neutral")

    if len(sel_scenarios) >= 1:
        s1_clean = clean_from_view(sel_scenarios[0])
        delta1 = s1_clean - base_clean if pd.notna(s1_clean) and pd.notna(base_clean) else np.nan
        big_kpi(k2, f"% Clean — {sel_scenarios[0]}", f"{s1_clean:.1f}%"
               + (f" ({delta1:+.1f} pp)" if pd.notna(delta1) else ""), "green" if (pd.notna(delta1) and delta1>=0) else "red")

    if len(sel_scenarios) >= 2:
        s2_clean = clean_from_view(sel_scenarios[1])
        delta2 = s2_clean - base_clean if pd.notna(s2_clean) and pd.notna(base_clean) else np.nan
        big_kpi(k3, f"% Clean — {sel_scenarios[1]}", f"{s2_clean:.1f}%"
               + (f" ({delta2:+.1f} pp)" if pd.notna(delta2) else ""), "green" if (pd.notna(delta2) and delta2>=0) else "red")

    # Show TE of *last selected* scenario in KPI 4 (quick glance)
    sel_te = None
    if not te_df.empty and len(sel_scenarios):
        last = sel_scenarios[-1]
        v = te_df.loc[te_df["Scenario"] == last, "TE"]
        if len(v):
            sel_te = float(v.iloc[0])
    big_kpi(k4, "Cost — Tracking Error (ann. %)", f"{(sel_te or 0):.2f}%" if sel_te is not None else "–",
            "red" if (sel_te or 0) > 0 else "neutral")

    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

    # ---------- Composition — Baseline vs Scenarios ----------
    st.markdown("**Composition — Baseline vs Scenarios**")

    comp_color = alt.Scale(
        domain=["Clean", "Controversial", "Other"],
        range=stack_colors
    )
    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar(opacity=0.95)
        .encode(
            x=alt.X("view:N", title=None, sort=labels),
            y=alt.Y("value:Q", stack="normalize",
                    title="Portfolio share",
                    axis=alt.Axis(format="%")),
            color=alt.Color("category:N", title=None, scale=comp_color),
            tooltip=[
                alt.Tooltip("view:N", title="Scenario"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("value:Q", title="Share (%)", format=".1f"),
            ],
        )
        .properties(height=280)
    )
    # Outline baseline
    baseline_rule = (
        alt.Chart(pd.DataFrame({"view":["Baseline"]}))
        .mark_rule(stroke=color_baseline, strokeWidth=2)
        .encode(x="view:N")
    )
    st.altair_chart(comp_chart, use_container_width=True)

    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

    # ---------- Performance (optional) ----------
    st.markdown("**Performance — annualized return & volatility**")
    if perf_df.empty or (perf_df[["Return","Vol"]].isna().all().all()):
        st.info("Return/vol not provided in the dataset for these scenarios.")
    else:
        # Two small aligned bars: Return and Vol
        left, right = st.columns(2)
        with left:
            ch_r = (
                alt.Chart(perf_df)
                .mark_bar()
                .encode(
                    x=alt.X("Scenario:N", sort=labels, title=None),
                    y=alt.Y("Return:Q", title="Return (ann. %)", axis=alt.Axis(format=".1f")),
                    color=alt.Color("Scenario:N", legend=None,
                                    scale=alt.Scale(domain=labels,
                                                    range=[color_baseline, color_s1, color_s2][:len(labels)])),
                    tooltip=[alt.Tooltip("Scenario:N"), alt.Tooltip("Return:Q", title="Return", format=".2f")]
                )
                .properties(height=250)
            )
            st.altair_chart(ch_r, use_container_width=True)
        with right:
            ch_v = (
                alt.Chart(perf_df)
                .mark_bar()
                .encode(
                    x=alt.X("Scenario:N", sort=labels, title=None),
                    y=alt.Y("Vol:Q", title="Volatility (ann. %)", axis=alt.Axis(format=".1f")),
                    color=alt.Color("Scenario:N", legend=None,
                                    scale=alt.Scale(domain=labels,
                                                    range=[color_baseline, color_s1, color_s2][:len(labels)])),
                    tooltip=[alt.Tooltip("Scenario:N"), alt.Tooltip("Vol:Q", title="Vol", format=".2f")]
                )
                .properties(height=250)
            )
            st.altair_chart(ch_v, use_container_width=True)

    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

    # ---------- Cost (Tracking Error) ----------
    tr_title = (
        '<div class="chart-head">'
        '<div class="chart-title">Cost — Tracking Error (ann. %)</div>'
        '<div class="info-badge has-tip" '
        'data-tip="Tracking error measures how much a scenario’s returns deviate from the baseline (or benchmark) on average. '
        'Higher TE = more index deviation.">'
        'i</div></div>'
    )
    st.markdown(tr_title, unsafe_allow_html=True)

    te_chart = (
        alt.Chart(te_df)
        .mark_bar()
        .encode(
            x=alt.X("Scenario:N", sort=labels, title=None),
            y=alt.Y("TE:Q", title="Tracking Error (ann. %)", axis=alt.Axis(format=".2f")),
            color=alt.Color("Scenario:N", legend=None,
                            scale=alt.Scale(domain=labels,
                                            range=[color_baseline, color_s1, color_s2][:len(labels)])),
            tooltip=[alt.Tooltip("Scenario:N"), alt.Tooltip("TE:Q", title="TE", format=".2f")],
        )
        .properties(height=260)
    )
    st.altair_chart(te_chart, use_container_width=True)

    # ---------- (Optional) small note for storyline) ----------
    st.caption(
        "Storyline: Compare **composition first** to see where the weight sits (Clean vs Controversial vs Other), "
        "then check **performance (return & vol)** if available, and finally the **cost** you pay "
        "in Tracking Error. Baseline is the anchor; scenarios show tradeoffs."
    )




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
