import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.dashboard_chatbot import render_dashboard_chatbot
from src.download_utils import render_plotly_with_download
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, PLOTLY_LAYOUT, PLOTLY_CLEAN,
)

st.set_page_config(page_title="Predictive Risk Forecast", page_icon="🔮", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = apply_global_filters(load_data(DATA_PATH))
df["Total_Replacement_Cost"] = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
df["Risk_Score"] = pd.to_numeric(df["Risk_Score"], errors="coerce").fillna(0)
df["Days_Past_EoL"] = pd.to_numeric(df["Days_Past_EoL"], errors="coerce").fillna(0)
df["Is_Decom"] = df["Is_Decom"].astype(bool)
if "EoL_Year" in df.columns:
    df["EoL_Year"] = pd.to_numeric(df["EoL_Year"], errors="coerce")

main = render_dashboard_chatbot(page_title="Predictive Risk Forecast", df=df)

with main:
    page_header(
        "Predictive Risk & Cost Forecast",
        subtitle="Forward-looking risk trajectory, cost-of-inaction modeling, and investment scenario analysis",
        breadcrumb="HOME > PREDICTIVE RISK FORECAST",
    )
    st.markdown("---")

    tab_forecast, tab_inaction, tab_scenario = st.tabs([
        "📈 Risk Trajectory Forecast",
        "💸 Cost of Inaction",
        "🎯 Scenario Comparison",
    ])

    # ── TAB 1: RISK TRAJECTORY ────────────────────────────────────────────
    with tab_forecast:
        st.subheader("Cumulative EoL Risk Trajectory (2024 – 2035)")

        if "EoL_Year" in df.columns:
            eol_data = df[df["EoL_Year"].notna() & (df["EoL_Year"] >= 2020) & (df["EoL_Year"] <= 2035)].copy()

            yearly_eol = eol_data.groupby("EoL_Year").agg(
                devices=("EoL_Year", "size"),
                cost=("Total_Replacement_Cost", "sum"),
            ).reset_index()

            all_years = pd.DataFrame({"EoL_Year": range(2020, 2036)})
            yearly_eol = all_years.merge(yearly_eol, on="EoL_Year", how="left").fillna(0)
            yearly_eol["cumulative_devices"] = yearly_eol["devices"].cumsum()
            yearly_eol["cumulative_cost"] = yearly_eol["cost"].cumsum()

            current_year = 2026
            past = yearly_eol[yearly_eol["EoL_Year"] <= current_year].copy()
            future = yearly_eol[yearly_eol["EoL_Year"] >= current_year].copy()

            fig_traj = go.Figure()
            fig_traj.add_trace(go.Scatter(
                x=past["EoL_Year"], y=past["cumulative_devices"],
                mode="lines+markers", name="Historical",
                line=dict(color=COLORS["coral"], width=3),
                marker=dict(size=8, color=COLORS["coral"]),
                fill="tozeroy", fillcolor="rgba(232, 115, 74, 0.08)",
            ))
            fig_traj.add_trace(go.Scatter(
                x=future["EoL_Year"], y=future["cumulative_devices"],
                mode="lines+markers", name="Projected (No Action)",
                line=dict(color=COLORS["crimson"], width=3, dash="dash"),
                marker=dict(size=8, color=COLORS["crimson"], symbol="diamond"),
                fill="tozeroy", fillcolor="rgba(231, 76, 60, 0.06)",
            ))

            fig_traj.add_vline(x=current_year, line_dash="dot", line_color="#6B7B8D",
                               annotation_text="Today", annotation_position="top")

            fig_traj.update_layout(
                **PLOTLY_LAYOUT,
                xaxis_title="Year",
                yaxis_title="Cumulative Devices Reaching EoL",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified",
            )
            fig_traj.update_layout(height=480)
            render_plotly_with_download(fig_traj, "risk_trajectory_forecast", "pred_risk_trajectory",
                                       use_container_width=True, config=PLOTLY_CLEAN)

            section_divider()

            st.subheader("Year-over-Year EoL Wave")
            fig_wave = px.bar(
                yearly_eol[yearly_eol["EoL_Year"] >= 2024],
                x="EoL_Year", y="devices", text="devices",
                color_discrete_sequence=[COLORS["coral"]],
                labels={"devices": "Devices Reaching EoL", "EoL_Year": "Year"},
            )
            fig_wave.update_traces(textposition="outside", textfont_size=13, textfont_color="#1A1F2E",
                                   marker_line_width=0)
            fig_wave.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            fig_wave.update_layout(height=380)
            render_plotly_with_download(fig_wave, "year_over_year_eol_wave", "pred_yoy_wave",
                                       use_container_width=True, config=PLOTLY_CLEAN)
        else:
            st.info("EoL_Year column not available for trajectory forecasting.")

    # ── TAB 2: COST OF INACTION ───────────────────────────────────────────
    with tab_inaction:
        st.subheader("The Price of Delay")
        st.markdown("""
        <div style="background: rgba(231,76,60,0.06); border-left: 4px solid #E74C3C;
                    border-radius: 0 12px 12px 0; padding: 16px 20px; margin-bottom: 20px;
                    font-size: 0.92rem; font-weight: 600; color: #1A1F2E; line-height: 1.6;">
            Every quarter of delayed action increases security exposure, compliance risk,
            and total replacement cost. This model projects the compounding financial impact
            of maintaining the status quo.
        </div>
        """, unsafe_allow_html=True)

        critical_devices = df[df["Risk_Level"].str.contains("Critical", case=False, na=False)]
        high_devices = df[df["Risk_Level"].str.contains("High", case=False, na=False)]
        critical_cost = critical_devices["Total_Replacement_Cost"].sum()
        high_cost = high_devices["Total_Replacement_Cost"].sum()

        incident_rate = 0.02
        support_premium = 0.08
        compliance_penalty_rate = 0.03

        quarters = list(range(0, 13))
        quarter_labels = [f"Q{(i % 4) + 1} {2026 + i // 4}" for i in quarters]

        base_cost = critical_cost + high_cost
        cumulative_costs = []
        incident_costs = []
        support_costs = []
        compliance_costs = []

        for q in quarters:
            incident = base_cost * incident_rate * q
            support = base_cost * support_premium * q
            compliance = base_cost * compliance_penalty_rate * max(0, q - 2)
            total = base_cost + incident + support + compliance
            cumulative_costs.append(total)
            incident_costs.append(incident)
            support_costs.append(support)
            compliance_costs.append(compliance)

        inaction_df = pd.DataFrame({
            "Quarter": quarter_labels,
            "quarter_num": quarters,
            "Base Replacement": [base_cost] * len(quarters),
            "Incident Risk": incident_costs,
            "Extended Support": support_costs,
            "Compliance Risk": compliance_costs,
            "Total Cost": cumulative_costs,
        })

        k1, k2, k3, k4 = st.columns(4)
        year1_cost = cumulative_costs[4] - base_cost
        year2_cost = cumulative_costs[8] - base_cost
        year3_cost = cumulative_costs[12] - base_cost
        k1.metric("Base Replacement Cost", fmt_currency(base_cost))
        k2.metric("Added Cost (Year 1)", fmt_currency(year1_cost), delta=f"+{year1_cost/max(base_cost,1)*100:.1f}%", delta_color="inverse")
        k3.metric("Added Cost (Year 2)", fmt_currency(year2_cost), delta=f"+{year2_cost/max(base_cost,1)*100:.1f}%", delta_color="inverse")
        k4.metric("Added Cost (Year 3)", fmt_currency(year3_cost), delta=f"+{year3_cost/max(base_cost,1)*100:.1f}%", delta_color="inverse")

        section_divider()

        fig_inaction = go.Figure()
        fig_inaction.add_trace(go.Scatter(
            x=quarter_labels, y=inaction_df["Base Replacement"],
            mode="lines", name="Base Replacement Cost",
            line=dict(color=COLORS["emerald"], width=2),
            stackgroup="one",
        ))
        fig_inaction.add_trace(go.Scatter(
            x=quarter_labels, y=inaction_df["Incident Risk"],
            mode="lines", name="Projected Incident Cost",
            line=dict(color=COLORS["gold"], width=2),
            stackgroup="one",
        ))
        fig_inaction.add_trace(go.Scatter(
            x=quarter_labels, y=inaction_df["Extended Support"],
            mode="lines", name="Extended Support Premium",
            line=dict(color=COLORS["coral"], width=2),
            stackgroup="one",
        ))
        fig_inaction.add_trace(go.Scatter(
            x=quarter_labels, y=inaction_df["Compliance Risk"],
            mode="lines", name="Compliance Penalty Risk",
            line=dict(color=COLORS["crimson"], width=2),
            stackgroup="one",
        ))

        fig_inaction.update_layout(
            **PLOTLY_LAYOUT,
            yaxis_title="Cumulative Cost Exposure ($)",
            xaxis_title="Quarter",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified",
            yaxis_tickformat="$,.0f",
        )
        fig_inaction.update_layout(height=500)
        render_plotly_with_download(fig_inaction, "cost_of_inaction_stacked", "pred_cost_inaction",
                                   use_container_width=True, config=PLOTLY_CLEAN)

        section_divider()

        st.subheader("Quarterly Cost Breakdown")
        display_inaction = inaction_df[["Quarter", "Base Replacement", "Incident Risk",
                                        "Extended Support", "Compliance Risk", "Total Cost"]].copy()
        for col in ["Base Replacement", "Incident Risk", "Extended Support", "Compliance Risk", "Total Cost"]:
            display_inaction[col] = display_inaction[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display_inaction, use_container_width=True, hide_index=True)

    # ── TAB 3: SCENARIO COMPARISON ────────────────────────────────────────
    with tab_scenario:
        st.subheader("Investment Scenario Analyzer")

        invest_col, _, viz_col = st.columns([3, 1, 6])
        with invest_col:
            annual_budget = st.slider(
                "Annual Investment Budget",
                min_value=0, max_value=5_000_000, value=1_500_000, step=100_000,
                format="$%d", key="scenario_budget",
            )
            replacement_pace = st.select_slider(
                "Replacement Pace",
                options=["Conservative", "Moderate", "Aggressive"],
                value="Moderate",
            )
            pace_multiplier = {"Conservative": 0.7, "Moderate": 1.0, "Aggressive": 1.4}[replacement_pace]

        total_devices = len(df)
        critical_count = (df["Risk_Level"].str.contains("Critical", case=False, na=False)).sum()
        high_count = (df["Risk_Level"].str.contains("High", case=False, na=False)).sum()
        at_risk = critical_count + high_count
        avg_cost = df.loc[df["Total_Replacement_Cost"] > 0, "Total_Replacement_Cost"].mean()
        avg_cost = avg_cost if pd.notna(avg_cost) else 2000

        years = list(range(2026, 2033))
        do_nothing_risk = []
        invest_risk = []

        remaining_risk_nothing = at_risk
        remaining_risk_invest = at_risk

        if "EoL_Year" in df.columns:
            future_eol = df[(df["EoL_Year"] >= 2026) & (df["EoL_Year"] <= 2032)]
            yearly_new_eol = future_eol.groupby("EoL_Year").size().to_dict()
        else:
            yearly_new_eol = {y: int(at_risk * 0.08) for y in years}

        for year in years:
            new_eol = yearly_new_eol.get(year, 0)
            remaining_risk_nothing += new_eol
            do_nothing_risk.append(remaining_risk_nothing)

            devices_replaced = int((annual_budget / max(avg_cost, 1)) * pace_multiplier)
            remaining_risk_invest = max(0, remaining_risk_invest + new_eol - devices_replaced)
            invest_risk.append(remaining_risk_invest)

        with viz_col:
            fig_scenario = go.Figure()
            fig_scenario.add_trace(go.Scatter(
                x=years, y=do_nothing_risk,
                mode="lines+markers", name="Do Nothing",
                line=dict(color=COLORS["crimson"], width=3),
                marker=dict(size=10, color=COLORS["crimson"]),
                fill="tozeroy", fillcolor="rgba(231, 76, 60, 0.06)",
            ))
            fig_scenario.add_trace(go.Scatter(
                x=years, y=invest_risk,
                mode="lines+markers", name=f"Invest {fmt_currency(annual_budget)}/yr",
                line=dict(color=COLORS["emerald"], width=3),
                marker=dict(size=10, color=COLORS["emerald"]),
                fill="tozeroy", fillcolor="rgba(39, 174, 96, 0.06)",
            ))

            fig_scenario.add_vline(x=2026, line_dash="dot", line_color="#6B7B8D",
                                   annotation_text="Now", annotation_position="top")

            fig_scenario.update_layout(
                **PLOTLY_LAYOUT,
                xaxis_title="Year",
                yaxis_title="At-Risk Devices",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                hovermode="x unified",
            )
            fig_scenario.update_layout(height=460)
            render_plotly_with_download(fig_scenario, "scenario_comparison", "pred_scenario_compare",
                                       use_container_width=True, config=PLOTLY_CLEAN)

        section_divider()

        devices_per_year = int((annual_budget / max(avg_cost, 1)) * pace_multiplier)
        years_to_clear = int(np.ceil(at_risk / max(devices_per_year, 1))) if devices_per_year > 0 else 999
        total_investment = annual_budget * min(years_to_clear, 7)
        risk_reduction_y1 = min(100, (devices_per_year / max(at_risk, 1)) * 100)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Devices Replaced/Year", f"{devices_per_year:,}")
        s2.metric("Years to Clear Backlog", f"{min(years_to_clear, 7)}+" if years_to_clear > 7 else str(years_to_clear))
        s3.metric("Year 1 Risk Reduction", f"{risk_reduction_y1:.1f}%")
        s4.metric("Total Investment Required", fmt_currency(total_investment))

        section_divider()

        st.subheader("Scenario Impact Summary")
        final_nothing = do_nothing_risk[-1]
        final_invest = invest_risk[-1]
        devices_saved = final_nothing - final_invest
        cost_saved = devices_saved * avg_cost

        st.markdown(f"""
        <div style="background: rgba(39,174,96,0.06); border-left: 4px solid #27AE60;
                    border-radius: 0 12px 12px 0; padding: 20px 24px; margin: 8px 0;
                    font-size: 0.95rem; line-height: 1.7; color: #1A1F2E;">
            <strong style="font-size: 1.05rem;">By investing {fmt_currency(annual_budget)} annually at a {replacement_pace.lower()} pace:</strong><br><br>
            By 2032, your at-risk fleet reduces from <strong>{final_nothing:,}</strong> devices (do nothing)
            to <strong>{final_invest:,}</strong> devices — a reduction of <strong>{devices_saved:,}</strong> devices
            ({devices_saved/max(final_nothing,1)*100:.0f}% improvement).<br><br>
            Estimated avoided replacement & incident cost: <strong>{fmt_currency(cost_saved)}</strong><br>
            Estimated avoided security incidents: <strong>{int(devices_saved * 0.02):,}</strong> per year<br>
            Projected compliance risk reduction: <strong>{min(99, devices_saved/max(final_nothing,1)*100):.0f}%</strong>
        </div>
        """, unsafe_allow_html=True)
