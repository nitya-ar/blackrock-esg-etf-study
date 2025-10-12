# app.py — BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
# Layout locked. Inter font + refined dark palette. 2025 Overview wired:
# KPI cards, 100% stacked composition, by-screen (incl. Clean200 + info badge),
# spotlight tables, and filter-first Explorer (no helper column exposed).
# Data loader: local -> GitHub raw -> GitHub API (token).

import os
from io import StringIO
import urllib.parse

import requests
import pandas as pd
import altair as alt
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution, Tradeoffs",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Repo / path settings (overridable via Secrets or env)
GITHUB_USER_REPO = st.secrets.get("ESG_REPO", os.getenv("ESG_REPO", "nitya-ar/blackrock-esg-etf-study"))
GITHUB_BRANCH    = st.secrets.get("ESG_BRANCH", os.getenv("ESG_BRANCH", "main"))
DASH_BASE_PATH   = st.secrets.get("ESG_DASH_PATH", os.getenv("ESG_DASH_PATH", "Data/Data for Dashboard"))
LOCAL_BASE       = st.secrets.get("ESG_LOCAL_BASE", os.getenv("ESG_LOCAL_BASE", ""))  # e.g., "/path/.../Data/Data for Dashboard"
GITHUB_TOKEN     = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))      # optional for private repos

ANALYSIS_DIRS = {1: "Analysis 1", 2: "Analysis 2", 3: "Analysis 3"}

# Brand colors
COLORS = {
    "bg": "#0A0B0D",
    "card": "#111318",
    "border": "#1E2228",
    "text": "#E7EBF0",
    "muted": "#9AA4B2",
    "primary": "#00A3FF",
    "clean": "#19C37D",
    "contro": "#F2555A",
    "other": "#94A3B8",
}

# =========================
# STYLES
# =========================
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

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
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }}

      h1, h2, h3, h4, h5 {{ color: var(--text); letter-spacing: .1px; }}
      .blx-divider {{ border-top: 1px solid var(--border); margin: 10px 0 24px 0; }}
      .blx-muted {{ color: var(--muted); }}

      .blx-card {{
        background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 16px;
      }}

      .kpi {{
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px;
      }}
      .kpi .label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
      .kpi .value {{ font-size: 28px; font-weight: 700; line-height: 1.1; }}

      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-color: var(--primary) !important;
      }}

      /* Dataframe font + density */
      div[data-testid="stDataframe"] * {{
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important;
        font-size: 13px !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

# =========================
# DATA LOADER
# =========================
def _url_join(*parts: str) -> str:
    path = "/".join(p.strip("/").replace("\\", "/") for p in parts if p)
    return "/".join(urllib.parse.quote(s, safe=":/") for s in path.split("/"))

def github_raw_url(analysis: int, filename: str) -> str:
    rel = _url_join(DASH_BASE_PATH, ANALYSIS_DIRS[analysis], filename)
    return f"https://raw.githubusercontent.com/{GITHUB_USER_REPO}/{GITHUB_BRANCH}/{rel}"

def github_api_url(analysis: int, filename: str) -> str:
    rel = _url_join(DASH_BASE_PATH, ANALYSIS_DIRS[analysis], filename)
    return f"https://api.github.com/repos/{GITHUB_USER_REPO}/contents/{rel}?ref={GITHUB_BRANCH}"

def local_path(analysis: int, filename: str) -> str:
    if not LOCAL_BASE:
        return ""
    return os.path.join(LOCAL_BASE, ANALYSIS_DIRS[analysis], filename)

@st.cache_data(show_spinner=False)
def load_csv(analysis: int, filename: str) -> pd.DataFrame:
    # 1) Local
    lp = local_path(analysis, filename)
    if lp and os.path.exists(lp):
        return pd.read_csv(lp)

    # 2) Public raw
    raw_url = github_raw_url(analysis, filename)
    try:
        return pd.read_csv(raw_url)
    except Exception as e_raw:
        # 3) Private API (needs token)
        api_url = github_api_url(analysis, filename)
        headers = {"Accept": "application/vnd.github.v3.raw"}
        tok = GITHUB_TOKEN
        if tok:
            headers["Authorization"] = f"token {tok}"
        try:
            r = requests.get(api_url, headers=headers, timeout=25)
            r.raise_for_status()
            return pd.read_csv(StringIO(r.text))
        except Exception as e_api:
            raise FileNotFoundError(
                f"Failed to load {filename}. Tried:\n"
                f"- Local: {lp or '(not set)'}\n"
                f"- Public: {raw_url}\n"
                f"- Private API: {api_url}\n"
                f"Last errors: raw={e_raw}; api={e_api}"
            )

# Analysis 1 loaders
@st.cache_data(show_spinner=False)
def load_context_summary():
    return load_csv(1, "context_summary_2025.csv")

@st.cache_data(show_spinner=False)
def load_by_screen():
    return load_csv(1, "context_breakdown_by_screen.csv")

@st.cache_data(show_spinner=False)
def load_spotlight():
    return load_csv(1, "top_holdings_spotlight.csv")

@st.cache_data(show_spinner=False)
def load_explorer():
    df = load_csv(1, "holdings_explorer_2025.csv")
    # normalize
    for col in ["classification", "sector", "region", "screen_categories"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    # internal normalized tag list (not displayed)
    if "screen_categories" in df.columns:
        scn = (
            df["screen_categories"]
            .astype(str)
            .str.split(r"\s*\|\s*")
            .apply(lambda xs: [x.strip() for x in xs if x and x.lower() != "nan"])
        )
    else:
        scn = [[] for _ in range(len(df))]
    df["_screen_categories_norm"] = scn

    rename_map = {
        "etf_ticker": "ETF",
        "etf_name": "ETF Name",
        "ticker": "Ticker",
        "holding_name": "Holding",
        "sector": "Sector",
        "region": "Region",
        "classification": "Class",
        "screen_categories": "Screens",
        "weight_pct_in_etf": "Weight % in ETF",
        "aum_usd": "ETF AUM (USD)",
        "weight_usd_in_agg": "$ Contribution (Agg)",
        "as_of_date": "As-of",
    }
    df_disp = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Fixed, clean column order
    cols = [c for c in [
        "ETF", "ETF Name", "Ticker", "Holding", "Sector", "Region",
        "Class", "Screens", "Weight % in ETF", "ETF AUM (USD)",
        "$ Contribution (Agg)", "As-of"
    ] if c in df_disp.columns]
    df_disp = df_disp[cols]

    tags = sorted({t for xs in scn for t in xs if t})
    return df, df_disp, tags

# =========================
# HEADER (full-width)
# =========================
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

def divider_small(px=6):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

def kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def pct_fmt(x):
    try: return f"{float(x):.1f}%"
    except: return "-"

def usd_fmt(x):
    try:
        x = float(x)
        if abs(x) >= 1e9: return f"${x/1e9:.1f}B"
        if abs(x) >= 1e6: return f"${x/1e6:.1f}M"
        return f"${x:,.0f}"
    except:
        return "-"

divider()

# =========================
# VIEW SWITCH
# =========================
mode = st.segmented_control(
    "View",
    options=["Dashboard", "Report"],
    default="Dashboard",
    label_visibility="collapsed",
    help="Switch between the interactive dashboard and a short report",
)

divider()

# =========================
# BODY
# =========================
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Lab"])

    # ---------- 2025 OVERVIEW ----------
    with tab1:
        st.subheader("2025 Overview")
        st.caption("Today’s composition and the names/screens that drive it.")

        # Load all data for this tab
        ctx = load_context_summary()
        scr = load_by_screen()
        spot = load_spotlight()

        # KPI cards
        k1, k2, k3, k4 = st.columns(4)
        if "classification" in ctx.columns and "share_of_total_aum_pct" in ctx.columns:
            clean_pct = ctx.loc[ctx["classification"].str.lower()=="clean", "share_of_total_aum_pct"].sum()
            contro_pct = ctx.loc[ctx["classification"].str.lower()=="controversial", "share_of_total_aum_pct"].sum()
        else:
            clean_pct = contro_pct = None

        total_aum = ctx.get("total_aum_usd")
        total_aum = float(total_aum.dropna().iloc[0]) if total_aum is not None and len(total_aum.dropna()) else None

        num_etfs = None
        if "num_etfs_in_scope" in ctx.columns and len(ctx["num_etfs_in_scope"].dropna()):
            num_etfs = int(ctx["num_etfs_in_scope"].dropna().iloc[0])

        with k1: kpi_card("% Controversial", pct_fmt(contro_pct))
        with k2: kpi_card("% Clean", pct_fmt(clean_pct))
        with k3: kpi_card("Total AUM", usd_fmt(total_aum))
        with k4: kpi_card("ETFs in scope", f"{num_etfs:,}" if num_etfs is not None else "-")

        divider_small(6)

        # Charts row
        c1, c2 = st.columns([0.5, 0.5])

        # Composition — 100% stacked bar
        with c1:
            if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
                comp = ctx[ctx["classification"].str.lower().isin(["clean","controversial","other"])].copy()
                comp["classification"] = comp["classification"].map({
                    "Clean": "Clean", "Controversial":"Controversial", "Other":"Other",
                    "clean":"Clean","controversial":"Controversial","other":"Other"
                })
                comp = comp.groupby("classification", as_index=False)["share_of_total_aum_pct"].sum()
                comp["share"] = comp["share_of_total_aum_pct"]/comp["share_of_total_aum_pct"].sum()

                color_scale = alt.Scale(
                    domain=["Clean","Controversial","Other"],
                    range=[COLORS["clean"], COLORS["contro"], COLORS["other"]]
                )

                chart = alt.Chart(comp).mark_bar().encode(
                    x=alt.X("sum(share):Q", stack="normalize", axis=alt.Axis(format='%', title=None, ticks=False, labels=False)),
                    y=alt.Y("o:O", title=None, axis=None),
                    color=alt.Color("classification:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
                    tooltip=[alt.Tooltip("classification:N"),
                             alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")]
                ).properties(height=120)

                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("composition columns missing in context_summary_2025.csv")

        # By-screen bars — includes Clean200 + info badge
        with c2:
            show_parts = []

            if {"screen_category","classification","share_of_total_aum_pct"}.issubset(scr.columns):
                s2 = scr.copy()
                s2["classification"] = s2["classification"].str.title()
                s2 = s2[s2["classification"]=="Controversial"]
                s2 = s2.groupby("screen_category", as_index=False)["share_of_total_aum_pct"].sum()
                show_parts.append(s2)

            if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
                clean_share = ctx.loc[ctx["classification"].str.lower()=="clean","share_of_total_aum_pct"].sum()
                show_parts.append(pd.DataFrame({"screen_category":["Clean200"], "share_of_total_aum_pct":[clean_share]}))

            if show_parts:
                scr_all = pd.concat(show_parts, ignore_index=True)
                scr_all = scr_all.groupby("screen_category", as_index=False)["share_of_total_aum_pct"].sum()
                scr_all = scr_all.sort_values("share_of_total_aum_pct", ascending=True)
                scr_all["color"] = scr_all["screen_category"].apply(
                    lambda x: COLORS["clean"] if str(x).strip().lower()=="clean200" else COLORS["contro"]
                )

                info_html = """
                <div style="display:flex; justify-content:flex-end; margin-bottom:-18px;">
                  <span title="Categories can overlap; not intended to sum to overall controversial exposure."
                        style="border:1px solid #2B2F36; color:#9AA4B2; border-radius:999px; padding:2px 8px; font-size:12px;">
                    info
                  </span>
                </div>
                """
                st.markdown(info_html, unsafe_allow_html=True)

                chart2 = alt.Chart(scr_all).mark_bar().encode(
                    x=alt.X("share_of_total_aum_pct:Q", title="Share of total AUM (%)", axis=alt.Axis(format=".1f")),
                    y=alt.Y("screen_category:N", sort="-x", title=None),
                    color=alt.Color("color:N", legend=None, scale=None),
                    tooltip=[alt.Tooltip("screen_category:N", title="Category"),
                             alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")],
                ).properties(height=240)

                st.altair_chart(chart2, use_container_width=True)

        # Spotlights
        s1, s2 = st.columns([0.5, 0.5])

        with s1:
            if "cohort" in spot.columns:
                cont = spot[spot["cohort"].str.lower()=="controversial"].copy()
                if "rank_within_cohort" in cont.columns:
                    cont = cont.sort_values("rank_within_cohort").head(10)
                cols = ["rank_within_cohort","ticker","holding_name","share_of_total_aum_pct","num_etfs","screen_categories"]
                cols = [c for c in cols if c in cont.columns]
                cont_disp = cont.rename(columns={
                    "rank_within_cohort":"Rank",
                    "ticker":"Ticker",
                    "holding_name":"Holding",
                    "share_of_total_aum_pct":"Share of AUM (%)",
                    "num_etfs":"#ETFs",
                    "screen_categories":"Screens"
                })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
                if "Share of AUM (%)" in cont_disp.columns:
                    cont_disp["Share of AUM (%)"] = pd.to_numeric(cont_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
                st.markdown("**Spotlight — Top 10 Controversial**")
                st.dataframe(cont_disp, use_container_width=True, hide_index=True)
            else:
                st.warning("Missing 'cohort' in top_holdings_spotlight.csv")

        with s2:
            if "cohort" in spot.columns:
                clean = spot[spot["cohort"].str.lower()=="clean"].copy()
                if "rank_within_cohort" in clean.columns:
                    clean = clean.sort_values("rank_within_cohort").head(10)
                cols = ["rank_within_cohort","ticker","holding_name","share_of_total_aum_pct","num_etfs","screen_categories"]
                cols = [c for c in cols if c in clean.columns]
                clean_disp = clean.rename(columns={
                    "rank_within_cohort":"Rank",
                    "ticker":"Ticker",
                    "holding_name":"Holding",
                    "share_of_total_aum_pct":"Share of AUM (%)",
                    "num_etfs":"#ETFs",
                    "screen_categories":"Screens"
                })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
                if "Share of AUM (%)" in clean_disp.columns:
                    clean_disp["Share of AUM (%)"] = pd.to_numeric(clean_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
                st.markdown("**Spotlight — Top 10 Clean**")
                st.dataframe(clean_disp, use_container_width=True, hide_index=True)

        # Explorer
        divider_small(8)
        st.markdown("### Holdings Explorer")
        st.caption("Filter and search across ETF × holding rows. Download the filtered view below.")

        df_raw, df_disp, all_tags = load_explorer()

        fc1, fc2, fc3, fc4, fc5 = st.columns([0.22, 0.18, 0.24, 0.18, 0.18])
        with fc1:
            etfs = sorted(df_disp["ETF"].dropna().unique().tolist()) if "ETF" in df_disp.columns else []
            sel_etfs = st.multiselect("ETF", etfs, placeholder="All")
        with fc2:
            classes = ["Clean","Controversial","Other"]
            sel_class = st.multiselect("Classification", classes, default=[], placeholder="Any")
        with fc3:
            sel_tags = st.multiselect("Screen tags", all_tags, default=[], placeholder="Any")
        with fc4:
            sectors = sorted([s for s in df_disp.get("Sector", pd.Series()).dropna().unique().tolist() if s])
            sel_sector = st.multiselect("Sector", sectors, default=[], placeholder="Any")
        with fc5:
            regions = sorted([r for r in df_disp.get("Region", pd.Series()).dropna().unique().tolist() if r])
            sel_region = st.multiselect("Region", regions, default=[], placeholder="Any")

        q = st.text_input("Search ticker or name", "", placeholder="Type to filter…").strip().lower()

        mask = pd.Series(True, index=df_raw.index)
        if sel_etfs:   mask &= df_disp["ETF"].isin(sel_etfs)
        if sel_class:  mask &= df_disp["Class"].isin(sel_class)
        if sel_sector: mask &= df_disp["Sector"].isin(sel_sector)
        if sel_region: mask &= df_disp["Region"].isin(sel_region)
        if sel_tags:   mask &= df_raw["_screen_categories_norm"].apply(lambda xs: all(t in xs for t in sel_tags))
        if q:
            qcols = [c for c in ["Ticker","Holding","ETF Name"] if c in df_disp.columns]
            if qcols:
                qmask = False
                for c in qcols:
                    qmask |= df_disp[c].astype(str).str.lower().str.contains(q, na=False)
                mask &= qmask

        df_f = df_disp.loc[mask].copy()
        default_sort = "$ Contribution (Agg)" if "$ Contribution (Agg)" in df_f.columns else ("Weight % in ETF" if "Weight % in ETF" in df_f.columns else None)
        if default_sort:
            df_f = df_f.sort_values(by=default_sort, ascending=False)

        show_all = st.toggle("Show all rows", value=False, help="Turn off to preview the first 500 rows for speed.")
        df_view = df_f if show_all else df_f.head(500)

        for c in ("Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)"):
            if c in df_view.columns:
                df_view[c] = pd.to_numeric(df_view[c], errors="coerce")

        st.dataframe(df_view, use_container_width=True, hide_index=True)

        csv_bytes = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered rows (CSV)",
            data=csv_bytes,
            file_name="holdings_explorer_filtered.csv",
            mime="text/csv",
        )

    # ---------- CHANGE SINCE 2017 ----------
    with tab2:
        st.subheader("Change since 2017")
        st.caption("How exposures moved over time, by fund and in aggregate.")
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="blx-card">Trend — % Clean over time (EW/AUM)</div>', unsafe_allow_html=True)
            divider_small(10)
            st.markdown('<div class="blx-card">Heatmap — Fund × Year by % Controversial (toggle % Clean)</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="blx-card">Trend — % Controversial over time (EW/AUM)</div>', unsafe_allow_html=True)
            divider_small(10)
            st.markdown('<div class="blx-card">Two stacked bars — 2017 vs 2025 (Clean/Controversial/Other) + Movers table</div>', unsafe_allow_html=True)

    # ---------- TRADEOFF LAB ----------
    with tab3:
        st.subheader("Tradeoff Lab")
        st.caption("Baseline vs cleaner scenarios, measuring cost (TE) vs benefit (% Clean).")
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            st.markdown('<div class="blx-card">Scenario KPIs — % Clean, % Controversial, TE, Active Share, Drift</div>', unsafe_allow_html=True)
            divider_small(10)
            st.markdown('<div class="blx-card">Side-by-side 100% bars — Baseline vs Scenario composition</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="blx-card">Mini frontier — x: TE, y: % Clean (point = ETF)</div>', unsafe_allow_html=True)
            divider_small(10)
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

# =========================
# FOOTER
# =========================
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
