import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data

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

# Ensure correct types
df["Total_Replacement_Cost"] = pd.to_numeric(
    df["Total_Replacement_Cost"], errors="coerce"
).fillna(0)
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df["Risk_Level"] = df["Risk_Level"].replace("Healthy", "Low (Healthy)")

# ── Consistent colour palette ───────────────────────────────────────────────
RISK_COLOR_MAP = {
    "Critical (Past EoL)": "#e74c3c",
    "High (Near EoL)": "#f39c12",
    "Medium (Approaching EoL)": "#2980b9",
    "Low (Healthy)": "#27ae60",
}
# RGBA versions for PyDeck (0-255 scale)
RISK_RGBA = {
    "Critical (Past EoL)": [231, 76, 60, 200],
    "High (Near EoL)": [243, 156, 18, 200],
    "Medium (Approaching EoL)": [41, 128, 185, 200],
    "Low (Healthy)": [39, 174, 96, 200],
}
RISK_ORDER = list(RISK_COLOR_MAP.keys())
PLOTLY_CLEAN = {"displayModeBar": False}


def fmt_currency(val: float) -> str:
    """Format a dollar value into a compact human-readable string."""
    if val >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE HEADER & FILTERS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='text-align:center; color:#1a1f36; margin-bottom:4px;'>"
    "Geographic Lifecycle Risk Mapping</h1>",
    unsafe_allow_html=True,
)
st.caption(
    "Identify risk hotspots and cluster aging infrastructure for optimized field deployments."
)
st.markdown("---")

# State multi-select filter
all_states = sorted(df["State"].dropna().unique().tolist())
selected_states = st.multiselect(
    "Filter by State",
    options=all_states,
    default=[],
    help="Leave empty to show all states.",
)

# Apply state filter
if selected_states:
    df_filtered = df[df["State"].isin(selected_states)].copy()
else:
    df_filtered = df.copy()

# ═══════════════════════════════════════════════════════════════════════════
#  INTERACTIVE 3-D RISK MAP
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("3-D Risk Map")

# Prepare map data — drop rows with missing coordinates
map_df = df_filtered.dropna(subset=["Latitude", "Longitude"]).copy()

if map_df.empty:
    st.info("No device locations available for the current filter selection.")
else:
    # Assign RGBA colour based on Risk_Level
    map_df["color"] = map_df["Risk_Level"].map(RISK_RGBA)
    map_df["color"] = map_df["color"].apply(
        lambda c: c if isinstance(c, list) else [150, 150, 150, 160]
    )

    # Compute auto view state centred on the filtered data
    view = pdk.data_utils.compute_view(
        map_df[["Longitude", "Latitude"]], view_proportion=0.9
    )
    view.pitch = 45
    view.bearing = 10

    # ScatterplotLayer — individual device locations coloured by risk
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["Longitude", "Latitude"],
        get_color="color",
        get_radius=1200,
        pickable=True,
        auto_highlight=True,
    )

    # ColumnLayer — aggregate replacement cost as 3-D towers
    col_layer = pdk.Layer(
        "ColumnLayer",
        data=map_df,
        get_position=["Longitude", "Latitude"],
        get_elevation="Total_Replacement_Cost",
        elevation_scale=0.5,
        radius=4000,
        get_fill_color=[231, 76, 60, 140],
        pickable=True,
        auto_highlight=True,
    )

    tooltip = {
        "html": (
            "<b>{Hostname}</b><br/>"
            "Risk: {Risk_Level}<br/>"
            "Cost: ${Total_Replacement_Cost}<br/>"
            "State: {State}"
        ),
        "style": {
            "backgroundColor": "#1a1f36",
            "color": "#ffffff",
            "fontSize": "13px",
            "padding": "8px 12px",
            "borderRadius": "6px",
        },
    }

    deck = pdk.Deck(
        layers=[col_layer, scatter_layer],
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True)



# ═══════════════════════════════════════════════════════════════════════════
#  RISK CLUSTERING INSIGHT TABLE
# ═══════════════════════════════════════════════════════════════════════════
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

    # Format cost as currency for display
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
