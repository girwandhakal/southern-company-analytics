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


def _resolve_gemini_api_key() -> Optional[str]:
    return (
        os.getenv("GOOGLE_GEMINI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


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
def _get_gemini_model() -> Any:
    import google.generativeai as genai

    api_key = _resolve_gemini_api_key()
    if not api_key:
        return None

    genai.configure(api_key=api_key)

    preferred_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-pro-latest",
    ]
    available: List[str] = []

    try:
        for model in genai.list_models():
            methods = getattr(model, "supported_generation_methods", [])
            if "generateContent" in methods:
                name = getattr(model, "name", "")
                if name.startswith("models/"):
                    name = name.split("models/", 1)[1]
                if name:
                    available.append(name)
    except Exception:
        return genai.GenerativeModel("gemini-2.0-flash")

    for name in preferred_models:
        if name in available:
            return genai.GenerativeModel(name)

    if available:
        return genai.GenerativeModel(available[0])

    return genai.GenerativeModel("gemini-2.0-flash")


def _generate_reply(prompt: str, context: str, history: List[Dict[str, str]]) -> str:
    model = _get_gemini_model()
    if model is None:
        return (
            "Gemini API key is not configured. Add `GOOGLE_GEMINI_API_KEY` in `.env.local` "
            "or `.env` and restart Streamlit."
        )

    system_text = (
        f"You are {BOT_NAME}, an assistant for Southern Company dashboard users.\n"
        "Only answer questions related to this dashboard, its KPIs, trends, filters, and insights.\n"
        "Be concise, data-driven, and practical.\n"
        "Do NOT re-introduce yourself after the first message — the user already knows who you are.\n\n"
        f"Dashboard context:\n{context}"
    )

    contents: list = [{"role": "user", "parts": [system_text]},
                      {"role": "model", "parts": ["Understood. I will assist with dashboard questions concisely."]}]

    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [msg["content"]]})

    contents.append({"role": "user", "parts": [prompt]})

    response = model.generate_content(contents)
    text = getattr(response, "text", None)
    return text.strip() if text else "I could not generate a response. Please try again."


def _inject_toggle_css() -> None:
    """Styles for the chat panel and message bubbles."""
    st.markdown(
        """
        <style>
            .spark-badge {
                display: inline-block;
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.35px;
                color: #fff;
                background: linear-gradient(135deg, #2563eb, #0ea5e9);
                border-radius: 999px;
                padding: 0.2rem 0.55rem;
                margin-bottom: 0.5rem;
            }
            .spark-msg {
                display: flex;
                width: 100%;
                margin: 0.45rem 0;
            }
            .spark-msg.user { justify-content: flex-end; }
            .spark-msg.assistant { justify-content: flex-start; }
            .spark-bubble {
                max-width: 85%;
                border-radius: 16px;
                padding: 0.6rem 0.85rem;
                font-size: 0.88rem;
                line-height: 1.45;
                word-break: break-word;
            }
            .spark-msg.user .spark-bubble {
                background: #2563EB;
                color: #fff;
                border-bottom-right-radius: 4px;
            }
            .spark-msg.assistant .spark-bubble {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-bottom-left-radius: 4px;
            }
            .spark-tip {
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 0.3rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_chat_panel(page_title: str, df: Optional[pd.DataFrame]) -> None:
    """Renders the chat panel: scrollable messages + Enter-to-send input."""
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

    # Scrollable message area — fills most of the viewport
    chat_area = st.container(height=520)
    with chat_area:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            safe_text = escape(str(msg.get("content", ""))).replace("\n", "<br>")
            st.markdown(
                f"<div class='spark-msg {role}'>"
                f"<div class='spark-bubble'>{safe_text}</div></div>",
                unsafe_allow_html=True,
            )

    # Input form — text_input submits on Enter, clear_on_submit resets it
    with st.form(f"spark-form-{page_title}", clear_on_submit=True):
        prompt = st.text_input(
            "Message",
            placeholder="Type a message and press Enter…",
            label_visibility="collapsed",
        )
        st.form_submit_button("Send", use_container_width=True)

    if prompt and prompt.strip():
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
                answer = f"Error contacting Gemini: {exc}"
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

    Usage in every page::

        main = render_dashboard_chatbot("Page Title", df)
        with main:
            st.title("...")
            # ... all page content ...
    """
    if OPEN_KEY not in st.session_state:
        st.session_state[OPEN_KEY] = False

    _inject_toggle_css()

    is_open = st.session_state[OPEN_KEY]

    if is_open:
        st.markdown(
            """
            <style>
                /* Collapse sidebar */
                section[data-testid="stSidebar"] {
                    width: 0px !important;
                    min-width: 0px !important;
                    max-width: 0px !important;
                    overflow: hidden !important;
                    opacity: 0 !important;
                    padding: 0 !important;
                    transition: all 0.25s ease;
                }
                [data-testid="collapsedControl"] {
                    display: none !important;
                }
                /* Stretch chat column to full viewport height */
                [data-testid="stHorizontalBlock"]:has(.spark-badge)
                    > [data-testid="stColumn"]:last-child
                    > div > div[data-testid="stVerticalBlockBorderWrapper"] {
                    position: sticky;
                    top: 3.5rem;
                    min-height: calc(100vh - 4rem);
                    max-height: calc(100vh - 4rem);
                    overflow-y: auto;
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
        # Push the open-chat icon to the far right
        spacer, icon_col = st.columns([14, 1])
        with icon_col:
            if st.button("⚡", key=f"spark-toggle-{page_title}", help=f"Open {BOT_NAME}"):
                st.session_state[OPEN_KEY] = True
                st.rerun()
        return st.container()
