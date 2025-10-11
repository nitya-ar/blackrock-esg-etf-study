st.markdown("<div class='section-2025'>Change since 2017</div>", unsafe_allow_html=True)

AN2_TRENDS = read_csv(AGG_TRENDS)
AN2_DISP = read_csv(AN2 / "exposure_dispersion_stats.csv")
AN2_BYFUND = read_csv(AN2 / "exposures_by_fund_year.csv")
AN2_YCOMP = read_csv(AN2 / "year_compare_summary.csv")
AN2_MOVERS = read_csv(AN2 / "movers_by_yearpair.csv")
AN2_SCREENS = read_csv(AN2 / "aggregate_screen_trends.csv")

def col_like(df, keys):
    low = {c.lower(): c for c in df.columns}
    for k in keys:
        for lc, c in low.items():
            if k in lc:
                return c
    return None

def series_from_trends(df, kind):
    y = col_like(df, ["year"])
    aum = col_like(df, [f"{kind}_pct_aum", f"aum_{kind}", f"{kind} aum", f"{kind}_aum"])
    ew = col_like(df, [f"{kind}_pct_ew", f"ew_{kind}", f"{kind} ew", f"{kind}_ew"])
    return y, aum, ew

def kpis_from_trends(df, weighting):
    y, aum_c, ew_c = series_from_trends(df, "clean")
    y2, aum_x, ew_x = series_from_trends(df, "controversial")
    aum_tot = col_like(df, ["total_aum"])
    base = df.copy()
    y17 = base.loc[base[y]==2017].tail(1)
    y25 = base.loc[base[y]==2025].tail(1)
    if weighting=="AUM":
        clean_17 = float(y17[aum_c].mean()) if aum_c else np.nan
        clean_25 = float(y25[aum_c].mean()) if aum_c else np.nan
        x_17 = float(y17[aum_x].mean()) if aum_x else np.nan
        x_25 = float(y25[aum_x].mean()) if aum_x else np.nan
        aum_17 = float(y17[aum_tot].mean()) if aum_tot else np.nan
        aum_25 = float(y25[aum_tot].mean()) if aum_tot else np.nan
    else:
        clean_17 = float(y17[ew_c].mean()) if ew_c else np.nan
        clean_25 = float(y25[ew_c].mean()) if ew_c else np.nan
        x_17 = float(y17[ew_x].mean()) if ew_x else np.nan
        x_25 = float(y25[ew_x].mean()) if ew_x else np.nan
        aum_17 = np.nan
        aum_25 = np.nan
    d_clean = clean_25 - clean_17 if not np.isnan(clean_17) and not np.isnan(clean_25) else np.nan
    d_contr = x_25 - x_17 if not np.isnan(x_17) and not np.isnan(x_25) else np.nan
    d_aum = (aum_25/aum_17 - 1) if (not np.isnan(aum_17) and aum_17>0 and not np.isnan(aum_25)) else np.nan
    return d_clean, d_contr, d_aum

weighting = st.segmented_control("Weighting", options=["AUM","Equal-weighted"], default="AUM")
d1,d2,d3 = kpis_from_trends(AN2_TRENDS, weighting) if AN2_TRENDS is not None else (np.nan,np.nan,np.nan)
m1,m2,m3 = st.columns([0.2,0.2,0.2])
m1.metric("Δ Clean (2017 → 2025)", f"{d1:+.1f} pp" if pd.notna(d1) else "—")
m2.metric("Δ Controversial (2017 → 2025)", f"{d2:+.1f} pp" if pd.notna(d2) else "—")
m3.metric("AUM growth", f"{d3:,.0%}" if pd.notna(d3) else "—")

def trend_chart(df, weighting):
    y = col_like(df, ["year"])
    c_aum = col_like(df, ["clean_pct_aum","aum_clean"])
    c_ew  = col_like(df, ["clean_pct_ew","ew_clean"])
    x_aum = col_like(df, ["controversial_pct_aum","aum_controversial"])
    x_ew  = col_like(df, ["controversial_pct_ew","ew_controversial"])
    if weighting=="AUM":
        plot = df[[y,c_aum,x_aum]].rename(columns={y:"year",c_aum:"Clean",x_aum:"Controversial"})
    else:
        plot = df[[y,c_ew,x_ew]].rename(columns={y:"year",c_ew:"Clean",x_ew:"Controversial"})
    plot = plot.melt("year", var_name="Series", value_name="pct")
    colors = {"Clean":CLEAN_COLOR,"Controversial":CONTRO_COLOR}
    return alt.Chart(plot).mark_line(point=False).encode(
        x=alt.X("year:O", title=""),
        y=alt.Y("pct:Q", axis=alt.Axis(format="%", title="Portfolio share")),
        color=alt.Color("Series:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("Series:N"), alt.Tooltip("pct:Q", title="Share", format=".1%")]
    ).properties(height=240)

def year_compare_chart(df, weighting):
    wkey = "AUM" if weighting=="AUM" else "EW"
    has_w = col_like(df, [f"{wkey.lower()}"])
    base = df if has_w is None else df[df[has_w]==wkey]
    y = col_like(base, ["year"])
    cls = col_like(base, ["class","classification"])
    val = col_like(base, ["pct","share"])
    short = base[(base[y].isin([2017,2025])) & (base[cls].isin(["Clean","Controversial","Other"]))].copy()
    short["year"] = short[y].astype(str)
    colors = {"Clean":CLEAN_COLOR,"Controversial":CONTRO_COLOR,"Other":OTHER_COLOR}
    return alt.Chart(short).mark_bar().encode(
        x=alt.X("year:N", title=""),
        y=alt.Y(f"{val}:Q", axis=alt.Axis(format="%", title="Share")),
        color=alt.Color(f"{cls}:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=alt.Legend(title="")),
        column=alt.Column(f"{cls}:N", title=None, spacing=8)
    ).resolve_scale(y='shared').properties(height=180)

row1a,row1b = st.columns([0.6,0.4], gap="small")
with row1a:
    st.markdown("<div class='minor-h'>Trend (Clean vs Controversial)</div>", unsafe_allow_html=True)
    if AN2_TRENDS is not None:
        st.altair_chart(trend_chart(AN2_TRENDS, weighting), use_container_width=True)
with row1b:
    st.markdown("<div class='minor-h'>2017 vs 2025</div>", unsafe_allow_html=True)
    if AN2_YCOMP is not None:
        st.altair_chart(year_compare_chart(AN2_YCOMP, weighting), use_container_width=True)

def heatmap(df):
    y = col_like(df, ["year"])
    f = col_like(df, ["etf","fund","ticker"])
    c = col_like(df, ["controversial_pct","pct_controversial","controversial"])
    if c is None: return None
    slim = df[[f,y,c]].copy()
    return alt.Chart(slim).mark_rect().encode(
        y=alt.Y(f"{f}:N", sort='-x', title="ETF"),
        x=alt.X(f"{y}:O", title="Year"),
        color=alt.Color(f"{c}:Q", scale=alt.Scale(scheme="reds"), legend=alt.Legend(title="% Controversial")),
        tooltip=[f, y, alt.Tooltip(c, title="% Controversial", format=".1f")]
    ).properties(height=260)

st.markdown("<div class='minor-h'>Heatmap: % Controversial by Fund × Year</div>", unsafe_allow_html=True)
if AN2_BYFUND is not None:
    hm = heatmap(AN2_BYFUND)
    if hm is not None:
        st.altair_chart(hm, use_container_width=True)

def screen_smalls(df):
    y = col_like(df, ["year"])
    cat = col_like(df, ["screen","category"])
    val = col_like(df, ["pct","share"])
    base = df[[y,cat,val]].copy()
    return alt.Chart(base).mark_line().encode(
        x=alt.X(f"{y}:O", title=""),
        y=alt.Y(f"{val}:Q", axis=alt.Axis(format="%", title="Share")),
        color=alt.Color(f"{cat}:N", legend=None),
        facet=alt.Facet(f"{cat}:N", columns=3, title=None)
    ).properties(height=120)

st.markdown("<div class='minor-h'>Screen trends (AUM-weighted)</div>", unsafe_allow_html=True)
if AN2_SCREENS is not None:
    st.altair_chart(screen_smalls(AN2_SCREENS), use_container_width=True)

def movers_table(df):
    name = col_like(df, ["holding_name","name"])
    tic = col_like(df, ["ticker"])
    d = col_like(df, ["delta","change","d_"])
    cats = col_like(df, ["screen"])
    cols = [name,tic,d,cats] if cats else [name,tic,d]
    tab = df[cols].copy()
    tab = tab.sort_values(d, ascending=False)
    top_up = tab.head(5).assign(Direction="Up")
    top_dn = tab.tail(5).sort_values(d).assign(Direction="Down")
    out = pd.concat([top_up, top_dn], axis=0)
    ren = {name:"Name", tic:"Ticker", d:"Δ share (pp)", cats:"Screens"}
    return out.rename(columns=ren)

st.markdown("<div class='minor-h'>Top movers (2017 → 2025, AUM-weighted contribution)</div>", unsafe_allow_html=True)
if AN2_MOVERS is not None:
    st.dataframe(movers_table(AN2_MOVERS), use_container_width=True, hide_index=True)
