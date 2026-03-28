# =============================================================================
# ECO Africa ECO Platform — Investment Intelligence Dashboard
# app.py  |  Built with Python + Streamlit + Plotly
#
# SETUP INSTRUCTIONS:
#   1. pip install streamlit pandas plotly openpyxl
#   2. Place app.py, Eco_Africa_ECO_Platform.xlsx, Eco_Africa_ECO_Platform.png
#      all in the SAME folder.
#   3. Run:  streamlit run app.py
#   4. Open: http://localhost:8501
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ECO Africa | Investment Intelligence Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand colours ─────────────────────────────────────────────────────────────
ECO_GREEN  = "rgb(50,209,116)"
ECO_TEAL   = "rgb(48,178,176)"
ECO_BLUE   = "rgb(64,152,202)"
ECO_ORANGE = "rgb(234,116,35)"
DEEP_BLACK = "rgb(10,12,14)"
GRAPHITE   = "rgb(20,24,28)"
DARK_GRAY  = "rgb(38,44,50)"
SILVER     = "rgb(210,218,226)"

# Hex equivalents for Plotly colour sequences
ACCENT_PALETTE = ["#32D174", "#30B2B0", "#4098CA", "#EA7423",
                  "#2ecc71", "#1abc9c", "#3498db", "#e67e22"]

# ── Custom CSS — enforce full dark ECO Africa theme ───────────────────────────
st.markdown(f"""
<style>
    /* App background */
    .stApp {{ background-color: {DEEP_BLACK}; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {GRAPHITE};
        border-right: 1px solid {DARK_GRAY};
    }}
    section[data-testid="stSidebar"] * {{ color: {SILVER} !important; }}

    /* Global text */
    * {{ color: {SILVER}; }}

    /* Headings */
    h1, h2, h3, h4 {{ color: {ECO_GREEN} !important; }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{ color: {ECO_GREEN} !important; }}

    /* KPI metric cards */
    [data-testid="stMetric"] {{
        background-color: {GRAPHITE};
        border: 1px solid {DARK_GRAY};
        border-radius: 8px;
        padding: 14px 16px;
    }}
    [data-testid="stMetric"] label  {{ color: {SILVER} !important; font-size: 0.78rem !important; }}
    [data-testid="stMetricValue"]   {{ color: {ECO_GREEN} !important; font-weight: 700 !important; font-size: 1.45rem !important; }}
    [data-testid="stMetricDelta"]   {{ color: {ECO_TEAL}  !important; }}

    /* Inputs / filters */
    .stSelectbox > div, .stMultiSelect > div, .stDateInput > div {{
        background-color: {DARK_GRAY} !important;
        border: 1px solid {DARK_GRAY} !important;
        border-radius: 6px;
    }}
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {ECO_GREEN} !important;
        color: {DEEP_BLACK} !important;
    }}

    /* Dataframe */
    .stDataFrame {{ background-color: {GRAPHITE}; border-radius: 8px; }}
    .stDataFrame thead tr th {{
        background-color: {DARK_GRAY} !important;
        color: {ECO_GREEN} !important;
    }}
    .stDataFrame tbody tr:hover td {{ background-color: {DARK_GRAY} !important; }}

    /* Expander */
    details {{ background-color: {GRAPHITE} !important; border: 1px solid {DARK_GRAY} !important; border-radius: 8px; }}
    summary {{ color: {ECO_GREEN} !important; font-weight: 600; }}

    /* Divider */
    hr {{ border-color: {DARK_GRAY}; }}

    /* Tab bar */
    .stTabs [data-baseweb="tab-list"] {{ background-color: {GRAPHITE}; border-radius: 8px; }}
    .stTabs [data-baseweb="tab"] {{ color: {SILVER} !important; }}
    .stTabs [aria-selected="true"] {{ color: {ECO_GREEN} !important; border-bottom: 2px solid {ECO_GREEN}; }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {DEEP_BLACK}; }}
    ::-webkit-scrollbar-thumb {{ background: {DARK_GRAY}; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)


# ── Helper: shared Plotly layout ──────────────────────────────────────────────
def dark_layout(title="", height=400):
    return dict(
        title=dict(text=title, font=dict(color=ECO_GREEN, size=14), x=0.01),
        paper_bgcolor=DARK_GRAY,
        plot_bgcolor=DARK_GRAY,
        font=dict(color=SILVER, size=11),
        margin=dict(l=40, r=20, t=45, b=40),
        height=height,
        legend=dict(bgcolor=GRAPHITE, bordercolor=DARK_GRAY, font=dict(color=SILVER)),
        xaxis=dict(gridcolor="rgba(210,218,226,0.08)", color=SILVER, zerolinecolor="rgba(210,218,226,0.1)"),
        yaxis=dict(gridcolor="rgba(210,218,226,0.08)", color=SILVER, zerolinecolor="rgba(210,218,226,0.1)"),
    )


# ── Data loading & preprocessing ──────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("Eco_Africa_ECO_Platform.xlsx", engine="openpyxl")

    # Strip whitespace from all string columns
    str_cols = [c for c in df.columns if df[c].dtype == object]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", np.nan)

    # Parse date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Numeric coerce
    for col in ["Funding_Amount_USD", "Jobs_Created", "CO2_Reduction_Tons",
                "Data_Utilization_Score", "Impact_Score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Derived metrics ──────────────────────────────────────────────────────

    # 1. Funding Tier
    def funding_tier(v):
        if pd.isna(v):
            return "Unknown"
        if v >= 2_000_000:
            return "Large"
        if v >= 500_000:
            return "Medium"
        return "Small"
    df["Funding_Tier"] = df["Funding_Amount_USD"].apply(funding_tier)

    # 2. Impact Classification
    def impact_class(v):
        if pd.isna(v):
            return "Unknown"
        if v >= 75:
            return "High Impact"
        if v >= 50:
            return "Medium Impact"
        return "Low Impact"
    df["Impact_Classification"] = df["Impact_Score"].apply(impact_class)

    # 3. CO₂ Efficiency Ratio (tons per $1M invested)
    df["CO2_Efficiency_Ratio"] = np.where(
        df["Funding_Amount_USD"] > 0,
        df["CO2_Reduction_Tons"] / (df["Funding_Amount_USD"] / 1_000_000),
        np.nan,
    )

    # 4. Jobs Per Million USD
    df["Jobs_Per_Million_USD"] = np.where(
        df["Funding_Amount_USD"] > 0,
        df["Jobs_Created"] / (df["Funding_Amount_USD"] / 1_000_000),
        np.nan,
    )

    # 5. On Hold Flag
    df["On_Hold_Flag"] = df["Project_Status"].str.strip() == "On Hold"

    # 6. High Data Utilisation Flag
    threshold = df["Data_Utilization_Score"].quantile(0.75)
    df["High_Data_Util_Flag"] = df["Data_Utilization_Score"] > threshold

    return df


df_raw = load_data()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("Eco_Africa_ECO_Platform.png", use_container_width=True)
    st.markdown(f"<hr style='border-color:{DARK_GRAY};margin:8px 0'>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{ECO_GREEN};font-weight:700;font-size:0.85rem;'>️ FILTER CONTROLS</p>", unsafe_allow_html=True)

    def ms(label, col):
        opts = sorted(df_raw[col].dropna().unique().tolist())
        return st.multiselect(label, opts, default=opts)

    sel_country    = ms(" Country",               "Country")
    sel_city       = ms("️ City",                  "City")
    sel_sector     = ms(" Sector",                "Sector")
    sel_funding_src= ms(" Funding Source",        "Funding_Source")
    sel_status     = ms(" Project Status",        "Project_Status")
    sel_platform   = ms(" Platform Used",         "Platform_Used")
    sel_analyst    = ms(" Lead Analyst",          "Lead_Analyst")
    sel_tier       = ms(" Funding Tier",          "Funding_Tier")
    sel_impact_cls = ms(" Impact Classification", "Impact_Classification")

    st.markdown(f"<p style='color:{ECO_GREEN};font-weight:700;font-size:0.85rem;margin-top:10px'> DATE RANGE</p>", unsafe_allow_html=True)
    min_d = df_raw["Date"].min()
    max_d = df_raw["Date"].max()
    if pd.isna(min_d): min_d = datetime(2020, 1, 1)
    if pd.isna(max_d): max_d = datetime.today()
    date_from = st.date_input("From", value=min_d.date() if hasattr(min_d, "date") else min_d)
    date_to   = st.date_input("To",   value=max_d.date() if hasattr(max_d, "date") else max_d)


# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()
df = df[
    df["Country"].isin(sel_country) &
    df["City"].isin(sel_city) &
    df["Sector"].isin(sel_sector) &
    df["Funding_Source"].isin(sel_funding_src) &
    df["Project_Status"].isin(sel_status) &
    df["Platform_Used"].isin(sel_platform) &
    df["Lead_Analyst"].isin(sel_analyst) &
    df["Funding_Tier"].isin(sel_tier) &
    df["Impact_Classification"].isin(sel_impact_cls)
]
# Date filter (only rows where date is not NaT)
date_mask = (
    df["Date"].isna() |
    ((df["Date"] >= pd.Timestamp(date_from)) & (df["Date"] <= pd.Timestamp(date_to)))
)
df = df[date_mask]


# ── Dashboard header ──────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='color:{ECO_GREEN};margin-bottom:0;'> ECO Africa — Investment Intelligence Dashboard</h1>"
    f"<p style='color:{SILVER};font-size:0.88rem;margin-top:2px;'>ECO Platform | Africa-wide Project Portfolio Analytics</p>",
    unsafe_allow_html=True,
)
st.markdown(f"<hr style='border-color:{DARK_GRAY};margin:6px 0 16px 0'>", unsafe_allow_html=True)


# ── KPI cards ─────────────────────────────────────────────────────────────────
total_projects    = len(df)
total_funding     = df["Funding_Amount_USD"].sum()
total_jobs        = df["Jobs_Created"].sum()
total_co2         = df["CO2_Reduction_Tons"].sum()
avg_impact        = df["Impact_Score"].mean()
active_projects   = (df["Project_Status"] == "Active").sum()
avg_data_util     = df["Data_Utilization_Score"].mean()
on_hold_count     = df["On_Hold_Flag"].sum()

c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
c1.metric(" Total Projects",        f"{total_projects:,}")
c2.metric(" Total Funding (USD)",   f"${total_funding/1e6:.2f}M")
c3.metric(" Jobs Created",          f"{int(total_jobs):,}")
c4.metric("🌱 CO₂ Reduced (Tons)",    f"{total_co2:,.0f}")
c5.metric(" Avg Impact Score",      f"{avg_impact:.1f}" if not np.isnan(avg_impact) else "N/A")
c6.metric(" Active Projects",       f"{active_projects:,}")
c7.metric(" Avg Data Util Score",   f"{avg_data_util:.1f}" if not np.isnan(avg_data_util) else "N/A")
c8.metric(" Projects On Hold",      f"{int(on_hold_count):,}")

st.markdown(f"<hr style='border-color:{DARK_GRAY};margin:16px 0'>", unsafe_allow_html=True)


# ── Row 1: Charts 1–3 ─────────────────────────────────────────────────────────
r1c1, r1c2, r1c3 = st.columns([1.2, 1.4, 1])

# Chart 1 — Projects by Sector
with r1c1:
    sec_cnt = df["Sector"].value_counts().reset_index()
    sec_cnt.columns = ["Sector", "Count"]
    fig1 = go.Figure(go.Bar(
        x=sec_cnt["Sector"], y=sec_cnt["Count"],
        marker_color=ECO_GREEN, marker_line_color=DARK_GRAY, marker_line_width=1,
        hovertemplate="<b>%{x}</b><br>Projects: %{y}<extra></extra>",
    ))
    fig1.update_layout(**dark_layout(" Projects by Sector"))
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2 — Total Funding by Country (horizontal bar)
with r1c2:
    cntry_fund = (df.groupby("Country")["Funding_Amount_USD"]
                  .sum().sort_values().reset_index())
    cntry_fund.columns = ["Country", "Funding"]
    fig2 = go.Figure(go.Bar(
        y=cntry_fund["Country"], x=cntry_fund["Funding"],
        orientation="h",
        marker=dict(
            color=cntry_fund["Funding"],
            colorscale=[[0, ECO_TEAL], [1, ECO_GREEN]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>Funding: $%{x:,.0f}<extra></extra>",
    ))
    fig2.update_layout(**dark_layout(" Total Funding by Country (USD)"))
    st.plotly_chart(fig2, use_container_width=True)

# Chart 3 — Funding Source Donut
with r1c3:
    fs_cnt = df["Funding_Source"].value_counts().reset_index()
    fs_cnt.columns = ["Source", "Count"]
    fig3 = go.Figure(go.Pie(
        labels=fs_cnt["Source"], values=fs_cnt["Count"],
        hole=0.55,
        marker=dict(colors=ACCENT_PALETTE[:len(fs_cnt)],
                    line=dict(color=DARK_GRAY, width=2)),
        textfont=dict(color=SILVER),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    fig3.update_layout(**dark_layout(" Funding Source Breakdown"), showlegend=True)
    st.plotly_chart(fig3, use_container_width=True)


# ── Row 2: Charts 4–6 ─────────────────────────────────────────────────────────
r2c1, r2c2, r2c3 = st.columns([1.2, 1, 1.4])

# Chart 4 — Impact Score Histogram
with r2c1:
    fig4 = go.Figure(go.Histogram(
        x=df["Impact_Score"].dropna(),
        nbinsx=20,
        marker_color=ECO_GREEN,
        marker_line_color=DARK_GRAY, marker_line_width=1,
        hovertemplate="Score: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig4.update_layout(**dark_layout(" Impact Score Distribution"))
    st.plotly_chart(fig4, use_container_width=True)

# Chart 5 — Project Status Pie
with r2c2:
    ps_cnt = df["Project_Status"].value_counts().reset_index()
    ps_cnt.columns = ["Status", "Count"]
    status_colors = {
        "Active":    ECO_GREEN,
        "Completed": ECO_TEAL,
        "On Hold":   ECO_ORANGE,
    }
    fig5 = go.Figure(go.Pie(
        labels=ps_cnt["Status"], values=ps_cnt["Count"],
        hole=0.45,
        marker=dict(
            colors=[status_colors.get(s, ECO_BLUE) for s in ps_cnt["Status"]],
            line=dict(color=DARK_GRAY, width=2),
        ),
        textfont=dict(color=SILVER),
        hovertemplate="<b>%{label}</b><br>%{value} projects (%{percent})<extra></extra>",
    ))
    fig5.update_layout(**dark_layout(" Project Status Share"), showlegend=True)
    st.plotly_chart(fig5, use_container_width=True)

# Chart 6 — Top 10 Projects by Funding
with r2c3:
    top10 = (df.nlargest(10, "Funding_Amount_USD")
               [["Project_Name", "Funding_Amount_USD"]]
               .sort_values("Funding_Amount_USD"))
    fig6 = go.Figure(go.Bar(
        y=top10["Project_Name"], x=top10["Funding_Amount_USD"],
        orientation="h",
        marker=dict(
            color=top10["Funding_Amount_USD"],
            colorscale=[[0, ECO_BLUE], [1, ECO_GREEN]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
    ))
    fig6.update_layout(**dark_layout(" Top 10 Projects by Funding", height=420))
    st.plotly_chart(fig6, use_container_width=True)


# ── Row 3: Charts 7–9 ─────────────────────────────────────────────────────────
r3c1, r3c2, r3c3 = st.columns([1.2, 1.4, 1.1])

# Chart 7 — Jobs Created by Country
with r3c1:
    jobs_cntry = (df.groupby("Country")["Jobs_Created"]
                  .sum().sort_values(ascending=False).reset_index())
    fig7 = go.Figure(go.Bar(
        x=jobs_cntry["Country"], y=jobs_cntry["Jobs_Created"],
        marker_color=ECO_TEAL, marker_line_color=DARK_GRAY, marker_line_width=1,
        hovertemplate="<b>%{x}</b><br>Jobs: %{y:,}<extra></extra>",
    ))
    fig7.update_layout(**dark_layout(" Jobs Created by Country"))
    st.plotly_chart(fig7, use_container_width=True)

# Chart 8 — Data Utilisation vs Impact Score scatter
with r3c2:
    scatter_df = df.dropna(subset=["Data_Utilization_Score", "Impact_Score"])
    fig8 = px.scatter(
        scatter_df,
        x="Data_Utilization_Score", y="Impact_Score",
        color="Sector",
        color_discrete_sequence=ACCENT_PALETTE,
        hover_data=["Project_Name", "Country", "Funding_Amount_USD"],
        labels={"Data_Utilization_Score": "Data Utilization Score",
                "Impact_Score": "Impact Score"},
    )
    fig8.update_traces(marker=dict(size=7, opacity=0.85,
                                   line=dict(width=0.5, color=DARK_GRAY)))
    fig8.update_layout(**dark_layout(" Data Utilization vs Impact Score", height=400))
    st.plotly_chart(fig8, use_container_width=True)

# Chart 9 — CO₂ Reduction by Sector
with r3c3:
    co2_sec = (df.groupby("Sector")["CO2_Reduction_Tons"]
               .sum().sort_values(ascending=True).reset_index())
    fig9 = go.Figure(go.Bar(
        y=co2_sec["Sector"], x=co2_sec["CO2_Reduction_Tons"],
        orientation="h",
        marker=dict(
            color=co2_sec["CO2_Reduction_Tons"],
            colorscale=[[0, ECO_BLUE], [0.5, ECO_TEAL], [1, ECO_GREEN]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>CO₂: %{x:,.1f} tons<extra></extra>",
    ))
    fig9.update_layout(**dark_layout("🌱 CO₂ Reduction by Sector"))
    st.plotly_chart(fig9, use_container_width=True)


# ── Chart 10 — Advanced 3D Intelligence Scatter ───────────────────────────────
st.markdown(f"<h3 style='color:{ECO_GREEN};'> 3D Investment Intelligence Scatter</h3>",
            unsafe_allow_html=True)
scatter3d_df = df.dropna(subset=["Funding_Amount_USD", "Jobs_Created",
                                  "CO2_Reduction_Tons", "Impact_Score"])
fig10 = go.Figure(go.Scatter3d(
    x=scatter3d_df["Funding_Amount_USD"],
    y=scatter3d_df["Jobs_Created"],
    z=scatter3d_df["CO2_Reduction_Tons"],
    mode="markers",
    marker=dict(
        size=5,
        color=scatter3d_df["Impact_Score"],
        colorscale=[[0, ECO_ORANGE], [0.5, ECO_TEAL], [1, ECO_GREEN]],
        opacity=0.85,
        colorbar=dict(
            title=dict(text="Impact Score", font=dict(color=SILVER)),
            tickfont=dict(color=SILVER),
            bgcolor=DARK_GRAY,
        ),
        line=dict(width=0.3, color=DARK_GRAY),
    ),
    customdata=scatter3d_df[["Project_Name", "Country", "Sector",
                              "Funding_Source", "Project_Status"]].values,
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Country: %{customdata[1]}<br>"
        "Sector: %{customdata[2]}<br>"
        "Source: %{customdata[3]}<br>"
        "Status: %{customdata[4]}<br>"
        "Funding: $%{x:,.0f}<br>"
        "Jobs: %{y:,}<br>"
        "CO₂: %{z:,.1f} tons<extra></extra>"
    ),
))
fig10.update_layout(
    paper_bgcolor=DARK_GRAY,
    height=580,
    margin=dict(l=0, r=0, t=30, b=0),
    scene=dict(
        bgcolor=DARK_GRAY,
        xaxis=dict(
            title=dict(text="Funding (USD)", font=dict(color=SILVER)),
            tickfont=dict(color=SILVER),
            gridcolor="rgba(210,218,226,0.10)",
            backgroundcolor=DARK_GRAY,
        ),
        yaxis=dict(
            title=dict(text="Jobs Created", font=dict(color=SILVER)),
            tickfont=dict(color=SILVER),
            gridcolor="rgba(210,218,226,0.10)",
            backgroundcolor=DARK_GRAY,
        ),
        zaxis=dict(
            title=dict(text="CO₂ Reduced (Tons)", font=dict(color=SILVER)),
            tickfont=dict(color=SILVER),
            gridcolor="rgba(210,218,226,0.10)",
            backgroundcolor=DARK_GRAY,
        ),
    ),
    font=dict(color=SILVER),
)
st.plotly_chart(fig10, use_container_width=True)

st.markdown(f"<hr style='border-color:{DARK_GRAY};margin:10px 0 20px 0'>", unsafe_allow_html=True)


# ── Filtered Data Table ────────────────────────────────────────────────────────
with st.expander(" Filtered Dataset — All Records"):
    display_cols = ["Record_ID", "Date", "Country", "City", "Sector", "Project_Name",
                    "Funding_Amount_USD", "Funding_Source", "Project_Status",
                    "Jobs_Created", "CO2_Reduction_Tons", "Data_Utilization_Score",
                    "Impact_Score", "Lead_Analyst", "Platform_Used",
                    "Funding_Tier", "Impact_Classification"]
    st.dataframe(
        df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=320,
    )
    st.markdown(
        f"<small style='color:{SILVER};'>Showing <b style='color:{ECO_GREEN};'>"
        f"{len(df):,}</b> of {len(df_raw):,} total records</small>",
        unsafe_allow_html=True,
    )


# ── Executive Insight Panel ────────────────────────────────────────────────────
with st.expander(" Executive Insights — ECO Africa Platform Operations Overview"):
    st.markdown(f"""
<div style="color:{SILVER};line-height:1.8;font-size:0.92rem;">

<p><span style="color:{ECO_GREEN};font-weight:700;"> Impact Score Distribution</span><br>
The distribution of Impact Scores across the portfolio reveals the overall quality and
effectiveness of ECO-funded projects in African markets. A high concentration of scores
above 75 signals strong project outcomes and sound analyst selection. Where scores cluster
below 50, leadership should review sector allocation and project governance frameworks
to raise average portfolio performance.</p>

<p><span style="color:{ECO_TEAL};font-weight:700;"> Funding Landscape & Concentration Risk</span><br>
Funding patterns across countries, sectors, and sources indicate where capital is being
deployed most heavily. Heavy reliance on a single source (e.g., Grants or Government)
introduces concentration risk. Diversifying funding across Private Equity, NGO, and Local
Investors builds resilience. Sectors like Clean Energy and FinTech consistently attract
larger ticket sizes — a signal for strategic pipeline prioritisation.</p>

<p><span style="color:{ECO_BLUE};font-weight:700;"> Project Status & Pipeline Health</span><br>
The Active vs. Completed vs. On Hold breakdown is a direct indicator of operational delivery
capacity. A high On Hold ratio signals bottlenecks in execution, regulatory friction, or
capital call delays. Commercial teams should triage On Hold projects quarterly and establish
escalation paths to convert them back into active delivery.</p>

<p><span style="color:{ECO_ORANGE};font-weight:700;">🌱 ESG & Social Return on Investment (SROI)</span><br>
The CO₂ Efficiency Ratio (tons reduced per $1M invested) and Jobs Per Million USD are the
platform's core ESG KPIs. High-efficiency projects should be showcased in investor reports.
Low-efficiency outliers need post-investment review. These metrics also inform UN SDG
alignment reporting, particularly SDG 8 (Decent Work) and SDG 13 (Climate Action).</p>

<p><span style="color:{ECO_GREEN};font-weight:700;"> Operational Decision-Making</span><br>
Platform analysts can use the sidebar filters to isolate specific countries, sectors, or
funding tiers for portfolio review. The 3D Intelligence Scatter enables exploration of the
relationship between capital invested, employment generated, and environmental impact — all
in one interactive view. Executives reviewing weekly performance should anchor on the 8 KPI
cards at the top, then drill into the charts to identify anomalies and growth opportunities.</p>

</div>
""", unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"<hr style='border-color:{DARK_GRAY};margin:20px 0 8px 0'>", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center;color:{SILVER};font-size:0.78rem;'>"
    f"ECO Africa ECO Platform Intelligence Dashboard &nbsp;|&nbsp; "
    f"<span style='color:{ECO_GREEN};'>ToheebBI</span> &nbsp;|&nbsp; "
    f"Powered by Streamlit + Plotly</p>",
    unsafe_allow_html=True,
)