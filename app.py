# app.py — BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
# Clean dark UI, single file. No emojis. Title & description span full width.
# "Dashboard / Report" switch appears after the description and before the tabs.

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

def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

# --------------------------------
# HEADER (full-width)
# --------------------------------
st.markdown(
    """
    <div style="display:flex; flex-direction:column; gap:8px;">
      <h2 style="margin:0; font-weight:800; letter-spacing:0.1px;">
        BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
      </h2>
      <div class="blx-muted" style="max-width:1400px;">
        Study of 20 BlackRock ESG-labelled ETFs. One 2025 ESG map (Clean200 plus controversial screens) is applied consistently
        to every fund and every year. The dashboard shows three things: (1) a 2025 snapshot of how ETF dollars are split across
        Clean, Controversial, and Other; (2) how those exposures changed from 2017 to 2025; and (3) a tradeoff experiment that
        pushes the portfolios cleaner and reports the cost in tracking error, active share, and diversification relative to the benchmark.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

divider()

# --------------------------------
# VIEW SWITCH (below description, before tabs)
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
Assess how BlackRock’s ESG-labelled ETFs align with a consistent 2025 ESG classification, how that alignment **changed from 2017 to 2025**, and what it **costs to push portfolios cleaner**.

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
