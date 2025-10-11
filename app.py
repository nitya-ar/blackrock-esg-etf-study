st.markdown("<div class='section-title'>Top Exposures (2025)</div>", unsafe_allow_html=True)
s1, s2 = st.columns(2, gap="small")

if top is not None:
    cohort = pick(top, [lambda s: s == "cohort"])
    rank = pick(top, [lambda s: "rank" in s])
    name = pick(top, [lambda s: s in ("holding_name","name")])
    ticker = pick(top, [lambda s: s == "ticker"])
    share = pick(top, [lambda s: "share_of_total_aum_pct" in s or s == "share_pct"])
    etfsn = pick(top, [lambda s: s in ("num_etfs","#etfs","count_etfs")])
    tags = pick(top, [lambda s: "screen_categories" in s or s == "tags"])
    cols = [rank, ticker, name, share, etfsn, tags]
    rename_map = {rank:"Rank", ticker:"Ticker", name:"Name", share:"Share of AUM (%)", etfsn:"#ETFs", tags:"Screens"}

    with s1:
        hdr_l, hdr_r = st.columns([0.65, 0.35])
        with hdr_l:
            st.markdown("<div class='minor-h'>Top Controversial</div>", unsafe_allow_html=True)
        with hdr_r:
            show_all_tc = st.toggle("Show full list", value=False, key="toggle_tc")
        tc = top[top[cohort].str.lower()=="controversial"][cols].rename(columns=rename_map).copy()
        tc["Share of AUM (%)"] = pd.to_numeric(tc["Share of AUM (%)"], errors="coerce").round(4)
        rows_tc = 10 if show_all_tc else 5
        st.dataframe(tc.head(rows_tc), use_container_width=True, hide_index=True,
                     height= (rows_tc+1)*32 + 24)

    with s2:
        hdr_l2, hdr_r2 = st.columns([0.65, 0.35])
        with hdr_l2:
            st.markdown("<div class='minor-h'>Top Clean</div>", unsafe_allow_html=True)
        with hdr_r2:
            show_all_tg = st.toggle("Show full list", value=False, key="toggle_tg")
        tg = top[top[cohort].str.lower()=="clean"][cols].rename(columns=rename_map).copy()
        tg["Share of AUM (%)"] = pd.to_numeric(tg["Share of AUM (%)"], errors="coerce").round(4)
        rows_tg = 10 if show_all_tg else 5
        st.dataframe(tg.head(rows_tg), use_container_width=True, hide_index=True,
                     height= (rows_tg+1)*32 + 24)
