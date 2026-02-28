import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Lifecycle & Asset Health", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stPlotlyChart { margin-top: 8px; }
    hr { border: none; border-top: 1px solid #e8ecf1; margin: 24px 0 18px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)

main = render_dashboard_chatbot(page_title="Lifecycle & Asset Health", df=df)

with main:
    tab_lifecycle, = st.tabs(["Lifecycle & Asset Health"])

    with tab_lifecycle:
        st.header("Lifecycle & Asset Health Monitoring")
        st.caption(
            "Track aging infrastructure, identify overdue assets, and monitor lifecycle risk trends."
        )

        required_cols = [
            "Hostname",
            "Model",
            "State",
            "Device Type",
            "Risk_Level",
            "EoL_Year",
            "Days_Past_EoL",
            "Total_Replacement_Cost",
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error("Missing required columns: " + ", ".join(missing_cols))
            st.stop()

        lifecycle_df = df[required_cols].copy()
        lifecycle_df["EoL_Year"] = pd.to_numeric(lifecycle_df["EoL_Year"], errors="coerce")
        lifecycle_df["Days_Past_EoL"] = pd.to_numeric(
            lifecycle_df["Days_Past_EoL"], errors="coerce"
        )
        lifecycle_df["Total_Replacement_Cost"] = pd.to_numeric(
            lifecycle_df["Total_Replacement_Cost"], errors="coerce"
        ).fillna(0)

        critical_df = lifecycle_df[lifecycle_df["Risk_Level"] == "Critical (Past EoL)"].copy()

        total_past_eol = len(critical_df)
        avg_days_past_eol = critical_df["Days_Past_EoL"].mean()
        cost_past_eol = critical_df["Total_Replacement_Cost"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Past EoL Devices", f"{total_past_eol:,}")
        c2.metric(
            "Average Days Past EoL",
            f"{(avg_days_past_eol if pd.notna(avg_days_past_eol) else 0):,.0f}",
        )
        c3.metric("Cost of Past EoL Devices", f"${cost_past_eol:,.0f}")

        st.markdown("---")

        left, right = st.columns(2)

        with left:
            st.subheader("Devices Approaching End of Life Over Time")
            eol_trend = (
                lifecycle_df[lifecycle_df["EoL_Year"].between(2024, 2035, inclusive="both")]
                .groupby("EoL_Year")
                .size()
                .reset_index(name="Count")
                .sort_values("EoL_Year")
            )

            if eol_trend.empty:
                st.info("No EoL year data available between 2024 and 2035.")
            else:
                fig_trend = px.line(
                    eol_trend,
                    x="EoL_Year",
                    y="Count",
                    markers=True,
                    line_shape="spline",
                )
                fig_trend.update_traces(line=dict(width=3, color="#2980b9"), marker=dict(size=8))
                fig_trend.update_layout(
                    showlegend=False,
                    xaxis_title="EoL Year",
                    yaxis_title="Device Count",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

        with right:
            st.subheader("Devices by Risk Level")
            risk_counts = (
                lifecycle_df.groupby("Risk_Level")
                .size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )
            risk_color_map = {
                "Critical (Past EoL)": "#e74c3c",
                "High (Near EoL)": "#f39c12",
                "Medium (Approaching EoL)": "#2980b9",
                "Low (Healthy)": "#27ae60",
            }

            if risk_counts.empty:
                st.info("No risk-level data available.")
            else:
                fig_risk = px.bar(
                    risk_counts,
                    x="Count",
                    y="Risk_Level",
                    orientation="h",
                    color="Risk_Level",
                    color_discrete_map=risk_color_map,
                    text="Count",
                )
                fig_risk.update_layout(
                    showlegend=False,
                    xaxis_title="Device Count",
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(family="Inter, sans-serif"),
                )
                fig_risk.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

        st.markdown("---")
        st.subheader("Critical Active Assets (Past End of Life)")

        critical_table = critical_df[
            [
                "Hostname",
                "Model",
                "State",
                "Device Type",
                "Days_Past_EoL",
                "Total_Replacement_Cost",
            ]
        ].sort_values("Days_Past_EoL", ascending=False)

        st.dataframe(
            critical_table.style.format({"Total_Replacement_Cost": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )
