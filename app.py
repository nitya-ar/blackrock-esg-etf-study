# streamlit run esg_dashboard_streamlit_layout.py
# Clean, modern layout scaffold for the BlackRock ESG ETFs project (no emojis, links only in footer)

import streamlit as st
from datetime import date

# -----------------------------
# Page & Theme
# -----------------------------
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution & Tradeoffs",
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

# Global CSS (sleek, modern, inspired by references)
st.markdown(
    f"""
    <style>
        html, body, [class^="css"]  {{
            background-color: {BG} !important;
        }}
        .block-container {{
            padding-top: 1.2rem; padding-bottom: 2rem; color: {TEXT};
        }}
        .app-header {{ display:flex; align-items:center; justify-content:space-between; }}
        .title-wrap h1 {{ margin:0; font-size: 28px; font-weight: 700; letter-spacing:.2px; }}
        .title-wrap p {{ margin:.25rem 0 0 0; color:{MUTED}; font-size:14px; }}
        .panel {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; }}
        .pill {{ display:inline-block; padding:6px 10px; border-radius:100px; border:1px solid {BORDER}; color:{MUTED}; font-size:13px; margin-right:6px; }}
        .footer {{ color:{MUTED}; text-align:center; margin-top:28px; padding-top:18px; border-top:1px solid {BORDER}; }}
        .tab-title {{ font-size:18px; font-weight:700; margin-bottom:6px; }}
        .subtle {{ color:{MUTED}; font-size:14px; }}
        .kpi {{ display:flex; align-items:center; justify-content:center; height:92px; background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; font-size:18px; color:{TEXT};}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header (minimal, no icons)
# -----------------------------
st.markdown(
    """
    <div class="app-header">
        <div class="title-wrap">
            <h1>Exploring BlackRock’s ESG ETFs</h1>
            <p>Alignment, evolution, and tradeoffs (2017–2025)</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Intro / Project Overview (third person)
# -----------------------------
st.markdown(
    f"""
    <div class="panel">
        <div class="tab-title">Project Overview</div>
        <p class="subtle">This project presents a clear, auditably‑sourced view of BlackRock’s ESG‑labelled ETFs. Using standardized 2017–2025 holdings, the 2025 clean/controversial classification map, and fund‑level AUM, it tells three parts of the story:</p>
        <ul>
            <li><b>2025 Snapshot:</b> How today’s ETF dollars split across Clean, Controversial, and Other — and which holdings drive the split.</li>
            <li><b>Change since 2017:</b> Applying the 2025 lens to past portfolios to show how exposure evolved (Equal‑Weighted and AUM‑Weighted views).</li>
            <li><b>Tradeoff Experiment:</b> Simulating cleaner portfolios through tilts and exclusions under a tracking‑error budget.</li>
        </ul>
        <p class="subtle">Screen categories can overlap (e.g., Fossil and Weapons). Per‑ETF weights are re‑normalized to 100% for consistency. Each charted number can be traced back to ETF × holding rows.</p>
        <div style="margin-top:10px;">
            <span class="pill">Clean = <span style=\"color:{GREEN}\">Green</span></span>
            <span class="pill">Controversial = <span style=\"color:{RED}\">Red</span></span>
            <span class="pill">Other = Blue‑grey</span>
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
                st.markdown("<div class='kpi'>KPI</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Stacked bar — 2025 composition (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>By screen category bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Spotlight Top 10 tables (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Holdings explorer table (placeholder)</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='tab-title'>Change since 2017</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Trend — % Clean over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Trend — % Controversial over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Heatmap Fund×Year (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Year‑vs‑Year bars + Movers list (placeholder)</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='tab-title'>Tradeoff Experiment</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Scenario KPI cards (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Baseline vs Scenario stacked bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Mini frontier: % Clean vs Tracking Error (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Movers table (placeholder)</div>", unsafe_allow_html=True)

# -----------------------------
# Report View (concise narrative only — methodology removed)
# -----------------------------
else:
    st.markdown("<div class='tab-title'>Report</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="panel">
            <h4 style="margin-top:0;">Context & Story</h4>
            <p>By 2025, BlackRock’s ESG‑labelled ETFs represent a substantial share of investor assets. This report frames how those portfolios align with a clean vs. controversial lens, how alignment evolved since 2017, and what changes when cleaner design choices are simulated under realistic constraints.</p>
            <h4>What’s Included</h4>
            <ol>
                <li><b>2025 Snapshot</b> — composition, screen exposure, top contributors, and a holdings explorer.</li>
                <li><b>Change since 2017</b> — trend views (EW/AUM), cross‑fund dispersion, fund×year heatmap, and largest movers.</li>
                <li><b>Tradeoff Experiment</b> — baseline vs cleaner scenarios with Tracking Error, Active Share, and drift.</li>
            </ol>
            <p class="subtle">Notes: screen categories may overlap; exposures are reported in percentage points; per‑ETF weights are re‑normalized to 100%.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Footer (links only here)
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
