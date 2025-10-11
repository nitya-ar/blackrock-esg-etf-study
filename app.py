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
    initial_sidebar_state="expanded",
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
        html, body, [class^="css"]  {{ background-color: {BG} !important; }}
        .block-container {{ padding-top: 0.8rem; padding-bottom: 1.6rem; color: {TEXT}; max-width: 1400px; }}
        .app-header {{ display:flex; align-items:center; justify-content:space-between; }}
        .title-wrap h1 {{ margin:0; font-size: 24px; font-weight: 700; letter-spacing:.2px; }}
        .title-wrap p {{ margin:.25rem 0 0 0; color:{MUTED}; font-size:13px; }}
        .panel {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; }}
        .pill {{ display:inline-block; padding:6px 10px; border-radius:100px; border:1px solid {BORDER}; color:{MUTED}; font-size:13px; margin-right:6px; }}
        .footer {{ color:{TEXT}; text-align:center; margin-top:28px; padding-top:18px; border-top:1px solid {BORDER}; }}
        .tab-title {{ font-size:18px; font-weight:700; margin-bottom:6px; }}
        .subtle {{ color:{MUTED}; font-size:14px; }}
        .kpi {{ display:flex; align-items:center; justify-content:center; height:92px; background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; font-size:18px; color:{TEXT};}}
        hr.divider {{ border:0; border-top:1px solid {BORDER}; opacity:.6; margin: 8px 0 12px 0; }}
        .footer a {{ text-decoration:none; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header (ultra compact)
# -----------------------------
st.markdown(
    """
    <div class="app-header">
        <div class="title-wrap">
            <h1>Exploring BlackRock’s ESG ETFs</h1>
            <p>Alignment, evolution, and tradeoffs (2017–2025)</p>
        </div>
    </div>
    <hr class='divider'>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Left Sidebar: Navigation + Quick Context
# -----------------------------
with st.sidebar:
    st.markdown("<div style='font-weight:700; font-size:14px; letter-spacing:.2px;'>Navigation</div>", unsafe_allow_html=True)
    view = st.radio("", ["Report (Context)", "Dashboard"], index=0, label_visibility="collapsed")
    st.markdown("<div style='margin:10px 0; height:1px; background:#2A2F36;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-weight:700; font-size:14px; letter-spacing:.2px;'>Dashboard Sections</div>", unsafe_allow_html=True)
    section = st.radio("", ["2025 Overview", "Change since 2017", "Tradeoff Experiment"], index=0, label_visibility="collapsed")
    st.markdown("<div style='margin:10px 0; height:1px; background:#2A2F36;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-weight:700; font-size:14px; letter-spacing:.2px;'>Legend</div>", unsafe_allow_html=True)
    st.markdown("<span class='pill'>Clean = <span style='color:#00D38D'>Green</span></span>", unsafe_allow_html=True)
    st.markdown("<span class='pill'>Controversial = <span style='color:#FF5C5C'>Red</span></span>", unsafe_allow_html=True)
    st.markdown("<span class='pill'>Other = Blue‑grey</span>", unsafe_allow_html=True)

# -----------------------------
# Compact overview banner (collapsible)
# -----------------------------
with st.expander("Project Overview (summary)", expanded=False):
    st.markdown(
        """
        <div class='subtle'>This study combines standardized ETF holdings (2017–2025) with the 2025 clean/controversial map and AUM to show: a 2025 snapshot, the change since 2017, and a tradeoff experiment that pushes portfolios cleaner under realistic risk constraints. Screen categories may overlap; ETF weights are re‑normalized to 100%.</div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Routing: Report first by default
# -----------------------------
if view == "Dashboard":
    if section == "2025 Overview":
        st.markdown("<div class='tab-title'>2025 Overview</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for c in (c1, c2, c3, c4):
            with c:
                st.markdown("<div class='kpi'>KPI</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Stacked bar — 2025 composition (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>By screen category bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Spotlight Top 10 tables (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Holdings explorer table (placeholder)</div>", unsafe_allow_html=True)

    elif section == "Change since 2017":
        st.markdown("<div class='tab-title'>Change since 2017</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Trend — % Clean over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Trend — % Controversial over time (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Heatmap Fund×Year (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Year‑vs‑Year bars + Movers list (placeholder)</div>", unsafe_allow_html=True)

    else:  # Tradeoff Experiment
        st.markdown("<div class='tab-title'>Tradeoff Experiment</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'>Scenario KPI cards (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Baseline vs Scenario stacked bars (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Mini frontier: % Clean vs Tracking Error (placeholder)</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px;'>Movers table (placeholder)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='tab-title'>Report (Context First)</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='panel'>
            <h4 style='margin-top:0;'>Context</h4>
            <p>By 2025, BlackRock’s ESG‑labelled ETFs represent a substantial share of investor assets. This report frames how those portfolios align with a clean vs. controversial lens, how alignment evolved since 2017, and what changes when cleaner design choices are simulated under realistic constraints.</p>
            <h4>What’s Inside</h4>
            <ol>
                <li><b>2025 Snapshot</b> — composition, by‑screen exposure, top contributors, explorer.</li>
                <li><b>Change since 2017</b> — trends (EW/AUM), dispersion, fund×year heatmap, movers.</li>
                <li><b>Tradeoff Experiment</b> — baseline vs cleaner scenarios with Tracking Error, Active Share, drift.</li>
            </ol>
            <div style='margin-top:10px; display:flex; gap:8px;'>
                <a href='#' onclick="const r=document.querySelector('section.main'); window.scrollTo({top:0, behavior:'smooth'});" style='background:#00A3FF; color:#0B0C10; padding:8px 14px; border-radius:10px; text-decoration:none; font-weight:600;'>Go to Dashboard</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Footer (emphasize Feedback; no copyright)
# -----------------------------
st.markdown(
    """
    <div class='footer'>
        <div style='display:flex; align-items:center; justify-content:center; gap:24px;'>
            <a href='https://forms.gle/qid7S1eJpGCuYdtY8' target='_blank' style='font-size:17px; font-weight:700; color:#E6E9EF; text-decoration:none; border:1px solid #2A2F36; padding:8px 16px; border-radius:12px;'>Feedback</a>
            <a href='https://github.com/nitya-ar' target='_blank' style='font-size:15px; color:#E6E9EF; text-decoration:none;'>GitHub</a>
            <a href='https://www.linkedin.com/in/nitya-arya/' target='_blank' style='font-size:15px; color:#E6E9EF; text-decoration:none;'>LinkedIn</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
