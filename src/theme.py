import streamlit as st

# ── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#EDF2EE",
    "card": "#FFFFFF",
    "sidebar_bg": "#1A1F2E",
    "sidebar_text": "#CBD5E1",
    "sidebar_heading": "#F1F5F9",
    "sidebar_hover": "#FFFFFF",
    "dark": "#1A1F2E",
    "text": "#1A1F2E",
    "muted": "#6B7B8D",
    "border": "#D8E0DB",
    "coral": "#E8734A",
    "emerald": "#27AE60",
    "sky": "#3498DB",
    "gold": "#F0A830",
    "crimson": "#E74C3C",
    "purple": "#8E44AD",
}

RISK_COLOR_MAP = {
    "Low (Healthy)": COLORS["emerald"],
    "Medium (Approaching EoL)": COLORS["sky"],
    "High (Near EoL)": COLORS["gold"],
    "Critical (Past EoL)": COLORS["crimson"],
}
RISK_ORDER = list(RISK_COLOR_MAP.keys())

RISK_COLOR_MAP_SHORT = {
    "Low": COLORS["emerald"],
    "Medium": COLORS["sky"],
    "High": COLORS["gold"],
    "Critical": COLORS["crimson"],
}

ACCENT_SEQUENCE = [
    COLORS["coral"], COLORS["emerald"], COLORS["sky"],
    COLORS["gold"], COLORS["purple"], COLORS["crimson"],
]

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=COLORS["dark"], size=13),
    margin=dict(l=20, r=20, t=30, b=40),
    height=400,
    xaxis=dict(
        title_font=dict(size=14, color=COLORS["dark"]),
        tickfont=dict(size=12, color=COLORS["dark"]),
        gridcolor="#D8E0DB",
    ),
    yaxis=dict(
        title_font=dict(size=14, color=COLORS["dark"]),
        tickfont=dict(size=12, color=COLORS["dark"]),
        gridcolor="#D8E0DB",
    )
)

PLOTLY_CLEAN = {"displayModeBar": False}


def inject_theme_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ── Global Background ────────────────────────── */
    .stApp {
        background: linear-gradient(160deg, #EDF2EE 0%, #E3EBE5 40%, #E8EDE9 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1A1F2E !important;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .block-container p,
    .block-container span,
    .block-container label,
    .block-container li,
    .block-container div {
        color: #1A1F2E;
    }

    /* ── Sidebar ────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1F2E 0%, #141824 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {
        gap: 0.02rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        min-height: 1.7rem !important;
        padding: 0.2rem 0.45rem !important;
        font-size: 1.03rem !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a * {
        font-size: inherit !important;
        font-weight: inherit !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 0.05rem !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect,
    section[data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.22rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.32rem 0 !important;
        border-top: 1px solid rgba(255,255,255,0.1) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        margin: 0.15rem 0 0.1rem 0 !important;
        font-size: 0.9rem !important;
        line-height: 1.15 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin: 0.08rem 0 0.22rem 0 !important;
        line-height: 1.1 !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stSelectbox label {
        margin-bottom: 0.1rem !important;
        font-size: 0.6rem !important;
        letter-spacing: 0.6px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        font-size: 0.92rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        min-height: 2rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        margin-bottom: 0.12rem !important;
    }
    /* Extra compact mode for shorter displays */
    @media (max-height: 900px) {
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div {
            zoom: 0.92;
        }
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] div {
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #F1F5F9 !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] a {
        color: #94A3B8 !important;
        transition: all 0.25s ease !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] a:hover,
    section[data-testid="stSidebar"] a[aria-selected="true"] {
        color: #FFFFFF !important;
        background: rgba(232, 115, 74, 0.15) !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #94A3B8 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 0.7rem !important;
        letter-spacing: 0.8px !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect > div > div,
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
    }
    /* Sidebar multiselect tags */
    section[data-testid="stSidebar"] [data-baseweb="tag"] {
        background: rgba(232, 115, 74, 0.25) !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    /* Sidebar Dropdown List */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="popover"] [role="option"] span,
    div[data-baseweb="popover"] [role="option"] div,
    [data-testid="stVirtualDropdown"],
    [data-testid="stVirtualDropdown"] ul,
    [data-testid="stVirtualDropdown"] li,
    [data-testid="stVirtualDropdown"] li span {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
    }
    
    div[data-baseweb="popover"] li:hover,
    [data-testid="stVirtualDropdown"] li:hover,
    div[data-baseweb="popover"] [role="option"]:hover,
    [data-testid="stVirtualDropdown"] [role="option"]:hover {
        background-color: rgba(232, 115, 74, 0.15) !important;
        background: rgba(232, 115, 74, 0.15) !important;
    }
    /* Sidebar input text */
    section[data-testid="stSidebar"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Force background to white for Streamlit multi-select dropdown popups */
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] ul li {
        background-color: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] ul li {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] ul li span {
        color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] ul li:hover,
    div[data-baseweb="popover"] ul li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        background: rgba(232, 115, 74, 0.1) !important;
        color: #1A1F2E !important;
    }

    /* ── Typography ─────────────────────────────────── */
    h1 {
        color: #1A1F2E !important;
        font-weight: 900 !important;
        font-size: 2.1rem !important;
        letter-spacing: -0.5px;
    }
    h2 {
        color: #1A1F2E !important;
        font-weight: 800 !important;
        font-size: 1.4rem !important;
    }
    h3 {
        color: #1A1F2E !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
    }

    /* ── Metric Cards ──────────────────────────────── */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: none;
        border-radius: 16px;
        padding: 22px 24px 18px 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04);
        transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                    box-shadow 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        animation: fadeInUp 0.5s ease-out both;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        color: #6B7B8D !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        color: #1A1F2E !important;
        line-height: 1.15 !important;
        letter-spacing: -1px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    /* ── Staggered metric animation delays ─────────── */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"] { animation-delay: 0.05s; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] { animation-delay: 0.1s; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] { animation-delay: 0.15s; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"] { animation-delay: 0.2s; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stMetric"] { animation-delay: 0.25s; }

    /* ── Chart Containers ──────────────────────────── */
    .stPlotlyChart {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeInUp 0.6s ease-out 0.15s both;
    }
    .stPlotlyChart:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.09);
    }

    /* ── HR ─────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid #D8E0DB;
        margin: 28px 0 22px 0;
    }

    /* ── Tabs ───────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #FFFFFF;
        border-radius: 14px;
        padding: 5px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 10px 22px !important;
        transition: all 0.25s ease !important;
        color: #6B7B8D !important;
    }
    .stTabs [data-baseweb="tab"] * {
        color: inherit !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1A1F2E !important;
        background: rgba(26, 31, 46, 0.05) !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1A1F2E !important;
        color: #FFFFFF !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #FFFFFF !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ── DataFrames ─────────────────────────────────── */
    [data-testid="stDataFrame"],
    .stDataFrame {
        border-radius: 16px !important;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
        animation: fadeInUp 0.5s ease-out 0.2s both;
    }

    /* ── Buttons ────────────────────────────────────── */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.25s ease !important;
        border: 1px solid #D8E0DB !important;
        background: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        border-color: #E8734A !important;
        color: #E8734A !important;
    }
    .stButton > button p {
        color: inherit !important;
    }
    .stDownloadButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.25s ease !important;
        border: 1px solid #D8E0DB !important;
        background: #F8FAFC !important;
        color: #1A1F2E !important;
    }
    .stDownloadButton > button * {
        color: #1A1F2E !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        border-color: #94A3B8 !important;
        background: #EEF2F7 !important;
        color: #1A1F2E !important;
    }
    .stDownloadButton > button:active,
    .stDownloadButton > button:focus {
        background: #E8EDF4 !important;
        color: #1A1F2E !important;
        border-color: #94A3B8 !important;
        box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2) !important;
    }

    /* ── Slider ─────────────────────────────────────── */
    div[data-testid="stSlider"] {
        padding: 8px 0;
    }
    div[data-testid="stSlider"] > div > div > div {
        background: #D8E0DB !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background: #E8734A !important;
        border-color: #E8734A !important;
    }

    /* ── Multiselect & Selectbox ──────────────────── */
    .stMultiSelect > div > div,
    .stSelectbox > div > div {
        border-radius: 12px !important;
        border-color: #D8E0DB !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    }
    .block-container .stMultiSelect [data-baseweb="select"],
    .block-container .stMultiSelect [data-baseweb="select"] > div,
    .block-container .stMultiSelect [data-baseweb="select"] > div > div,
    .block-container .stMultiSelect div[data-baseweb="input"],
    .block-container .stSelectbox [data-baseweb="select"],
    .block-container .stSelectbox [data-baseweb="select"] > div,
    .block-container .stSelectbox [data-baseweb="select"] > div > div {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    .stMultiSelect > div > div:focus-within,
    .stSelectbox > div > div:focus-within {
        border-color: #E8734A !important;
        box-shadow: 0 0 0 2px rgba(232, 115, 74, 0.15) !important;
    }
    /* Input text inside filters */
    .stMultiSelect input,
    .stSelectbox input,
    .stTextInput input {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    .block-container .stMultiSelect input::placeholder,
    .block-container .stSelectbox input::placeholder {
        color: #6B7B8D !important;
        -webkit-text-fill-color: #6B7B8D !important;
        opacity: 1 !important;
    }
    .stMultiSelect span[data-baseweb="tag"] span,
    .stSelectbox span,
    div[data-baseweb="select"] span {
        color: #1A1F2E;
    }
    
    /* Ensure Streamlit dropdown text is dark */
    div[data-baseweb="select"] ul li,
    div[data-baseweb="select"] ul li span {
        color: #1A1F2E !important;
    }
    
    /* Selected tags in multiselect */
    [data-baseweb="tag"] {
        background: #E8734A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-baseweb="tag"] svg {
        fill: #FFFFFF !important;
    }
    
    /* Ensure dropdown option text is dark */
    ul[data-baseweb="menu"] li {
        color: #1A1F2E !important;
    }
    /* Value texts inside single select */
    [data-baseweb="select"] div,
    [data-baseweb="select"] span {
        color: #1A1F2E;
    }
    
    /* Ensure multiselect tags keep white text */
    .stMultiSelect [data-baseweb="tag"] span,
    .stMultiSelect [data-baseweb="tag"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background: #E8734A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* Global Selectbox text override */
    div[data-baseweb="select"] > div > div > div {
        color: #1A1F2E !important;
    }
    
    /* Multiselect input text */
    .stMultiSelect div[data-baseweb="select"] span[data-baseweb="tag"] ~ span {
        color: #1A1F2E !important;
    }
    
    /* Fix text color in multi-select when a filter is selected */
    .stMultiSelect div[data-baseweb="select"] > div > div > div {
        color: #1A1F2E !important;
    }
    
    /* Ensure the placeholder text is visible */
    .stMultiSelect input::placeholder {
        color: #6B7B8D !important;
    }
    
    /* Make sure the selected text in multiselect is white */
    .stMultiSelect div[data-baseweb="select"] span[title] {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* Ensure the input text color inside the selected tag is white */
    .stMultiSelect div[data-baseweb="select"] [data-baseweb="tag"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stMultiSelect div[data-baseweb="select"] [data-baseweb="tag"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stMultiSelect div[data-baseweb="select"] [data-baseweb="tag"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* Fix text color for unselected items in the dropdown */
    ul[data-baseweb="menu"] li {
        color: #1A1F2E !important;
    }
    
    /* Fix text color for the input field itself */
    .stMultiSelect input {
        color: #1A1F2E !important;
    }
    
    /* Fix plotly chart text colors */
    text.annotation-text {
        fill: #1A1F2E !important;
    }
    
    g.text > text {
        fill: #1A1F2E !important;
        text-shadow: none !important;
    }
    
    .stPlotlyChart text {
        fill: #1A1F2E !important;
    }
    /* Dropdown menus */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    ul[role="listbox"],
    [data-testid="stVirtualDropdown"],
    ul[data-testid="stVirtualDropdown"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] li span,
    div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="popover"] [role="option"] span,
    [data-testid="stVirtualDropdown"] li,
    [data-testid="stVirtualDropdown"] li span {
        background-color: transparent !important;
        background: transparent !important;
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
    }
    
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] [role="option"]:hover,
    div[data-baseweb="popover"] [role="option"][aria-selected="true"],
    [data-testid="stVirtualDropdown"] li:hover,
    [data-testid="stVirtualDropdown"] li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.15) !important;
        background: rgba(232, 115, 74, 0.15) !important;
    }
    
    /* Dropdown options color explicitly for dark themes */
    div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="popover"] [role="option"] span,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] li span,
    .stSelectbox [role="listbox"] li,
    .stSelectbox [role="listbox"] li span,
    .stMultiSelect [role="listbox"] li,
    .stMultiSelect [role="listbox"] li span,
    ul[data-testid="stVirtualDropdown"] li,
    ul[data-testid="stVirtualDropdown"] li span {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
    }
    
    ul[data-testid="stVirtualDropdown"] li:hover,
    ul[data-testid="stVirtualDropdown"] li:focus,
    ul[data-testid="stVirtualDropdown"] li:active {
        background-color: rgba(232, 115, 74, 0.15) !important;
    }
    
    .stSelectbox [role="listbox"],
    .stMultiSelect [role="listbox"],
    .stSelectbox [role="listbox"] li,
    .stMultiSelect [role="listbox"] li {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    
    .stSelectbox [role="listbox"] li:hover,
    .stMultiSelect [role="listbox"] li:hover,
    .stSelectbox [role="listbox"] li[aria-selected="true"],
    .stMultiSelect [role="listbox"] li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        background: rgba(232, 115, 74, 0.1) !important;
    }
    
    /* Fix Virtual Dropdown Text specifically used by Streamlit */
    div[data-testid="stVirtualDropdown"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    div[data-testid="stVirtualDropdown"] ul {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    div[data-testid="stVirtualDropdown"] li {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    div[data-testid="stVirtualDropdown"] li span {
        color: #1A1F2E !important;
    }
    div[data-testid="stVirtualDropdown"] li:hover,
    div[data-testid="stVirtualDropdown"] li:focus,
    div[data-testid="stVirtualDropdown"] li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.15) !important;
        background: rgba(232, 115, 74, 0.15) !important;
        color: #1A1F2E !important;
    }
    
    /* Fix for Virtual Dropdown text content */
    div[data-testid="stVirtualDropdown"] *,
    div[data-baseweb="popover"] * {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    div[data-testid="stVirtualDropdown"] li {
        background-color: #FFFFFF !important;
    }
    div[data-testid="stVirtualDropdown"] li:hover {
        background-color: rgba(232, 115, 74, 0.15) !important;
    }
    
    /* Global Sidebar specific dropdown override */
    section[data-testid="stSidebar"] [data-baseweb="popover"] > div,
    section[data-testid="stSidebar"] [data-baseweb="popover"] > div > div,
    section[data-testid="stSidebar"] [data-baseweb="popover"],
    section[data-testid="stSidebar"] ul[role="listbox"],
    div[data-baseweb="popover"] ul[role="listbox"],
    section[data-testid="stSidebar"] div[data-testid="stVirtualDropdown"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    
    div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="popover"] [role="option"] span,
    div[data-baseweb="popover"] [role="option"] div,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] li span,
    div[data-baseweb="popover"] li div,
    div[role="listbox"] *,
    div[data-baseweb="menu"] *,
    div[data-baseweb="popover"] * {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] [role="option"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    
    div[data-baseweb="popover"] [role="option"]:hover,
    div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        color: #1A1F2E !important;
    }
    
    section[data-testid="stSidebar"] [role="option"] {
        color: #1A1F2E !important;
    }
    
    /* Text color for dropdown items */
    [data-baseweb="popover"] *,
    [data-baseweb="menu"] *,
    ul[role="listbox"] *,
    [role="option"],
    [role="option"] span,
    li[role="option"],
    li[role="option"] span,
    div[data-baseweb="select"] div {
        color: #1A1F2E !important;
    }
    
    [role="option"] {
        background-color: transparent !important;
        color: #1A1F2E !important;
    }
    
    [role="option"]:hover,
    [role="option"][aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        background: rgba(232, 115, 74, 0.1) !important;
        color: #1A1F2E !important;
    }
    /* Sidebar overrides for dark text inside filters */
    section[data-testid="stSidebar"] [data-baseweb="select"] div,
    section[data-testid="stSidebar"] [data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div > div > div,
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] span[data-baseweb="tag"] ~ span,
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div > div > div {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="tag"] span,
    section[data-testid="stSidebar"] [data-baseweb="tag"] div,
    section[data-testid="stSidebar"] [data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* VERY STRONG dropdown text override */
    ul[role="listbox"] li,
    ul[role="listbox"] li span,
    ul[role="listbox"] li div,
    [data-testid="stVirtualDropdown"] li,
    [data-testid="stVirtualDropdown"] li span,
    [data-testid="stVirtualDropdown"] li div,
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] li span {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    
    /* Global Control Options text colors */
    [data-testid="stVirtualDropdown"] li,
    ul[data-testid="stVirtualDropdown"] li,
    [data-testid="stVirtualDropdown"] li *,
    ul[data-testid="stVirtualDropdown"] li * {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
        background-color: transparent !important;
    }
    
    [data-testid="stVirtualDropdown"] li,
    ul[data-testid="stVirtualDropdown"] li {
        background-color: #FFFFFF !important;
    }
    [data-testid="stVirtualDropdown"] li span,
    ul[data-testid="stVirtualDropdown"] li span {
        color: #1A1F2E !important;
    }
    [data-testid="stVirtualDropdown"] li:hover,
    [data-testid="stVirtualDropdown"] li[aria-selected="true"],
    ul[data-testid="stVirtualDropdown"] li:hover,
    ul[data-testid="stVirtualDropdown"] li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        color: #1A1F2E !important;
    }
    
    /* Ensure text in data-testid virtual dropdown is correct */
    [data-testid="stVirtualDropdown"] li {
        background-color: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    
    [data-testid="stVirtualDropdown"] li:hover,
    [data-testid="stVirtualDropdown"] li:focus,
    [data-testid="stVirtualDropdown"] li:active,
    [data-testid="stVirtualDropdown"] li[aria-selected="true"] {
        background-color: rgba(232, 115, 74, 0.1) !important;
        color: #1A1F2E !important;
    }
    
    [data-testid="stVirtualDropdown"] li span {
        color: #1A1F2E !important;
    }
    
    /* Extremely specific override for the Virtual Dropdown lists */
    [data-testid="stVirtualDropdown"] [role="listbox"] li,
    [data-testid="stVirtualDropdown"] [role="listbox"] li span {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
        opacity: 1 !important;
    }
    
    /* Force white text in the sidebar multi-select input box */
    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* Make SURE Streamlit multi-select popovers always have a white background */
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div,
    [data-baseweb="popover"] ul,
    [data-baseweb="popover"] li,
    [data-testid="stVirtualDropdown"],
    [data-testid="stVirtualDropdown"] ul,
    [data-testid="stVirtualDropdown"] li {
        background-color: #FFFFFF !important;
        color: #1A1F2E !important;
    }
    
    [data-baseweb="popover"] li:hover,
    [data-testid="stVirtualDropdown"] li:hover {
        background-color: rgba(232, 115, 74, 0.15) !important;
    }
    
    [data-baseweb="popover"] li *,
    [data-testid="stVirtualDropdown"] li * {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] li *,
    ul[data-testid="stVirtualDropdown"] li *,
    ul[role="listbox"] li *,
    div[role="listbox"] * {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    
    div[data-baseweb="popover"] li:hover {
        background: rgba(232, 115, 74, 0.15) !important;
        background-color: rgba(232, 115, 74, 0.15) !important;
    }
    
    /* Robust fix for sidebar placeholder and input text */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] .stMultiSelect input,
    section[data-testid="stSidebar"] .stSelectbox input,
    section[data-testid="stSidebar"] .stTextInput input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    
    /* Ensure the search text inside the dropdown is dark so you can see what you type */
    div[data-baseweb="popover"] input {
        color: #1A1F2E !important;
        -webkit-text-fill-color: #1A1F2E !important;
    }
    
    /* Make the entire select list white to show dark text properly */
    div[role="listbox"],
    ul[role="listbox"],
    div[data-baseweb="menu"],
    div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] input::placeholder,
    section[data-testid="stSidebar"] .stMultiSelect input::placeholder,
    section[data-testid="stSidebar"] .stSelectbox input::placeholder,
    section[data-testid="stSidebar"] .stTextInput input::placeholder {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
        opacity: 1 !important;
    }
    
    /* Placeholder text */
    .stMultiSelect input::placeholder,
    .stSelectbox input::placeholder,
    .stTextInput input::placeholder {
        color: #94A3B8 !important;
    }

    /* ── Caption & small text ──────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6B7B8D !important;
    }
    .stMarkdown p, .stMarkdown span, .stMarkdown li {
        color: #1A1F2E !important;
    }

    /* ── Form submit button ────────────────────────── */
    .stFormSubmitButton > button {
        background: #E8734A !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stFormSubmitButton > button p {
        color: #FFFFFF !important;
    }
    .stFormSubmitButton > button:hover {
        background: #D35400 !important;
        color: #FFFFFF !important;
    }

    /* ── Alert boxes ───────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        font-weight: 500 !important;
    }

    /* ── Expander ───────────────────────────────────── */
    details {
        background: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1px solid #D8E0DB !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
    }
    details summary {
        font-weight: 700 !important;
    }

    /* ── Animations ─────────────────────────────────── */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(24px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .block-container > div {
        animation: fadeIn 0.4s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=None, breadcrumb=None):
    bc_html = ""
    if breadcrumb:
        bc_html = f"""<div style="
            font-size: 0.72rem; font-weight: 700; color: #6B7B8D;
            text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px;
        ">{breadcrumb}</div>"""

    sub_html = ""
    if subtitle:
        sub_html = f"""<p style="
            text-align: center; color: #6B7B8D; font-size: 1rem;
            font-weight: 500; margin-top: 4px; max-width: 600px; margin-left: auto; margin-right: auto;
        ">{subtitle}</p>"""

    st.markdown(f"""
    <div style="text-align: center; padding: 8px 0 20px 0; animation: fadeInUp 0.5s ease-out;">
        {bc_html}
        <h1 style="
            font-size: 2.2rem !important; font-weight: 900 !important;
            color: #1A1F2E !important; margin-bottom: 2px;
            letter-spacing: -0.5px; line-height: 1.2;
        ">{title}</h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def section_divider():
    st.markdown("""<div style="
        border-top: 1px solid #D8E0DB; margin: 28px 0 22px 0;
    "></div>""", unsafe_allow_html=True)


def fmt_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"
