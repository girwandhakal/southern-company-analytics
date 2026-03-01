import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.dashboard_chatbot import render_dashboard_chatbot
from src.download_utils import render_plotly_with_download, render_table_with_download
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, RISK_COLOR_MAP, RISK_ORDER, PLOTLY_LAYOUT, PLOTLY_CLEAN,
)

st.set_page_config(page_title="Lifecycle & Asset Health", page_icon="🔧", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)
df = apply_global_filters(df)

main = render_dashboard_chatbot(page_title="Lifecycle & Asset Health", df=df)

with main:
    tab_lifecycle, = st.tabs(["🔧 Lifecycle & Asset Health"])

    with tab_lifecycle:
        page_header(
            "Lifecycle & Asset Health Monitoring",
            subtitle="Track aging infrastructure, identify overdue assets, and monitor lifecycle risk trends.",
            breadcrumb="HOME > LIFECYCLE & ASSET HEALTH",
        )

        required_cols = [
            "Hostname", "Model", "State", "Device Type", "Risk_Level",
            "EoL_Year", "Days_Past_EoL", "Total_Replacement_Cost",
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error("Missing required columns: " + ", ".join(missing_cols))
            st.stop()

        lifecycle_df = df[required_cols].copy()
        lifecycle_df["EoL_Year"] = pd.to_numeric(lifecycle_df["EoL_Year"], errors="coerce")
        lifecycle_df["Days_Past_EoL"] = pd.to_numeric(lifecycle_df["Days_Past_EoL"], errors="coerce")
        lifecycle_df["Total_Replacement_Cost"] = pd.to_numeric(
            lifecycle_df["Total_Replacement_Cost"], errors="coerce"
        ).fillna(0)

        critical_df = lifecycle_df[lifecycle_df["Risk_Level"] == "Critical (Past EoL)"].copy()
        max_days = int(critical_df["Days_Past_EoL"].max()) if not critical_df.empty and pd.notna(critical_df["Days_Past_EoL"].max()) else 0

        min_days_slider = st.slider(
            "Minimum Days Past End-of-Life",
            min_value=0, max_value=max(max_days, 1), value=0,
        )

        slider_df = critical_df[critical_df["Days_Past_EoL"] >= min_days_slider]
        total_past_eol = len(slider_df)
        avg_days_past_eol = slider_df["Days_Past_EoL"].mean()
        cost_past_eol = slider_df["Total_Replacement_Cost"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Past EoL Devices", f"{total_past_eol:,}")
        c2.metric("Avg Days Past EoL", f"{(avg_days_past_eol if pd.notna(avg_days_past_eol) else 0):,.0f}")
        c3.metric("Cost of Past EoL Devices", fmt_currency(cost_past_eol))

        section_divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Devices Approaching End of Life Over Time")
            eol_trend = (
                lifecycle_df[lifecycle_df["EoL_Year"].between(2024, 2035, inclusive="both")]
                .groupby("EoL_Year").size().reset_index(name="Count")
                .sort_values("EoL_Year")
            )
            if eol_trend.empty:
                st.info("No EoL year data available between 2024 and 2035.")
            else:
                fig_trend = px.area(
                    eol_trend, x="EoL_Year", y="Count",
                    markers=True, line_shape="spline",
                )
                fig_trend.update_traces(
                    line=dict(width=3, color=COLORS["coral"]),
                    marker=dict(size=8, color=COLORS["coral"]),
                    fillcolor="rgba(232, 115, 74, 0.1)",
                )
                fig_trend.update_layout(
                    **PLOTLY_LAYOUT,
                    showlegend=False,
                    xaxis_title="EoL Year", yaxis_title="Device Count",
                )
                render_plotly_with_download(
                    fig_trend,
                    "lifecycle_eol_trend",
                    "lifecycle_asset_health_eol_trend",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )

        with right:
            st.subheader("Devices by Risk Level")
            risk_counts = (
                lifecycle_df.groupby("Risk_Level").size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )
            if risk_counts.empty:
                st.info("No risk-level data available.")
            else:
                fig_risk = px.bar(
                    risk_counts, x="Count", y="Risk_Level",
                    orientation="h", color="Risk_Level",
                    color_discrete_map=RISK_COLOR_MAP, text="Count",
                )
                fig_risk.update_layout(
                    **PLOTLY_LAYOUT, showlegend=False,
                    xaxis_title="Device Count", yaxis_title=None,
                )
                fig_risk.update_traces(
                    textposition="outside", marker_line_width=0,
                    textfont_size=14,
                )
                render_plotly_with_download(
                    fig_risk,
                    "lifecycle_risk_level_distribution",
                    "lifecycle_asset_health_risk_distribution",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )

        section_divider()
        st.subheader("Critical Active Assets (Past End of Life)")

        critical_table = slider_df[
            ["Hostname", "Model", "State", "Device Type", "Days_Past_EoL", "Total_Replacement_Cost"]
        ].sort_values("Days_Past_EoL", ascending=False)

        render_table_with_download(
            critical_table.style.format({"Total_Replacement_Cost": "${:,.0f}"}),
            "critical_active_assets_past_eol",
            "lifecycle_asset_health_critical_assets",
            export_df=critical_table,
            use_container_width=True, hide_index=True,
        )
