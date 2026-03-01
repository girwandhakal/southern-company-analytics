import os
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

BOT_NAME = "Southern Spark"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(PROJECT_ROOT / ".env.local", override=True)
load_dotenv(override=True)

OPEN_KEY = "spark_chat_open"


def _resolve_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")


def _build_dashboard_context(df: Optional[pd.DataFrame], page_title: str) -> str:
    if df is None or df.empty:
        return (
            f"Current page: {page_title}\n"
            "No dataframe is available for this page. Provide guidance based on dashboard context."
        )

    context_lines: List[str] = [
        f"Current page: {page_title}",
        f"Rows: {len(df):,}, Columns: {len(df.columns):,}",
        "Columns: " + ", ".join([str(c) for c in df.columns[:30]]),
    ]

    if "Risk_Level" in df.columns:
        risk_counts = df["Risk_Level"].astype(str).value_counts().head(8)
        context_lines.append(
            "Risk levels: " + "; ".join([f"{name}={count}" for name, count in risk_counts.items()])
        )
    if "State" in df.columns:
        state_counts = df["State"].astype(str).value_counts().head(8)
        context_lines.append(
            "Top states: " + "; ".join([f"{name}={count}" for name, count in state_counts.items()])
        )
    if "Total_Replacement_Cost" in df.columns:
        cost = pd.to_numeric(df["Total_Replacement_Cost"], errors="coerce").fillna(0)
        context_lines.append(f"Total replacement cost: ${cost.sum():,.0f}")
        context_lines.append(f"Average replacement cost: ${cost.mean():,.0f}")
    if "Support_Status" in df.columns:
        support_counts = df["Support_Status"].astype(str).value_counts().head(6)
        context_lines.append(
            "Support status: " + "; ".join([f"{name}={count}" for name, count in support_counts.items()])
        )

    return "\n".join(context_lines)


@st.cache_resource(show_spinner=False)
def _get_openai_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError:
        return None

    api_key = _resolve_openai_api_key()
    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def _generate_reply(prompt: str, context: str, history: List[Dict[str, str]]) -> str:
    client = _get_openai_client()
    if client is None:
        return (
            "OpenAI API key is not configured or `openai` package is not installed. Add `OPENAI_API_KEY` in `.env.local` "
            "and ensure you have run `pip install openai`."
        )

    global_app_context = """
Available Dashboard Pages (direct the user here if their question relates to these topics):
1. 'Home' - Main dashboard hub and high-level entry point.
2. 'Executive Overview' - Executive level snapshot of risk, cost, and lifecycle metrics.
3. 'Geographic Risk Intelligence' - Regional/state risk distribution map and location-based analysis.
4. 'Lifecycle & Asset Health' - End-of-Life (EoL) tracking, hardware support milestones, and asset health.
5. 'Cost & Support Risk Analysis' - Financial exposure and support risk analysis (unsupported/expired devices).
6. 'Investment Prioritization' - Optimization and prioritizing investments for hardware replacement.
"""

    system_text = (
        f"You are {BOT_NAME}, an assistant for Southern Company dashboard users.\n"
        "Only answer questions related to this dashboard, its KPIs, trends, filters, and insights.\n"
        "Be concise, data-driven, and practical.\n"
        "Do NOT re-introduce yourself after the first message — the user already knows who you are.\n\n"
        f"{global_app_context}\n"
        f"Current Page Context:\n{context}"
    )

    messages: list = [{"role": "system", "content": system_text}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
        )
        text = response.choices[0].message.content
        return text.strip() if text else "I could not generate a response. Please try again."
    except Exception as exc:
        import traceback
        return f"Error contacting OpenAI: {exc}\n\nDetails: {traceback.format_exc()}"


def _inject_toggle_css() -> None:
    st.markdown(
        """
        <style>
            .spark-badge {
                display: inline-block;
                font-size: 0.62rem;
                font-weight: 800;
                letter-spacing: 1px;
                color: #FFFFFF;
                background: linear-gradient(135deg, #E8734A, #D35400);
                border-radius: 999px;
                padding: 4px 14px;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                box-shadow: 0 3px 12px rgba(232, 115, 74, 0.3);
            }
            .spark-msg {
                display: flex;
                width: 100%;
                margin: 0.4rem 0;
            }
            .spark-msg.user { justify-content: flex-end; }
            .spark-msg.assistant { justify-content: flex-start; }
            .spark-bubble {
                max-width: 88%;
                border-radius: 16px;
                padding: 0.65rem 0.9rem;
                font-size: 0.86rem;
                line-height: 1.5;
                word-break: break-word;
                font-family: 'Inter', sans-serif;
            }
            .spark-msg.user .spark-bubble {
                background: linear-gradient(135deg, #E8734A, #D35400);
                color: #FFFFFF;
                border-bottom-right-radius: 4px;
                box-shadow: 0 2px 12px rgba(232, 115, 74, 0.2);
            }
            .spark-msg.assistant .spark-bubble {
                background: #FFFFFF;
                color: #1A1F2E;
                border: 1px solid #E0E6E3;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            }
            .spark-tip {
                font-size: 0.72rem;
                color: #94A3B8;
                margin-top: 0.3rem;
                font-weight: 500;
            }
            /* Keep chat controls readable regardless of global theme overrides */
            div[class*="st-key-spark-close-"] button {
                background: #F8FAFC !important;
                color: #1A1F2E !important;
                border: 1px solid #D8E0DB !important;
            }
            div[class*="st-key-spark-close-"] button p {
                color: #1A1F2E !important;
                font-weight: 800 !important;
            }
            div[class*="st-key-spark-close-"] button:hover {
                background: #EEF2F7 !important;
                color: #1A1F2E !important;
                border-color: #94A3B8 !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput > div > div {
                background: #FFFFFF !important;
                border: 1px solid #D8E0DB !important;
                border-radius: 10px !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput input {
                background: #FFFFFF !important;
                color: #1A1F2E !important;
                -webkit-text-fill-color: #1A1F2E !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput input::placeholder {
                color: #6B7B8D !important;
                -webkit-text-fill-color: #6B7B8D !important;
                opacity: 1 !important;
            }
            /* Extra-specific targeting for the chat message input */
            div[class*="st-key-spark-input-"] [data-baseweb="input"] {
                background: #FFFFFF !important;
                border: 1px solid #D8E0DB !important;
                border-radius: 10px !important;
            }
            div[class*="st-key-spark-input-"] input {
                background: #FFFFFF !important;
                color: #1A1F2E !important;
                -webkit-text-fill-color: #1A1F2E !important;
                caret-color: #1A1F2E !important;
            }
            div[class*="st-key-spark-input-"] input::placeholder {
                color: #6B7B8D !important;
                -webkit-text-fill-color: #6B7B8D !important;
                opacity: 1 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_chat_panel(page_title: str, df: Optional[pd.DataFrame]) -> None:
    history_key = f"spark_chat_history::{page_title}"
    if history_key not in st.session_state:
        st.session_state[history_key] = [
            {
                "role": "assistant",
                "content": (
                    f"Hi, I am {BOT_NAME}. Ask about risk, lifecycle, "
                    "cost, support, and recommendations."
                ),
            }
        ]

    st.markdown(f"#### {BOT_NAME}")
    st.caption("Ask about dashboard KPIs, trends, and actions to prioritize.")

    history: List[Dict[str, str]] = st.session_state[history_key]

    chat_area = st.container(height=420)
    with chat_area:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            safe_text = escape(str(msg.get("content", ""))).replace("\n", "<br>")
            st.markdown(
                f"<div class='spark-msg {role}'>"
                f"<div class='spark-bubble'>{safe_text}</div></div>",
                unsafe_allow_html=True,
            )

    with st.form(f"spark-form-{page_title}", clear_on_submit=True):
        prompt = st.text_input(
            "Message",
            placeholder="Type a message and press Enter…",
            label_visibility="collapsed",
            key=f"spark-input-{page_title}",
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and prompt and prompt.strip():
        history.append({"role": "user", "content": prompt.strip()})
        with chat_area:
            st.markdown(
                f"<div class='spark-msg user'>"
                f"<div class='spark-bubble'>{escape(prompt.strip())}</div></div>",
                unsafe_allow_html=True,
            )
        with st.spinner(f"{BOT_NAME} is thinking…"):
            try:
                context = _build_dashboard_context(df, page_title)
                answer = _generate_reply(prompt.strip(), context, history)
            except Exception as exc:
                import traceback
                answer = f"Error contacting OpenAI: {exc}\n\nDetails: {traceback.format_exc()}"
        history.append({"role": "assistant", "content": answer})
        st.session_state[history_key] = history
        st.rerun()

    st.markdown(
        "<div class='spark-tip'>Tip: Ask for top risk states, spend reduction "
        "opportunities, or remediation priorities.</div>",
        unsafe_allow_html=True,
    )


def render_dashboard_chatbot(page_title: str, df: Optional[pd.DataFrame] = None) -> st.container:
    """Call at the top of each page.  Returns a container for all page content.

    When the chat panel is closed the container spans the full width with a
    small chat icon pinned to the far right.
    When the chat panel is open the page is split into [content | chat] columns
    so that all visualisations squeeze naturally.
    """
    if OPEN_KEY not in st.session_state:
        st.session_state[OPEN_KEY] = False
    if "spark_sidebar_hidden" not in st.session_state:
        st.session_state["spark_sidebar_hidden"] = False

    _inject_toggle_css()

    is_open = st.session_state[OPEN_KEY]

    if is_open:
        hide_sidebar = st.session_state.get("spark_sidebar_hidden", False)

        if hide_sidebar:
            st.markdown(
                """
                <style>
                    section[data-testid="stSidebar"] {
                        width: 0px !important;
                        min-width: 0px !important;
                        max-width: 0px !important;
                        overflow: hidden !important;
                        opacity: 0 !important;
                        padding: 0 !important;
                        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    }
                    [data-testid="collapsedControl"] {
                        display: none !important;
                    }
                    [data-testid="stColumn"]:has(#custom-expand-btn) {
                        position: fixed !important;
                        top: 20px !important;
                        left: 20px !important;
                        z-index: 99999 !important;
                        width: 45px !important;
                        flex: none !important;
                    }
                    [data-testid="stColumn"]:has(#custom-expand-btn) button {
                        background: rgba(26, 31, 46, 0.8) !important;
                        border: 1px solid rgba(255,255,255,0.1) !important;
                        color: white !important;
                        font-weight: bold !important;
                        padding: 5px !important;
                        border-radius: 10px !important;
                        transition: all 0.25s ease !important;
                        backdrop-filter: blur(8px) !important;
                    }
                    [data-testid="stColumn"]:has(#custom-expand-btn) button:hover {
                        background: #E8734A !important;
                        border-color: #E8734A !important;
                        transform: scale(1.05) !important;
                    }
                    [data-testid="stHorizontalBlock"]:has(#custom-expand-btn) {
                        height: 0px !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        gap: 0 !important;
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            btn_container = st.container()
            with btn_container:
                expand_col, _ = st.columns([1, 10])
                with expand_col:
                    st.markdown("<div id='custom-expand-btn'></div>", unsafe_allow_html=True)
                    if st.button("⟫", key=f"expand-sidebar-{page_title}", help="Show Sidebar Pages"):
                        st.session_state["spark_sidebar_hidden"] = False
                        st.rerun()

        st.markdown(
            """
            <style>
                @keyframes slideInChat {
                    0% { opacity: 0; transform: translateX(30px); }
                    100% { opacity: 1; transform: translateX(0); }
                }
                [data-testid="stHorizontalBlock"]:has(.spark-badge) > [data-testid="stColumn"]:last-child {
                    animation: slideInChat 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
                }
                [data-testid="stHorizontalBlock"]:has(.spark-badge)
                    > [data-testid="stColumn"]:last-child
                    > div > div[data-testid="stVerticalBlockBorderWrapper"] {
                    position: sticky;
                    top: 2.5rem;
                    min-height: calc(100vh - 6rem);
                    max-height: calc(100vh - 6rem);
                    overflow-y: auto;
                    background: #FFFFFF !important;
                    border-radius: 18px !important;
                    border: 1px solid #E0E6E3 !important;
                    box-shadow: 0 8px 40px rgba(0,0,0,0.08) !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        main_col, chat_col = st.columns([7, 3], gap="medium")
        with chat_col:
            with st.container(border=True):
                header_left, header_right = st.columns([6, 1])
                with header_left:
                    st.markdown(
                        "<span class='spark-badge'>LIVE COPILOT</span>",
                        unsafe_allow_html=True,
                    )
                with header_right:
                    if st.button("✕", key=f"spark-close-{page_title}", help="Close chat"):
                        st.session_state[OPEN_KEY] = False
                        st.rerun()
                _render_chat_panel(page_title, df)
        return main_col
    else:
        st.markdown(
            """
            <style>
                [data-testid="stColumn"]:has(#spark-button-container) {
                    position: fixed !important;
                    bottom: 36px !important;
                    right: 36px !important;
                    z-index: 9999 !important;
                    width: 68px !important;
                    flex: none !important;
                }
                [data-testid="stColumn"]:has(#spark-button-container) button {
                    border-radius: 16px !important;
                    width: 62px !important;
                    height: 62px !important;
                    padding: 0 !important;
                    background: linear-gradient(135deg, #E8734A, #D35400) !important;
                    color: white !important;
                    border: none !important;
                    box-shadow: 0 6px 24px rgba(232, 115, 74, 0.4), 0 2px 8px rgba(232, 115, 74, 0.2) !important;
                    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                [data-testid="stColumn"]:has(#spark-button-container) button:hover {
                    transform: scale(1.08) translateY(-2px) !important;
                    box-shadow: 0 10px 36px rgba(232, 115, 74, 0.5), 0 4px 12px rgba(232, 115, 74, 0.3) !important;
                }
                [data-testid="stColumn"]:has(#spark-button-container) button p {
                    font-size: 28px !important;
                    margin: 0 !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        main_container = st.container()

        spacer, icon_col = st.columns([1, 1])
        with icon_col:
            st.markdown("<div id='spark-button-container'></div>", unsafe_allow_html=True)
            if st.button("💬", key=f"spark-toggle-{page_title}", help=f"Open {BOT_NAME}"):
                st.session_state[OPEN_KEY] = True
                st.session_state["spark_sidebar_hidden"] = True
                st.rerun()

        return main_container
