import streamlit as st

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

# Inject custom CSS for executive styling
st.markdown("""
    <style>
    /* Clean up the main content area */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Make metrics look more premium */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E3A8A; /* Dark blue */
    }
    
    /* Style headers */
    h1, h2, h3 {
        color: #0F172A; /* Slate 900 */
        font-weight: 700;
    }
    
    /* Subtle borders for containers */
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
- **Radius Bundling:** Strategic site consolidation
- **Exceptions:** In-production lifecycle overrides
- **Cost & Security:** Financial impact and security posture
""")
