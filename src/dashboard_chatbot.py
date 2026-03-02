import os
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

BOT_NAME = "Southern Spark"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OPEN_KEY = "spark_chat_open"


def _resolve_openai_api_key() -> Optional[str]:
    try:
        return st.secrets["OPENAI_API_KEY"]
    except KeyError:
        try:
            return st.secrets["openai"]["OPENAI_API_KEY"]
        except KeyError:
            return None


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


def _get_openai_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError:
        return None

    api_key = _resolve_openai_api_key()
    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def _generate_reply(prompt: str, context: str, history: List[Dict[str, str]]):
    """Generates a reply and yields text chunks as they arrive from OpenAI."""
    client = _get_openai_client()
    if client is None:
        yield (
            "OpenAI API key is not configured or `openai` package is not installed. Add `OPENAI_API_KEY` in `secrets.toml` "
            "and ensure you have run `pip install openai`."
        )
        return

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
        "Be concise, data-driven, and practical. Format your answers using markdown when necessary.\n"
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
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as exc:
        import traceback
        yield f"Error contacting OpenAI: {exc}\n\nDetails: {traceback.format_exc()}"


def _inject_toggle_css() -> None:
    st.markdown(
        """
        <style>
            /* Animations */
            @keyframes slideUpFade {
                0% { opacity: 0; transform: translateY(12px) scale(0.98); }
                100% { opacity: 1; transform: translateY(0) scale(1); }
            }
            @keyframes pulseGlow {
                0% { box-shadow: 0 4px 18px rgba(142, 68, 173, 0.4), 0 0 0 0 rgba(142, 68, 173, 0.4); }
                70% { box-shadow: 0 4px 18px rgba(142, 68, 173, 0.4), 0 0 0 10px rgba(142, 68, 173, 0); }
                100% { box-shadow: 0 4px 18px rgba(142, 68, 173, 0.4), 0 0 0 0 rgba(142, 68, 173, 0); }
            }
            
            /* Header Badge */
            .spark-badge {
                display: inline-block;
                font-size: 0.62rem;
                font-weight: 800;
                letter-spacing: 1.2px;
                color: #FFFFFF;
                background: linear-gradient(135deg, #8E44AD, #6C3483);
                border-radius: 999px;
                padding: 4px 14px;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                box-shadow: 0 3px 12px rgba(142, 68, 173, 0.3);
            }
            
            /* Message Area */
            .spark-msg {
                display: flex;
                width: 100%;
                margin: 0.5rem 0;
                animation: slideUpFade 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
            }
            .spark-msg.user { justify-content: flex-end; }
            .spark-msg.assistant { justify-content: flex-start; }
            
            /* Bubbles */
            .spark-bubble {
                max-width: 88%;
                border-radius: 16px;
                padding: 0.7rem 1rem;
                font-size: 0.88rem;
                line-height: 1.55;
                word-break: break-word;
                font-family: 'Inter', sans-serif;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .spark-bubble:hover {
                transform: translateY(-1px);
            }
            
            /* User Bubble (Dark Slate — frosted depth) */
            .spark-msg.user .spark-bubble {
                background: rgba(26, 31, 46, 0.92);
                color: #FFFFFF;
                border: none;
                border-bottom-right-radius: 4px;
                box-shadow: 0 4px 18px rgba(26, 31, 46, 0.18);
                backdrop-filter: blur(6px);
                -webkit-backdrop-filter: blur(6px);
            }
            
            /* Assistant Bubble (White text-only appearance) */
            .spark-msg.assistant .spark-bubble {
                background: transparent;
                color: #1A1F2E;
                border: none;
                box-shadow: none;
                padding-left: 0.2rem; /* small padding adjust for missing border */
            }
            
            /* Tip text */
            .spark-tip {
                font-size: 0.72rem;
                color: #94A3B8;
                margin-top: 0.4rem;
                font-weight: 500;
                text-align: center;
                animation: slideUpFade 0.6s ease-out 0.2s both;
            }
            
            /* Close Button Style */
            div[class*="st-key-spark-close-"] button {
                background: rgba(248, 250, 252, 0.7) !important;
                color: #1A1F2E !important;
                border: none !important;
                border-radius: 50% !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
                backdrop-filter: blur(8px) !important;
                -webkit-backdrop-filter: blur(8px) !important;
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important;
            }
            div[class*="st-key-spark-close-"] button p {
                color: #1A1F2E !important;
                font-weight: 800 !important;
            }
            div[class*="st-key-spark-close-"] button:hover {
                background: rgba(254, 226, 226, 0.8) !important;
                color: #E74C3C !important;
                box-shadow: 0 4px 14px rgba(231, 76, 60, 0.15) !important;
                transform: rotate(90deg) scale(1.1) !important;
            }
            
            /* Standard text input overrides (Form) */
            div[class*="st-key-spark-form-"] .stTextInput > div > div {
                background: rgba(255, 255, 255, 0.6) !important;
                border: none !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
                backdrop-filter: blur(8px) !important;
                -webkit-backdrop-filter: blur(8px) !important;
                transition: box-shadow 0.2s ease !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput > div > div:focus-within {
                box-shadow: 0 0 0 2px rgba(142, 68, 173, 0.18), 0 4px 16px rgba(0,0,0,0.06) !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput input {
                background: transparent !important;
                color: #1A1F2E !important;
                -webkit-text-fill-color: #1A1F2E !important;
                padding: 12px !important;
            }
            div[class*="st-key-spark-form-"] .stTextInput input::placeholder {
                color: #94A3B8 !important;
                -webkit-text-fill-color: #94A3B8 !important;
                opacity: 1 !important;
            }
            
            /* Deep targeting for text input (BaseWeb / Streamlit constraints) */
            div[class*="st-key-spark-input-"] [data-baseweb="input"] {
                background: #FFFFFF !important;
                border-radius: 12px !important;
            }
            div[class*="st-key-spark-input-"] input {
                color: #1A1F2E !important;
                -webkit-text-fill-color: #1A1F2E !important;
                caret-color: #8E44AD !important;
            }
            
            /* Send Button Inside the Chat Panel */
            div[class*="st-key-spark-form-"] .stButton button {
                background: #1A1F2E !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 12px !important;
                transition: transform 0.2s ease, box-shadow 0.2s ease !important;
            }
            div[class*="st-key-spark-form-"] .stButton button p {
                color: #FFFFFF !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
            }
            div[class*="st-key-spark-form-"] .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 14px rgba(26, 31, 46, 0.2) !important;
                background: #272f45 !important;
            }
            
            /* Hide the "Press Enter to submit form" text */
            div[class*="st-key-spark-input-"] [data-testid="InputInstructions"] {
                display: none !important;
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

    chat_area = st.container(height=380)
    with chat_area:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            safe_text = escape(str(msg.get("content", ""))).replace("\n", "<br>")
            st.markdown(
                f"<div class='spark-msg {role}'>"
                f"<div class='spark-bubble'>{safe_text}</div></div>",
                unsafe_allow_html=True,
            )

    # Form is now inside the same parent container as the chat area
    with st.form(f"spark-form-{page_title}", clear_on_submit=True):
        input_col, btn_col = st.columns([5, 1], gap="small")
        with input_col:
            prompt = st.text_input(
                "Message",
                placeholder="Ask Southern Spark…",
                label_visibility="collapsed",
                key=f"spark-input-{page_title}",
            )
        with btn_col:
            submitted = st.form_submit_button("➤", use_container_width=True)

    if submitted and prompt and prompt.strip():
        history.append({"role": "user", "content": prompt.strip()})
        with chat_area:
            st.markdown(
                f"<div class='spark-msg user'>"
                f"<div class='spark-bubble'>{escape(prompt.strip())}</div></div>",
                unsafe_allow_html=True,
            )

            # Create a placeholder for the assistant's streaming response
            with st.container():
                st.markdown("<div class='spark-msg assistant'><div class='spark-bubble'>", unsafe_allow_html=True)
                assistant_placeholder = st.empty()
                st.markdown("</div></div>", unsafe_allow_html=True)

        with st.spinner(f"{BOT_NAME} is typing…"):
            try:
                context = _build_dashboard_context(df, page_title)
                stream = _generate_reply(prompt.strip(), context, history)
                answer = assistant_placeholder.write_stream(stream)
            except Exception as exc:
                import traceback
                answer = f"Error contacting OpenAI: {exc}\n\nDetails: {traceback.format_exc()}"
                assistant_placeholder.markdown(answer)

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
                    background: rgba(255, 255, 255, 0.45) !important;
                    border-radius: 20px !important;
                    border: 1px solid rgba(255, 255, 255, 0.5) !important;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.08), inset 0 0 0 0.5px rgba(255,255,255,0.6) !important;
                    backdrop-filter: blur(20px) saturate(1.4) !important;
                    -webkit-backdrop-filter: blur(20px) saturate(1.4) !important;
                }
                /* Remove Streamlit's default inner container borders */
                [data-testid="stHorizontalBlock"]:has(.spark-badge)
                    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
                    border: none !important;
                    box-shadow: none !important;
                    background: transparent !important;
                }
                /* Soften the scrollable chat area border */
                [data-testid="stHorizontalBlock"]:has(.spark-badge)
                    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"][data-testid] {
                    border: 1px solid rgba(0,0,0,0.04) !important;
                    border-radius: 14px !important;
                    box-shadow: inset 0 1px 3px rgba(0,0,0,0.03) !important;
                    background: rgba(255,255,255,0.3) !important;
                }
                /* Send button inline styling */
                div[class*="st-key-spark-form-"] .stFormSubmitButton button {
                    background: #1A1F2E !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 10px !important;
                    padding: 0.5rem !important;
                    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
                    min-height: 42px !important;
                }
                div[class*="st-key-spark-form-"] .stFormSubmitButton button:hover {
                    transform: translateY(-1px) !important;
                    box-shadow: 0 4px 12px rgba(26, 31, 46, 0.2) !important;
                    background: #272f45 !important;
                }
                div[class*="st-key-spark-form-"] .stFormSubmitButton button p {
                    color: #FFFFFF !important;
                    font-weight: 700 !important;
                    font-size: 1.1rem !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        main_col, chat_col = st.columns([7, 3], gap="medium")
        with chat_col:
            with st.container():
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
                    background: linear-gradient(135deg, #8E44AD, #6C3483) !important;
                    color: white !important;
                    border: none !important;
                    box-shadow: 0 6px 24px rgba(142, 68, 173, 0.4), 0 2px 8px rgba(142, 68, 173, 0.2) !important;
                    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    animation: pulseGlow 3s infinite;
                }
                [data-testid="stColumn"]:has(#spark-button-container) button:hover {
                    transform: scale(1.08) translateY(-2px) !important;
                    box-shadow: 0 10px 36px rgba(142, 68, 173, 0.5), 0 4px 12px rgba(142, 68, 173, 0.3) !important;
                    animation: none !important;
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
