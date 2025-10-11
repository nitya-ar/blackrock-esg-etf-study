import streamlit as st

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #E6E9EF;
        background-color: #0B0C10;
    }
    .stTabs [data-baseweb="tab-list"] button {
        color: #E6E9EF;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #00A3FF;
        border-bottom: 3px solid #00A3FF;
    }
    .icon-bar a {
        text-decoration: none;
        color: #E6E9EF;
        margin-left: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.markdown("### BlackRock ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)")
    st.caption("Explore alignment, evolution (2017–2025), and tradeoffs of BlackRock’s ESG ETFs.")
with c2:
    st.markdown(
        """
        <div class="icon-bar" style="text-align:right;">
          <a href="https://github.com/yourusername/blackrock-esg-etf-dashboard" target="_blank">🔗 GitHub</a>
          <a href="#methodology">📘 Methodology</a>
          <a href="https://forms.gle/yourgoogleformlink" target="_blank">✉️ Feedback</a>
        </div>
        """,
        unsafe_allow_html=True
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "2025 Snapshot", "Change since 2017", "Tradeoffs", "Report & Methods"]
)

with tab1:
    st.header("Overview")
    st.write("Key metrics and overall composition snapshot.")

with tab2:
    st.header("2025 Snapshot")
    st.write("Explore current holdings and exposures by category.")

with tab3:
    st.header("Change since 2017")
    st.write("View how ESG alignment evolved between 2017 and 2025.")

with tab4:
    st.header("Tradeoffs")
    st.write("Simulated alternative portfolios and their financial vs ESG tradeoffs.")

with tab5:
    st.header("Report & Methods", anchor="methodology")
    st.write("Project summary, methodology, and assumptions.")

