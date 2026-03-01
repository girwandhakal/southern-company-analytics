import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.dashboard_chatbot import render_dashboard_chatbot
from src.theme import (
    inject_theme_css, page_header, section_divider, fmt_currency,
    COLORS, RISK_COLOR_MAP, RISK_ORDER, PLOTLY_LAYOUT, PLOTLY_CLEAN,
)

st.set_page_config(page_title="Risk & Geography", page_icon="🌎", layout="wide")
inject_theme_css()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)
df = apply_global_filters(df)
df["Total_Replacement_Cost"] = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

main = render_dashboard_chatbot(page_title="Risk & Geography", df=df)

RISK_RGBA = {
    "Critical (Past EoL)": [231, 76, 60, 200],
    "High (Near EoL)": [240, 168, 48, 200],
    "Medium (Approaching EoL)": [52, 152, 219, 200],
    "Low (Healthy)": [39, 174, 96, 200],
}

with main:
    page_header(
        "Geographic Lifecycle Risk Mapping",
        subtitle="Identify risk hotspots and cluster aging infrastructure for optimized field deployments.",
        breadcrumb="HOME > GEOGRAPHIC RISK INTELLIGENCE",
    )
    st.markdown("---")

    all_states = sorted(df["State"].dropna().unique().tolist())
    selected_states = st.multiselect(
        "Filter by State", options=all_states, default=[],
        help="Leave empty to show all states.",
    )

    df_filtered = df[df["State"].isin(selected_states)].copy() if selected_states else df.copy()

    # ── 3-D Risk Map ─────────────────────────────────────────────────────
    st.subheader("3-D Risk Map")
    map_df = df_filtered.dropna(subset=["Latitude", "Longitude"]).copy()

    if map_df.empty:
        st.info("No device locations available for the current filter selection.")
    else:
        map_df["color"] = map_df["Risk_Level"].map(RISK_RGBA)
        map_df["color"] = map_df["color"].apply(
            lambda c: c if isinstance(c, list) else [150, 150, 150, 160]
        )

        view = pdk.data_utils.compute_view(map_df[["Longitude", "Latitude"]], view_proportion=0.9)
        view.pitch = 45
        view.bearing = 10

        scatter_layer = pdk.Layer(
            "ScatterplotLayer", data=map_df,
            get_position=["Longitude", "Latitude"],
            get_color="color", get_radius=1200,
            pickable=True, auto_highlight=True,
        )
        col_layer = pdk.Layer(
            "ColumnLayer", data=map_df,
            get_position=["Longitude", "Latitude"],
            get_elevation="Total_Replacement_Cost",
            elevation_scale=0.5, radius=4000,
            get_fill_color=[232, 115, 74, 140],
            pickable=True, auto_highlight=True,
        )
        tooltip = {
            "html": (
                "<b>{Hostname}</b><br/>"
                "Risk: {Risk_Level}<br/>"
                "Cost: ${Total_Replacement_Cost}<br/>"
                "State: {State}"
            ),
            "style": {
                "backgroundColor": "#1A1F2E",
                "color": "#ffffff",
                "fontSize": "13px",
                "padding": "10px 14px",
                "borderRadius": "10px",
                "boxShadow": "0 8px 24px rgba(0,0,0,0.25)",
                "fontFamily": "Inter, sans-serif",
            },
        }
        deck = pdk.Deck(
            layers=[col_layer, scatter_layer],
            initial_view_state=view,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip=tooltip,
        )
        st.pydeck_chart(deck, use_container_width=True)

    # ── Risk Clustering Table ────────────────────────────────────────────
    section_divider()
    st.subheader("Risk Clustering — Priority Sites for Field Deployment")
    st.caption(
        "Sites ranked by total replacement cost of Critical and High-risk devices. "
        "Send technicians to the top rows first."
    )

    cluster_mask = df_filtered["Risk_Level"].isin(["Critical (Past EoL)", "High (Near EoL)"])
    cluster_df = df_filtered[cluster_mask]

    if cluster_df.empty:
        st.info("No high-risk clusters found for the selected filters.")
    else:
        site_summary = (
            cluster_df.groupby(["Site_Code", "State"])
            .agg(
                High_Risk_Device_Count=("Hostname", "size"),
                Total_Replacement_Cost=("Total_Replacement_Cost", "sum"),
            )
            .reset_index()
            .sort_values("Total_Replacement_Cost", ascending=False)
        )
        site_summary["Total_Replacement_Cost"] = site_summary[
            "Total_Replacement_Cost"
        ].apply(lambda v: f"${v:,.2f}")

        st.dataframe(
            site_summary, use_container_width=True, hide_index=True,
            column_config={
                "Site_Code": st.column_config.TextColumn("Site Code"),
                "State": st.column_config.TextColumn("State"),
                "High_Risk_Device_Count": st.column_config.NumberColumn("High-Risk Devices"),
                "Total_Replacement_Cost": st.column_config.TextColumn("Total Replacement Cost"),
            },
        )
