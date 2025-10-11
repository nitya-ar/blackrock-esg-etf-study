# ---- 2025 OVERVIEW → HOLDINGS EXPLORER ----
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_explorer():
    df = pd.read_csv("/mnt/data/holdings_explorer_2025.csv")
    # Normalize helpful fields
    for col in ["classification","sector","region","screen_categories"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    # build a normalized list of unique screen tags
    tags = set()
    if "screen_categories" in df.columns:
        df["screen_categories_norm"] = (
            df["screen_categories"]
            .astype(str)
            .str.split(r"\s*\|\s*")  # split on " | "
            .apply(lambda xs: [x.strip() for x in xs if x and x.lower() != "nan"])
        )
        for xs in df["screen_categories_norm"]:
            tags.update(xs)
    else:
        df["screen_categories_norm"] = [[] for _ in range(len(df))]
    tag_list = sorted([t for t in tags if t])
    # Minor renames for display
    rename_map = {
        "etf_ticker":"ETF",
        "etf_name":"ETF Name",
        "ticker":"Ticker",
        "holding_name":"Holding",
        "sector":"Sector",
        "region":"Region",
        "classification":"Class",
        "screen_categories":"Screens",
        "weight_pct_in_etf":"Weight % in ETF",
        "aum_usd":"ETF AUM (USD)",
        "weight_usd_in_agg":"$ Contribution (Agg)",
        "as_of_date":"As-of",
    }
    df_disp = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})
    return df, df_disp, tag_list

df_raw, df_disp, all_tags = load_explorer()

# --- Filters row
fc1, fc2, fc3, fc4, fc5 = st.columns([0.22, 0.18, 0.24, 0.18, 0.18])

with fc1:
    etfs = sorted(df_disp["ETF"].dropna().unique().tolist()) if "ETF" in df_disp.columns else []
    sel_etfs = st.multiselect("ETF", etfs, placeholder="All")

with fc2:
    classes = ["Clean","Controversial","Other"]
    sel_class = st.multiselect("Classification", classes, default=[], placeholder="Any")

with fc3:
    sel_tags = st.multiselect("Screen tags", all_tags, default=[], placeholder="Any (Fossil, Weapons, …)")

with fc4:
    sectors = sorted([s for s in df_disp.get("Sector", pd.Series()).dropna().unique().tolist() if s])
    sel_sector = st.multiselect("Sector", sectors, default=[], placeholder="Any")

with fc5:
    regions = sorted([r for r in df_disp.get("Region", pd.Series()).dropna().unique().tolist() if r])
    sel_region = st.multiselect("Region", regions, default=[], placeholder="Any")

q = st.text_input("Search ticker or name", "", placeholder="Type to filter…").strip().lower()

# --- Apply filters
mask = pd.Series(True, index=df_raw.index)

if sel_etfs:
    mask &= df_disp["ETF"].isin(sel_etfs)

if sel_class:
    mask &= df_disp["Class"].isin(sel_class)

if sel_sector:
    mask &= df_disp["Sector"].isin(sel_sector)

if sel_region:
    mask &= df_disp["Region"].isin(sel_region)

if sel_tags:
    # keep rows that contain ALL selected tags
    mask &= df_raw["screen_categories_norm"].apply(lambda xs: all(t in xs for t in sel_tags))

if q:
    qcols = []
    if "Ticker" in df_disp.columns: qcols.append("Ticker")
    if "Holding" in df_disp.columns: qcols.append("Holding")
    if "ETF Name" in df_disp.columns: qcols.append("ETF Name")
    if qcols:
        qmask = False
        for c in qcols:
            qmask |= df_disp[c].astype(str).str.lower().str.contains(q, na=False)
        mask &= qmask

df_f = df_disp.loc[mask].copy()

# --- Sort & display options
sort_cols = [c for c in ["$ Contribution (Agg)", "Weight % in ETF", "Class","ETF","Sector","Region","Ticker"] if c in df_f.columns]
default_sort = "$ Contribution (Agg)" if "$ Contribution (Agg)" in df_f.columns else ( "Weight % in ETF" if "Weight % in ETF" in df_f.columns else None )
if default_sort:
    df_f = df_f.sort_values(by=default_sort, ascending=False)

# Row limiter for speed
show_all = st.toggle("Show all rows", value=False, help="Turn off to preview the first 500 rows for speed.")
df_view = df_f if show_all else df_f.head(500)

# Number formatting
fmt = {
    "Weight % in ETF": "{:.2f}",
    "ETF AUM (USD)": "{:,.0f}",
    "$ Contribution (Agg)": "{:,.0f}",
}
for c,f in fmt.items():
    if c in df_view.columns:
        try: df_view[c] = pd.to_numeric(df_view[c], errors="coerce")
        except: pass

st.dataframe(
    df_view,
    use_container_width=True,
    hide_index=True,
)

# Download current view
csv_bytes = df_f.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered rows (CSV)",
    data=csv_bytes,
    file_name="holdings_explorer_filtered.csv",
    mime="text/csv",
)
