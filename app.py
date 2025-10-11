import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="BlackRock ESG ETFs Dashboard", layout="wide")

st.markdown(
    """
    <style>
      html, body, [class*="css"] {
        font-family: Avenir, "Avenir Next", -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, "Helvetica Neue", Arial, sans-serif;
        color:#E6E9EF; background:#0B0C10;
      }
      .block-container { padding-top: 32px; padding-bottom: 32px; max-width: 1200px; }
      .brandrow { display:flex; align-items:center; gap:16px; margin-bottom:6px; }
      .brandrow h2 { margin:0; font-size:28px; font-weight:700; letter-spacing:.2px; }

      .footer { margin-top: 18px; padding-top: 14px; border-top:1px solid #2A2F36;
                display:flex; justify-content:space-between; align-items:center; }
      .footer a { color:#E6E9EF; text-decoration:none; font-size:13px; margin-right:16px; opacity:0.9; }
      .footer a:hover { opacity:1; text-decoration:underline; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#121419;
              border:1px solid #2A2F36; font-size:12px; color:#9AA4B2; margin-right:8px; }
      .muted-accent { background:#191c22; border:1px solid #2A2F36; color:#C9D2DF;
                      padding:6px 10px; border-radius:8px; display:inline-block; }
      .asof { font-size:12px; color:#9AA4B2; text-align:right; }

      div[data-testid="stMetric"] { padding: 0 4px; }
      div[data-testid="stMetricValue"] { font-size: 26px; }
      div[data-testid="stMetricLabel"] { font-size: 13px; color:#C9D2DF; }
      div[data-testid="stMetricDelta"] { font-size: 12px; }

      .section-2025 { font-size:34px; font-weight:800; margin:8px 0 14px 0; }
      .section-2017 { font-size:30px; font-weight:800; margin:22px 0 10px 0; }
      .minor-h { font-size:18px; font-weight:700; margin:10px 0 6px 0; }
      .pairhead { display:flex; align-items:center; justify-content:space-between; margin:8px 0 4px 0; }
      .infopill { font-size:12px; color:#C8DAFF; background:#1A2437;
                  border:1px solid #334a78; padding:2px 8px; border-radius:999px; cursor:help; }
      .infopill:hover { filter:brightness(1.1); }
    </style>
    """,
    unsafe_allow_html=True
)

BASE = Path("Data") / "Data for Dashboard" / "Analysis 2"
AGG_TRENDS = BASE / "aggregate_exposure_trends.csv"
YEAR_COMPARE = BASE / "year_compare_summary.csv"
DISPERSION = BASE / "exposure_dispersion_stats.csv"
BY_FUND_YEAR = BASE / "exposures_by_fund_year.csv"
SCREEN_TRENDS = BASE / "aggregate_screen_trends.csv"
MOVERS = BASE / "movers_by_yearpair.csv"

CLEAN_COLOR = "#0A6F56"
CONTRO_COLOR = "#8F3131"
OTHER_COLOR = "#414B55"
SERIES_COLORS = {"Clean": CLEAN_COLOR, "Controversial": CONTRO_COLOR, "Other": OTHER_COLOR}

@st.cache_data
def read_csv(p: Path):
    return pd.read_csv(p) if p.exists() else None

def pick(df, fns):
    low = {c.lower(): c for c in df.columns}
    for fn in fns:
        for k, v in low.items():
            if fn(k):
                return v
    return None

def line_trends(df, weighting):
    wcol = pick(df, [lambda s: s in ("weighting","agg","type")])
    ycol = pick(df, [lambda s: s=="year"])
    clean = pick(df, [lambda s: ("clean" in s and "pct" in s)])
    contro = pick(df, [lambda s: ("controversial" in s and "pct" in s)])
    other = pick(df, [lambda s: ("other" in s and "pct" in s)])
    d = df.copy()
    if wcol:
        d = d[d[wcol].str.lower().str.contains(weighting.lower().split("-")[0])]
    tidy = pd.melt(
        d[[ycol, clean, contro, other]].rename(
            columns={clean: "Clean", contro: "Controversial", other: "Other"}
        ),
        id_vars=ycol, var_name="Series", value_name="pct"
    )
    return alt.Chart(tidy).mark_line(point=True).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y("pct:Q", axis=alt.Axis(format="%", title="Portfolio share")),
        color=alt.Color("Series:N",
                        scale=alt.Scale(domain=list(SERIES_COLORS.keys()),
                                        range=list(SERIES_COLORS.values())),
                        legend=alt.Legend(title="")),
        tooltip=[ycol, "Series", alt.Tooltip("pct:Q", title="Share (%)", format=".1f")]
    ).properties(height=260)

def ribbon_from_dispersion(df, weighting):
    wcol = pick(df, [lambda s: s in ("weighting","agg","type")])
    ycol = pick(df, [lambda s: s=="year"])
    med = pick(df, [lambda s: s in ("controversial_median","median_controversial","controversial_p50")])
    p10 = pick(df, [lambda s: "controversial_p10" in s or s=="p10_controversial"])
    p90 = pick(df, [lambda s: "controversial_p90" in s or s=="p90_controversial"])
    if not all([wcol, ycol, med, p10, p90]):
        return None
    d = df[df[wcol].str.lower().str.contains(weighting.lower().split("-")[0])][[ycol, med, p10, p90]].rename(
        columns={med: "median", p10: "p10", p90: "p90"}
    )
    area = alt.Chart(d).mark_area(opacity=0.2, color=CONTRO_COLOR).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y="p10:Q",
        y2="p90:Q"
    )
    line = alt.Chart(d).mark_line(color=CONTRO_COLOR).encode(
        x=alt.X(f"{ycol}:O"),
        y=alt.Y("median:Q", axis=alt.Axis(format="%", title="Controversial share")),
        tooltip=[ycol, alt.Tooltip("median:Q", title="Median (%)", format=".1f"),
                 alt.Tooltip("p10:Q", title="p10 (%)", format=".1f"),
                 alt.Tooltip("p90:Q", title="p90 (%)", format=".1f")]
    )
    return area + line

def heatmap_by_fund_year(df, metric="controversial"):
    ycol = pick(df, [lambda s: s=="year"])
    fund = pick(df, [lambda s: s in ("etf_ticker","etf","fund","etf_name")])
    if metric=="controversial":
        mcol = pick(df, [lambda s: ("controversial" in s and "pct" in s)])
        title = "% Controversial"
    else:
        mcol = pick(df, [lambda s: ("clean" in s and "pct" in s)])
        title = "% Clean"
    d = df[[fund, ycol, mcol]].rename(columns={mcol:"pct"})
    latest = d[d[ycol]==d[ycol].max()].sort_values("pct", ascending=False)[fund].tolist()
    d[fund] = pd.Categorical(d[fund], categories=latest, ordered=True)
    return alt.Chart(d).mark_rect().encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y(f"{fund}:O", title="ETF"),
        color=alt.Color("pct:Q", scale=alt.Scale(scheme="reds" if metric=="controversial" else "greens"),
                        legend=alt.Legend(title=title, format="%")),
        tooltip=[fund, ycol, alt.Tooltip("pct:Q", title="Share (%)", format=".1f")]
    ).properties(height=420)

def stacked_year_compare(df, weighting, year_a, year_b):
    wcol = pick(df, [lambda s: s in ("weighting","agg","type")])
    ycol = pick(df, [lambda s: s=="year"])
    cohort = pick(df, [lambda s: s in ("cohort","classification","bucket")])
    pct = pick(df, [lambda s: "pct" in s])
    d = df[df[wcol].str.lower().str.contains(weighting.lower().split("-")[0])]
    d = d[d[ycol].isin([year_a, year_b])]
    d[cohort] = pd.Categorical(d[cohort], categories=["Clean","Controversial","Other"], ordered=True)
    colors = [CLEAN_COLOR, CONTRO_COLOR, OTHER_COLOR]
    return alt.Chart(d).mark_bar().encode(
        x=alt.X(f"{ycol}:O", title="", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{pct}:Q", axis=alt.Axis(format="%", title="Portfolio share"), stack="normalize"),
        color=alt.Color(f"{cohort}:N", scale=alt.Scale(domain=["Clean","Controversial","Other"], range=colors), legend=alt.Legend(title="")),
        tooltip=[ycol, cohort, alt.Tooltip(pct, title="Share (%)", format=".1f")]
    ).properties(height=220)

def screen_small_multiples(df, weighting):
    wcol = pick(df, [lambda s: s in ("weighting","agg","type")])
    ycol = pick(df, [lambda s: s=="year"])
    cat = pick(df, [lambda s: s in ("screen_category","category")])
    pct = pick(df, [lambda s: "pct" in s])  # <-- fixed bracket here
    d = df[df[wcol].str.lower().str.contains(weighting.lower().split("-")[0])]
    screens = d[cat].unique().tolist()
    base = alt.Chart(d).encode(
        x=alt.X(f"{ycol}:O", title="Year"),
        y=alt.Y(f"{pct}:Q", axis=alt.Axis(format="%", title="AUM-weighted share")),
        tooltip=[ycol, alt.Tooltip(pct, title="Share (%)", format=".1f")]
    )
    charts = []
    for s in screens:
        c = base.transform_filter(alt.datum[cat] == s).mark_line(
            color=CONTRO_COLOR if s!="Clean200" else CLEAN_COLOR
        ).properties(title=s, height=110)
        charts.append(c)
    return alt.vconcat(*charts).resolve_scale(y='independent')

# ----- Header -----
st.markdown(
    """
    <div class="brandrow">
      <img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/BlackRock_wordmark.svg"
           alt="BlackRock" style="height:32px; filter:brightness(0) invert(1);">
      <h2>ESG ETFs: Evolution, Alignment, and Tradeoffs (2017–2025)</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("We built a tool where anyone can explore how BlackRock’s ESG ETFs align with clean/controversial classifications, see how that changed since 2017, and test tradeoff scenarios.")

# ----- Change since 2017 -----
st.markdown("<div class='section-2017'>Change since 2017</div>", unsafe_allow_html=True)

colL, colR = st.columns([0.55, 0.45])
with colL:
    weighting = st.radio("Weighting", ["AUM-weighted", "Equal-weighted"], horizontal=True, index=0)
with colR:
    yc = read_csv(YEAR_COMPARE)
    if yc is not None:
        ycol = pick(yc, [lambda s: s=="year"])
        years = sorted(yc[ycol].unique().tolist())
    else:
        years = list(range(2017, 2025+1))
    cA, cB = st.columns(2)
    with cA:
        year_a = st.selectbox("Year A", years, index=0)
    with cB:
        year_b = st.selectbox("Year B", years, index=len(years)-1)

agg = read_csv(AGG_TRENDS)
if agg is not None:
    wcol = pick(agg, [lambda s: s in ("weighting","agg","type")])
    ycol = pick(agg, [lambda s: s=="year"])
    clean = pick(agg, [lambda s: ("clean" in s and "pct" in s)])
    contro = pick(agg, [lambda s: ("controversial" in s and "pct" in s)])
    filt = agg[agg[wcol].str.lower().str.contains(weighting.lower().split("-")[0])]
    y17 = filt[filt[ycol]==min(years)]
    y25 = filt[filt[ycol]==max(years)]
    d_clean = (y25[clean].mean() - y17[clean].mean()) if len(y17) and len(y25) else np.nan
    d_contro = (y25[contro].mean() - y17[contro].mean()) if len(y17) and len(y25) else np.nan
else:
    d_clean = d_contro = np.nan

m1, m2 = st.columns(2)
m1.metric("Δ Clean (2017 → 2025)", f"{d_clean:+.1f} pp" if pd.notna(d_clean) else "—")
m2.metric("Δ Controversial (2017 → 2025)", f"{d_contro:+.1f} pp" if pd.notna(d_contro) else "—")

left, right = st.columns([0.58, 0.42], gap="small")
with left:
    st.markdown("<div class='minor-h'>Trend (Clean / Controversial / Other)</div>", unsafe_allow_html=True)
    if agg is not None:
        st.altair_chart(line_trends(agg, weighting), use_container_width=True)
with right:
    disp = read_csv(DISPERSION)
    st.markdown("<div class='minor-h'>Cross-fund dispersion (Controversial)</div>", unsafe_allow_html=True)
    if disp is not None:
        rib = ribbon_from_dispersion(disp, weighting)
        if rib is not None:
            st.altair_chart(rib, use_container_width=True)

st.markdown("<div class='minor-h'>Heatmap: % Controversial by ETF × Year</div>", unsafe_allow_html=True)
byfy = read_csv(BY_FUND_YEAR)
if byfy is not None:
    st.altair_chart(heatmap_by_fund_year(byfy, metric="controversial"), use_container_width=True)

st.markdown("<div class='minor-h'>Year vs Year (stacked share)</div>", unsafe_allow_html=True)
yc = read_csv(YEAR_COMPARE)
if yc is not None:
    st.altair_chart(stacked_year_compare(yc, weighting, year_a, year_b), use_container_width=True)

st.markdown(
    "<div class='pairhead'>"
    "<div class='minor-h'>Screen trends (AUM-weighted)</div>"
    "<span class='infopill' title='Screen categories can overlap; their series are not meant to sum to overall controversial exposure.'>ⓘ</span>"
    "</div>", unsafe_allow_html=True
)
scr = read_csv(SCREEN_TRENDS)
if scr is not None:
    st.altair_chart(screen_small_multiples(scr, "AUM" if "AUM" in weighting.upper() else "EW"), use_container_width=True)

st.markdown("<div class='minor-h'>Top movers (Year A → Year B)</div>", unsafe_allow_html=True)
mov = read_csv(MOVERS)
if mov is not None:
    ya = pick(mov, [lambda s: s in ("year_a","from_year")])
    yb = pick(mov, [lambda s: s in ("year_b","to_year")])
    if ya and yb:
        mov = mov[(mov[ya]==year_a) & (mov[yb]==year_b)]
    name = pick(mov, [lambda s: s in ("holding_name","name")])
    tic = pick(mov, [lambda s: s=="ticker"])
    delta = pick(mov, [lambda s: "delta" in s or "change" in s])
    num = pick(mov, [lambda s: s in ("num_etfs","fund_count","#etfs")])
    cols = [tic, name, delta, num]
    tidy = mov[cols].rename(columns={tic:"Ticker", name:"Name", delta:"Δ contribution (pp)", num:"#ETFs"}).copy()
    tidy["Δ contribution (pp)"] = tidy["Δ contribution (pp)"].astype(float)
    up = tidy.sort_values("Δ contribution (pp)", ascending=False).head(10).reset_index(drop=True)
    dn = tidy.sort_values("Δ contribution (pp)", ascending=True).head(10).reset_index(drop=True)

    t1, t2 = st.columns(2)
    with t1:
        st.subheader("Largest increases", divider=False)
        st.dataframe(up, use_container_width=True, hide_index=True)
    with t2:
        st.subheader("Largest decreases", divider=False)
        st.dataframe(dn, use_container_width=True, hide_index=True)

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
