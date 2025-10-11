import streamlit as st

st.set_page_config(page_title="BlackRock ESG ETFs", layout="wide")

# ---- Top bar ----
left, right = st.columns([0.75, 0.25])
with left:
    st.markdown("## BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)")
    st.caption(
        "Analysis of 20 ESG-labelled ETFs: 2025 snapshot, evolution since 2017, and a tradeoff experiment that "
        "pushes portfolios cleaner while measuring tracking error and diversification shifts."
    )
with right:
    mode = st.segmented_control("",
        options=["Dashboard", "Report"],
        default="Dashboard",
        help="Switch between the interactive dashboard and a short report",
        label_visibility="collapsed",
    )

st.markdown("---")

# ---- Dashboard ----
if mode == "Dashboard":
    # Global quick info row (kept simple)
    as_of = st.session_state.get("as_of_date", "2025")
    st.info(f"As of: **{as_of}** • Colors: Clean=green, Controversial=red, Other=blue-grey")

    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Lab"])

    with tab1:
        st.subheader("2025 Overview")
        st.caption("Today’s composition and the names/screens that drive it.")
        # (placeholder containers; charts/tables will be wired next)
        c1, c2 = st.columns([0.5, 0.5])
        with c1: st.empty()
        with c2: st.empty()
        st.container().empty()  # explorer placeholder

    with tab2:
        st.subheader("Change since 2017")
        st.caption("How exposures moved over time, by fund and in aggregate.")
        c1, c2 = st.columns([0.5, 0.5])
        with c1: st.empty()
        with c2: st.empty()
        st.container().empty()  # heatmap / year-vs-year / movers

    with tab3:
        st.subheader("Tradeoff Lab")
        st.caption("Baseline vs cleaner scenarios, measuring cost (TE) vs benefit (% Clean).")
        c1, c2 = st.columns([0.5, 0.5])
        with c1: st.empty()   # KPI cards / bars
        with c2: st.empty()   # mini frontier
        st.container().empty()  # movers

# ---- Report ----
else:
    st.subheader("Project Overview (Short Report)")
    st.markdown(
        """
**Purpose.** Assess how BlackRock’s ESG-labelled ETFs align with a consistent 2025 ESG classification, how that alignment has **evolved since 2017**, and what it **costs to get cleaner**.

**Method (high level).**
1) Standardize 2025 holdings for 20 ETFs and tag Clean200/controversial screens.  
2) Apply the same map retroactively to 2017–2025 holdings to measure change.  
3) Simulate cleaner portfolios (tilt & exclusion) and estimate tracking error via a covariance matrix.

**What to read.** Use the tabs on the **Dashboard**: *2025 Overview*, *Change since 2017*, *Tradeoff Lab*.
        """
    )

st.markdown("---")
# ---- Footer with emphasis on Feedback ----
f1, f2, f3, f4 = st.columns([0.5, 0.16, 0.16, 0.18])
with f1:
    st.caption("Built by **Nitya Arya**")
with f2:
    st.markdown("[LinkedIn](https://www.linkedin.com/in/nitya-arya/)")
with f3:
    st.markdown("[GitHub](https://github.com/nitya-ar)")
with f4:
    st.markdown("**[Send Feedback](https://forms.gle/qid7S1eJpGCuYdtY8)**")
