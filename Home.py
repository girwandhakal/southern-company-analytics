import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from src.theme import inject_theme_css, COLORS
from src.data_loader import render_sidebar_logo

st.set_page_config(page_title="Southern Company Analytics", page_icon="⚡", layout="wide")
inject_theme_css()
render_sidebar_logo()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hero Section */
.hero-section {
    text-align: center;
    padding: 44px 20px 42px;
    animation: fadeInUp 0.6s ease-out;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.hero-badge {
    display: inline-block;
    background: #E8734A;
    color: #FFFFFF;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 7px 22px;
    border-radius: 50px;
    margin-bottom: 22px;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 900;
    color: #1A1F2E;
    line-height: 1.15;
    margin-bottom: 14px;
    letter-spacing: -0.5px;
    text-align: center;
}
.hero-subtitle {
    font-size: 1.02rem;
    color: #64748B;
    max-width: 660px;
    line-height: 1.65;
    margin: 0 auto;
    font-weight: 400;
    text-align: center;
}

/* Card Grid — force single row */
.card-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 18px;
    padding: 10px 0 40px;
    margin: 0 auto;
    width: 100%;
}
.nav-card {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 26px 20px 22px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.05), 0 1px 4px rgba(0,0,0,0.03);
    transition: transform 0.35s cubic-bezier(0.25,0.46,0.45,0.94),
                box-shadow 0.35s cubic-bezier(0.25,0.46,0.45,0.94);
    animation: fadeInUp 0.55s ease-out both;
    display: flex;
    flex-direction: column;
    cursor: default;
    text-decoration: none !important;
    min-width: 0;
}
.nav-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.10), 0 4px 12px rgba(0,0,0,0.06);
}
.card-grid .nav-card:nth-child(1) { animation-delay: 0.05s; }
.card-grid .nav-card:nth-child(2) { animation-delay: 0.10s; }
.card-grid .nav-card:nth-child(3) { animation-delay: 0.15s; }
.card-grid .nav-card:nth-child(4) { animation-delay: 0.20s; }
.card-grid .nav-card:nth-child(5) { animation-delay: 0.25s; }
.card-grid .nav-card:nth-child(6) { animation-delay: 0.30s; }

.card-icon {
    width: 48px;
    height: 48px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    margin-bottom: 16px;
    flex-shrink: 0;
}
.card-title {
    font-size: 0.97rem;
    font-weight: 800;
    color: #1A1F2E;
    margin-bottom: 7px;
    line-height: 1.3;
}
.card-desc {
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.5;
    flex: 1;
    margin-bottom: 14px;
}
.card-badge {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 6px;
    width: fit-content;
}

/* Hide the page-link row visually but keep it functional */
.page-links-row {
    visibility: hidden;
    height: 0;
    overflow: hidden;
    margin: 0;
    padding: 0;
}

/* Footer */
.home-footer {
    text-align: center;
    padding: 24px 20px 14px;
    color: #94A3B8;
    font-size: 0.82rem;
    font-weight: 500;
    border-top: 1px solid #D8E0DB;
    max-width: 900px;
    margin: 0 auto;
}
.home-footer span {
    color: #94A3B8 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="hero-badge">Enterprise Intelligence Platform</div>
    <div class="hero-title">Southern Company<br>Fleet Analytics</div>
    <p class="hero-subtitle">
        Strategic insights into fleet lifecycle status, risk exposure, geographic distribution,
        and cost optimization &mdash; all in one place.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Page cards ────────────────────────────────────────────────────────────────
PAGE_CARDS = [
    {
        "icon": "📊",
        "title": "Executive Overview",
        "desc": "High-level KPIs, risk distribution, and support status across the entire fleet.",
        "badge": "Strategic",
        "badge_bg": "rgba(232,115,74,0.12)",
        "badge_color": "#D35400",
        "icon_bg": "rgba(232,115,74,0.12)",
        "path": "pages/1_Executive_Overview.py",
    },
    {
        "icon": "🌍",
        "title": "Geographic Risk Intelligence",
        "desc": "3D risk map, state-level hotspots, and priority site clustering for field deployment.",
        "badge": "Geospatial",
        "badge_bg": "rgba(52,152,219,0.12)",
        "badge_color": "#2471A3",
        "icon_bg": "rgba(52,152,219,0.12)",
        "path": "pages/2_Geographic_Risk_Intelligence.py",
    },
    {
        "icon": "⚙️",
        "title": "Lifecycle & Asset Health",
        "desc": "EoL trends, aging infrastructure tracking, and critical overdue asset monitoring.",
        "badge": "Monitoring",
        "badge_bg": "rgba(142,68,173,0.12)",
        "badge_color": "#7D3C98",
        "icon_bg": "rgba(142,68,173,0.12)",
        "path": "pages/3_Lifecycle_Asset_Health.py",
    },
    {
        "icon": "💲",
        "title": "Cost & Support Risk",
        "desc": "Financial exposure analysis, support coverage gaps, and technical debt visualization.",
        "badge": "Financial",
        "badge_bg": "rgba(240,168,48,0.12)",
        "badge_color": "#B7791F",
        "icon_bg": "rgba(240,168,48,0.12)",
        "path": "pages/5_Support_Security_Cost.py",
    },
    {
        "icon": "🎯",
        "title": "Investment Prioritization",
        "desc": "Budget simulator, priority ranking, and site-level action plans for CapEx allocation.",
        "badge": "Planning",
        "badge_bg": "rgba(39,174,96,0.12)",
        "badge_color": "#1E8449",
        "icon_bg": "rgba(39,174,96,0.12)",
        "path": "pages/6_Investment_Prioritization.py",
    },
    {
        "icon": "🔮",
        "title": "Predictive Risk Forecast",
        "desc": "Forward-looking risk trajectories and scenario-based outcomes for proactive decisions.",
        "badge": "Forecasting",
        "badge_bg": "rgba(231,76,60,0.12)",
        "badge_color": "#C0392B",
        "icon_bg": "rgba(231,76,60,0.12)",
        "path": "pages/7_Predictive_Risk_Forecast.py",
    },
]

cards_html = '<div class="card-grid">'
for card in PAGE_CARDS:
    cards_html += f"""
    <div class="nav-card">
        <div class="card-icon" style="background:{card['icon_bg']};">
            {card['icon']}
        </div>
        <div class="card-title">{card['title']}</div>
        <div class="card-desc">{card['desc']}</div>
        <div class="card-badge" style="background:{card['badge_bg']};color:{card['badge_color']};">
            {card['badge']}
        </div>
    </div>"""
cards_html += "</div>"

st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("""
<div class="home-footer">
    <span>Use the sidebar to navigate across all dashboard modules.</span>
</div>
""", unsafe_allow_html=True)
