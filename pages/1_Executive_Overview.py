import datetime
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
    COLORS, RISK_COLOR_MAP, RISK_ORDER, PLOTLY_LAYOUT, PLOTLY_CLEAN, ACCENT_SEQUENCE,
)

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = apply_global_filters(load_data(DATA_PATH))
df["Is_Decom"] = df["Is_Decom"].astype(bool)
df["Total_Replacement_Cost"] = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
df["Risk_Score"] = pd.to_numeric(df["Risk_Score"], errors="coerce").fillna(0)
df["Days_Past_EoL"] = pd.to_numeric(df["Days_Past_EoL"], errors="coerce").fillna(0)
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

main = render_dashboard_chatbot(page_title="Executive Overview", df=df)

SUPPORT_COLORS = {
    "Unknown / No Data": "#95a5a6",
    "No Support (Past EoL)": COLORS["crimson"],
    "Expired Support / At Risk (Past EoS)": COLORS["gold"],
}


# ── AI Report helpers ─────────────────────────────────────────────────────────

def _compute_fleet_metrics(data: pd.DataFrame) -> dict:
    total = len(data)
    active = data[~data["Is_Decom"]]
    critical = data["Risk_Level"].str.contains("Critical", case=False, na=False).sum()
    high = data["Risk_Level"].str.contains("High", case=False, na=False).sum()
    medium = data["Risk_Level"].str.contains("Medium", case=False, na=False).sum()
    low = total - critical - high - medium
    total_cost = data["Total_Replacement_Cost"].sum()
    critical_cost = data.loc[data["Risk_Level"].str.contains("Critical", case=False, na=False), "Total_Replacement_Cost"].sum()
    avg_days_past = data.loc[data["Days_Past_EoL"] > 0, "Days_Past_EoL"].mean()
    max_days_past = data["Days_Past_EoL"].max()
    top_states = data[data["Risk_Level"].str.contains("Critical|High", case=False, na=False)]
    state_risk = top_states.groupby("State").agg(count=("State", "size"), cost=("Total_Replacement_Cost", "sum")).sort_values("count", ascending=False).head(5)
    top_device_types = data.groupby("Device Type").agg(count=("Device Type", "size"), cost=("Total_Replacement_Cost", "sum")).sort_values("count", ascending=False).head(5)
    support_status = data["Support_Status"].value_counts().to_dict() if "Support_Status" in data.columns else {}
    decom_sites = data[data["Is_Decom"]]
    health_score = max(0, min(100, 100 - (critical / max(total, 1) * 200) - (high / max(total, 1) * 80)))
    return {
        "total": total, "total_active": len(active), "critical": critical, "high": high,
        "medium": medium, "low": low, "total_cost": total_cost, "critical_cost": critical_cost,
        "avg_days_past_eol": avg_days_past if pd.notna(avg_days_past) else 0,
        "max_days_past_eol": max_days_past, "top_states": state_risk,
        "top_device_types": top_device_types, "support_status": support_status,
        "decom_savings": decom_sites["Total_Replacement_Cost"].sum(),
        "decom_count": len(decom_sites), "health_score": round(health_score, 1),
        "critical_pct": round(critical / max(total, 1) * 100, 1),
        "high_pct": round(high / max(total, 1) * 100, 1),
    }


def _build_report_prompt(metrics: dict) -> str:
    state_lines = ""
    if not metrics["top_states"].empty:
        for state, row in metrics["top_states"].iterrows():
            state_lines += f"  - {state}: {int(row['count'])} devices, ${row['cost']:,.0f} exposure\n"
    device_lines = ""
    if not metrics["top_device_types"].empty:
        for dtype, row in metrics["top_device_types"].iterrows():
            device_lines += f"  - {dtype}: {int(row['count'])} devices, ${row['cost']:,.0f} cost\n"
    support_lines = ""
    for status, count in metrics["support_status"].items():
        support_lines += f"  - {status}: {count}\n"

    return f"""You are a senior infrastructure strategy consultant writing an executive intelligence brief for Southern Company leadership.

FLEET DATA SNAPSHOT:
- Total devices: {metrics['total']:,}
- Active devices: {metrics['total_active']:,}
- Critical (Past EoL): {metrics['critical']:,} ({metrics['critical_pct']}%)
- High Risk (Near EoL): {metrics['high']:,} ({metrics['high_pct']}%)
- Medium Risk: {metrics['medium']:,}
- Low Risk / Healthy: {metrics['low']:,}
- Fleet Health Score: {metrics['health_score']}/100
- Total Replacement Exposure: ${metrics['total_cost']:,.0f}
- Critical Device Exposure: ${metrics['critical_cost']:,.0f}
- Average Days Past EoL (affected devices): {metrics['avg_days_past_eol']:.0f}
- Maximum Days Past EoL: {metrics['max_days_past_eol']:.0f}
- Decommissioned Sites: {metrics['decom_count']:,} devices (${metrics['decom_savings']:,.0f} avoidable spend)

TOP RISK STATES:
{state_lines}
TOP DEVICE TYPES:
{device_lines}
SUPPORT STATUS:
{support_lines}
Write a comprehensive executive intelligence report in HTML format. Use clean HTML. Do NOT include <html>, <head>, or <body> tags.

SECTIONS TO INCLUDE (write ALL of these in full detail):
1. Executive Summary (2-3 paragraphs synthesizing overall fleet posture, urgency, key takeaway)
2. Fleet Health Assessment (analysis of health score, trend implications)
3. Critical Risk Analysis (deep dive into critical/high-risk devices, what's at stake)
4. Financial Impact Assessment (total exposure, cost of inaction per quarter, ROI of replacement)
5. Regional Risk Hotspots (state-by-state analysis with specific recommendations)
6. Device Category Risk Matrix (which device types need priority attention)
7. Top 10 Strategic Recommendations (specific, actionable items with priority labels)
8. 90-Day Action Roadmap — THIS SECTION IS MANDATORY AND MUST BE DETAILED:
   - Use <h2>90-Day Action Roadmap</h2> as the section header
   - Phase 1 (Days 1-30): Use <h3>Phase 1: Days 1-30 — Triage & Scope</h3> then a detailed <ul><li> list of 4-5 specific actions
   - Phase 2 (Days 31-60): Use <h3>Phase 2: Days 31-60 — Execute & Deploy</h3> then a detailed <ul><li> list of 4-5 specific actions
   - Phase 3 (Days 61-90): Use <h3>Phase 3: Days 61-90 — Validate & Scale</h3> then a detailed <ul><li> list of 4-5 specific actions
   - Each phase should reference specific data: device counts, dollar amounts, states, device types

FORMATTING RULES:
- Use <h2> for section titles
- Use <h3> for subsection titles
- Use <div class="highlight-box"> for key callouts
- For action items use: <div class="action-item"><span class="priority priority-critical">CRITICAL</span><div>content</div></div>
- Also use priority-high and priority-medium classes
- Use <strong> for emphasis
- Use <ul><li> for lists
- Be specific with numbers — reference actual data points
- Write in a confident, authoritative executive tone
- Include specific dollar amounts and percentages
- Each recommendation should have a clear business justification
- DO NOT truncate or shorten ANY section, especially the 90-Day Roadmap"""


def _generate_report_exec(prompt: str) -> str:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except KeyError:
        try:
            api_key = st.secrets["openai"]["OPENAI_API_KEY"]
        except KeyError:
            api_key = None
    if not api_key:
        return _generate_fallback_report_exec()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a senior enterprise infrastructure strategy consultant. Write detailed, data-driven executive reports."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7, max_tokens=6000,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _generate_fallback_report_exec()


def _generate_fallback_report_exec():
    m = st.session_state.get("exec_report_metrics", {})
    if not m:
        return "<p>Unable to generate report. Please try again.</p>"
    return f"""
<h2>Executive Summary</h2>
<p>The Southern Company network fleet comprises <strong>{m.get('total',0):,}</strong> devices, with <strong>{m.get('critical',0):,}</strong> ({m.get('critical_pct',0)}%) in critical status — past End-of-Life and requiring immediate remediation. An additional <strong>{m.get('high',0):,}</strong> devices ({m.get('high_pct',0)}%) are approaching end-of-life. The Fleet Health Score stands at <strong>{m.get('health_score',0)}/100</strong>.</p>
<p>Total replacement exposure: <strong>{fmt_currency(m.get('total_cost',0))}</strong>, with critical devices representing <strong>{fmt_currency(m.get('critical_cost',0))}</strong> in immediate risk. Decommissioned sites represent <strong>{fmt_currency(m.get('decom_savings',0))}</strong> in avoidable spend.</p>
<div class="highlight-box"><strong>Key Finding:</strong> Every quarter of delayed action increases security exposure. The average critical device is <strong>{m.get('avg_days_past_eol',0):.0f} days</strong> past End-of-Life.</div>
<h2>Fleet Health Assessment</h2>
<p>A score of <strong>{m.get('health_score',0)}/100</strong> indicates {'significant risk requiring immediate attention' if m.get('health_score',0) < 50 else 'moderate risk to address this fiscal cycle' if m.get('health_score',0) < 75 else 'a generally healthy fleet with targeted needs'}. Critical and high-risk devices comprise <strong>{m.get('critical_pct',0) + m.get('high_pct',0):.1f}%</strong> of the fleet.</p>
<h2>Critical Risk Analysis</h2>
<p><strong>{m.get('critical',0):,}</strong> devices are past EoL — no security patches or vendor support. Maximum age beyond EoL: <strong>{m.get('max_days_past_eol',0):.0f} days</strong>.</p>
<h2>Financial Impact Assessment</h2>
<p>Total exposure: <strong>{fmt_currency(m.get('total_cost',0))}</strong>. Critical replacement: <strong>{fmt_currency(m.get('critical_cost',0))}</strong>. Quarterly inaction cost: <strong>{fmt_currency(m.get('critical_cost',0) * 0.05)}</strong>.</p>
<h2>Top 10 Strategic Recommendations</h2>
<div class="action-item"><span class="priority priority-critical">CRITICAL</span><div>Immediately scope replacement of all {m.get('critical',0):,} past-EoL devices by risk score.</div></div>
<div class="action-item"><span class="priority priority-critical">CRITICAL</span><div>Exclude {m.get('decom_count',0):,} decom-site devices to avoid {fmt_currency(m.get('decom_savings',0))} unnecessary spend.</div></div>
<div class="action-item"><span class="priority priority-high">HIGH</span><div>Execute 90-day replacement wave for the top 100 highest-risk devices.</div></div>
<div class="action-item"><span class="priority priority-high">HIGH</span><div>Negotiate bulk replacement pricing for high-volume device types.</div></div>
<div class="action-item"><span class="priority priority-high">HIGH</span><div>Create proactive replacement schedules for {m.get('high',0):,} near-EoL devices.</div></div>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Implement quarterly fleet health reviews with automated EoL tracking.</div></div>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Standardize lifecycle policies across all affiliates.</div></div>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Evaluate lease-vs-buy models for high-turnover categories.</div></div>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Establish regional deployment teams for top-risk states.</div></div>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Create monthly health score reporting cadence for leadership.</div></div>

<h2>90-Day Action Roadmap</h2>

<h3>Phase 1: Days 1-30 — Triage & Scope</h3>
<div class="action-item"><span class="priority priority-critical">CRITICAL</span><div>Conduct a comprehensive audit of all <strong>{m.get('critical',0):,}</strong> critical devices past EoL to prioritize replacements and mitigate operational risks. Identify devices with the highest risk scores and longest time past EoL for immediate action.</div></div>
<ul>
<li>Complete scope validation and risk assessment for all critical-tier devices across all affiliates</li>
<li>Approve decommissioned site exceptions to unlock <strong>{fmt_currency(m.get('decom_savings',0))}</strong> in avoidable replacement spend</li>
<li>Procure replacement hardware for the top 50 highest-priority devices based on risk score ranking</li>
<li>Initiate vendor contract negotiations for bulk replacement pricing — target <strong>15-20% discount</strong> on volume orders</li>
<li>Stand up a cross-functional project team with representatives from Network Ops, Procurement, and each affiliate</li>
</ul>

<h3>Phase 2: Days 31-60 — Execute & Deploy</h3>
<div class="action-item"><span class="priority priority-high">HIGH</span><div>Initiate procurement processes for high-risk devices in top-risk states (Georgia, Alabama, California), focusing on routers and switches that represent the highest replacement exposure.</div></div>
<ul>
<li>Deploy first wave of replacements to the <strong>top 10 highest-risk sites</strong> identified in Geographic Risk Intelligence</li>
<li>Complete near-EoL assessment for all <strong>{m.get('high',0):,}</strong> high-risk devices and create pre-emptive replacement schedules</li>
<li>Establish regional deployment coordination centers in top-risk states to accelerate field operations</li>
<li>Begin tracking fleet health score weekly to measure impact of replacement program</li>
<li>Execute vendor onboarding and hardware staging for Phase 3 expansion</li>
</ul>

<h3>Phase 3: Days 61-90 — Validate & Scale</h3>
<div class="action-item"><span class="priority priority-medium">MEDIUM</span><div>Develop a long-term budget and strategy plan to address <strong>{m.get('medium',0):,}</strong> medium-risk devices, ensuring alignment with future technological advancements and evolving business needs across all affiliates.</div></div>
<ul>
<li>Validate fleet health score improvement — target minimum <strong>10-point increase</strong> from baseline of {m.get('health_score',0)}</li>
<li>Scale replacement program to remaining high-risk devices across all geographies</li>
<li>Publish first quarterly fleet health report to executive leadership with ROI metrics</li>
<li>Establish ongoing lifecycle management governance framework with automated alerting</li>
<li>Create FY2027 CapEx budget proposal based on remaining replacement backlog and projected EoL timeline</li>
</ul>"""


# ── Report CSS ────────────────────────────────────────────────────────────────

REPORT_CSS = """
<style>
.report-container {
    background: #FFFFFF; border-radius: 20px; padding: 36px 40px;
    box-shadow: 0 8px 48px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
    margin: 16px 0; animation: fadeInUp 0.6s ease-out; line-height: 1.7;
}
.report-container h2 {
    font-size: 1.3rem !important; font-weight: 900 !important; color: #1A1F2E !important;
    border-bottom: 3px solid #E8734A; padding-bottom: 8px; margin: 28px 0 14px 0;
}
.report-container h2:first-child { margin-top: 0; }
.report-container h3 { font-size: 1.05rem !important; font-weight: 800 !important; color: #334155 !important; margin: 18px 0 8px; }
.report-container p, .report-container li { font-size: 0.92rem; color: #334155 !important; line-height: 1.75; }
.report-container ul { padding-left: 20px; }
.report-container li { margin-bottom: 5px; }
.report-container strong { color: #1A1F2E !important; }
.report-container .highlight-box {
    background: linear-gradient(135deg, rgba(232,115,74,0.08), rgba(232,115,74,0.03));
    border-left: 4px solid #E8734A; border-radius: 0 12px 12px 0;
    padding: 14px 18px; margin: 14px 0; font-weight: 600;
}
.report-container .action-item {
    background: #F8FAFC; border-radius: 12px; padding: 12px 16px; margin: 8px 0;
    border: 1px solid #E0E6E3; display: flex; align-items: flex-start; gap: 10px;
}
.report-container .action-item .priority {
    font-size: 0.6rem; font-weight: 800; letter-spacing: 0.5px; padding: 3px 9px;
    border-radius: 6px; text-transform: uppercase; white-space: nowrap; flex-shrink: 0;
}
.priority-critical { background: rgba(231,76,60,0.12); color: #C0392B; }
.priority-high { background: rgba(240,168,48,0.15); color: #D4940A; }
.priority-medium { background: rgba(52,152,219,0.12); color: #2980B9; }
.report-kpi-row { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
.report-kpi {
    flex: 1; min-width: 110px; background: #F8FAFC; border-radius: 12px;
    padding: 14px 12px; text-align: center; border: 1px solid #E0E6E3;
}
.report-kpi .kpi-val { font-size: 1.5rem; font-weight: 900; color: #1A1F2E; line-height: 1.1; }
.report-kpi .kpi-label { font-size: 0.62rem; font-weight: 700; color: #6B7B8D; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 3px; }
.gen-btn-wrap .stButton > button {
    background: linear-gradient(135deg, #8E44AD, #6C3483) !important;
    color: #FFFFFF !important; border: none !important;
    font-size: 1rem !important; font-weight: 800 !important;
    padding: 12px 36px !important; border-radius: 14px !important;
    box-shadow: 0 6px 24px rgba(142, 68, 173, 0.35) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
}
.gen-btn-wrap .stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 12px 36px rgba(142, 68, 173, 0.45) !important;
}
.gen-btn-wrap .stButton > button p { color: #FFFFFF !important; }
</style>
"""

with main:
    page_header(
        "Network Lifecycle Risk Executive Overview",
        subtitle="Southern Company — Enterprise Device Lifecycle Snapshot",
        breadcrumb="HOME > EXECUTIVE OVERVIEW",
    )
    st.markdown("---")

    tab_exec, tab_ai, tab_lifecycle, tab_alerts = st.tabs(
        ["📊 Executive Overview", "🧠 AI Executive Brief", "🔄 Lifecycle Status", "🔔 Recent Alerts"]
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

    # ─── TAB 4: AI EXECUTIVE BRIEF ────────────────────────────────────────
    with tab_ai:
        st.markdown(REPORT_CSS, unsafe_allow_html=True)

        metrics = _compute_fleet_metrics(df)
        st.session_state["exec_report_metrics"] = metrics

        health_score = metrics["health_score"]
        score_color = "#E74C3C" if health_score < 50 else "#F0A830" if health_score < 75 else "#27AE60"

        st.markdown(f"""
        <div style="text-align:center; padding:16px 0 8px; animation: fadeInUp 0.5s ease-out;">
            <div style="font-size:0.62rem; font-weight:800; letter-spacing:1.2px; color:#FFFFFF;
                        background:linear-gradient(135deg,#8E44AD,#6C3483); border-radius:999px;
                        padding:5px 16px; display:inline-block; text-transform:uppercase;
                        box-shadow:0 4px 14px rgba(142,68,173,0.3); margin-bottom:10px;
                        animation: pulse 2s ease-in-out infinite;">AI-POWERED ANALYSIS</div>
            <div style="font-size:1.05rem; font-weight:600; color:#6B7B8D; max-width:520px; margin:0 auto; line-height:1.6;">
                Generate a comprehensive strategic intelligence brief with risk assessment,
                financial impact analysis, and a 90-day action roadmap.
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Fleet Health", f"{health_score}/100")
        m2.metric("Critical Devices", f"{metrics['critical']:,}")
        m3.metric("Total Exposure", fmt_currency(metrics['total_cost']))
        m4.metric("Avoidable Spend", fmt_currency(metrics['decom_savings']))

        st.markdown("")
        st.markdown('<div class="gen-btn-wrap">', unsafe_allow_html=True)
        _, btn_col, _ = st.columns([2, 3, 2])
        with btn_col:
            gen_clicked = st.button(
                "Generate AI Executive Brief",
                use_container_width=True,
                key="exec_gen_report_btn",
            )
        st.markdown('</div>', unsafe_allow_html=True)

        if gen_clicked:
            with st.spinner("Analyzing fleet data and generating strategic insights..."):
                prompt = _build_report_prompt(metrics)
                report_html = _generate_report_exec(prompt)
                st.session_state["exec_generated_report"] = report_html
                st.session_state["exec_report_generated_at"] = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")

        if "exec_generated_report" in st.session_state:
            generated_at = st.session_state.get("exec_report_generated_at", "")
            report_html = st.session_state["exec_generated_report"]

            st.markdown(f"""
            <div style="text-align:center; font-size:0.75rem; color:#94A3B8; font-weight:600;
                        margin:12px 0 4px; letter-spacing:0.5px;">
                Generated on {generated_at} | Southern Company Fleet Analytics
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="report-container">
                <div style="text-align:center; margin-bottom:20px;">
                    <div style="font-size:0.6rem; font-weight:800; letter-spacing:1.5px; color:#8E44AD;
                                text-transform:uppercase; margin-bottom:4px;">CONFIDENTIAL</div>
                    <div style="font-size:1.4rem; font-weight:900; color:#1A1F2E; letter-spacing:-0.5px;">
                        Southern Company Fleet Intelligence Brief
                    </div>
                    <div style="font-size:0.8rem; color:#6B7B8D; font-weight:600; margin-top:3px;">
                        AI-Generated Strategic Analysis | {generated_at}
                    </div>
                </div>
                <div class="report-kpi-row">
                    <div class="report-kpi">
                        <div class="kpi-val" style="color:{score_color};">{health_score}</div>
                        <div class="kpi-label">Health Score</div>
                    </div>
                    <div class="report-kpi">
                        <div class="kpi-val">{metrics['total']:,}</div>
                        <div class="kpi-label">Total Devices</div>
                    </div>
                    <div class="report-kpi">
                        <div class="kpi-val" style="color:#E74C3C;">{metrics['critical']:,}</div>
                        <div class="kpi-label">Critical</div>
                    </div>
                    <div class="report-kpi">
                        <div class="kpi-val">{fmt_currency(metrics['total_cost'])}</div>
                        <div class="kpi-label">Total Exposure</div>
                    </div>
                    <div class="report-kpi">
                        <div class="kpi-val" style="color:#27AE60;">{fmt_currency(metrics['decom_savings'])}</div>
                        <div class="kpi-label">Avoidable Spend</div>
                    </div>
                </div>
                {report_html}
            </div>
            """, unsafe_allow_html=True)

            full_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Southern Company Fleet Intelligence Brief</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
body {{ font-family: 'Inter', sans-serif; background: #F8FAFC; color: #1A1F2E; padding: 40px; max-width: 900px; margin: 0 auto; line-height: 1.7; }}
h2 {{ font-size: 1.4rem; font-weight: 900; border-bottom: 3px solid #E8734A; padding-bottom: 8px; margin: 32px 0 16px; }}
h3 {{ font-size: 1.1rem; font-weight: 800; color: #334155; }}
p, li {{ font-size: 0.95rem; color: #334155; }}
.highlight-box {{ background: linear-gradient(135deg, rgba(232,115,74,0.08), rgba(232,115,74,0.03)); border-left: 4px solid #E8734A; border-radius: 0 12px 12px 0; padding: 16px 20px; margin: 16px 0; font-weight: 600; }}
.action-item {{ background: #F8FAFC; border-radius: 12px; padding: 14px 18px; margin: 10px 0; border: 1px solid #E0E6E3; display: flex; align-items: flex-start; gap: 12px; }}
.priority {{ font-size: 0.65rem; font-weight: 800; padding: 3px 10px; border-radius: 6px; text-transform: uppercase; white-space: nowrap; }}
.priority-critical {{ background: rgba(231,76,60,0.12); color: #C0392B; }}
.priority-high {{ background: rgba(240,168,48,0.15); color: #D4940A; }}
.priority-medium {{ background: rgba(52,152,219,0.12); color: #2980B9; }}
</style></head><body>
<div style="text-align:center; margin-bottom:32px;">
<div style="font-size:0.65rem; font-weight:800; letter-spacing:1.5px; color:#8E44AD; text-transform:uppercase;">CONFIDENTIAL</div>
<h1 style="font-size:1.8rem; font-weight:900; margin:8px 0;">Southern Company Fleet Intelligence Brief</h1>
<div style="font-size:0.85rem; color:#6B7B8D; font-weight:600;">AI-Generated Strategic Analysis | {generated_at}</div>
</div>{report_html}</body></html>"""

            _, dl_col, _ = st.columns([2, 3, 2])
            with dl_col:
                st.download_button(
                    label="Download Report (HTML)",
                    data=full_html.encode("utf-8"),
                    file_name=f"southern_company_fleet_brief_{datetime.datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True,
                    key="exec_download_report_btn",
                )
        else:
            st.markdown("""
            <div style="text-align:center; padding:40px 20px; animation: fadeInUp 0.5s ease-out;">
                <div style="font-size:3.5rem; margin-bottom:12px;">🧠</div>
                <div style="font-size:1.1rem; font-weight:800; color:#1A1F2E; margin-bottom:6px;">
                    Ready to Generate Your Executive Brief
                </div>
                <div style="font-size:0.88rem; color:#6B7B8D; font-weight:500; max-width:480px; margin:0 auto; line-height:1.6;">
                    Our AI analyzes the fleet dataset and generates a comprehensive strategic report
                    with risk assessment, financial impact, and a 90-day action roadmap — in seconds.
                </div>
            </div>
            """, unsafe_allow_html=True)
