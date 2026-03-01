import json
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.download_utils import render_plotly_with_download, render_table_with_download
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, PLOTLY_LAYOUT, PLOTLY_CLEAN,
)

st.set_page_config(page_title="Investment Prioritization", page_icon="🎯", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
EXCEPTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "exceptions.json")

REQUIRED_COLS = [
    "Hostname", "State", "Site_Code", "Risk_Level",
    "Total_Replacement_Cost", "Risk_Score", "Is_Decom",
]

EXCEPTION_REASONS = [
    "Planned Decommission",
    "Vendor Negotiation in Progress",
    "Budget Deferred to Next Cycle",
    "Site Closure Scheduled",
    "Covered by Separate Project",
    "Other",
]


def load_exceptions():
    if os.path.exists(EXCEPTIONS_PATH):
        try:
            with open(EXCEPTIONS_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_exceptions(exc):
    with open(EXCEPTIONS_PATH, "w") as f:
        json.dump(exc, f, indent=2)


all_df = apply_global_filters(load_data(DATA_PATH))[REQUIRED_COLS].copy()
all_df["Total_Replacement_Cost"] = pd.to_numeric(all_df["Total_Replacement_Cost"], errors="coerce").fillna(0)
all_df["Risk_Score"] = pd.to_numeric(all_df["Risk_Score"], errors="coerce").fillna(0)
all_df["Is_Decom"] = all_df["Is_Decom"].astype(bool)
all_df = all_df[(~all_df["Is_Decom"]) & (all_df["Risk_Score"] > 0)].copy()

exceptions = load_exceptions()
excepted_hosts = set(exceptions.keys())
n_excepted = int(all_df["Hostname"].isin(excepted_hosts).sum())
df = all_df[~all_df["Hostname"].isin(excepted_hosts)].copy()

page_header(
    "Investment Prioritization & Risk Reduction",
    subtitle="Data-driven replacement roadmap based on risk severity, support status, and cost.",
    breadcrumb="HOME > INVESTMENT PRIORITIZATION",
)
st.markdown("---")

if n_excepted > 0:
    st.markdown(
        f"<div style='background: #FFF3CD; border: 1px solid #FFEEBA; border-radius: 8px; "
        f"padding: 10px 16px; font-family: Inter, sans-serif; font-size: 14px; "
        f"color: #856404; margin-bottom: 16px;'>"
        f"&#9432; <b>{n_excepted}</b> device(s) excluded from scope via "
        f"Exception Management below.</div>",
        unsafe_allow_html=True,
    )

# ── Budget Impact Simulator ──────────────────────────────────────────────────
st.subheader("Budget Impact Simulator")

budget = st.slider(
    "Select 2026 CapEx Budget",
    min_value=0, max_value=5_000_000, value=1_000_000, step=50_000,
    format="$%d",
)

priority_df = df.sort_values("Risk_Score", ascending=False).reset_index(drop=True)
priority_df["Cumulative_Cost"] = priority_df["Total_Replacement_Cost"].cumsum()

devices_in_budget = int((priority_df["Cumulative_Cost"] <= budget).sum())
total_devices = len(priority_df)
pct_cleared = (devices_in_budget / total_devices * 100) if total_devices > 0 else 0

k1, k2, k3 = st.columns(3)
k1.metric("Selected Budget", fmt_currency(budget))
k2.metric("Devices Fully Replaced", f"{devices_in_budget:,} / {total_devices:,}")
k3.metric("Critical Debt Cleared", f"{pct_cleared:.1f}%")

if devices_in_budget > 0:
    actual_spend = priority_df.loc[: devices_in_budget - 1, "Total_Replacement_Cost"].sum()
    summary_text = (
        f"With a budget of <b>{fmt_currency(budget)}</b>, you can fully replace the top "
        f"<b>{devices_in_budget:,}</b> highest-risk devices (actual cost "
        f"<b>{fmt_currency(actual_spend)}</b>), completely clearing "
        f"<b>{pct_cleared:.1f}%</b> of critical technical debt."
    )
    st.markdown(
        f"<div style='background:#d4edda; border:1px solid #b7dfb9; border-radius:8px; "
        f"padding:14px 18px; font-family:Inter,sans-serif; font-size:15px; "
        f"color:#1a1f36; line-height:1.6;'>✅ {summary_text}</div>",
        unsafe_allow_html=True,
    )
else:
    st.warning(
        "The selected budget does not cover even the single highest-risk device. "
        "Consider increasing the allocation."
    )

section_divider()

# ── Priority Ranking Table ───────────────────────────────────────────────────
st.subheader("Priority Ranking — Top Devices Within Budget")

DISPLAY_COLS = [
    "Hostname", "State", "Site_Code", "Risk_Level",
    "Risk_Score", "Total_Replacement_Cost",
]

table_df = priority_df.loc[priority_df["Cumulative_Cost"] <= budget, DISPLAY_COLS].head(100)

if table_df.empty:
    st.info("No devices fall within the selected budget.")
else:
    display_df = table_df.copy()
    display_df["Total_Replacement_Cost"] = display_df["Total_Replacement_Cost"].round(0)
    max_risk = float(display_df["Risk_Score"].max()) if not display_df.empty else 100
    render_table_with_download(
        display_df,
        "priority_ranking_top_devices_within_budget",
        "investment_priority_ranking_table",
        export_df=display_df,
        use_container_width=True, height=460, hide_index=True,
        column_config={
            "Risk_Score": st.column_config.ProgressColumn(
                "Risk Score", format="%.1f", min_value=0, max_value=max_risk,
            ),
            "Total_Replacement_Cost": st.column_config.NumberColumn(
                "Total Replacement Cost", format="$ %.0f",
            ),
        },
    )

section_divider()

# ── Top Sites ────────────────────────────────────────────────────────────────
st.subheader("Top 10 Sites Requiring Immediate Intervention")

site_risk = (
    df.groupby("Site_Code", as_index=False)["Risk_Score"]
    .sum()
    .sort_values("Risk_Score", ascending=False)
    .head(10)
    .sort_values("Risk_Score", ascending=True)
)

if site_risk.empty:
    st.info("No site-level risk data available.")
else:
    fig_sites = px.bar(
        site_risk, x="Risk_Score", y="Site_Code",
        orientation="h", text="Risk_Score",
        color_discrete_sequence=[COLORS["crimson"]],
        labels={"Risk_Score": "Aggregate Risk Score", "Site_Code": "Site Code"},
    )
    fig_sites.update_traces(
        texttemplate="%{text:.0f}", textposition="outside",
        textfont_size=14,
        marker_line_width=0,
    )
    fig_sites.update_layout(PLOTLY_LAYOUT)
    fig_sites.update_layout(
        showlegend=False,
        xaxis_title="Aggregate Risk Score", yaxis_title=None,
        height=440,
    )
    render_plotly_with_download(
        fig_sites,
        "top_sites_requiring_immediate_intervention",
        "investment_top_sites_intervention",
        use_container_width=True,
        config=PLOTLY_CLEAN,
    )

section_divider()

# ── Scope Exception Management ───────────────────────────────────────────────
st.subheader("Scope Exception Management")
st.caption(
    "Flag active devices to exclude from replacement scope. "
    "Excluded devices are omitted from the budget simulation and priority rankings above."
)

exc_left, exc_right = st.columns(2)

with exc_left:
    st.markdown("**Add Exception**")
    with st.form("add_exception_form", clear_on_submit=True):
        available = sorted(
            all_df[~all_df["Hostname"].isin(excepted_hosts)]["Hostname"].tolist()
        )
        selected_to_exclude = st.multiselect(
            "Select devices to exclude",
            options=available,
            help="Search by hostname. Only non-excluded active devices are shown.",
        )
        reason = st.selectbox("Reason for exclusion", options=EXCEPTION_REASONS)
        add_submitted = st.form_submit_button(
            "Mark as Exception", type="primary"
        )
        if add_submitted and selected_to_exclude:
            for h in selected_to_exclude:
                exceptions[h] = {
                    "reason": reason,
                    "added": str(pd.Timestamp.now().date()),
                }
            save_exceptions(exceptions)
            st.rerun()

with exc_right:
    st.markdown("**Current Exceptions**")
    if exceptions:
        exc_display = pd.DataFrame(
            [
                {
                    "Hostname": k,
                    "Reason": v.get("reason", ""),
                    "Date Added": v.get("added", ""),
                }
                for k, v in exceptions.items()
            ]
        )
        render_table_with_download(
            exc_display,
            "scope_exception_management_current_exceptions",
            "investment_scope_exceptions_table",
            export_df=exc_display,
            use_container_width=True,
            hide_index=True,
            height=250,
        )
        with st.form("remove_exception_form", clear_on_submit=True):
            to_remove = st.multiselect(
                "Select exceptions to remove",
                options=list(exceptions.keys()),
            )
            remove_submitted = st.form_submit_button("Remove Selected")
            if remove_submitted and to_remove:
                for h in to_remove:
                    exceptions.pop(h, None)
                save_exceptions(exceptions)
                st.rerun()
    else:
        st.info("No devices are currently excluded from scope.")
