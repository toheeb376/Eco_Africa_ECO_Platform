# =============================================================================
# MIRABEL CENTRE — Case Management Intelligence Dashboard
# Stack: Python · Streamlit · Plotly · Pandas · OpenPyXL
# Theme: Burnt-Orange / Terracotta on Deep Black
# =============================================================================
# HOW TO RUN:
#   1. pip install streamlit pandas plotly openpyxl
#   2. Place app.py, Mirabel_Centre_Dataset.xlsx, Mirabel_Centre.png in same folder
#   3. streamlit run app.py
#   4. Open http://localhost:8501 in your browser
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mirabel Centre Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand Colour Palette ────────────────────────────────────────────────────────
C = {
    "burnt_orange": "rgb(255,110,12)",
    "warm_peach":   "rgb(251,148,80)",
    "terracotta":   "rgb(227,114,69)",
    "deep_sienna":  "rgb(182,95,56)",
    "near_black":   "rgb(12,10,8)",
    "charcoal":     "rgb(24,22,20)",
    "dark_surface": "rgb(42,38,34)",
    "warm_silver":  "rgb(220,210,200)",
}

CHART_COLORS = [
    C["burnt_orange"], C["warm_peach"], C["terracotta"],
    C["deep_sienna"],  C["warm_silver"],
]

# ── CSS Injection ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif !important;
    color: {C['warm_silver']} !important;
  }}
  .stApp {{
    background-color: {C['near_black']};
  }}
  section[data-testid="stSidebar"] {{
    background-color: {C['charcoal']} !important;
    border-right: 1px solid {C['deep_sienna']};
  }}
  section[data-testid="stSidebar"] * {{
    color: {C['warm_silver']} !important;
  }}
  .stMetric {{
    background-color: {C['dark_surface']};
    border: 1px solid {C['deep_sienna']};
    border-radius: 8px;
    padding: 16px 14px !important;
  }}
  .stMetric label {{ color: {C['warm_silver']} !important; font-size: 0.78rem !important; letter-spacing: 0.05em; text-transform: uppercase; }}
  .stMetric [data-testid="stMetricValue"] {{
    color: {C['burnt_orange']} !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
    font-family: 'JetBrains Mono', monospace !important;
  }}
  .stMetric [data-testid="stMetricDelta"] {{ color: {C['warm_peach']} !important; }}
  h1, h2, h3 {{ color: {C['burnt_orange']} !important; }}
  h4, h5, h6 {{ color: {C['warm_peach']} !important; }}
  hr {{ border-color: {C['deep_sienna']} !important; }}
  .stSelectbox > div, .stMultiSelect > div {{
    background-color: {C['dark_surface']} !important;
    border: 1px solid {C['deep_sienna']} !important;
    border-radius: 6px !important;
  }}
  .stDateInput > div {{
    background-color: {C['dark_surface']} !important;
    border: 1px solid {C['deep_sienna']} !important;
    border-radius: 6px !important;
  }}
  .stDataFrame, .dataframe {{
    background-color: {C['dark_surface']} !important;
    color: {C['warm_silver']} !important;
  }}
  .stExpander {{
    background-color: {C['dark_surface']};
    border: 1px solid {C['deep_sienna']};
    border-radius: 8px;
  }}
  .stExpander summary {{
    color: {C['burnt_orange']} !important;
    font-weight: 600;
  }}
  .block-container {{ padding-top: 2.5rem !important; padding-bottom: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }}
  div[data-testid="stSidebarNav"] {{ display: none; }}
  .stMultiSelect [data-baseweb="tag"] {{
    background-color: {C['burnt_orange']} !important;
    color: {C['near_black']} !important;
  }}
  .dashboard-title {{
    font-size: 1.7rem;
    font-weight: 700;
    color: {C['burnt_orange']};
    letter-spacing: 0.04em;
    padding-bottom: 0;
    margin-bottom: 0;
  }}
  .dashboard-subtitle {{
    font-size: 0.82rem;
    color: {C['warm_silver']};
    opacity: 0.7;
    margin-top: 2px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }}
  .section-header {{
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {C['warm_peach']};
    font-weight: 600;
    margin-bottom: 6px;
    margin-top: 18px;
    border-bottom: 1px solid {C['deep_sienna']};
    padding-bottom: 4px;
  }}
</style>
""", unsafe_allow_html=True)


# ── Data Loading & Preprocessing ───────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("Mirabel_Centre_Dataset.xlsx", dtype=str)

    # Strip whitespace from all string columns
    for col in df.columns:
        df[col] = df[col].str.strip()

    # Convert numeric columns
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Counseling_Sessions"] = pd.to_numeric(df["Counseling_Sessions"], errors="coerce")

    # Parse dates
    df["Date_Reported"] = pd.to_datetime(df["Date_Reported"], errors="coerce")

    # Derived: Reporting Year-Month for time series
    df["Year_Month"] = df["Date_Reported"].dt.to_period("M").astype(str)
    df["Year"] = df["Date_Reported"].dt.year.astype("Int64")
    df["Month"] = df["Date_Reported"].dt.month

    # Derived: Age Group Tier
    def age_group(age):
        if pd.isna(age): return "Unknown"
        if age < 18: return "Minor (< 18)"
        if age <= 35: return "Young Adult (18–35)"
        return "Adult (> 35)"

    df["Age_Group_Tier"] = df["Age"].apply(age_group)

    # Derived: Case Complexity Score (normalised 0–1)
    max_s = df["Counseling_Sessions"].max()
    df["Complexity_Score"] = (df["Counseling_Sessions"] / max_s).clip(0, 1)

    # Derived: Flags
    df["Full_Service_Flag"]   = df["Service_Type"] == "Full Support"
    df["Unresolved_Flag"]     = df["Case_Status"].isin(["Open", "In Progress"])
    df["Medical_Gap_Flag"]    = df["Medical_Exam_Completed"] == "No"
    df["Legal_Gap_Flag"]      = df["Legal_Assistance_Provided"] == "No"

    # Numeric encode Case_Status for 3D scatter
    status_map = {"Open": 0, "In Progress": 1, "Closed": 2}
    df["Case_Status_Num"] = df["Case_Status"].map(status_map)

    return df


df = load_data()


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("Mirabel_Centre.png", use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header"> Date Range</div>', unsafe_allow_html=True)
    min_date = df["Date_Reported"].min().date()
    max_date = df["Date_Reported"].max().date()
    date_range = st.date_input(
        "Date Reported",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-header"> Filters</div>', unsafe_allow_html=True)

    def multiselect(label, col):
        opts = sorted(df[col].dropna().unique().tolist())
        return st.multiselect(label, opts, default=opts)

    sel_gender       = multiselect("Gender",                    "Gender")
    sel_state        = multiselect("State",                     "State")
    sel_referral     = multiselect("Referral Source",           "Referral_Source")
    sel_service      = multiselect("Service Type",              "Service_Type")
    sel_medical      = multiselect("Medical Exam Completed",    "Medical_Exam_Completed")
    sel_legal        = multiselect("Legal Assistance Provided", "Legal_Assistance_Provided")
    sel_followup     = multiselect("Follow-Up Status",          "Follow_Up_Status")
    sel_case_status  = multiselect("Case Status",               "Case_Status")
    sel_age_group    = multiselect("Age Group",                 "Age_Group_Tier")


# ── Apply Filters ───────────────────────────────────────────────────────────────
dff = df.copy()

# Date filter
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    d0 = pd.Timestamp(date_range[0])
    d1 = pd.Timestamp(date_range[1])
    dff = dff[(dff["Date_Reported"] >= d0) & (dff["Date_Reported"] <= d1)]

dff = dff[
    dff["Gender"].isin(sel_gender) &
    dff["State"].isin(sel_state) &
    dff["Referral_Source"].isin(sel_referral) &
    dff["Service_Type"].isin(sel_service) &
    dff["Medical_Exam_Completed"].isin(sel_medical) &
    dff["Legal_Assistance_Provided"].isin(sel_legal) &
    dff["Follow_Up_Status"].isin(sel_followup) &
    dff["Case_Status"].isin(sel_case_status) &
    dff["Age_Group_Tier"].isin(sel_age_group)
]


# ── Shared chart layout function ────────────────────────────────────────────────
def chart_layout(fig, title="", height=360):
    fig.update_layout(
        title=dict(text=title, font=dict(color=C["warm_peach"], size=13, family="Sora"), x=0),
        plot_bgcolor  = C["dark_surface"],
        paper_bgcolor = C["dark_surface"],
        font=dict(color=C["warm_silver"], family="Sora", size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(
            bgcolor=C["charcoal"], bordercolor=C["deep_sienna"],
            borderwidth=1, font=dict(color=C["warm_silver"], size=10)
        ),
        hoverlabel=dict(bgcolor=C["charcoal"], font_color=C["warm_silver"]),
    )
    fig.update_xaxes(
        gridcolor=C["deep_sienna"], linecolor=C["deep_sienna"],
        tickfont=dict(color=C["warm_silver"]), title_font=dict(color=C["warm_silver"]),
        zerolinecolor=C["deep_sienna"],
    )
    fig.update_yaxes(
        gridcolor=C["deep_sienna"], linecolor=C["deep_sienna"],
        tickfont=dict(color=C["warm_silver"]), title_font=dict(color=C["warm_silver"]),
        zerolinecolor=C["deep_sienna"],
    )
    return fig


# ── Dashboard Header ────────────────────────────────────────────────────────────
# ── Dashboard Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 24px 0 12px 0;">
    <div class="dashboard-title" style="font-size:2.2rem;"> MIRABEL CENTRE</div>
    <div class="dashboard-subtitle" style="font-size:0.9rem; margin-top:6px;">
        Case Management Intelligence Dashboard — Survivor Support Analytics
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


# ── KPI Section ─────────────────────────────────────────────────────────────────
total_cases     = len(dff)
total_survivors = dff["Case_ID"].nunique()
open_cases      = (dff["Case_Status"] == "Open").sum()
closed_cases    = (dff["Case_Status"] == "Closed").sum()
med_pct         = round((dff["Medical_Exam_Completed"] == "Yes").sum() / total_cases * 100, 1) if total_cases else 0
legal_pct       = round((dff["Legal_Assistance_Provided"] == "Yes").sum() / total_cases * 100, 1) if total_cases else 0
avg_counseling  = round(dff["Counseling_Sessions"].mean(), 1) if total_cases else 0
pending_followup= (dff["Follow_Up_Status"] == "Pending").sum()

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
k1.metric("Total Cases",           f"{total_cases:,}")
k2.metric("Survivors Served",      f"{total_survivors:,}")
k3.metric("Open Cases",            f"{open_cases:,}")
k4.metric("Cases Closed",          f"{closed_cases:,}")
k5.metric("Medical Exams Done",    f"{med_pct}%")
k6.metric("Legal Assistance Rate", f"{legal_pct}%")
k7.metric("Avg Counseling Sessions", f"{avg_counseling}")
k8.metric("Pending Follow-Ups",    f"{pending_followup:,}")

st.markdown("---")


# ── ROW 1: Cases by State  |  Service Type Donut ───────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    state_counts = dff.groupby("State", observed=True).size().reset_index(name="Count").sort_values("Count")
    fig = px.bar(state_counts, x="Count", y="State", orientation="h",
                 color_discrete_sequence=[C["burnt_orange"]],
                 labels={"Count": "Cases", "State": ""})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{y}</b><br>Cases: %{x}<extra></extra>")
    st.plotly_chart(chart_layout(fig, " Cases by State"), use_container_width=True)

with col2:
    svc_counts = dff["Service_Type"].value_counts().reset_index()
    svc_counts.columns = ["Service", "Count"]
    fig = go.Figure(go.Pie(
        labels=svc_counts["Service"], values=svc_counts["Count"],
        hole=0.58,
        marker=dict(colors=CHART_COLORS, line=dict(color=C["near_black"], width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} cases (%{percent})<extra></extra>",
        textfont=dict(color=C["warm_silver"]),
    ))
    fig.add_annotation(text="Service<br>Type", x=0.5, y=0.5, showarrow=False,
                       font=dict(color=C["warm_peach"], size=12, family="Sora"))
    st.plotly_chart(chart_layout(fig, " Service Type Distribution"), use_container_width=True)


# ── ROW 2: Referral Source  |  Case Status  |  Follow-Up Status ────────────────
col3, col4, col5 = st.columns(3)

with col3:
    ref_counts = dff["Referral_Source"].value_counts().reset_index()
    ref_counts.columns = ["Source", "Count"]
    fig = px.bar(ref_counts, x="Source", y="Count",
                 color_discrete_sequence=[C["terracotta"]],
                 labels={"Source": "", "Count": "Cases"})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{y} cases<extra></extra>")
    st.plotly_chart(chart_layout(fig, " Referral Source Breakdown"), use_container_width=True)

with col4:
    status_counts = dff["Case_Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    color_map = {"Open": C["burnt_orange"], "In Progress": C["warm_peach"], "Closed": C["deep_sienna"]}
    fig = px.bar(status_counts, x="Status", y="Count",
                 color="Status", color_discrete_map=color_map,
                 labels={"Status": "", "Count": "Cases"})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{y} cases<extra></extra>")
    fig.update_layout(showlegend=False)
    st.plotly_chart(chart_layout(fig, " Case Status Overview"), use_container_width=True)

with col5:
    fu_counts = dff["Follow_Up_Status"].value_counts().reset_index()
    fu_counts.columns = ["Status", "Count"]
    fig = go.Figure(go.Pie(
        labels=fu_counts["Status"], values=fu_counts["Count"],
        hole=0.55,
        marker=dict(colors=CHART_COLORS, line=dict(color=C["near_black"], width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
        textfont=dict(color=C["warm_silver"]),
    ))
    fig.add_annotation(text="Follow-Up", x=0.5, y=0.5, showarrow=False,
                       font=dict(color=C["warm_peach"], size=11, family="Sora"))
    st.plotly_chart(chart_layout(fig, " Follow-Up Status Distribution"), use_container_width=True)


# ── ROW 3: Gender  |  Cases Over Time ──────────────────────────────────────────
col6, col7 = st.columns([1, 3])

with col6:
    gender_counts = dff["Gender"].value_counts().reset_index()
    gender_counts.columns = ["Gender", "Count"]
    fig = go.Figure(go.Pie(
        labels=gender_counts["Gender"], values=gender_counts["Count"],
        hole=0.52,
        marker=dict(colors=[C["burnt_orange"], C["warm_peach"]], line=dict(color=C["near_black"], width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
        textfont=dict(color=C["warm_silver"]),
    ))
    fig.add_annotation(text="Gender", x=0.5, y=0.5, showarrow=False,
                       font=dict(color=C["warm_peach"], size=12, family="Sora"))
    st.plotly_chart(chart_layout(fig, " Gender Breakdown"), use_container_width=True)

with col7:
    time_df = dff.dropna(subset=["Date_Reported"]).copy()
    time_df["YearMonth"] = time_df["Date_Reported"].dt.to_period("M").dt.to_timestamp()
    monthly = time_df.groupby("YearMonth").size().reset_index(name="Cases")
    monthly = monthly.sort_values("YearMonth")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["YearMonth"], y=monthly["Cases"],
        mode="lines+markers",
        line=dict(color=C["burnt_orange"], width=2.5, shape="spline"),
        marker=dict(color=C["warm_peach"], size=6, line=dict(color=C["near_black"], width=1)),
        fill="tozeroy",
        fillcolor="rgba(255,110,12,0.12)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Cases: %{y}<extra></extra>",
    ))
    st.plotly_chart(chart_layout(fig, " Cases Reported Over Time", height=320), use_container_width=True)


# ── ROW 4: Medical Exam by State  |  Counseling Distribution ───────────────────
col8, col9 = st.columns(2)

with col8:
    med_state = dff.groupby(["State", "Medical_Exam_Completed"], observed=True).size().reset_index(name="Count")
    fig = px.bar(med_state, x="State", y="Count", color="Medical_Exam_Completed",
                 barmode="group",
                 color_discrete_map={"Yes": C["burnt_orange"], "No": C["deep_sienna"]},
                 labels={"State": "", "Count": "Cases", "Medical_Exam_Completed": "Exam Done"})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{y} cases<extra></extra>")
    st.plotly_chart(chart_layout(fig, " Medical Exam Completion by State"), use_container_width=True)

with col9:
    fig = px.histogram(
        dff.dropna(subset=["Counseling_Sessions"]),
        x="Counseling_Sessions",
        nbins=10,
        color_discrete_sequence=[C["terracotta"]],
        labels={"Counseling_Sessions": "Sessions", "count": "Frequency"},
    )
    fig.update_traces(marker_line_color=C["near_black"], marker_line_width=1,
                      hovertemplate="Sessions: %{x}<br>Count: %{y}<extra></extra>")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(chart_layout(fig, " Counseling Sessions Distribution"), use_container_width=True)


# ── ROW 5: Age Group  |  Legal Assistance by State ─────────────────────────────
col10, col11 = st.columns(2)

with col10:
    age_counts = dff["Age_Group_Tier"].value_counts().reset_index()
    age_counts.columns = ["Age Group", "Count"]
    fig = px.bar(age_counts, x="Age Group", y="Count",
                 color="Age Group",
                 color_discrete_sequence=CHART_COLORS,
                 labels={"Age Group": "", "Count": "Survivors"})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{y} survivors<extra></extra>")
    fig.update_layout(showlegend=False)
    st.plotly_chart(chart_layout(fig, "👤 Survivors by Age Group"), use_container_width=True)

with col11:
    legal_state = dff.groupby(["State", "Legal_Assistance_Provided"], observed=True).size().reset_index(name="Count")
    fig = px.bar(legal_state, x="State", y="Count", color="Legal_Assistance_Provided",
                 barmode="group",
                 color_discrete_map={"Yes": C["warm_peach"], "No": C["deep_sienna"]},
                 labels={"State": "", "Count": "Cases", "Legal_Assistance_Provided": "Legal Help"})
    fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{y} cases<extra></extra>")
    st.plotly_chart(chart_layout(fig, " Legal Assistance Provided by State"), use_container_width=True)


# ── ROW 6: 3D Intelligence Scatter ─────────────────────────────────────────────
st.markdown("---")
st.markdown("####  Advanced 3D Case Intelligence Scatter")
st.caption("X — Age  ·  Y — Counseling Sessions  ·  Z — Case Status (0=Open, 1=In Progress, 2=Closed)  ·  Colour — Case Complexity Score")

scatter_df = dff.dropna(subset=["Age", "Counseling_Sessions", "Case_Status_Num"]).copy()

fig3d = go.Figure(go.Scatter3d(
    x=scatter_df["Age"],
    y=scatter_df["Counseling_Sessions"],
    z=scatter_df["Case_Status_Num"],
    mode="markers",
    marker=dict(
        size=5,
        color=scatter_df["Complexity_Score"],
        colorscale=[
            [0.0, C["deep_sienna"]],
            [0.5, C["terracotta"]],
            [1.0, C["burnt_orange"]],
        ],
        colorbar=dict(
            title=dict(text="Complexity", font=dict(color=C["warm_silver"], size=11)),
            tickfont=dict(color=C["warm_silver"]),
            bgcolor=C["dark_surface"],
            bordercolor=C["deep_sienna"],
        ),
        opacity=0.85,
        line=dict(width=0),
    ),
    customdata=scatter_df[["Case_ID", "State", "Service_Type", "Referral_Source", "Gender"]].values,
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "State: %{customdata[1]}<br>"
        "Service: %{customdata[2]}<br>"
        "Referral: %{customdata[3]}<br>"
        "Gender: %{customdata[4]}<br>"
        "Age: %{x}  Sessions: %{y}  Status: %{z}<extra></extra>"
    ),
))

fig3d.update_layout(
    height=550,
    paper_bgcolor=C["dark_surface"],
    margin=dict(l=0, r=0, t=20, b=0),
    scene=dict(
        bgcolor=C["dark_surface"],
        xaxis=dict(
            title=dict(text="Age", font=dict(color=C["warm_silver"], size=11)),
            tickfont=dict(color=C["warm_silver"]),
            gridcolor=C["deep_sienna"],
            backgroundcolor=C["dark_surface"],
        ),
        yaxis=dict(
            title=dict(text="Counseling Sessions", font=dict(color=C["warm_silver"], size=11)),
            tickfont=dict(color=C["warm_silver"]),
            gridcolor=C["deep_sienna"],
            backgroundcolor=C["dark_surface"],
        ),
        zaxis=dict(
            title=dict(text="Case Status (0/1/2)", font=dict(color=C["warm_silver"], size=11)),
            tickfont=dict(color=C["warm_silver"]),
            gridcolor=C["deep_sienna"],
            backgroundcolor=C["dark_surface"],
            tickvals=[0, 1, 2],
            ticktext=["Open", "In Progress", "Closed"],
        ),
    ),
    hoverlabel=dict(bgcolor=C["charcoal"], font_color=C["warm_silver"]),
)

st.plotly_chart(fig3d, use_container_width=True)


# ── Filtered Data Table ─────────────────────────────────────────────────────────
st.markdown("---")
with st.expander(" View Filtered Case Records"):
    display_cols = ["Case_ID", "Date_Reported", "Age", "Gender", "State",
                    "Referral_Source", "Service_Type", "Medical_Exam_Completed",
                    "Counseling_Sessions", "Legal_Assistance_Provided",
                    "Follow_Up_Status", "Case_Status", "Age_Group_Tier"]
    st.dataframe(
        dff[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=320,
    )
    st.caption(f"Showing {len(dff):,} records matching current filters.")


# ── Executive Insights Panel ────────────────────────────────────────────────────
st.markdown("---")
with st.expander(" Executive Insights — Mirabel Centre Case Management Overview"):
    st.markdown(f"""
<div style="color:{C['warm_silver']}; line-height:1.85; font-size:0.92rem;">

<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 Case Resolution Capacity
</span><br>
The <b>Case Status</b> distribution reveals the balance between active demand and operational throughput.
A high proportion of <i>Open</i> or <i>In Progress</i> cases relative to <i>Closed</i> cases signals caseload pressure and
may indicate the need for additional caseworkers, faster triaging pathways, or streamlined documentation processes.
Management should monitor the ratio of Closed to Open cases weekly as a primary performance indicator.

<br><br>
<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 Referral Channel Intelligence
</span><br>
The <b>Referral Source</b> breakdown identifies which community channels — hospitals, NGOs, police, family, or self-referral —
are most actively routing survivors to the Centre. Dominant referral sources deserve sustained institutional partnerships,
while underperforming channels represent untapped outreach opportunities. A significant volume of self-referrals indicates
growing community trust and awareness of Mirabel's services.

<br><br>
<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 Service Delivery Gaps
</span><br>
The <b>Medical Exam Completion</b> and <b>Legal Assistance Provided</b> rates are critical service quality metrics.
A completion rate below 80% in either dimension signals systemic bottlenecks — whether staffing shortfalls,
geographic access barriers, or documentation delays. These gaps should be broken down by State to
identify which locations require targeted resource deployment or referral network strengthening.

<br><br>
<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 Counseling Resource Planning
</span><br>
The <b>Counseling Sessions</b> histogram informs staffing and scheduling strategy. A distribution skewed toward
higher session counts signals complex, long-term cases requiring sustained engagement. Programme managers
should use average sessions per service type to allocate counselor capacity, forecast workload,
and justify staffing requests to donors or board stakeholders.

<br><br>
<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 3D Intelligence Scatter — Priority Intervention Profiling
</span><br>
The 3D scatter view cross-references <b>Age</b>, <b>Counseling Sessions</b>, and <b>Case Status</b>
with colour-coded <b>Case Complexity Score</b>. High-complexity cases (deep orange) that remain Open
represent the highest-priority intervention candidates. Clusters of young survivors (minors and young adults)
with elevated session counts and unresolved status should trigger immediate supervisory review.

<br><br>
<span style="color:{C['burnt_orange']}; font-weight:700; font-size:1.0rem;">
🔹 Operational & Donor Reporting
</span><br>
Programme officers can use this dashboard for <b>weekly operational stand-ups</b>, surfacing real-time case volumes
by state, referral source trends, and pending follow-up queues. For donor reporting, the KPI row provides
instant access to headline impact metrics — survivors served, legal assistance rate, and medical exam completion —
all filterable by date range to match any reporting period. The filtered data table supports direct case-level
export for case conference preparation or audit documentation.

</div>
""", unsafe_allow_html=True)


# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="text-align:center; color:{C["deep_sienna"]}; font-size:0.72rem; letter-spacing:0.08em;">'
    f'MIRABEL CENTRE · Case Intelligence Dashboard · Built by <b style="color:{C["terracotta"]};">ToheebBI</b> '
    f'· Transforming Data into Strategic Intelligence'
    f'</div>',
    unsafe_allow_html=True,
)