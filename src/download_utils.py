import re
from typing import Any, Optional

import pandas as pd
import streamlit as st


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
    return cleaned.strip("_") or "download"


def render_plotly_with_download(
    fig: Any,
    title: str,
    key_prefix: str,
    *,
    use_container_width: bool = True,
    config: Optional[dict] = None,
) -> None:
    """Render Plotly chart without download controls."""
    _ = title, key_prefix
    # Enforce a consistent, readable tooltip style across all charts.
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="#F8FAFC",
            bordercolor="#D8E0DB",
            font=dict(
                color="#1A1F2E",
                family="Inter, sans-serif",
                size=12,
            ),
            namelength=-1,
        )
    )
    st.plotly_chart(fig, use_container_width=use_container_width, config=config)


def render_table_with_download(
    data: Any,
    title: str,
    key_prefix: str,
    *,
    export_df: Optional[pd.DataFrame] = None,
    **dataframe_kwargs: Any,
) -> None:
    """Render table with a direct CSV download button."""
    st.dataframe(data, **dataframe_kwargs)

    if export_df is not None:
        to_export = export_df.copy()
    elif isinstance(data, pd.DataFrame):
        to_export = data.copy()
    elif isinstance(data, pd.Series):
        to_export = data.to_frame()
    elif hasattr(data, "data") and isinstance(data.data, pd.DataFrame):
        to_export = data.data.copy()
    else:
        to_export = pd.DataFrame(data)

    csv_bytes = to_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download table (CSV)",
        data=csv_bytes,
        file_name=f"{_safe_name(title)}.csv",
        mime="text/csv",
        key=f"{key_prefix}_table_download",
    )
