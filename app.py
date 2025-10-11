import streamlit as st
import pandas as pd

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; color:#E6E9EF; background:#0B0C10; }
      .block-container { padding-top: 2rem; padding-bottom: 3rem; }
      h1,h2,h3 { letter-spacing:0.2px; }
      .subtle { color:#9AA4B2; }
      .footer { margin-top: 36px; padding-top: 16px; border-top:1px solid #2A2F36; display:flex; justify-content:space-between; align-items:center; }
      .footer a { color:#E6E9EF; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1.0; text-decoration:underline; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#121419; border:1px solid #2A2F36; font-size:12px; color:#9AA4B2; margin-right:8px; }
      .asof { font-size:12px; color:#9AA4B2; }
      .stTabs [data-baseweb="tab-list"] { gap: 18px; }
      .stTabs [data-baseweb="tab-list"] button { font-weight:600; color:#E6E9EF; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color:#00A3FF; border-bottom:3px solid #00A3FF; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("## BlackRock ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)")
st.caption("We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.")

tab_dash, tab_report = st.tabs(["Dashboard","Report"])

with tab_dash:
    filt = st.container()
    with filt:
        c1,c2,c3 = st.columns([0.45,0.25,0.3])
        with c1:
            etfs = st.multiselect("ETFs", ["All ESG ETFs"], default=["All ESG ETFs"])
        with c2:
            weighting = st.segmented_control("Weighting", options=["AUM","Equal-weighted"], default="AUM")
        with c3:
            st.markdown("<div class='asof'>As of: 2025</div>", unsafe_allow_html=True)

    st.markdown("### Overview")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("% Controversial", "—")
    k2.metric("% Clean", "—")
    k3.metric("Total AUM", "—")
    k4.metric("Δ Clean since 2017", "—")

    st.markdown("### 2025 Composition")
    cA, cB = st.columns([0.55,0.45])
    with cA:
        st.empty()
    with cB:
        st.empty()

    st.markdown("### Spotlight")
    s1,s2 = st.columns(2)
    with s1:
        st.dataframe(pd.DataFrame(), use_container_width=True)
    with s2:
        st.dataframe(pd.DataFrame(), use_container_width=True)

    st.markdown("### Holdings Explorer")
    st.dataframe(pd.DataFrame(), use_container_width=True)

    st.markdown("### Change since 2017")
    t1,t2 = st.columns(2)
    with t1:
        st.empty()
    with t2:
        st.empty()
    st.markdown("#### Fund × Year")
    st.empty()
    st.markdown("#### Year vs Year")
    y1,y2 = st.columns([0.5,0.5])
    with y1:
        st.empty()
    with y2:
        st.dataframe(pd.DataFrame(), use_container_width=True)

    st.markdown("### Tradeoffs")
    scenario = st.segmented_control("Scenario", options=["Baseline","Pragmatic Tilt","Strict Exclusion"], default="Baseline")
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("% Clean", "—")
    m2.metric("% Controversial", "—")
    m3.metric("Tracking Error", "—")
    m4.metric("Active Share", "—")
    m5.metric("Sector/Region Drift", "—")
    b1,b2 = st.columns([0.5,0.5])
    with b1:
        st.empty()
    with b2:
        st.empty()
    st.dataframe(pd.DataFrame(), use_container_width=True)

with tab_report:
    st.header("Report")
    st.markdown("Context, methods, results highlights, and notes will appear here.")
    st.header("Methodology", anchor="methodology")
    st.markdown("Will be added here when you share the copy.")

st.markdown(
    """
    <div class="footer">
      <div>
        <span class="pill">Clean = Green</span>
        <span class="pill">Controversial = Red</span>
        <span class="pill">Other = Blue-grey</span>
      </div>
      <div>
        <a href="https://github.com/nitya-ar/blackrock-esg-etf-study" target="_blank">GitHub</a>
        <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a>
        <a href="https://forms.gle/1fFm9cXQfx9fbD2u5" target="_blank">Feedback</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
