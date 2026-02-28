import streamlit as st

st.set_page_config(page_title="Overview", page_icon="📈", layout="wide")

st.title("Executive Overview")
st.markdown("---")

# Tabbed layout for easy expansion
tab1, tab2, tab3 = st.tabs(["Fleet Health", "Lifecycle Status", "Recent Alerts"])

with tab1:
    st.subheader("Global Fleet Health")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Active Sites", "1,245", "+12 this month")
    col2.metric("Total Devices Managed", "45,892", "+890 this month")
    col3.metric("Overall Compliance", "94.2%", "↑ 1.4%")
    col4.metric("Critical Incidents", "3", "↓ 2 from last week")
    
    st.info("Interactive global health map and trend charts will be rendered here.")

with tab2:
    st.subheader("Lifecycle Posture")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Managed", "85%")
    col2.metric("Approaching EoL/EoS", "10%")
    col3.metric("Past EoL/EoS", "5%")
    
    st.info("Detailed breakdown by vendor and lifecycle stage will be rendered here.")

with tab3:
    st.subheader("System Alerts")
    st.warning("3 Sites require immediate attention due to expired hardware.")
    st.success("All primary data centers are currently fully compliant.")
