import os
import pandas as pd
import streamlit as st
from typing import Optional

@st.cache_data
def load_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads data from a parquet or csv file, utilizing caching for performance.
    
    Args:
        file_path (str, optional): The path to the dataset.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    if file_path is None:
        file_path = os.getenv("DATA_PATH", "dataset/sample_data.parquet")

    # For scaffolding, return an empty placeholder if the file doesn't exist
    if not os.path.exists(file_path):
        st.warning(f"Data file not found at {file_path}. Using placeholder data.")
        return get_placeholder_data()

    if file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    elif file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please use .csv or .parquet")

def get_placeholder_data() -> pd.DataFrame:
    """
    Returns a simple placeholder dataframe for scaffolding purposes.
    """
    data = {
        "site_id": [1, 2, 3],
        "state": ["AL", "GA", "MS"],
        "lifecycle_status": ["Active", "EoL", "EoS"],
        "cost": [1000, 2000, 1500]
    }
    return pd.DataFrame(data)

def apply_global_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renders sidebar multiselect filters for State and Device Type,
    then returns a filtered copy of the dataframe.
    Empty selections mean 'show all'.
    """
    st.sidebar.markdown(
        "<h3 style='margin-bottom: 4px;'>⚙️ Global Controls</h3>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<p style='font-size: 0.72rem; color: #64748B !important; "
        "font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; "
        "margin-bottom: 12px;'>Filter across all pages</p>",
        unsafe_allow_html=True,
    )

    if "State" in df.columns:
        all_states = sorted(df["State"].dropna().unique().tolist())
        selected_states = st.sidebar.multiselect(
            "State",
            options=all_states,
            default=[],
            help="Leave empty to show all states.",
        )
    else:
        selected_states = []

    if "Device Type" in df.columns:
        all_device_types = sorted(df["Device Type"].dropna().unique().tolist())
        selected_device_types = st.sidebar.multiselect(
            "Device Type",
            options=all_device_types,
            default=[],
            help="Leave empty to show all device types.",
        )
    else:
        selected_device_types = []

    filtered_df = df.copy()

    if selected_states:
        filtered_df = filtered_df[filtered_df["State"].isin(selected_states)]

    if selected_device_types:
        filtered_df = filtered_df[filtered_df["Device Type"].isin(selected_device_types)]

    return filtered_df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    A pure function to clean and preprocess the input data.
    """
    # Example cleaning steps
    return df.dropna().copy()
