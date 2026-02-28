import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Cost & Support Risk Analysis", page_icon="💰", layout="wide")

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

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
required_columns = [
    "Risk_Level",
    "Support_Status",
    "Total_Replacement_Cost",
    "Device Type",
    "Days_Past_EoL",
]

df = load_data(DATA_PATH)[required_columns].copy()
df["Total_Replacement_Cost"] = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
df["Days_Past_EoL"] = pd.to_numeric(df["Days_Past_EoL"], errors="coerce").fillna(0)

main = render_dashboard_chatbot(page_title="Cost & Support Risk Analysis", df=df)

PLOTLY_CLEAN = {"displayModeBar": False}


def fmt_currency(value: float) -> str:
    return f"${value:,.0f}"


def normalize_risk_level(value: str) -> str:
    text = str(value).lower()
    if "critical" in text:
        return "Critical"
    if "high" in text:
        return "High"
    if "medium" in text:
        return "Medium"
    return "Low"


def normalize_support_status(value: str) -> str:
    text = str(value).lower()
    if "no support" in text:
        return "No Support (Past EoL)"
    if "expired support" in text or "at risk" in text:
        return "Expired Support / At Risk"
    return "Under Support"


with main:
    tab_risk, = st.tabs(["Cost & Support Risk Analysis"])

    with tab_risk:
        st.header("Financial Exposure & Support Risk")

        risk_analysis_df = df.copy()
        risk_analysis_df["Risk_Level"] = risk_analysis_df["Risk_Level"].apply(normalize_risk_level)
        risk_analysis_df["Support_Status"] = risk_analysis_df["Support_Status"].apply(normalize_support_status)

        critical_high_mask = risk_analysis_df["Risk_Level"].isin(["Critical", "High"])
        total_critical_high_cost = risk_analysis_df.loc[
            critical_high_mask, "Total_Replacement_Cost"
        ].sum()
        unsupported_count = (
            risk_analysis_df["Support_Status"].eq("No Support (Past EoL)").sum()
        )
        avg_replacement_cost = risk_analysis_df["Total_Replacement_Cost"].mean()

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Cost of Critical/High Risk Devices", fmt_currency(total_critical_high_cost))
        k2.metric("Devices Completely Unsupported", f"{unsupported_count:,}")
        k3.metric("Average Replacement Cost per Device", fmt_currency(avg_replacement_cost))

        st.markdown("---")

        risk_color_map = {
            "Critical": "#e74c3c",
            "High": "#f39c12",
            "Medium": "#2980b9",
            "Low": "#27ae60",
        }
        risk_order = ["Critical", "High", "Medium", "Low"]

        support_color_map = {
            "No Support (Past EoL)": "#8B0000",
            "Expired Support / At Risk": "#f1c40f",
            "Under Support": "#27ae60",
        }

        left, right = st.columns(2)

        with left:
            st.subheader("Cost Exposure by Device Type & Risk Level")
            cost_by_device_risk = (
                risk_analysis_df.groupby(["Device Type", "Risk_Level"], as_index=False)[
                    "Total_Replacement_Cost"
                ]
                .sum()
            )

            fig_cost_stack = px.bar(
                cost_by_device_risk,
                x="Device Type",
                y="Total_Replacement_Cost",
                color="Risk_Level",
                barmode="stack",
                category_orders={"Risk_Level": risk_order},
                color_discrete_map=risk_color_map,
                labels={
                    "Device Type": "Device Type",
                    "Total_Replacement_Cost": "Total Replacement Cost",
                    "Risk_Level": "Risk Level",
                },
            )
            fig_cost_stack.update_layout(
                xaxis_title="Device Type",
                yaxis_title="Total Replacement Cost ($)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=40),
                font=dict(family="Inter, sans-serif"),
                legend_title_text="Risk Level",
            )
            fig_cost_stack.update_yaxes(tickprefix="$", separatethousands=True)
            st.plotly_chart(fig_cost_stack, use_container_width=True, config=PLOTLY_CLEAN)

        with right:
            st.subheader("Support Coverage Distribution")
            support_counts = (
                risk_analysis_df.groupby("Support_Status", as_index=False)
                .size()
                .rename(columns={"size": "Count"})
            )
            support_order = [
                "No Support (Past EoL)",
                "Expired Support / At Risk",
                "Under Support",
            ]

            fig_support_donut = px.pie(
                support_counts,
                names="Support_Status",
                values="Count",
                hole=0.55,
                category_orders={"Support_Status": support_order},
                color="Support_Status",
                color_discrete_map=support_color_map,
            )
            fig_support_donut.update_traces(
                textinfo="label+percent",
                textposition="outside",
                marker_line_width=0,
            )
            fig_support_donut.update_layout(
                legend_title_text="Support Status",
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig_support_donut, use_container_width=True, config=PLOTLY_CLEAN)

        st.markdown("---")

        st.subheader("Technical Debt Matrix: Cost vs. Days Unsupported")
        debt_df = risk_analysis_df[risk_analysis_df["Days_Past_EoL"] > 0].copy()

        if debt_df.empty:
            st.info("No devices with Days_Past_EoL > 0 were found.")
        else:
            fig_scatter = px.scatter(
                debt_df,
                x="Days_Past_EoL",
                y="Total_Replacement_Cost",
                color="Device Type",
                title="Technical Debt Matrix: Cost vs. Days Unsupported",
                labels={
                    "Days_Past_EoL": "Days Past EoL",
                    "Total_Replacement_Cost": "Total Replacement Cost",
                    "Device Type": "Device Type",
                },
            )
            fig_scatter.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=50, b=30),
                font=dict(family="Inter, sans-serif"),
                legend_title_text="Device Type",
            )
            fig_scatter.update_yaxes(tickprefix="$", separatethousands=True)
            st.plotly_chart(fig_scatter, use_container_width=True, config=PLOTLY_CLEAN)
