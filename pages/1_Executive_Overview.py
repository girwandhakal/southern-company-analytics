import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, RISK_COLOR_MAP, RISK_ORDER, PLOTLY_LAYOUT, PLOTLY_CLEAN, ACCENT_SEQUENCE,
)

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)
df["Is_Decom"] = df["Is_Decom"].astype(bool)
df["Total_Replacement_Cost"] = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

main = render_dashboard_chatbot(page_title="Executive Overview", df=df)

SUPPORT_COLORS = {
    "Unknown / No Data": "#95a5a6",
    "No Support (Past EoL)": COLORS["crimson"],
    "Expired Support / At Risk (Past EoS)": COLORS["gold"],
}

with main:
    page_header(
        "Network Lifecycle Risk Executive Overview",
        subtitle="Southern Company — Enterprise Device Lifecycle Snapshot",
        breadcrumb="HOME > EXECUTIVE OVERVIEW",
    )
    st.markdown("---")

    tab_exec, tab_lifecycle, tab_alerts = st.tabs(
        ["📊 Executive Overview", "🔄 Lifecycle Status", "🔔 Recent Alerts"]
    )

    # ─── TAB 1: EXECUTIVE OVERVIEW ───────────────────────────────────────
    with tab_exec:
        total_devices = len(df)
        past_eol = (df["Risk_Level"] == "Critical (Past EoL)").sum()
        near_eol = (df["Risk_Level"] == "High (Near EoL)").sum()
        total_replacement_exposure = df["Total_Replacement_Cost"].sum()

        wasted_mask = (df["Is_Decom"]) & (
            df["Risk_Level"].isin(["Critical (Past EoL)", "High (Near EoL)"])
        )
        wasted_spend_prevented = df.loc[wasted_mask, "Total_Replacement_Cost"].sum()

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Active Devices", f"{total_devices:,}")
        k2.metric("Devices Past EoL", f"{past_eol:,}")
        k3.metric("Devices Near EoL", f"{near_eol:,}")
        k4.metric("Replacement Exposure", fmt_currency(total_replacement_exposure))
        k5.metric(
            "Spend Prevented",
            fmt_currency(wasted_spend_prevented),
            delta=fmt_currency(wasted_spend_prevented),
            delta_color="normal",
            help="Saved by stopping replacements at decommissioned sites",
        )

        section_divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Device Distribution by Risk Level")
            risk_counts = (
                df["Risk_Level"]
                .value_counts()
                .reindex(RISK_ORDER)
                .dropna()
                .reset_index()
            )
            risk_counts.columns = ["Risk_Level", "Count"]

            if risk_counts.empty:
                st.info("No risk-level data available.")
            else:
                fig_risk = px.bar(
                    risk_counts, x="Risk_Level", y="Count",
                    color="Risk_Level", color_discrete_map=RISK_COLOR_MAP,
                    text="Count", category_orders={"Risk_Level": RISK_ORDER},
                )
                fig_risk.update_traces(
                    textposition="outside", textfont_size=14,
                    textfont_color="#1A1F2E",
                    marker_line_width=0,
                )
                fig_risk.update_layout(
                    **PLOTLY_LAYOUT,
                    showlegend=False, xaxis_title=None,
                    yaxis_title="Number of Devices",
                    xaxis_tickangle=-20,
                )
                st.plotly_chart(fig_risk, use_container_width=True, config=PLOTLY_CLEAN)

        with right:
            st.subheader("Top 10 States — High-Risk Devices")
            high_risk_df = df[df["Risk_Level"].isin(["Critical (Past EoL)", "High (Near EoL)"])]
            if high_risk_df.empty:
                st.info("No high-risk devices found.")
            else:
                state_counts = (
                    high_risk_df.groupby("State").size()
                    .reset_index(name="Count")
                    .sort_values("Count", ascending=False).head(10)
                    .sort_values("Count", ascending=True)
                )
                fig_states = px.bar(
                    state_counts, x="Count", y="State",
                    orientation="h", text="Count",
                    color_discrete_sequence=[COLORS["crimson"]],
                )
                fig_states.update_traces(
                    textposition="outside", textfont_size=14,
                    textfont_color="#1A1F2E",
                    marker_line_width=0,
                )
                fig_states.update_layout(
                    **PLOTLY_LAYOUT,
                    showlegend=False,
                    xaxis_title="High-Risk Device Count",
                    yaxis_title=None,
                )
                st.plotly_chart(fig_states, use_container_width=True, config=PLOTLY_CLEAN)

        section_divider()

        st.subheader("Support Status Distribution")
        support_counts = df["Support_Status"].value_counts().reset_index()
        support_counts.columns = ["Support_Status", "Count"]

        if support_counts.empty:
            st.info("No support-status data available.")
        else:
            fig_donut = px.pie(
                support_counts, values="Count", names="Support_Status",
                hole=0.55, color="Support_Status",
                color_discrete_map=SUPPORT_COLORS,
            )
            fig_donut.update_traces(
                textinfo="label+percent", textposition="outside",
                textfont_size=13, textfont_color="#1A1F2E",
                pull=[0.02] * len(support_counts),
                marker_line_width=0,
            )
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
                            font=dict(size=12)),
                margin=dict(l=40, r=40, t=30, b=60),
                height=440, paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=COLORS["dark"]),
            )
            st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CLEAN)

    # ─── TAB 2: LIFECYCLE STATUS ────────────────────────────────────────
    with tab_lifecycle:
        st.subheader("Lifecycle Posture")
        total = len(df)
        if total > 0:
            low_pct = (df["Risk_Level"] == "Low (Healthy)").sum() / total * 100
            med_pct = (df["Risk_Level"] == "Medium (Approaching EoL)").sum() / total * 100
            high_pct = (df["Risk_Level"] == "High (Near EoL)").sum() / total * 100
            crit_pct = (df["Risk_Level"] == "Critical (Past EoL)").sum() / total * 100
        else:
            low_pct = med_pct = high_pct = crit_pct = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Healthy", f"{low_pct:.1f}%")
        c2.metric("Approaching EoL", f"{med_pct:.1f}%")
        c3.metric("Near EoL", f"{high_pct:.1f}%")
        c4.metric("Past EoL (Critical)", f"{crit_pct:.1f}%")

        section_divider()
        st.subheader("Device Type Breakdown")
        if "Device Type" in df.columns:
            dtype_risk = (
                df.groupby(["Device Type", "Risk_Level"]).size()
                .reset_index(name="Count")
            )
            fig_dt = px.bar(
                dtype_risk, x="Device Type", y="Count",
                color="Risk_Level", color_discrete_map=RISK_COLOR_MAP,
                category_orders={"Risk_Level": RISK_ORDER},
                barmode="stack", text="Count",
            )
            fig_dt.update_traces(textfont_color="#1A1F2E")
            fig_dt.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_dt, use_container_width=True, config=PLOTLY_CLEAN)
        else:
            st.info("Device Type column not found in dataset.")

    # ─── TAB 3: RECENT ALERTS ──────────────────────────────────────────
    with tab_alerts:
        st.subheader("System Alerts")
        critical_devices = df[df["Risk_Level"] == "Critical (Past EoL)"]
        critical_count = len(critical_devices)

        if critical_count > 0:
            st.warning(
                f"**{critical_count:,}** devices are past End-of-Life and require immediate attention."
            )
        else:
            st.success("No critical devices detected — all devices are within lifecycle.")

        healthy_count = (df["Risk_Level"] == "Low (Healthy)").sum()
        if healthy_count > 0:
            st.success(f"**{healthy_count:,}** devices are healthy with no lifecycle concerns.")

        decom_count = df["Is_Decom"].sum()
        if decom_count > 0:
            st.info(
                f"**{int(decom_count):,}** devices are at decommissioned sites — "
                "replacement spend can be avoided."
            )
