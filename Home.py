import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from src.theme import inject_theme_css, COLORS

st.set_page_config(page_title="Southern Company Analytics", page_icon="⚡", layout="wide")
inject_theme_css()

# ── Additional Home-specific CSS ─────────────────────────────────────────────
st.markdown("""
<style>
.home-hero {
    text-align: center;
    padding: 40px 20px 30px 20px;
    animation: fadeInUp 0.6s ease-out;
}
.home-hero h1 {
    font-size: 2.8rem !important;
    font-weight: 900 !important;
    color: #1A1F2E !important;
    letter-spacing: -1px;
    margin-bottom: 8px;
    line-height: 1.1;
}
.home-hero .subtitle {
    font-size: 1.1rem;
    color: #6B7B8D;
    font-weight: 500;
    max-width: 620px;
    margin: 0 auto;
    line-height: 1.6;
}
.home-hero .badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 1.2px;
    color: #FFFFFF;
    background: linear-gradient(135deg, #E8734A, #D35400);
    border-radius: 999px;
    padding: 5px 16px;
    margin-bottom: 16px;
    text-transform: uppercase;
    box-shadow: 0 4px 14px rgba(232, 115, 74, 0.3);
}

.nav-card {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 28px 26px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.03);
    transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                box-shadow 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    cursor: pointer;
    height: 100%;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    animation: fadeInUp 0.5s ease-out both;
}
.nav-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.06);
}
.nav-card .icon-circle {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    margin-bottom: 16px;
    flex-shrink: 0;
}
.nav-card .card-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #1A1F2E;
    margin-bottom: 6px;
    letter-spacing: -0.2px;
}
.nav-card .card-desc {
    font-size: 0.84rem;
    color: #6B7B8D;
    line-height: 1.5;
    font-weight: 500;
    flex-grow: 1;
}
.nav-card .card-tag {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 3px 10px;
    border-radius: 6px;
    margin-top: 12px;
    text-transform: uppercase;
}

.nav-card:nth-child(1) { animation-delay: 0.1s; }
.nav-card:nth-child(2) { animation-delay: 0.15s; }
.nav-card:nth-child(3) { animation-delay: 0.2s; }
.nav-card:nth-child(4) { animation-delay: 0.25s; }
.nav-card:nth-child(5) { animation-delay: 0.3s; }

.home-footer {
    text-align: center;
    padding: 32px 20px 16px 20px;
    animation: fadeIn 0.8s ease-out 0.4s both;
}
.home-footer p {
    font-size: 0.82rem;
    color: #94A3B8;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── Hero Section ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="home-hero">
    <div class="badge">Enterprise Intelligence Platform</div>
    <h1>Southern Company<br>Fleet Analytics</h1>
    <p class="subtitle">
        Strategic insights into fleet lifecycle status, risk exposure,
        geographic distribution, and cost optimization — all in one place.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Navigation Cards ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    {
        "icon": "📈",
        "title": "Executive Overview",
        "desc": "High-level KPIs, risk distribution, and support status across the entire fleet.",
        "color": "#E8734A",
        "tag": "Strategic",
        "tag_bg": "rgba(232, 115, 74, 0.12)",
        "tag_color": "#E8734A",
    },
    {
        "icon": "🌎",
        "title": "Geographic Risk Intelligence",
        "desc": "3D risk map, state-level hotspots, and priority site clustering for field deployment.",
        "color": "#3498DB",
        "tag": "Geospatial",
        "tag_bg": "rgba(52, 152, 219, 0.12)",
        "tag_color": "#3498DB",
    },
    {
        "icon": "🔧",
        "title": "Lifecycle & Asset Health",
        "desc": "EoL trends, aging infrastructure tracking, and critical overdue asset monitoring.",
        "color": "#27AE60",
        "tag": "Monitoring",
        "tag_bg": "rgba(39, 174, 96, 0.12)",
        "tag_color": "#27AE60",
    },
    {
        "icon": "💰",
        "title": "Cost & Support Risk",
        "desc": "Financial exposure analysis, support coverage gaps, and technical debt visualization.",
        "color": "#F0A830",
        "tag": "Financial",
        "tag_bg": "rgba(240, 168, 48, 0.12)",
        "tag_color": "#D4940A",
    },
    {
        "icon": "🎯",
        "title": "Investment Prioritization",
        "desc": "Budget simulator, priority ranking, and site-level action plans for CapEx allocation.",
        "color": "#8E44AD",
        "tag": "Planning",
        "tag_bg": "rgba(142, 68, 173, 0.12)",
        "tag_color": "#8E44AD",
    },
]

cols = st.columns(5, gap="medium")
for i, item in enumerate(NAV_ITEMS):
    with cols[i]:
        st.markdown(f"""
        <div class="nav-card">
            <div class="icon-circle" style="background: {item['color']}15;">
                {item['icon']}
            </div>
            <div class="card-title">{item['title']}</div>
            <div class="card-desc">{item['desc']}</div>
            <div>
                <span class="card-tag" style="background: {item['tag_bg']}; color: {item['tag_color']};">
                    {item['tag']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Quick-start guidance ─────────────────────────────────────────────────────
st.markdown("""
<div class="home-footer">
    <p>Navigate using the <b>sidebar</b> to explore each dashboard module.
    Use the <b>AI Copilot</b> chat on any page for instant insights.</p>
</div>
""", unsafe_allow_html=True)
