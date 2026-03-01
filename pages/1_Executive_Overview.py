import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.dashboard_chatbot import render_dashboard_chatbot
from src.download_utils import render_plotly_with_download, render_table_with_download
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, RISK_COLOR_MAP, RISK_ORDER, PLOTLY_LAYOUT, PLOTLY_CLEAN, ACCENT_SEQUENCE,
)

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = apply_global_filters(load_data(DATA_PATH))
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
            help="Saved by stopping replacements at inactive sites",
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
                render_plotly_with_download(
                    fig_risk,
                    "executive_overview_risk_distribution",
                    "exec_overview_risk_distribution",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )

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
                render_plotly_with_download(
                    fig_states,
                    "executive_overview_top_states_high_risk",
                    "exec_overview_top_states_high_risk",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )

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
            render_plotly_with_download(
                fig_donut,
                "executive_overview_support_status_distribution",
                "exec_overview_support_status_distribution",
                use_container_width=True,
                config=PLOTLY_CLEAN,
            )

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
            render_plotly_with_download(
                fig_dt,
                "lifecycle_status_device_type_breakdown",
                "exec_lifecycle_device_type_breakdown",
                use_container_width=True,
                config=PLOTLY_CLEAN,
            )
        else:
            st.info("Device Type column not found in dataset.")

        section_divider()
        st.subheader("Device Distribution by Affiliate")
        if "Owner" in df.columns:
            affiliate_risk = (
                df.groupby(["Owner", "Risk_Level"]).size()
                .reset_index(name="Count")
            )
            if affiliate_risk.empty:
                st.info("No affiliate data available.")
            else:
                fig_aff = px.bar(
                    affiliate_risk,
                    x="Owner",
                    y="Count",
                    color="Risk_Level",
                    color_discrete_map=RISK_COLOR_MAP,
                    category_orders={"Risk_Level": RISK_ORDER},
                    barmode="stack",
                    text="Count",
                    labels={"Owner": "Affiliate", "Count": "Device Count"},
                )
                fig_aff.update_traces(
                    textfont_color="#1A1F2E", marker_line_width=0,
                )
                fig_aff.update_layout(
                    **PLOTLY_LAYOUT,
                    xaxis_title="Affiliate",
                    yaxis_title="Device Count",
                )
                render_plotly_with_download(
                    fig_aff,
                    "lifecycle_status_affiliate_distribution",
                    "exec_lifecycle_affiliate_distribution",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )
        else:
            st.info("Affiliate (Owner) column not found in dataset.")

    # ─── TAB 3: RECENT ALERTS ──────────────────────────────────────────
    with tab_alerts:
        st.markdown(
            """
            <div class="alerts-section-title">System Alerts</div>
            <div class="alerts-section-subtitle">Lifecycle signals with recommended operational actions.</div>
            """,
            unsafe_allow_html=True,
        )

        critical_devices = df[df["Risk_Level"] == "Critical (Past EoL)"]
        healthy_devices = df[df["Risk_Level"] == "Low (Healthy)"]
        decom_devices = df[df["Is_Decom"]]

        critical_count = len(critical_devices)
        healthy_count = len(healthy_devices)
        decom_count = len(decom_devices)
        total_devices = max(len(df), 1)

        critical_pct = (critical_count / total_devices) * 100
        healthy_pct = (healthy_count / total_devices) * 100
        decom_pct = (decom_count / total_devices) * 100
        avoidable_spend = decom_devices["Total_Replacement_Cost"].sum()

        st.markdown(
            """
            <style>
            .alerts-section-title {
                font-size: 1.5rem;
                font-weight: 900;
                color: #1A1F2E;
                letter-spacing: -0.3px;
                margin-bottom: 2px;
                line-height: 1.2;
            }
            .alerts-section-subtitle {
                font-size: 1rem;
                font-weight: 700;
                color: #334155;
                margin-bottom: 10px;
                line-height: 1.35;
            }
            .alert-card {
                border-radius: 14px;
                padding: 14px 14px 12px 14px;
                min-height: 145px;
                border: 1px solid transparent;
                box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            }
            .alert-card h4 {
                margin: 0 0 8px 0;
                font-size: 1.08rem;
                font-weight: 900;
            }
            .alert-card .metric {
                font-size: 1.6rem;
                line-height: 1.1;
                margin: 0 0 5px 0;
                font-weight: 900;
                letter-spacing: -0.4px;
            }
            .alert-card .meta {
                font-size: 0.74rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                margin-bottom: 6px;
                opacity: 0.9;
            }
            .alert-card p {
                margin: 0;
                font-size: 0.82rem;
                line-height: 1.4;
                font-weight: 500;
            }
            .alert-critical {
                background: rgba(231, 76, 60, 0.08);
                border-color: rgba(231, 76, 60, 0.22);
            }
            .alert-healthy {
                background: rgba(39, 174, 96, 0.08);
                border-color: rgba(39, 174, 96, 0.2);
            }
            .alert-opportunity {
                background: rgba(52, 152, 219, 0.08);
                border-color: rgba(52, 152, 219, 0.2);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="alert-card alert-critical">
                    <h4>Critical Alert</h4>
                    <div class="metric">{critical_count:,}</div>
                    <div class="meta">{critical_pct:.1f}% of fleet</div>
                    <p>Devices are past End-of-Life and require immediate remediation planning.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="alert-card alert-healthy">
                    <h4>Healthy Estate</h4>
                    <div class="metric">{healthy_count:,}</div>
                    <div class="meta">{healthy_pct:.1f}% of fleet</div>
                    <p>Devices are within lifecycle support windows with low immediate risk exposure.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="alert-card alert-opportunity">
                    <h4>Savings Opportunity</h4>
                    <div class="metric">{decom_count:,}</div>
                    <div class="meta">{decom_pct:.1f}% of fleet</div>
                    <p><b>Approval required:</b> {decom_count:,} devices are at inactive sites. Approve scope exclusion to avoid <b>{fmt_currency(avoidable_spend)}</b> in replacement spend.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")
        a1, a2, a3 = st.columns(3)
        with a1:
            show_critical = st.button(
                "View Critical Devices",
                use_container_width=True,
                disabled=critical_count == 0,
            )
        with a2:
            show_healthy = st.button(
                "View Healthy Devices",
                use_container_width=True,
                disabled=healthy_count == 0,
            )
        with a3:
            show_decom = st.button(
                "View Devices at Inactive Sites",
                use_container_width=True,
                disabled=decom_count == 0,
            )

        if show_critical:
            st.markdown("**Critical Device Queue**")
            display_cols = [
                col for col in
                ["Owner", "State", "PhysicalAddressCounty", "Device Type", "Risk_Level", "Total_Replacement_Cost"]
                if col in critical_devices.columns
            ]
            critical_table = critical_devices[display_cols].sort_values(
                "Total_Replacement_Cost", ascending=False
            ).head(200)
            render_table_with_download(
                critical_table,
                "critical_device_queue",
                "exec_alerts_critical_queue",
                export_df=critical_table,
                use_container_width=True,
            )

        if show_healthy:
            st.markdown("**Healthy Device Snapshot**")
            display_cols = [
                col for col in
                ["Owner", "State", "PhysicalAddressCounty", "Device Type", "Risk_Level", "Total_Replacement_Cost"]
                if col in healthy_devices.columns
            ]
            healthy_table = healthy_devices[display_cols].head(200)
            render_table_with_download(
                healthy_table,
                "healthy_device_snapshot",
                "exec_alerts_healthy_snapshot",
                export_df=healthy_table,
                use_container_width=True,
            )

        if show_decom:
            st.markdown("**Inactive Sites Opportunity Queue**")
            display_cols = [
                col for col in
                ["Owner", "State", "PhysicalAddressCounty", "Device Type", "Risk_Level", "Total_Replacement_Cost"]
                if col in decom_devices.columns
            ]
            decom_table = decom_devices[display_cols].sort_values(
                "Total_Replacement_Cost", ascending=False
            ).head(200)
            render_table_with_download(
                decom_table,
                "decommissioned_site_opportunity_queue",
                "exec_alerts_decom_queue",
                export_df=decom_table,
                use_container_width=True,
            )
