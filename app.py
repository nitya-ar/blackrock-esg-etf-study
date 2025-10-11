# streamlit run esg_dashboard_streamlit_layout.py
# Clean, modern layout scaffold for the BlackRock ESG ETFs project

import streamlit as st
from datetime import date

# -----------------------------
# Page & Theme
# -----------------------------
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution & Tradeoffs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRIMARY = "#00A3FF"  # accent blue
GREEN = "#00D38D"     # clean
RED = "#FF5C5C"       # controversial
TEXT = "#E6E9EF"
BG = "#0B0C10"
PANEL = "#121419"
MUTED = "#9AA4B2"
BORDER = "#2A2F36"

# Global CSS (subtle, modern)
st.markdown(
    f"""
    <style>
        html, body, [class^="css"]  {{
            background-color: {BG} !important;
        }}
        .block-container {{
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            color: {TEXT};
        }}
        .app-header {{
            display:flex; align-items:center; justify-content:space-between;
            padding: 12px 18px; border: 1px solid {BORDER}; border-radius: 16px; background:{PANEL};
        }}
        .title-wrap h1 {{ margin: 0 0 4px 0; font-size: 28px; font-weight: 700; letter-spacing: .2px; }}
        .title-wrap p {{ margin: 0; color:{MUTED}; font-size: 14px; }}
        .iconbar a {{ text-decoration:none; margin-left: 14px; color:{TEXT}; opacity:.9; }}
        .icon {{ display:inline-flex; gap:8px; align-items:center; padding:8px 10px; border:1px solid {BORDER}; border-radius:12px; background:{BG};}}
        .panel {{ background:{PANEL}; border:1px solid {BORDER}; border-radius: 16px; padding:16px 18px; }}
        .pill {{ display:inline-block; padding:6px 10px; border-radius:100px; border:1px solid {BORDER}; color:{MUTED}; font-size:13px; margin-right:6px; }}
        .footer {{ color:{MUTED}; text-align:center; margin-top:28px; padding-top:18px; border-top:1px solid {BORDER}; }}
        .tab-title {{ font-size:18px; font-weight:700; margin-bottom:6px; }}
        .subtle {{ color:{MUTED}; font-size:14px; }}
        .cta {{ color:{TEXT}; background:{PRIMARY}; border: none; padding: 6px 12px; border-radius: 999px; font-weight:600; }}
        .badge {{ display:inline-block; padding:3px 8px; background:{BORDER}; border-radius:10px; color:{MUTED}; font-size:12px; margin-left:8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header
# -----------------------------
col1, col2 = st.columns([0.75, 0.25])
with col1:
    st.markdown(
        """
        <div class="app-header">
            <div class="title-wrap">
                <h1>Exploring BlackRock’s ESG ETFs</h1>
                <p>Alignment, evolution, and tradeoffs (2017–2025)</p>
            </div>
            <div class="iconbar">
                <a class="icon" href="https://github.com/nitya-ar" target="_blank">🧠 GitHub</a>
                <a class="icon" href="#methodology" >📘 Methodology</a>
                <a class="icon" href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank">✉️ Feedback</a>
                <a class="icon" href="https://www.linkedin.com/in/nitya-arya/" target="_blank">in LinkedIn</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown("""
        <div class="panel" style="text-align:right;">
            <div style="font-size:12px; color:#9AA4B2;">As of</div>
            <div style="font-size:18px; font-weight:700;">2025</div>
        </div>
    """, unsafe_allow_html=True)

st.empty()

# -----------------------------
# Intro / Project Overview (third person)
# -----------------------------
with st.container():
    st.markdown(
        f"""
        <div class="panel">
        <div class="tab-title">Project Overview</div>
        <p class="subtle">This project presents a clear, auditably-sourced look at BlackRock’s ESG‑labelled ETFs. Using standardized 2017–2025 holdings, today’s (2025) clean and controversial classifications, and fund‑level AUM, it answers three questions:</p>
        <ul>
            <li><b>2025 Snapshot:</b> How today’s ETF dollars split across Clean, Controversial, and Other — and which names drive those exposures.</li>
            <li><b>Change since 2017:</b> How those exposures evolved when applying 2025 rules to past portfolios, shown in both Equal‑Weighted and AUM‑Weighted views.</li>
            <li><b>Tradeoff Experiment:</b> What happens to risk and diversification if the portfolios are pushed cleaner via tilts and exclusions under a tracking‑error budget.</li>
        </ul>
        <p class="subtle">All screens can overlap (e.g., Fossil and Weapons); exposure totals are reported transparently with per‑ETF weights re‑normalized to 100% for consistency. Users can audit every charted number back to ETF × holding rows.</p>
        <div style="margin-top:10px;">
            <span class="pill">Clean = <span style="color:{GREEN}">Green</span></span>
            <span class="pill">Controversial = <span style="color:{RED}">Red</span></span>
            <span class="pill">Other = Blue‑grey</span>
            <span class="badge">Streamlit</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Primary Panel Switcher (Dashboard | Report)
# -----------------------------
view = st.segmented_control(
    "View",
    options=["Dashboard", "Report"],
    selection_mode="single",
    default="Dashboard",
)

# -----------------------------
# Dashboard Tabs (layout only; placeholders for charts)
# -----------------------------
if view == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Experiment"])

    with tab1:
        st.markdown("<div class='tab-title'>2025 Overview</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for c in (c1, c2, c3, c4):
            with c:
                st.markdown("<div class='panel'>KPI</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Stacked bar — 2025 composition (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>By screen category bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Spotlight Top 10 tables (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Holdings explorer table (placeholder)</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='tab-title'>Change since 2017</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Trend — % Clean over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Trend — % Controversial over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Heatmap Fund×Year (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Year-vs-Year bars + Movers list (placeholder)</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='tab-title'>Tradeoff Experiment</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Scenario KPI cards (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Baseline vs Scenario stacked bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Mini frontier: % Clean vs Tracking Error (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Movers table (placeholder)</div>", unsafe_allow_html=True)

# -----------------------------
# Report View (concise narrative; layout only)
# -----------------------------
else:
    st.markdown("<div class='tab-title'>Short Report</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel" id="methodology">
        <h4 style="margin-top:0;">Context</h4>
        <p>By 2025, BlackRock’s ESG‑branded ETFs are large and diverse. This study examines how those portfolios align with a clean vs. controversial framework and what changes over time and under stricter ESG constraints.</p>
        <h4>Data & Method (high‑level)</h4>
        <ul>
            <li>Standardized holdings for 2017–2025 with tickers, sectors, regions, and prices.</li>
            <li>Applied 2025 classifications (Clean200; Fossil, Tobacco, Weapons, Prisons, Deforestation) — categories may overlap.</li>
            <li>Weights re‑normalized to 100% per ETF; AUM used for dollar‑weighting; exposure in percentage points.</li>
            <li>Tradeoffs tested via tilts/exclusions under a covariance‑based tracking‑error budget.</li>
        </ul>
        <h4>What the Dashboard Shows</h4>
        <ol>
            <li><b>2025 Snapshot:</b> Composition, by‑screen exposure, top contributors, and full holdings explorer.</li>
            <li><b>Change since 2017:</b> Trends (EW/AUM), cross‑fund dispersion, heatmap by fund×year, and biggest movers.</li>
            <li><b>Tradeoff Experiment:</b> Baseline vs. cleaner scenarios with Tracking Error, Active Share, and drift.</li>
        </ol>
        <p class="subtle">Note: Screen categories overlap and are not intended to sum to overall controversial exposure.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Footer
# -----------------------------
st.markdown(
    f"""
    <div class="footer">
        <span>© {date.today().year} • BlackRock ESG ETFs — Alignment, Evolution & Tradeoffs</span><br/>
        <a href="https://github.com/nitya-ar" target="_blank">GitHub</a> · 
        <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a> · 
        <a href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank">Feedback</a>
    </div>
    """,
    unsafe_allow_html=True,
)
