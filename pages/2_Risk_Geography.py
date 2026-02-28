import streamlit as st

st.set_page_config(page_title="Risk & Geography", page_icon="🌎", layout="wide")

st.title("Geographic Risk Exposure")
st.markdown("---")

tab1, tab2 = st.tabs(["Regional Map", "Affiliate Breakdown"])

with tab1:
    st.subheader("Risk Distribution by Region")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.selectbox("Select Region", ["All Regions", "North America", "Europe", "Asia-Pacific"])
        st.selectbox("Risk Level", ["Critical", "High", "Medium", "Low"])
        
    with col2:
        st.info("A rich geographic map (e.g., PyDeck or Plotly Mapbox) showing risk heatmaps will be rendered here.")

with tab2:
    st.subheader("Exposure by Affiliate")
    st.info("A bar chart or treemap detailing risk distribution across different business units and affiliates will be rendered here.")
