# app.py — BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
# Clean dark UI, single file, no emojis. As-of date shows only if we have day+month+year.
# "Dashboard / Report" switch appears after the description and before the tabs.

import os
import re
import pandas as pd
import streamlit as st

# --------------------------------
# CONFIG
# --------------------------------
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution, Tradeoffs",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

CONTEXT_SUMMARY_PATH = "/mnt/data/context_summary_2025.csv"  # update if needed

COLORS = {
    "bg": "#0A0B0D",
    "card": "#111318",
    "border": "#1E2228",
    "text": "#E7EBF0",
    "muted": "#9AA4B2",
    "primary": "#00A3FF",
    "clean": "#16C784",
    "contro": "#EF4444",
    "other": "#7B8A9A",
    "focus": "#1F6FEB",
}

# --------------------------------
# STYLES (inline CSS)
# --------------------------------
st.markdown(
    f"""
    <style>
      :root {{
        --bg: {COLORS['bg']};
        --card: {COLORS['card']};
        --border: {COLORS['border']};
        --text: {COLORS['text']};
        --muted: {COLORS['muted']};
        --primary: {COLORS['primary']};
      }}
      html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
      }}
      h1, h2, h3, h4, h5 {{ color: var(--text); }}
      .blx-divider {{ border-top: 1px solid var(--border); margin: 10px 0 24px 0; }}
      .blx-muted {{ color: var(--muted); }}
      .blx-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 16px;
      }}
      /* Selected tab underline color */
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-color: var(--primary) !important;
      }}
      /* Footer links */
      .blx-footer a {{ color: var(--text) !important; opacity: 0.9; text-decoration: none; }}
      .blx-footer a:hover {{ opacity: 1; text-decoration: underline; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------
# HELPERS
# --------------------------------
def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

def read_as_of_display():
    """
    Try to read an as-of date from context_summary_2025.csv.
    Only return a formatted date if the original string clearly includes day+month+year.
    Otherwise return None (we hide the as-of).
    """
    if not os.path.exists(CONTEXT_SUMMARY_PATH):
        return None
    try:
        df = pd.read_csv(CONTEXT_SUMMARY_PATH)
        cols = {c.lower(): c for c in df.columns}
        src_col = cols.get("as_of_date") or cols.get("as_of") or cols.get("asof")
        if not src_col:
            return None
        raw = str(df[src_col].dropna().astype(str).iloc[0]).strip()
        # Require pattern that contains day + month + year
        if not re.search(r"\b\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}}\b", raw) and not re.search(r"\b\d{{1,2}}[-/]\d{{1,2}}[-/]\d{{2,4}}\b", raw):
            return None
        dt = pd.to_datetime(raw, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.strftime("%d %b %Y")  # e.g., 12 Oct 2025
    except Exception:
        return None

# --------------------------------
# HEADER
# --------------------------------
as_of_display = read_as_of_display()

hdr_left, hdr_right = st.columns([0.72, 0.28], gap="large")
with hdr_left:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; gap:6px;">
          <h2 style="margin:0; font-weight:800; letter-spacing:0.1px;">
            BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
          </h2>
          <div class="blx-muted" style="max-width:1100px;">
            This application analyzes 20 BlackRock ESG-labelled ETFs using a single 2025 ESG map (Clean200 plus controversial screens).
            It provides a 2025 point-in-time snapshot of Clean vs Controversial vs Other exposure, a retroactive view of how those exposures
            evolved from 2017 to 2025, and a tradeoff experiment that simulates cleaner portfolios and quantifies the cost in tracking error,
            active share, and diversification relative to current benchmarks.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hdr_right:
    if as_of_display:
        st.markdown(
            f"""
            <div style="text-align:right; margin-bottom:8px;">
              <span class="blx-muted">As of:&nbsp;</span>
              <span style="font-weight:600;">{as_of_display}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

divider()

# --------------------------------
# VIEW SWITCH (moved here: after description, before tabs)
# --------------------------------
mode = st.segmented_control(
    "View",
    options=["Dashboard", "Report"],
    default="Dashboard",
    label_visibility="collapsed",
    help="Switch between the interactive dashboard and a short report",
)

divider()

# --------------------------------
# BODY
# --------------------------------
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Lab"])

    # ---------- 2025 OVERVIEW ----------
    with tab1:
        st.subheader("2025 Overview")
        st.caption("Today’s composition and the names/screens that drive it.")
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.markdown('<div class="blx-card">100% stacked bar — 2025 composition</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">By-screen bars — Fossil, Weapons, Tobacco, Prisons, Deforestation</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="blx-card">Spotlight — Top 10 Controversial (by AUM contribution)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Spotlight — Top 10 Clean (by AUM contribution)</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="blx-card">Holdings Explorer — filterable ETF × holding table</div>', unsafe_allow_html=True)

    # ---------- CHANGE SINCE 2017 ----------
    with tab2:
        st.subheader("Change since 2017")
        st.caption("How exposures moved over time, by fund and in aggregate.")
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.markdown('<div class="blx-card">Trend — % Clean over time (EW/AUM)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Heatmap — Fund × Year by % Controversial (toggle % Clean)</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="blx-card">Trend — % Controversial over time (EW/AUM)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Two stacked bars — 2017 vs 2025 (Clean/Controversial/Other) + Movers table</div>', unsafe_allow_html=True)

    # ---------- TRADEOFF LAB ----------
    with tab3:
        st.subheader("Tradeoff Lab")
        st.caption("Baseline vs cleaner scenarios, measuring cost (TE) vs benefit (% Clean).")
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.markdown('<div class="blx-card">Scenario KPIs — % Clean, % Controversial, TE, Active Share, Drift</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Side-by-side 100% bars — Baseline vs Scenario composition</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="blx-card">Mini frontier — x: TE, y: % Clean (point = ETF)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">Movers — adds/drops/ups/downs vs baseline</div>', unsafe_allow_html=True)

else:
    # ---------------- REPORT ----------------
    st.subheader("Project Overview (Short Report)")
    st.markdown(
        """
**Purpose**  
Assess how BlackRock’s ESG-labelled ETFs align with a consistent 2025 ESG classification, how that alignment has **changed from 2017 to 2025**, and what it **costs to push portfolios cleaner**.

**Method (high level)**  
1) Standardize 2025 holdings for 20 ETFs; tag Clean200 and controversial screens.  
2) Apply the same map retroactively to 2017–2025 holdings to measure change.  
3) Simulate cleaner portfolios (tilt and exclusion) and estimate tracking error with a covariance matrix.

**How to read this app**  
Use the three tabs on the **Dashboard**: *2025 Overview*, *Change since 2017*, and *Tradeoff Lab*.
        """
    )

# --------------------------------
# FOOTER
# --------------------------------
divider()
f1, f2, f3, f4 = st.columns([0.5, 0.16, 0.16, 0.18])
with f1:
    st.caption("Built by **Nitya Arya**")
with f2:
    st.markdown('<div class="blx-footer"><a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a></div>', unsafe_allow_html=True)
with f3:
    st.markdown('<div class="blx-footer"><a href="https://github.com/nitya-ar" target="_blank">GitHub</a></div>', unsafe_allow_html=True)
with f4:
    st.markdown('<div class="blx-footer"><a href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank"><strong>Send Feedback</strong></a></div>', unsafe_allow_html=True)
