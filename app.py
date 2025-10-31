import os
from io import StringIO, BytesIO
import urllib.parse
import base64
import requests
import pandas as pd
import altair as alt
import streamlit as st
from pathlib import Path
from PIL import Image

_GH_RAW = "https://raw.githubusercontent.com/nitya-ar/blackrock-esg-etf-study/main/Blackrock%20esg%20study%20icon.png"

def _read_bytes(p: Path):
    try:
        return p.read_bytes()
    except Exception:
        return None

def _pil_to_png_bytes(img: Image.Image):
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _load_icon_bytes():
    here = Path(__file__).parent if "__file__" in globals() else Path.cwd()
    candidates = [
        Path("Blackrock esg study icon.png"),
        Path("assets/Blackrock esg study icon.png"),
        here / "Blackrock esg study icon.png",
        here / "assets/Blackrock esg study icon.png",
        Path("/mnt/data/Blackrock esg study icon.png"),
    ]
    for p in candidates:
        if p.exists():
            try:
                img = Image.open(p)
                return _pil_to_png_bytes(img)
            except Exception:
                b = _read_bytes(p)
                if b:
                    return b
    try:
        r = requests.get(_GH_RAW, timeout=8)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        return _pil_to_png_bytes(img)
    except Exception:
        return None

_icon_bytes = _load_icon_bytes()
st.set_page_config(
    page_title="BlackRock ESG ETFs — Alignment, Evolution, Tradeoffs",
    page_icon=_icon_bytes if _icon_bytes else "🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if _icon_bytes:
    _b64 = base64.b64encode(_icon_bytes).decode()
    st.markdown(
        f"""
        <script>
        const setFav = () => {{
            const link = document.querySelector("link[rel='icon']") || document.createElement('link');
            link.type = 'image/png';
            link.rel = 'icon';
            link.href = "data:image/png;base64,{_b64}";
            document.getElementsByTagName('head')[0].appendChild(link);
        }};
        setFav();
        </script>
        """,
        unsafe_allow_html=True,
    )

# ---------- Theme detection (auto from OS, persisted in ?theme=) ----------
try:
    q = st.query_params
    get_param = q.get
    set_params = q.update
except Exception:
    get_param = st.experimental_get_query_params
    def set_params(d): st.experimental_set_query_params(**d)

st.markdown("""
<script>
(function(){
  try{
    const url = new URL(window.location.href);
    if(!url.searchParams.get('theme')){
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      url.searchParams.set('theme', prefersDark ? 'dark' : 'light');
      window.history.replaceState({}, '', url);
    }
    document.documentElement.setAttribute('data-theme', url.searchParams.get('theme') || 'dark');
    try{
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      mq.addEventListener('change', (e)=>{
        const t = e.matches ? 'dark' : 'light';
        const u = new URL(window.location.href);
        u.searchParams.set('theme', t);
        window.location.replace(u.toString());
      });
    }catch(_){}
  }catch(_){}
})();
</script>
""", unsafe_allow_html=True)

params = get_param()
THEME = (params["theme"] if isinstance(params.get("theme"), str) else (params.get("theme",[None])[0])) or "dark"
THEME = "dark" if str(THEME).lower().strip() not in ("light","dark") else str(THEME).lower().strip()

PALETTE = {
    "dark": dict(
        bg="#0A0B0D", card="#0F1116", border="#1C2027",
        text="#E7EBF0", muted="#97A2B0", primary="#00A3FF",
        clean="#0E8F66", contro="#C63C41", other="#768397",
        bar_stroke="rgba(0,0,0,0)"
    ),
    "light": dict(
        bg="#FFFFFF", card="#F6F8FB", border="#E3E8EF",
        text="#0F172A", muted="#5B6471", primary="#0B7BD3",
        clean="#0E8F66", contro="#C63C41", other="#5B6B84",
        bar_stroke="rgba(0,0,0,0)"
    ),
}
COLORS = PALETTE[THEME]
BAR_STROKE = COLORS["bar_stroke"]

# ---------- Altair themes for both modes ----------
def _alt_theme_dark():
    return {
        "config": {
            "background": "transparent",
            "view": {"fill": "transparent", "stroke": COLORS["border"]},
            "axis": {
                "labelColor": COLORS["text"],
                "titleColor": COLORS["muted"],
                "domainColor": "#2A2F36",
                "tickColor":   "#2A2F36",
                "grid": True,
                "gridColor": "#222831",
                "gridOpacity": 0.45,
            },
            "legend": {"labelColor": COLORS["text"], "titleColor": COLORS["muted"]},
            "title": {"color": COLORS["text"]},
        }
    }

def _alt_theme_light():
    return {
        "config": {
            "background": "transparent",
            "view": {"fill": "transparent", "stroke": COLORS["border"]},
            "axis": {
                "labelColor": COLORS["text"],
                "titleColor": COLORS["muted"],
                "domainColor": COLORS["border"],
                "tickColor":   COLORS["border"],
                "grid": True,
                "gridColor": "#EDF2F7",
                "gridOpacity": 1.0,
            },
            "legend": {"labelColor": COLORS["text"], "titleColor": COLORS["muted"]},
            "title": {"color": COLORS["text"]},
        }
    }

alt.themes.register("custom_dark", _alt_theme_dark)
alt.themes.register("custom_light", _alt_theme_light)
alt.themes.enable("custom_dark" if THEME=="dark" else "custom_light")

# ---------- Global CSS (dual-theme variables; no forced dark) ----------
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  :root[data-theme="dark"] {{
    --bg:{PALETTE['dark']['bg']}; --card:{PALETTE['dark']['card']}; --border:{PALETTE['dark']['border']};
    --text:{PALETTE['dark']['text']}; --muted:{PALETTE['dark']['muted']}; --primary:{PALETTE['dark']['primary']};
    --clean:{PALETTE['dark']['clean']}; --contro:{PALETTE['dark']['contro']}; --other:{PALETTE['dark']['other']};
    --bar-stroke:{PALETTE['dark']['bar_stroke']};
    --table-hdr:#11151C; --table-cell:#0E1015; --tooltip-bg:#0F1116;
  }}
  :root[data-theme="light"] {{
    --bg:{PALETTE['light']['bg']}; --card:{PALETTE['light']['card']}; --border:{PALETTE['light']['border']};
    --text:{PALETTE['light']['text']}; --muted:{PALETTE['light']['muted']}; --primary:{PALETTE['light']['primary']};
    --clean:{PALETTE['light']['clean']}; --contro:{PALETTE['light']['contro']}; --other:{PALETTE['light']['other']};
    --bar-stroke:{PALETTE['light']['bar_stroke']};
    --table-hdr:#F4F7FB; --table-cell:#FFFFFF; --tooltip-bg:#FFFFFF;
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
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px; padding: 14px 16px;
  }}
  .kpi {{
    background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
    border: 1px solid var(--border); border-radius: 16px; padding: 18px 20px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
  }}
  .kpi .label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
  .kpi .value {{ font-size: 30px; font-weight: 700; line-height: 1.05; }}
  .kpi.kpi-red {{ background: linear-gradient(180deg, rgba(198,60,65,0.16), rgba(255,255,255,0)); border-color: rgba(198,60,65,0.45); }}
  .kpi.kpi-green {{ background: linear-gradient(180deg, rgba(14,143,102,0.16), rgba(255,255,255,0)); border-color: rgba(14,143,102,0.45); }}
  .kpi.kpi-neutral {{ background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0)); border-color: rgba(255,255,255,0.08); }}

  .stAltairChart, .stVegaLiteChart, .stPlotlyChart {{ background: var(--card) !important; border: 1px solid var(--border) !important; }}
  .vega-embed, .stAltairChart {{ background: transparent !important; }}
  .vega-tooltip, .vega-tooltip * {{ background: var(--tooltip-bg) !important; color:var(--text) !important; border-color:var(--border) !important; }}

  :where([data-testid="stDataFrame"], [data-testid="stDataframe"], [data-testid="stTable"]) table {{
    background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
  }}
  :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="columnheader"],
  :where([data-testid="stTable"]) thead th {{
    background: var(--table-hdr) !important; color: var(--text) !important; border-bottom: 1px solid var(--border) !important;
  }}
  :where([data-testid="stDataFrame"], [data-testid="stDataframe"]) [role="row"] [role="gridcell"],
  :where([data-testid="stTable"]) tbody td {{
    background: var(--table-cell) !important; color: var(--text) !important; border-top: 1px solid var(--border) !important;
  }}
</style>
""", unsafe_allow_html=True)

def divider():
    st.markdown('<div class="blx-divider"></div>', unsafe_allow_html=True)

def gap(px=6):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

def grid(df: pd.DataFrame):
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Paths, secrets, loaders ----------
GITHUB_USER_REPO = st.secrets.get("ESG_REPO", os.getenv("ESG_REPO", "nitya-ar/blackrock-esg-etf-study"))
GITHUB_BRANCH    = st.secrets.get("ESG_BRANCH", os.getenv("ESG_BRANCH", "main"))
DASH_BASE_PATH   = st.secrets.get("ESG_DASH_PATH", os.getenv("ESG_DASH_PATH", "Data/Data for Dashboard"))
LOCAL_BASE       = st.secrets.get("ESG_LOCAL_BASE", os.getenv("ESG_LOCAL_BASE", ""))
GITHUB_TOKEN     = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
ANALYSIS_DIRS = {1: "Analysis 1", 2: "Analysis 2", 3: "Analysis 3"}

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
    lp = local_path(analysis, filename)
    if lp and os.path.exists(lp):
        return pd.read_csv(lp)
    raw_url = github_raw_url(analysis, filename)
    try:
        return pd.read_csv(raw_url)
    except Exception as e_raw:
        api_url = github_api_url(analysis, filename)
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        r = requests.get(api_url, headers=headers, timeout=25)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))

@st.cache_data(show_spinner=False)
def load_context_summary():   return load_csv(1, "context_summary_2025.csv")
@st.cache_data(show_spinner=False)
def load_by_screen():         return load_csv(1, "context_breakdown_by_screen.csv")
@st.cache_data(show_spinner=False)
def load_spotlight():         return load_csv(1, "top_holdings_spotlight.csv")
@st.cache_data(show_spinner=False)
def load_explorer():
    df = load_csv(1, "holdings_explorer_2025.csv")
    for col in ["classification","sector","region","screen_categories"]:
        if col in df.columns: df[col] = df[col].fillna("")
    if "screen_categories" in df.columns:
        scn = (
            df["screen_categories"].astype(str)
            .str.split(r"\s*\|\s*")
            .apply(lambda xs: [x.strip() for x in xs if x and x.lower() != "nan"])
        )
    else:
        scn = [[] for _ in range(len(df))]
    df["_screen_categories_norm"] = scn

    rename_map = {
        "etf_ticker":"ETF","etf_name":"ETF Name","ticker":"Ticker","holding_name":"Holding",
        "sector":"Sector","region":"Region","classification":"Class","screen_categories":"Screens",
        "weight_pct_in_etf":"Weight % in ETF","aum_usd":"ETF AUM (USD)","weight_usd_in_agg":"$ Contribution (Agg)",
        "as_of_date":"As-of",
    }
    df_disp = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})
    ordered = [c for c in [
        "ETF","ETF Name","Ticker","Holding","Sector","Region","Class","Screens",
        "Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)","As-of"
    ] if c in df_disp.columns]
    df_disp = df_disp[ordered]
    tags = sorted({t for xs in scn for t in xs if t})
    return df, df_disp, tags

# ---------- Header ----------
st.markdown(
    """
    <div style="display:flex; flex-direction:column; gap:8px;">
      <h2 style="margin:0; font-weight:800; letter-spacing:0.1px;">
        BlackRock ESG ETFs: Alignment, Evolution, and Tradeoffs (2017–2025)
      </h2>
      <div class="blx-muted" style="max-width:1400px; text-align:justify; text-justify:inter-word;">
        This project analyzes 20 BlackRock ETFs positioned as sustainable to evaluate how their holdings align with core sustainability themes from 2017 to 2025. It applies a consistent classification framework for 2025 that distinguishes companies considered clean from those associated with five controversial categories: fossil fuels, weapons, tobacco, prisons, and deforestation. The dashboard brings this analysis to life through three views: the 2025 Overview, which outlines current exposure to clean and controversial holdings; Change since 2017, which traces how these exposures have evolved; and Tradeoff Scenarios, which model cleaner portfolio versions to illustrate the relationship between sustainability alignment and investment performance.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

def kpi_card(label: str, value: str, tone: str = "neutral"):
    tone_class = {"red":"kpi-red","green":"kpi-green","neutral":"kpi-neutral"}.get(tone, "kpi-neutral")
    st.markdown(f"""
        <div class="kpi {tone_class}">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def pct_fmt(x):
    try: return f"{float(x):.1f}%"
    except: return "-"

def usd_fmt(x):
    try:
        x = float(x)
        if abs(x) >= 1e9: return f"${x/1e9:.1f}B"
        if abs(x) >= 1e6: return f"${x/1e6:.1f}M"
        return f"${x:,.0f}"
    except: return "-"

divider()
mode = "Dashboard"
divider()

# ---------- TAB 1: 2025 Overview ----------
def render_tab1():
    st.subheader("2025 Overview")

    ctx = load_context_summary()
    scr = load_by_screen()
    spot = load_spotlight()

    k1, k2, k3, k4 = st.columns(4)
    if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
        clean_pct  = ctx.loc[ctx["classification"].str.lower()=="clean","share_of_total_aum_pct"].sum()
        contro_pct = ctx.loc[ctx["classification"].str.lower()=="controversial","share_of_total_aum_pct"].sum()
    else:
        clean_pct = contro_pct = None
    total_aum = ctx.get("total_aum_usd")
    total_aum = float(total_aum.dropna().iloc[0]) if total_aum is not None and len(total_aum.dropna()) else None
    num_etfs = int(ctx["num_etfs_in_scope"].dropna().iloc[0]) if "num_etfs_in_scope" in ctx.columns and len(ctx["num_etfs_in_scope"].dropna()) else None

    with k1: kpi_card("% Controversial", pct_fmt(contro_pct), tone="red")
    with k2: kpi_card("% Clean",         pct_fmt(clean_pct),  tone="green")
    with k3: kpi_card("Total AUM",       usd_fmt(total_aum),  tone="neutral")
    with k4: kpi_card("ETFs in scope",   f"{num_etfs:,}" if num_etfs is not None else "-", tone="neutral")

    gap(6)

    c1, c2 = st.columns([0.5, 0.5])

    with c1:
        st.markdown(
            """<div class="chart-head">
                  <div class="chart-title">2025 Composition — Clean vs Controversial vs Other</div>
                  <div></div>
               </div>""",
            unsafe_allow_html=True,
        )

        if {"classification","share_of_total_aum_pct"}.issubset(ctx.columns):
            comp = ctx[ctx["classification"].str.lower().isin(["clean","controversial","other"])].copy()
            comp["classification"] = comp["classification"].map({
                "Clean":"Clean","Controversial":"Controversial","Other":"Other",
                "clean":"Clean","controversial":"Controversial","other":"Other"
            })
            comp = comp.groupby("classification", as_index=False)["share_of_total_aum_pct"].sum()
            comp["share"] = comp["share_of_total_aum_pct"]/comp["share_of_total_aum_pct"].sum()
            comp["Group"] = "All"

            color_scale = alt.Scale(domain=["Clean","Controversial","Other"],
                                    range=[COLORS["clean"], COLORS["contro"], COLORS["other"]])

            chart = alt.Chart(comp).mark_bar(opacity=0.92, stroke=BAR_STROKE, strokeWidth=0.6).encode(
                x=alt.X("sum(share):Q", stack="normalize",
                        axis=alt.Axis(format='%', title=None, ticks=False, labels=False)),
                y=alt.Y("Group:N", title=None, axis=None),
                color=alt.Color("classification:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
                tooltip=[alt.Tooltip("classification:N"),
                         alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")]
            ).properties(height=120)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("composition columns missing in context_summary_2025.csv")

    with c2:
        st.markdown(
            """<div class="chart-head">
                  <div class="chart-title">By-screen exposures — share of total AUM</div>
                  <div class="info-badge has-tip" data-tip="Categories can overlap; not intended to sum to overall controversial exposure.">i</div>
               </div>""",
            unsafe_allow_html=True,
        )

        parts = []
        clean200 = 0.0
        if {"screen_category","classification","share_of_total_aum_pct"}.issubset(scr.columns):
            s2 = scr.copy()
            s2["classification"] = s2["classification"].str.title()
            s_con = s2[s2["classification"]=="Controversial"].groupby(
                "screen_category", as_index=False
            )["share_of_total_aum_pct"].sum()
            parts.append(s_con)
            c2_row = scr.loc[
                scr["screen_category"].astype(str).str.strip().str.lower()=="clean200",
                "share_of_total_aum_pct"
            ].sum()
            clean200 = float(c2_row) if pd.notna(c2_row) else 0.0

        parts.append(pd.DataFrame({"screen_category":["Clean200"], "share_of_total_aum_pct":[clean200]}))

        scr_all = pd.concat(parts, ignore_index=True)
        scr_all = scr_all.groupby("screen_category", as_index=False)["share_of_total_aum_pct"].sum()
        scr_all = scr_all.sort_values("share_of_total_aum_pct", ascending=True)
        scr_all["color"] = scr_all["screen_category"].apply(
            lambda x: COLORS["clean"] if str(x).strip().lower()=="clean200" else COLORS["contro"]
        )

        chart2 = alt.Chart(scr_all).mark_bar(opacity=0.92, stroke=BAR_STROKE, strokeWidth=0.6).encode(
            x=alt.X("share_of_total_aum_pct:Q", title="Share of total AUM (%)", axis=alt.Axis(format=".1f")),
            y=alt.Y("screen_category:N", sort="-x", title=None),
            color=alt.Color("color:N", legend=None, scale=None),
            tooltip=[alt.Tooltip("screen_category:N", title="Category"),
                     alt.Tooltip("share_of_total_aum_pct:Q", title="Share (%)", format=".1f")],
        ).properties(height=240)
        st.altair_chart(chart2, use_container_width=True)

    s1, s2c = st.columns([0.5, 0.5])
    with s1:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Controversial Holdings</div>', unsafe_allow_html=True)
        if "cohort" in spot.columns:
            cont = spot[spot["cohort"].str.lower()=="controversial"].copy()
            if "rank_within_cohort" in cont.columns:
                cont = cont.sort_values("rank_within_cohort").head(10)
            cont_disp = cont.rename(columns={
                "rank_within_cohort":"Rank","ticker":"Ticker","holding_name":"Holding",
                "share_of_total_aum_pct":"Share of AUM (%)","num_etfs":"#ETFs","screen_categories":"Screens"
            })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
            if "Share of AUM (%)" in cont_disp.columns:
                cont_disp["Share of AUM (%)"] = pd.to_numeric(cont_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
            grid(cont_disp)
    with s2c:
        st.markdown('<div class="chart-title" style="margin-bottom:6px;">Top 10 Clean Holdings</div>', unsafe_allow_html=True)
        if "cohort" in spot.columns:
            clean = spot[spot["cohort"].str.lower()=="clean"].copy()
            if "rank_within_cohort" in clean.columns:
                clean = clean.sort_values("rank_within_cohort").head(10)
            clean_disp = clean.rename(columns={
                "rank_within_cohort":"Rank","ticker":"Ticker","holding_name":"Holding",
                "share_of_total_aum_pct":"Share of AUM (%)","num_etfs":"#ETFs","screen_categories":"Screens"
            })[["Rank","Ticker","Holding","Share of AUM (%)","#ETFs","Screens"]]
            if "Share of AUM (%)" in clean_disp.columns:
                clean_disp["Share of AUM (%)"] = pd.to_numeric(clean_disp["Share of AUM (%)"], errors="coerce").map(lambda v: f"{v:.2f}")
            grid(clean_disp)

    gap(8)
    st.markdown('<div class="chart-title" style="margin-bottom:6px;">Holdings Explorer</div>', unsafe_allow_html=True)

    df_raw, df_disp, all_tags = load_explorer()
    fc1, fc2, fc3, fc4, fc5 = st.columns([0.22, 0.18, 0.24, 0.18, 0.18])
    with fc1:
        etfs = sorted(df_disp["ETF"].dropna().unique().tolist()) if "ETF" in df_disp.columns else []
        sel_etfs_explorer = st.multiselect("ETF", etfs, placeholder="All")
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
    if sel_etfs_explorer:   mask &= df_disp["ETF"].isin(sel_etfs_explorer)
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

    df_view = df_f.copy()
    for c in ("Weight % in ETF","ETF AUM (USD)","$ Contribution (Agg)"):
        if c in df_view.columns:
            df_view[c] = pd.to_numeric(df_view[c], errors="coerce")
    grid(df_view)

    csv_bytes = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered rows (CSV)", data=csv_bytes, file_name="holdings_explorer_filtered.csv", mime="text/csv")

# ---------- TAB 2 and TAB 3 stubs (drop your existing functions if you want them unchanged) ----------
def render_change_since_2017():
    st.subheader("Change since 2017")
    st.info("This tab uses your existing logic. If you want me to paste the full themed version here as well, say “paste Tab 2 themed”.")
def render_tradeoff_scenarios():
    st.subheader("Tradeoff Scenarios")
    st.info("This tab uses your existing logic. If you want me to paste the full themed version here as well, say “paste Tab 3 themed”.")

# ---------- BODY ----------
if mode == "Dashboard":
    tab1, tab2, tab3 = st.tabs(["2025 Overview", "Change since 2017", "Tradeoff Scenarios"])
    with tab1:
        render_tab1()
    with tab2:
        render_change_since_2017()
    with tab3:
        render_tradeoff_scenarios()

# ---------- FOOTER ----------
def footer():
    gap(28)
    divider()
    github_url = f"https://github.com/{GITHUB_USER_REPO}"
    st.markdown(
        f"""
        <style>
          .footer-cta {{
            margin: 16px 0 8px 0;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(0,0,0,0.04));
            border: 1px solid var(--border);
            border-radius: 12px;
          }}
          .footer-cta a {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--text);
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            opacity: .95;
          }}
          .footer-cta a:hover {{ opacity: 1; transform: translateY(-0.5px); }}
          .footer-cta .muted {{ color: var(--muted); font-weight: 500; }}
          .footer-wrap {{
            display:flex; align-items:center; justify-content:space-between; width:100%;
            padding-top: 12px;
          }}
          .footer-left {{ color: var(--muted); font-size: 14px; white-space: nowrap; }}
          .footer-links {{ display:flex; gap:28px; align-items:center; justify-content:flex-end; }}
          .footer-links a {{ color: var(--text); text-decoration:none; font-size:15.5px; font-weight:500; opacity:.9; }}
          .footer-links a:hover {{ opacity:1; }}
          @media (max-width: 820px) {{
            .footer-cta {{ flex-wrap: wrap; gap:10px; }}
            .footer-wrap {{ flex-direction: column; gap: 8px; align-items: flex-start; }}
          }}
        </style>

        <div class="footer-cta">
          <span class="muted">Explore the data, methodology, and full code</span>
          <a href="{github_url}" target="_blank" aria-label="Open GitHub">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 .2a8 8 0 0 0-2.53 15.6c.4.07.55-.17.55-.38l-.01-1.34c-2.25.49-2.72-1.09-2.72-1.09-.36-.9-.89-1.13-.89-1.13-.73-.5.06-.49.06-.49.8.06 1.22.83 1.22.83.72 1.23 1.9.87 2.37.66.07-.53.28-.87.5-1.07-1.8-.2-3.69-.9-3.69-4 0-.88.31-1.6.83-2.17-.08-.2-.36-1.02.08-2.12 0 0 .68-.22 2.22.83.65-.18 1.34-.27 2.03-.27.69 0 1.38.09 2.03.27 1.54-1.05 2.22-.83 2.22-.83.44 1.1.16 1.92.08 2.12.52.57.83 1.29.83 2.17 0 3.11-1.89 3.8-3.69 4 .29.25.54.73.54 1.48l-.01 2.19c0 .21.15.45.55.38A8 8 0 0 0 8 .2Z"/>
            </svg>
            <span>Open on GitHub</span>
            <span style="opacity:.7;">→</span>
          </a>
        </div>

        <div class="footer-wrap">
          <div class="footer-left">Built by <strong>Nitya Arya</strong></div>
          <div class="footer-links">
            <a href="https://www.linkedin.com/in/nitya-arya/" target="_blank">LinkedIn</a>
            <a href="https://github.com/nitya-ar" target="_blank">GitHub</a>
            <a href="https://forms.gle/qid7S1eJpGCuYdtY8" target="_blank"><strong>Send Feedback</strong></a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

footer()
