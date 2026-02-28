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

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    A pure function to clean and preprocess the input data.
    """
    # Example cleaning steps
    return df.dropna().copy()
