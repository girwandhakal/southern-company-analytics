import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_data
from src.dashboard_chatbot import render_dashboard_chatbot

st.set_page_config(page_title="Exceptions & In-Production", page_icon="⚠️", layout="wide")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dashboard_master_data.csv")
df = load_data(DATA_PATH)

main = render_dashboard_chatbot(page_title="Exceptions & In-Production", df=df)

with main:
    st.title("Production Exceptions Management")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Active Exceptions", "Log New Exception"])

    with tab1:
        st.subheader("Devices Past Lifecycle in Production")
        col1, col2 = st.columns(2)
        col1.metric("Total Active Exceptions", "142", "Requires Review: 12")
        col2.metric("Critical Overrides", "8", "Immediate Action")

        st.info("A high-level summary view or chart of current exceptions categorized by reason and risk will be rendered here.")

    with tab2:
        st.subheader("Capture Exception")
        with st.form("exception_form"):
            st.text_input("Device / Site ID", placeholder="Enter ID...")
            st.selectbox("Override Reason", ["Pending Hardware Delivery", "Budget Constraints", "Business Critical Hold", "Other"])
            st.text_area("Justification Notes", placeholder="Provide business context...")

            col1, col2 = st.columns([1, 4])
            with col1:
                st.form_submit_button("Submit Exception", type="primary")
