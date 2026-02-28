import streamlit as st

st.set_page_config(page_title="Support, Security, & Cost", page_icon="💰", layout="wide")

st.title("Financial & Security Posture")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Cost Projections", "Security Risk Matrix", "Prioritization"])

with tab1:
    st.subheader("Lifecycle Replacement Cost")
    col1, col2, col3 = st.columns(3)
    col1.metric("Q1 Projected Impact", "$1.2M")
    col2.metric("Q2 Projected Impact", "$850K")
    col3.metric("Deferred Cost", "$3.4M")
    
    st.info("A financial forecast chart showing CapEx/OpEx impact over time will be rendered here.")

with tab2:
    st.subheader("Security Vulnerability Exposure")
    st.info("A scatter plot mapping devices by Support Coverage vs. Security Risk Level will be rendered here.")

with tab3:
    st.subheader("Action Prioritization")
    st.info("A ranked list of recommended actions based on the intersection of cost, security risk, and lifecycle status will be rendered here.")
