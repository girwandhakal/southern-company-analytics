import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import pydeck as pdk
import json
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Risk & Geography", page_icon="🌎", layout="wide")

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

# ── Data loading ────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv"
)
df = load_data(DATA_PATH)

df["Total_Replacement_Cost"] = pd.to_numeric(
    df["Total_Replacement_Cost"], errors="coerce"
).fillna(0)
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

main = render_dashboard_chatbot(page_title="Risk & Geography", df=df)

# ── Consistent colour palette ───────────────────────────────────────────────
RISK_COLOR_MAP = {
    "Critical (Past EoL)": "#e74c3c",
    "High (Near EoL)": "#f39c12",
    "Medium (Approaching EoL)": "#2980b9",
    "Low (Healthy)": "#27ae60",
}
RISK_RGBA = {
    "Critical (Past EoL)": [231, 76, 60, 200],
    "High (Near EoL)": [243, 156, 18, 200],
    "Medium (Approaching EoL)": [41, 128, 185, 200],
    "Low (Healthy)": [39, 174, 96, 200],
}
RISK_ORDER = list(RISK_COLOR_MAP.keys())
# Severity ranking: lower index = higher severity (used for aggregation)
RISK_SEVERITY = {level: i for i, level in enumerate(RISK_ORDER)}
PLOTLY_CLEAN = {"displayModeBar": False}


def fmt_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"


with main:
    # ═══════════════════════════════════════════════════════════════════════
    #  PAGE HEADER & FILTERS
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        "<h1 style='text-align:center; color:#1a1f36; margin-bottom:4px;'>"
        "Geographic Lifecycle Risk Mapping</h1>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Identify risk hotspots and cluster aging infrastructure for optimized field deployments."
    )
    st.markdown("---")

    all_states = sorted(df["State"].dropna().unique().tolist())
    selected_states = st.multiselect(
        "Filter by State",
        options=all_states,
        default=[],
        help="Leave empty to show all states.",
    )

    if selected_states:
        df_filtered = df[df["State"].isin(selected_states)].copy()
    else:
        df_filtered = df.copy()

    # ═══════════════════════════════════════════════════════════════════════
    #  INTERACTIVE 3-D RISK MAP
    # ═══════════════════════════════════════════════════════════════════════
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
                    background: #1a1f36; color: #fff; font-size: 13px;
                    padding: 8px 12px; border-radius: 6px;
                    display: none; max-width: 280px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                }}
                #legend {{
                    position: absolute; bottom: 24px; left: 16px; z-index: 10;
                    background: rgba(255,255,255,0.92); border-radius: 8px;
                    padding: 10px 14px; font-size: 12px; color: #1a1f36;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                    line-height: 1.7;
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
                <div class="legend-item"><span class="legend-dot" style="background:#f39c12"></span> High (Near EoL)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#2980b9"></span> Medium (Approaching EoL)</div>
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

    # ═══════════════════════════════════════════════════════════════════════
    #  RISK CLUSTERING INSIGHT TABLE
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("Risk Clustering — Priority Sites for Field Deployment")
    st.caption(
        "Sites ranked by total replacement cost of Critical and High-risk devices. "
        "Send technicians to the top rows first."
    )

    cluster_mask = df_filtered["Risk_Level"].isin(
        ["Critical (Past EoL)", "High (Near EoL)"]
    )
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
            site_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Site_Code": st.column_config.TextColumn("Site Code"),
                "State": st.column_config.TextColumn("State"),
                "High_Risk_Device_Count": st.column_config.NumberColumn(
                    "High-Risk Devices"
                ),
                "Total_Replacement_Cost": st.column_config.TextColumn(
                    "Total Replacement Cost"
                ),
            },
        )
