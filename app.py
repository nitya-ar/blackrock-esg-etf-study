import streamlit as st
from datetime import date

st.set_page_config(page_title="BlackRock ESG ETFs", layout="wide")

# --- derive as-of (replace with real value later) ---
as_of_date = st.session_state.get("as_of_date", "2025")  # e.g., "2025-09-30"

# --- top header row: title (L) • as-of + mode switch (R) ---
h_left, h_right = st.columns([0.72, 0.28], gap="large")
with h_left:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; gap:4px;">
          <h2 style="margin:0; font-weight:700;">BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)</h2>
          <div style="opacity:0.8;">Analysis of 20 ESG-labelled ETFs: 2025 snapshot, evolution since 2017, and a tradeoff experiment that pushes portfolios cleaner while measuring tracking error and diversification shifts.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with h_right:
    st.markdown(
        f"""
        <div style="text-align:right; color:#9AA4B2; margin-bottom:6px;">
            As of: <span style="color:#E7EBF0;"><b>{as_of_date}</b></span>
        </div>
        """,
        unsafe_allow_html=True
    )
    mode = st.segmented_control(
        "View",
        options=["Dashboard", "Report"],
        default="Dashboard",
        label_visibility="collapsed",
        help="Switch between the interactive dashboard and a short report",
    )

st.markdown("<hr style='border-color:#1E2228;'>", unsafe_allow_html=True)
