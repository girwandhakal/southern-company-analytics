import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
import json
import math
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data, apply_global_filters
from src.dashboard_chatbot import render_dashboard_chatbot
from src.download_utils import render_plotly_with_download, render_table_with_download
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
# Severity ranking: lower index = higher severity (used for worst-risk aggregation)
RISK_SEVERITY = {
    "Critical (Past EoL)": 0,
    "High (Near EoL)": 1,
    "Medium (Approaching EoL)": 2,
    "Low (Healthy)": 3,
}

CLUSTER_PALETTE = [
    COLORS["crimson"], COLORS["sky"], COLORS["emerald"], COLORS["gold"],
    COLORS["coral"], "#9B59B6", "#1ABC9C", "#E67E22", "#2980B9", "#C0392B",
    "#16A085", "#D35400", "#8E44AD", "#27AE60", "#F39C12",
]

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

    # Filter out points not in continental US roughly (Lat 24 to 50, Lon -125 to -66)
    us_bounds_mask = (
        (map_df["Latitude"] >= 24) & (map_df["Latitude"] <= 50) &
        (map_df["Longitude"] >= -125) & (map_df["Longitude"] <= -66)
    )
    map_df = map_df[us_bounds_mask]

    if map_df.empty:
        st.info("No device locations available for the current filter selection.")
    else:
        map_df["color"] = map_df["Risk_Level"].map(RISK_RGBA)
        map_df["color"] = map_df["color"].apply(
            lambda c: c if isinstance(c, list) else [150, 150, 150, 160]
        )

        # Aggregate by location for columns: stack co-located devices
        map_df["risk_severity"] = map_df["Risk_Level"].map(RISK_SEVERITY).fillna(99)
        col_agg = map_df.groupby(["Latitude", "Longitude"], as_index=False).agg(
            Total_Replacement_Cost=("Total_Replacement_Cost", "sum"),
            Device_Count=("Hostname", "size"),
            Hostnames=("Hostname", lambda x: ", ".join(x.head(5)) + ("..." if len(x) > 5 else "")),
            State=("State", "first"),
            risk_severity=("risk_severity", "min"),  # worst (lowest index) risk
        )
        # Map worst severity back to risk level and color
        severity_to_risk = {v: k for k, v in RISK_SEVERITY.items()}
        col_agg["Risk_Level"] = col_agg["risk_severity"].map(severity_to_risk)
        col_agg["color"] = col_agg["Risk_Level"].map(RISK_RGBA)
        col_agg["color"] = col_agg["color"].apply(
            lambda c: c if isinstance(c, list) else [150, 150, 150, 160]
        )
        column_records = col_agg[
            ["Longitude", "Latitude", "Total_Replacement_Cost",
             "Risk_Level", "Device_Count", "Hostnames", "State", "color"]
        ].to_dict(orient="records")
        column_data_json = json.dumps(column_records)

        # Compute dynamic view: zoom to data bounds when state filter is active
        if selected_states:
            lat_min, lat_max = map_df["Latitude"].min(), map_df["Latitude"].max()
            lon_min, lon_max = map_df["Longitude"].min(), map_df["Longitude"].max()
            view_lat = (lat_min + lat_max) / 2
            view_lon = (lon_min + lon_max) / 2
            # Estimate zoom from bounding box span (larger span = lower zoom)
            lat_span = max(lat_max - lat_min, 0.01)
            lon_span = max(lon_max - lon_min, 0.01)
            span = max(lat_span, lon_span)
            view_zoom = max(4.0, min(10.0, 7.0 - math.log2(span + 0.1)))
        else:
            view_lat = 39.8283
            view_lon = -98.5795
            view_zoom = 4.0

        # ── Dynamic zoom-aware scaling map ────────────────────────────────
        # Uses a custom deck.gl embed to implement inverse zoom scaling:
        #   - Markers grow when zooming out (overview visibility)
        #   - Markers shrink when zooming in (location precision)
        #   - Smooth exponential interpolation, clamped to min/max bounds
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <script src="https://unpkg.com/deck.gl@8.9.35/dist.min.js"></script>
            <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
            <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; }}
                #map {{ width: 100%; height: 100vh; position: relative; }}
                #tooltip {{
                    position: absolute; z-index: 10; pointer-events: none;
                    background: #F8FAFC; color: #1A1F2E; font-size: 13px;
                    padding: 10px 14px; border-radius: 10px;
                    display: none; max-width: 280px;
                    border: 1px solid #D8E0DB;
                    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
                    font-family: Inter, sans-serif;
                }}
                #legend {{
                    position: absolute; bottom: 24px; left: 16px; z-index: 10;
                    background: rgba(255,255,255,0.92); border-radius: 8px;
                    padding: 10px 14px; font-size: 12px; color: #1a1f36;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                    line-height: 1.7; font-family: Inter, sans-serif;
                }}
                #legend b {{ font-size: 13px; }}
                .legend-item {{ display: flex; align-items: center; gap: 8px; }}
                .legend-dot {{
                    width: 12px; height: 12px; border-radius: 3px;
                    display: inline-block; flex-shrink: 0;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <div id="tooltip"></div>
            <div id="legend">
                <b>Risk Level</b>
                <div class="legend-item"><span class="legend-dot" style="background:#e74c3c"></span> Critical (Past EoL)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f0a830"></span> High (Near EoL)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#3498db"></span> Medium (Approaching EoL)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#27ae60"></span> Low (Healthy)</div>
            </div>
            <script>
            const COLUMN_DATA = {column_data_json};

            // ── Zoom-aware scaling parameters ────────────────────────────
            const SCALE_CONFIG = {{
                referenceZoom: 6.0,   // midpoint zoom where scale = 1.0
                sensitivity: 0.55,    // how aggressively size responds to zoom
                minScale: 0.12,       // floor: prevents invisibly small markers
                maxScale: 4.0,        // ceiling: prevents oversized markers
                smoothingFactor: 0.3  // lerp factor for smooth transitions
            }};

            // Column base radius (in meters)
            const COLUMN_BASE_RADIUS = 8000;

            // Initialize scale to match the computed value at initial zoom
            let currentColumnScale = computeZoomScale({view_zoom});

            /**
             * Compute inverse zoom scale factor.
             * As zoom increases (zooming in), scale DECREASES → smaller markers.
             * As zoom decreases (zooming out), scale INCREASES → larger markers.
             * Uses exponential curve for smooth non-linear response.
             */
            function computeZoomScale(zoom) {{
                const raw = Math.pow(2, (SCALE_CONFIG.referenceZoom - zoom) * SCALE_CONFIG.sensitivity);
                return Math.max(SCALE_CONFIG.minScale, Math.min(SCALE_CONFIG.maxScale, raw));
            }}

            /** Smooth linear interpolation to prevent jitter during rapid zoom. */
            function lerp(current, target, factor) {{
                return current + (target - current) * factor;
            }}

            // Column layer: aggregated by location, colored by worst risk
            const columnLayer = new deck.ColumnLayer({{
                id: "columns",
                data: COLUMN_DATA,
                getPosition: d => [d.Longitude, d.Latitude],
                getElevation: d => d.Total_Replacement_Cost,
                elevationScale: 0.5,
                radius: COLUMN_BASE_RADIUS,
                getFillColor: d => d.color,
                pickable: true,
                autoHighlight: true,
                highlightColor: [255, 200, 200, 100]
            }});

            const tooltipEl = document.getElementById("tooltip");

            // ── Create deck.gl instance ──────────────────────────────────
            const deckgl = new deck.DeckGL({{
                container: "map",
                mapStyle: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initialViewState: {{
                    latitude: {view_lat},
                    longitude: {view_lon},
                    zoom: {view_zoom},
                    pitch: 45,
                    bearing: 10
                }},
                controller: true,
                layers: [columnLayer],

                /**
                 * Core zoom-aware scaling logic.
                 * Fires on every view state change (zoom, pan, tilt).
                 * Computes target scale from zoom, then lerps for smoothness.
                 */
                onViewStateChange: ({{viewState}}) => {{
                    const targetScale = computeZoomScale(viewState.zoom);

                    // Smooth interpolation prevents flickering during rapid scroll
                    currentColumnScale = lerp(currentColumnScale, targetScale, SCALE_CONFIG.smoothingFactor);

                    // Re-render layers with updated scale
                    deckgl.setProps({{
                        layers: [
                            columnLayer.clone({{ radius: COLUMN_BASE_RADIUS * currentColumnScale }})
                        ]
                    }});
                }},

                // ── Tooltip on hover ─────────────────────────────────────
                onHover: ({{object, x, y}}) => {{
                    if (object) {{
                        tooltipEl.style.display = "block";
                        tooltipEl.style.left = x + 12 + "px";
                        tooltipEl.style.top = y + 12 + "px";
                        const count = object.Device_Count || 1;
                        tooltipEl.innerHTML =
                            "<b>" + count + " device" + (count > 1 ? "s" : "") + "</b><br/>" +
                            "Worst Risk: " + (object.Risk_Level || "") + "<br/>" +
                            "Total Cost: $" + Number(object.Total_Replacement_Cost || 0).toLocaleString() + "<br/>" +
                            "Devices: " + (object.Hostnames || "") + "<br/>" +
                            "State: " + (object.State || "");
                    }} else {{
                        tooltipEl.style.display = "none";
                    }}
                }}
            }});
            </script>
        </body>
        </html>
        """
        components.html(map_html, height=550)
        st.download_button(
            label="Download map data (CSV)",
            data=col_agg.to_csv(index=False).encode("utf-8"),
            file_name="geographic_risk_map_data.csv",
            mime="text/csv",
            key="geo_risk_map_data_download",
        )

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

        render_table_with_download(
            site_summary,
            "risk_clustering_priority_sites",
            "geo_risk_priority_sites",
            export_df=site_summary,
            use_container_width=True, hide_index=True,
            column_config={
                "Site_Code": st.column_config.TextColumn("Site Code"),
                "State": st.column_config.TextColumn("State"),
                "High_Risk_Device_Count": st.column_config.NumberColumn("High-Risk Devices"),
                "Total_Replacement_Cost": st.column_config.TextColumn("Total Replacement Cost"),
            },
        )

    section_divider()
    geo_tab, proximity_tab = st.tabs(
        ["🌐 Geographic Risk Views", "📍 Proximity-Based Site Clustering"]
    )

    with proximity_tab:
        st.subheader("Proximity-Based Site Clustering")
        st.caption(
            "Identify nearby sites that can be bundled into a single field deployment. "
            "This directly answers radius-based lifecycle planning (1 / 5 / 10+ miles)."
        )

        ctrl_left, ctrl_right = st.columns([1, 2])
        with ctrl_left:
            radius_miles = st.select_slider(
                "Cluster Radius",
                options=[1, 2, 5, 10, 15, 25],
                value=5,
                format_func=lambda x: f"{x} mi",
                help="Maximum distance between sites to form a deployment cluster.",
                key="geo_proximity_radius",
            )
        with ctrl_right:
            risk_filter = st.multiselect(
                "Risk Levels to Include",
                options=RISK_ORDER,
                default=["Critical (Past EoL)", "High (Near EoL)", "Medium (Approaching EoL)"],
                help="Only selected risk levels are considered for proximity clustering.",
                key="geo_proximity_risk_filter",
            )

        work_df = df_filtered[df_filtered["Risk_Level"].isin(risk_filter)].copy() if risk_filter else df_filtered.copy()
        work_df = work_df.dropna(subset=["Latitude", "Longitude"])
        us_mask = (
            (work_df["Latitude"] >= 24) & (work_df["Latitude"] <= 50) &
            (work_df["Longitude"] >= -125) & (work_df["Longitude"] <= -66)
        )
        work_df = work_df[us_mask]

        if work_df.empty:
            st.info("No devices match the selected filters for proximity analysis.")
        else:
            site_df = work_df.groupby("Site_Code", as_index=False).agg(
                Latitude=("Latitude", "first"),
                Longitude=("Longitude", "first"),
                State=("State", "first"),
                Device_Count=("Hostname", "size"),
                Total_Cost=("Total_Replacement_Cost", "sum"),
                Risk_Score_Sum=("Risk_Score", "sum"),
                Critical=("Risk_Level", lambda x: (x == "Critical (Past EoL)").sum()),
                High=("Risk_Level", lambda x: (x == "High (Near EoL)").sum()),
            )

            from sklearn.cluster import DBSCAN

            coords = site_df[["Latitude", "Longitude"]].values
            eps_rad = radius_miles / 3958.8
            labels = DBSCAN(eps=eps_rad, min_samples=2, metric="haversine").fit_predict(
                np.radians(coords)
            )
            site_df["Cluster"] = labels

            clustered = site_df[site_df["Cluster"] >= 0].copy()
            n_clusters = int(clustered["Cluster"].nunique()) if not clustered.empty else 0
            n_sites_clustered = len(clustered)
            n_sites_total = len(site_df)
            total_cluster_cost = clustered["Total_Cost"].sum() if not clustered.empty else 0
            avg_per_cluster = round(n_sites_clustered / n_clusters, 1) if n_clusters > 0 else 0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Clusters Found", f"{n_clusters:,}")
            k2.metric("Sites in Clusters", f"{n_sites_clustered:,} / {n_sites_total:,}")
            k3.metric("Clustered Replacement Cost", fmt_currency(total_cluster_cost))
            k4.metric("Avg Sites per Cluster", f"{avg_per_cluster}")

            if n_clusters == 0:
                st.info(
                    "No clusters found at the selected radius. "
                    "Try increasing the radius or including more risk levels."
                )
            else:
                map_data = site_df.copy()
                map_data["Cluster_Label"] = map_data["Cluster"].apply(
                    lambda x: f"Cluster {x + 1}" if x >= 0 else "Unclustered"
                )
                map_data["Marker_Size"] = map_data["Device_Count"].clip(upper=50)

                unique_labels = sorted(
                    [l for l in map_data["Cluster_Label"].unique() if l != "Unclustered"]
                )
                color_map = {"Unclustered": "#C0C0C0"}
                for i, label in enumerate(unique_labels):
                    color_map[label] = CLUSTER_PALETTE[i % len(CLUSTER_PALETTE)]

                center_lat = map_data["Latitude"].mean()
                center_lon = map_data["Longitude"].mean()
                lat_span = map_data["Latitude"].max() - map_data["Latitude"].min()
                lon_span = map_data["Longitude"].max() - map_data["Longitude"].min()
                span = max(lat_span, lon_span, 0.01)
                zoom = max(3.0, min(10.0, 7.0 - math.log2(span + 0.1)))

                fig_map = px.scatter_mapbox(
                    map_data,
                    lat="Latitude",
                    lon="Longitude",
                    color="Cluster_Label",
                    size="Marker_Size",
                    color_discrete_map=color_map,
                    hover_name="Site_Code",
                    hover_data={
                        "State": True,
                        "Device_Count": True,
                        "Total_Cost": ":$,.0f",
                        "Cluster_Label": True,
                        "Marker_Size": False,
                        "Latitude": ":.4f",
                        "Longitude": ":.4f",
                    },
                    zoom=zoom,
                    center={"lat": center_lat, "lon": center_lon},
                    mapbox_style="carto-positron",
                    opacity=0.85,
                )
                fig_map.update_layout(
                    height=520,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif"),
                    legend=dict(
                        title="Cluster",
                        orientation="v",
                        yanchor="top", y=0.98,
                        xanchor="left", x=0.01,
                        bgcolor="rgba(255,255,255,0.92)",
                        bordercolor="#E0E6E3",
                        borderwidth=1,
                    ),
                )
                render_plotly_with_download(
                    fig_map,
                    "geographic_proximity_cluster_map",
                    "geo_risk_proximity_cluster_map",
                    use_container_width=True,
                    config=PLOTLY_CLEAN,
                )

                cluster_summary = (
                    clustered.groupby("Cluster", as_index=False)
                    .agg(
                        Sites=("Site_Code", "count"),
                        States=("State", lambda x: ", ".join(sorted(x.unique()))),
                        Site_Codes=("Site_Code", lambda x: ", ".join(sorted(x))),
                        Total_Devices=("Device_Count", "sum"),
                        Critical_Devices=("Critical", "sum"),
                        High_Risk_Devices=("High", "sum"),
                        Total_Replacement_Cost=("Total_Cost", "sum"),
                        Avg_Risk_Score=("Risk_Score_Sum", "mean"),
                    )
                    .sort_values("Total_Replacement_Cost", ascending=False)
                )
                cluster_summary["Cluster"] = cluster_summary["Cluster"].apply(
                    lambda x: f"Cluster {x + 1}"
                )
                cluster_summary["Avg_Risk_Score"] = cluster_summary["Avg_Risk_Score"].round(1)

                render_table_with_download(
                    cluster_summary,
                    "geographic_proximity_cluster_details",
                    "geo_risk_proximity_cluster_details",
                    export_df=cluster_summary,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Cluster": st.column_config.TextColumn("Cluster"),
                        "Sites": st.column_config.NumberColumn("Sites"),
                        "States": st.column_config.TextColumn("States"),
                        "Site_Codes": st.column_config.TextColumn("Site Codes"),
                        "Total_Devices": st.column_config.NumberColumn("Total Devices"),
                        "Critical_Devices": st.column_config.NumberColumn("Critical"),
                        "High_Risk_Devices": st.column_config.NumberColumn("High Risk"),
                        "Total_Replacement_Cost": st.column_config.NumberColumn(
                            "Replacement Cost", format="$ %.0f"
                        ),
                        "Avg_Risk_Score": st.column_config.NumberColumn(
                            "Avg Risk Score", format="%.1f"
                        ),
                    },
                )

                top = cluster_summary.iloc[0]
                st.markdown(
                    f"<div style='background:#d4edda; border:1px solid #b7dfb9; border-radius:8px; "
                    f"padding:14px 18px; font-family:Inter,sans-serif; font-size:15px; "
                    f"color:#1a1f36; line-height:1.6;'>"
                    f"<b>Top Priority:</b> <b>{top['Cluster']}</b> — "
                    f"{int(top['Sites'])} sites across {top['States']} "
                    f"with {int(top['Total_Devices'])} devices "
                    f"({int(top['Critical_Devices'])} critical, "
                    f"{int(top['High_Risk_Devices'])} high-risk). "
                    f"Bundled replacement cost: <b>{fmt_currency(top['Total_Replacement_Cost'])}</b>.</div>",
                    unsafe_allow_html=True,
                )

    with geo_tab:
        st.subheader("County-Level Risk Distribution")
        st.caption("Device risk aggregated by county for granular regional planning.")

        if "PhysicalAddressCounty" in df_filtered.columns:
            county_data = df_filtered.dropna(subset=["PhysicalAddressCounty"]).copy()
            if county_data.empty:
                st.info("No county data available for the current selection.")
            else:
                county_agg = (
                    county_data.groupby(
                        ["PhysicalAddressCounty", "State"], as_index=False
                    )
                    .agg(
                        Total_Devices=("Hostname", "size"),
                        High_Risk_Devices=(
                            "Risk_Level",
                            lambda x: x.isin(
                                ["Critical (Past EoL)", "High (Near EoL)"]
                            ).sum(),
                        ),
                        Total_Replacement_Cost=("Total_Replacement_Cost", "sum"),
                    )
                    .sort_values("Total_Replacement_Cost", ascending=False)
                )

                left_c, right_c = st.columns(2)

                with left_c:
                    top_counties = county_agg.head(15).sort_values(
                        "Total_Replacement_Cost", ascending=True
                    )
                    fig_county = px.bar(
                        top_counties,
                        x="Total_Replacement_Cost",
                        y="PhysicalAddressCounty",
                        orientation="h",
                        text="Total_Devices",
                        color_discrete_sequence=[COLORS["coral"]],
                        labels={
                            "Total_Replacement_Cost": "Total Replacement Cost",
                            "PhysicalAddressCounty": "County",
                        },
                    )
                    fig_county.update_traces(
                        texttemplate="%{text} devices",
                        textposition="outside",
                        textfont_size=12,
                        marker_line_width=0,
                    )
                    fig_county.update_layout(PLOTLY_LAYOUT)
                    fig_county.update_layout(
                        showlegend=False,
                        xaxis_title="Total Replacement Cost ($)",
                        yaxis_title=None,
                        height=max(360, len(top_counties) * 30 + 100),
                        hoverlabel=dict(
                            bgcolor="#FFFFFF",
                            font_color="#1A1F2E",
                            font_size=13,
                            font_family="Inter, sans-serif",
                            bordercolor="#E0E6E3",
                        ),
                    )
                    fig_county.update_xaxes(
                        tickprefix="$", separatethousands=True
                    )
                    render_plotly_with_download(
                        fig_county,
                        "county_level_replacement_cost_distribution",
                        "geo_risk_county_replacement_distribution",
                        use_container_width=True,
                        config=PLOTLY_CLEAN,
                    )

                with right_c:
                    county_table = county_agg.head(25)
                    render_table_with_download(
                        county_table,
                        "county_level_risk_distribution_table",
                        "geo_risk_county_distribution_table",
                        export_df=county_table,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "PhysicalAddressCounty": st.column_config.TextColumn(
                                "County"
                            ),
                            "State": st.column_config.TextColumn("State"),
                            "Total_Devices": st.column_config.NumberColumn(
                                "Devices"
                            ),
                            "High_Risk_Devices": st.column_config.NumberColumn(
                                "High-Risk"
                            ),
                            "Total_Replacement_Cost": st.column_config.NumberColumn(
                                "Replacement Cost", format="$ %.0f"
                            ),
                        },
                    )
        else:
            st.info("County data column not found in dataset.")
