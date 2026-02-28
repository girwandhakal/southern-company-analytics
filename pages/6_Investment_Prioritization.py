import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data

st.set_page_config(
    page_title="Investment Prioritization", page_icon="💰", layout="wide"
)

# ── Executive styling (consistent with other tabs) ──────────────────────────
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fc 0%, #ffffff 100%);
        border: 1px solid #e2e6ed;
        border-radius: 12px;
        padding: 18px 20px 14px 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.82rem !important;
        font-weight: 600;
        color: #5a6577 !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
        font-weight: 700;
        color: #1a1f36 !important;
    }
    .stPlotlyChart { margin-top: 8px; }
    hr { border: none; border-top: 1px solid #e8ecf1; margin: 24px 0 18px 0; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data loading & filtering ────────────────────────────────────────────────
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv"
)

REQUIRED_COLS = [
    "Hostname",
    "State",
    "Site_Code",
    "Risk_Level",
    "Total_Replacement_Cost",
    "Risk_Score",
    "Is_Decom",
]

df = load_data(DATA_PATH)[REQUIRED_COLS].copy()
df["Total_Replacement_Cost"] = pd.to_numeric(
    df["Total_Replacement_Cost"], errors="coerce"
).fillna(0)
df["Risk_Score"] = pd.to_numeric(df["Risk_Score"], errors="coerce").fillna(0)
df["Is_Decom"] = df["Is_Decom"].astype(bool)

# Only actionable, non-decommissioned devices with real risk
df = df[(~df["Is_Decom"]) & (df["Risk_Score"] > 0)].copy()

PLOTLY_CLEAN = {"displayModeBar": False}


def fmt_currency(val: float) -> str:
    """Format a number as compact USD currency."""
    if val >= 1_000_000:
        return f"\\${val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"\\${val / 1_000:,.1f}K"
    return f"\\${val:,.0f}"


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='text-align:center; color:#1a1f36; margin-bottom:4px;'>"
    "Investment Prioritization &amp; Risk Reduction</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#7b8794; margin-top:0; font-size:1.05rem;'>"
    "Data-driven replacement roadmap based on risk severity, support status, and cost.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
#  BUDGET IMPACT SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Budget Impact Simulator")

budget = st.slider(
    "Select 2026 CapEx Budget",
    min_value=0,
    max_value=5_000_000,
    value=1_000_000,
    step=50_000,
    format="$%d",
)

# Sort by risk then compute cumulative cost
priority_df = df.sort_values("Risk_Score", ascending=False).reset_index(drop=True)
priority_df["Cumulative_Cost"] = priority_df["Total_Replacement_Cost"].cumsum()

# Devices fully replaceable within budget
devices_in_budget = int((priority_df["Cumulative_Cost"] <= budget).sum())
total_devices = len(priority_df)
pct_cleared = (devices_in_budget / total_devices * 100) if total_devices > 0 else 0

# KPI cards
k1, k2, k3 = st.columns(3)
k1.metric("Selected Budget", fmt_currency(budget))
k2.metric("Devices Fully Replaced", f"{devices_in_budget:,} / {total_devices:,}")
k3.metric("Critical Debt Cleared", f"{pct_cleared:.1f}%")

if devices_in_budget > 0:
    actual_spend = priority_df.loc[: devices_in_budget - 1, "Total_Replacement_Cost"].sum()
    st.success(
        f"With a budget of {fmt_currency(budget)}, you can fully replace the top "
        f"{devices_in_budget:,} highest-risk devices (actual cost "
        f"{fmt_currency(actual_spend)}), completely clearing "
        f"{pct_cleared:.1f}% of critical technical debt."
    )
else:
    st.warning(
        "The selected budget does not cover even the single highest-risk device. "
        "Consider increasing the allocation."
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
#  PRIORITY RANKING TABLE
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Priority Ranking — Top Devices Within Budget")

DISPLAY_COLS = [
    "Hostname",
    "State",
    "Site_Code",
    "Risk_Level",
    "Risk_Score",
    "Total_Replacement_Cost",
]

table_df = priority_df.loc[
    priority_df["Cumulative_Cost"] <= budget, DISPLAY_COLS
].head(100)

if table_df.empty:
    st.info("No devices fall within the selected budget.")
else:
    display_df = table_df.copy()
    display_df["Total_Replacement_Cost"] = display_df["Total_Replacement_Cost"].round(0)
    max_risk = float(display_df["Risk_Score"].max()) if not display_df.empty else 100
    st.dataframe(
        display_df,
        use_container_width=True,
        height=460,
        column_config={
            "Risk_Score": st.column_config.ProgressColumn(
                "Risk Score",
                format="%.1f",
                min_value=0,
                max_value=max_risk,
            ),
            "Total_Replacement_Cost": st.column_config.NumberColumn(
                "Total Replacement Cost",
                format="$ %.0f",
            ),
        },
        hide_index=True,
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
#  SITE-LEVEL ACTION PLAN
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Top 10 Sites Requiring Immediate Intervention")

site_risk = (
    df.groupby("Site_Code", as_index=False)["Risk_Score"]
    .sum()
    .sort_values("Risk_Score", ascending=False)
    .head(10)
    .sort_values("Risk_Score", ascending=True)  # ascending for horizontal bar
)

if site_risk.empty:
    st.info("No site-level risk data available.")
else:
    fig_sites = px.bar(
        site_risk,
        x="Risk_Score",
        y="Site_Code",
        orientation="h",
        text="Risk_Score",
        color_discrete_sequence=["#e74c3c"],
        labels={"Risk_Score": "Aggregate Risk Score", "Site_Code": "Site Code"},
    )
    fig_sites.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        textfont_size=13,
        marker_line_width=0,
    )
    fig_sites.update_layout(
        showlegend=False,
        xaxis_title="Aggregate Risk Score",
        yaxis_title=None,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=40, t=30, b=40),
        height=420,
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_sites, use_container_width=True, config=PLOTLY_CLEAN)
