import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")

# ── Executive styling ───────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fc 0%, #ffffff 100%);
        border: 1px solid #e2e6ed;
        border-radius: 12px;
        padding: 18px 20px 14px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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
    hr { border: none; border-top: 1px solid #e8ecf1; margin: 28px 0 20px 0; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data loading via shared loader ──────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)

df["Is_Decom"] = df["Is_Decom"].astype(bool)
df["Total_Replacement_Cost"] = pd.to_numeric(
    df["Total_Replacement_Cost"], errors="coerce"
).fillna(0)
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

main = render_dashboard_chatbot(page_title="Executive Overview", df=df)

# ── Consistent colour palette for Risk_Level ────────────────────────────────
RISK_COLOR_MAP = {
    "Low (Healthy)": "#27ae60",
    "Medium (Approaching EoL)": "#2980b9",
    "High (Near EoL)": "#f39c12",
    "Critical (Past EoL)": "#e74c3c",
}
RISK_ORDER = list(RISK_COLOR_MAP.keys())

PLOTLY_CLEAN = {"displayModeBar": False}


def fmt_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"


with main:
    # ═══════════════════════════════════════════════════════════════════════════
    #  PAGE HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<h1 style='text-align:center; color:#1a1f36; margin-bottom:4px;'>"
        "Network Lifecycle Risk Executive Overview</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#7b8794; margin-top:0; font-size:1.05rem;'>"
        "Southern Company — Enterprise Device Lifecycle Snapshot</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    #  TABBED LAYOUT
    # ═══════════════════════════════════════════════════════════════════════════
    tab_exec, tab_lifecycle, tab_alerts = st.tabs(
        ["Executive Overview", "Lifecycle Status", "Recent Alerts"]
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
        k4.metric("Total Replacement Exposure", fmt_currency(total_replacement_exposure))
        k5.metric(
            "Wasted Spend Prevented",
            fmt_currency(wasted_spend_prevented),
            delta=fmt_currency(wasted_spend_prevented),
            delta_color="normal",
            help="Saved by stopping replacements at decommissioned sites",
        )

        st.markdown("---")

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
                    risk_counts,
                    x="Risk_Level",
                    y="Count",
                    color="Risk_Level",
                    color_discrete_map=RISK_COLOR_MAP,
                    text="Count",
                    category_orders={"Risk_Level": RISK_ORDER},
                )
                fig_risk.update_traces(
                    textposition="outside", textfont_size=13, marker_line_width=0,
                )
                fig_risk.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title="Number of Devices",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=80),
                    height=400,
                    xaxis_tickangle=-20,
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(fig_risk, use_container_width=True, config=PLOTLY_CLEAN)

        with right:
            st.subheader("Top 10 States — High-Risk Devices")
            high_risk_df = df[
                df["Risk_Level"].isin(["Critical (Past EoL)", "High (Near EoL)"])
            ]
            if high_risk_df.empty:
                st.info("No high-risk devices found.")
            else:
                state_counts = (
                    high_risk_df.groupby("State")
                    .size()
                    .reset_index(name="Count")
                    .sort_values("Count", ascending=False)
                    .head(10)
                    .sort_values("Count", ascending=True)
                )
                fig_states = px.bar(
                    state_counts,
                    x="Count",
                    y="State",
                    orientation="h",
                    text="Count",
                    color_discrete_sequence=["#e74c3c"],
                )
                fig_states.update_traces(
                    textposition="outside", textfont_size=13, marker_line_width=0,
                )
                fig_states.update_layout(
                    showlegend=False,
                    xaxis_title="High-Risk Device Count",
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=40, t=30, b=40),
                    height=400,
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(fig_states, use_container_width=True, config=PLOTLY_CLEAN)

        st.markdown("---")

        st.subheader("Support Status Distribution")
        support_counts = df["Support_Status"].value_counts().reset_index()
        support_counts.columns = ["Support_Status", "Count"]

        SUPPORT_COLORS = {
            "Unknown / No Data": "#95a5a6",
            "No Support (Past EoL)": "#e74c3c",
            "Expired Support / At Risk (Past EoS)": "#f39c12",
        }

        if support_counts.empty:
            st.info("No support-status data available.")
        else:
            fig_donut = px.pie(
                support_counts,
                values="Count",
                names="Support_Status",
                hole=0.52,
                color="Support_Status",
                color_discrete_map=SUPPORT_COLORS,
            )
            fig_donut.update_traces(
                textinfo="label+percent",
                textposition="outside",
                textfont_size=13,
                pull=[0.02] * len(support_counts),
                marker_line_width=0,
            )
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
                margin=dict(l=40, r=40, t=30, b=60),
                height=420,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
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

        st.markdown("---")
        st.subheader("Device Type Breakdown")
        if "Device Type" in df.columns:
            dtype_risk = (
                df.groupby(["Device Type", "Risk_Level"])
                .size()
                .reset_index(name="Count")
            )
            fig_dt = px.bar(
                dtype_risk,
                x="Device Type",
                y="Count",
                color="Risk_Level",
                color_discrete_map=RISK_COLOR_MAP,
                category_orders={"Risk_Level": RISK_ORDER},
                barmode="stack",
                text="Count",
            )
            fig_dt.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=60),
                height=400,
                font=dict(family="Inter, sans-serif"),
            )
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
            st.success(
                f"**{healthy_count:,}** devices are healthy with no lifecycle concerns."
            )

        decom_count = df["Is_Decom"].sum()
        if decom_count > 0:
            st.info(
                f"**{int(decom_count):,}** devices are at decommissioned sites — "
                "replacement spend can be avoided."
            )
