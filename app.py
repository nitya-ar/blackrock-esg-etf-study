# app.py
# Streamlit layout shell for "BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)"
# One file. Clean dark UI. Header shows As-of near the title. Dashboard/Report switch above tabs.

import os
import pandas as pd
import streamlit as st

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution, Tradeoffs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Brand colors (BlackRock-ish, calm, professional)
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

# Optional: where your 2025 context CSV lives (for auto as-of)
CONTEXT_SUMMARY_PATH = "/mnt/data/context_summary_2025.csv"  # change if needed


# ----------------------------
# STYLES (inline CSS so it's truly single-file)
# ----------------------------
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
      /* nicer tabs underline color */
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-color: var(--primary) !important;
      }}
      /* segmented control minify spacing on top */
      div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stSegmentedControl"]) {{
        margin-bottom: 0.35rem;
      }}
      /* footer links */
      .blx-footer a {{
        color: var(--text) !important;
        opacity: 0.9;
        text-decoration: none;
      }}
      .blx-footer a:hover {{ opacity: 1; text-decoration: underline; }}
      /* subtle cards */
      .blx-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 16px;
      }}
      .blx-muted {{ color: var(--muted); }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# HELPERS
# ----------------------------
def get_as_of_date(default="2025"):
    """Try to read as_of_date from context_summary_2025.csv; fall back to default."""
    try:
        if os.path.exists(CONTEXT_SUMMARY_PATH):
            df = pd.read_csv(CONTEXT_SUMMARY_PATH)
            # accept either 'as_of_date' or 'as_of' in any case
            cols = {c.lower(): c for c in df.columns}
            col = cols.get("as_of_date") or cols.get("as_of")
            if col and not df[col].isna().all():
                # take the first non-null value
                val = df[col].dropna().astype(str).iloc[0]
                return val
    except Exception:
        pass
    return default


def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)


# ----------------------------
# HEADER
# ----------------------------
as_of = get_as_of_date()

h_left, h_right = st.columns([0.72, 0.28], gap="large")
with h_left:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; gap:6px;">
          <h2 style="margin:0; font-weight:800; letter-spacing:0.1px;">
            BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
          </h2>
          <div class="blx-muted" style="max-width:1100px;">
            Analysis of 20 ESG-labelled ETFs: 2025 snapshot, evolution since 2017,
            and a tradeoff experiment that pushes portfolios cleaner while measuring tracking error and diversification shifts.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_right:
    st.markdown(
        f"""
        <div style="text-align:right; margin-bottom:8px;">
          <span class="blx-muted">As of:&nbsp;</span>
          <span style="font-weight:600;">{as_of}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    mode = st.segmented_control(
        "View",
        options=["Dashboard", "Report"],
        default="Dashboard",
        label_visibility="collapsed",
        help="Switch between the interactive dashboard and a short report",
    )

divider()

# ----------------------------
# BODY
# ----------------------------
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Lab"])

    # -------- 2025 OVERVIEW --------
    with tab1:
        st.subheader("2025 Overview")
        st.caption("Today’s composition and the names/screens that drive it.")
        # Placeholders: add charts/tables later
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="blx-card">📊 100% stacked bar — 2025 composition</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">📈 By-screen bars — Fossil, Weapons, Tobacco, Prisons, Deforestation</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="blx-card">⭐ Spotlight — Top 10 Controversial (by AUM contribution)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">🌿 Spotlight — Top 10 Clean (by AUM contribution)</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="blx-card">🔍 Holdings Explorer — filterable ETF × holding table</div>', unsafe_allow_html=True)

    # -------- CHANGE SINCE 2017 --------
    with tab2:
        st.subheader("Change since 2017")
        st.caption("How exposures moved over time, by fund and in aggregate.")
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="blx-card">📈 Trend — % Clean over time (EW/AUM)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">🟪 Heatmap — Fund × Year by % Controversial (toggle % Clean)</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="blx-card">📉 Trend — % Controversial over time (EW/AUM)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">🆚 Stacked bars — 2017 vs 2025 (Clean/Controversial/Other) + Movers table</div>', unsafe_allow_html=True)

    # -------- TRADEOFF LAB --------
    with tab3:
        st.subheader("Tradeoff Lab")
        st.caption("Baseline vs cleaner scenarios, measuring cost (TE) vs benefit (% Clean).")
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="blx-card">🧮 Scenario KPIs — % Clean, % Controversial, TE, Active Share, Drift</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">🟩🟥 Side-by-side 100% bars — Baseline vs Scenario composition</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="blx-card">🎯 Mini frontier — x: TE, y: % Clean (point = ETF)</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="blx-card">📋 Movers — adds/drops/ups/downs vs baseline</div>', unsafe_allow_html=True)

else:
    # ---------------- REPORT ----------------
    st.subheader("Project Overview (Short Report)")
    st.markdown(
        """
**What this project is.**  
This project examines **20 BlackRock ESG-labelled ETFs**. The team standardized each fund’s 2025 holdings, applied a unified ESG map (Clean200 plus controversial screens), and built two views: a **2025 snapshot** of how ETF dollars split across Clean / Controversial / Other, and a **2017→2025 change** view that retrofits today’s lens to past portfolios. Finally, a **tradeoff experiment** simulates cleaner alternatives (tilts and exclusions) and quantifies impacts on tracking error, active share, and diversification.

**What you’ll see.**
- **2025 Overview:** today’s composition and the names/screens that drive it.  
- **Change since 2017:** how exposures moved over time, by fund and in aggregate.  
- **Tradeoff Lab:** Baseline vs cleaner scenarios, with measured cost (TE) vs benefit (% Clean).

**Notes.** Screen categories can overlap; percentages for categories don’t sum to total controversial exposure.
        """
    )

# ----------------------------
# FOOTER
# ----------------------------
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
