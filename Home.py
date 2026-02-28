import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset", "dashboard_master_data.csv")
home_df = load_data(DATA_PATH)

main = render_dashboard_chatbot(page_title="Dashboard Home", df=home_df)

with main:
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 600;
            color: #1E3A8A;
        }
        h1, h2, h3 {
            color: #0F172A;
            font-weight: 700;
        }
        div[data-testid="stVerticalBlock"] > div {
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Enterprise Fleet Analytics")
    st.markdown("""
---
### Welcome to the Executive Dashboard
This platform provides strategic insights into fleet lifecycle status, risk exposure, consolidation opportunities, and cost optimizations.

**Navigate using the sidebar to explore:**
- **Overview:** High-level executive KPIs
- **Risk & Geography:** Geographic exposure and EoL tracking
- **Lifecycle & Asset Health:** Aging infrastructure and overdue assets
- **Exceptions:** In-production lifecycle overrides
- **Cost & Security:** Financial impact and security posture
""")
