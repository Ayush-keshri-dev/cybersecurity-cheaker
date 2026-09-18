"""
app.py — Streamlit UI entry point.

This file contains ONLY user interface code.
All business logic lives in analyzer.py, password_advisor.py, and chatbot.py.

Run with:  streamlit run app.py
"""

import streamlit as st

from ai_client import AIClient, AIServiceError, InvalidInputError
from analyzer import MessageAnalyzer
from chatbot import ChatMessage, CyberChatbot
from password_advisor import PasswordAdvisor

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cybersecurity Awareness Assistant",
    page_icon="🛡️",
    layout="centered",
)


# ---------------------------------------------------------------------------
# Initialise shared objects once per session using st.session_state.
# This avoids recreating API clients on every Streamlit rerun.
# ---------------------------------------------------------------------------
@st.cache_resource
def get_ai_client() -> AIClient | None:
    """
    Create the AIClient once and cache it for the session.
    Returns None if the API key is missing so the app can show a friendly error.
    """
    try:
        return AIClient()
    except AIServiceError:
        return None


def get_analyzer(client: AIClient) -> MessageAnalyzer:
    return MessageAnalyzer(client)


def get_chatbot(client: AIClient) -> CyberChatbot:
    return CyberChatbot(client)


# Initialise chat history in session state on first load
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🛡️ Cybersecurity Awareness Assistant")
st.info(
    "**Educational tool only.** This app helps you learn about cybersecurity risks. "
    "It is not a substitute for professional security software. "
    "AI analysis can make mistakes — always verify suspicious messages through official channels.",
    icon="ℹ️",
)

# ---------------------------------------------------------------------------
# Three main tabs
# ---------------------------------------------------------------------------
tab_analyzer, tab_password, tab_chatbot = st.tabs(
    ["🔍 Is This Safe?", "🔑 Password Advisor", "💬 Cyber Chatbot"]
)


# ===========================================================================
# TAB 1 — "Is This Safe?" Message Analyzer
# ===========================================================================
with tab_analyzer:
    st.header("🔍 Is This Safe?")
    st.write(
        "Paste a suspicious email, SMS, or social media message below. "
        "The app will check it for common signs of phishing or scams."
    )

    message_input = st.text_area(
        label="Paste the suspicious message here",
        placeholder="e.g. 'Your account has been suspended. Click here to verify immediately...'",
        height=200,
        max_chars=2000,
        key="analyzer_input",
    )

    analyze_button = st.button("🔍 Analyze Message", type="primary", key="analyze_btn")

    if analyze_button:
        ai_client = get_ai_client()

        if ai_client is None:
            st.error(
                "⚠️ AI service is not configured. "
                "Please add your GOOGLE_API_KEY to the .env file. "
                "See README.md for instructions.",
                icon="🔑",
            )
        else:
            analyzer = get_analyzer(ai_client)
            try:
                with st.spinner("Analyzing message..."):
                    result = analyzer.analyze(message_input)

                # --- Verdict ---
                verdict_display = {
                    "Likely Safe": ("✅ Likely Safe", "success"),
                    "Needs Caution": ("⚠️ Needs Caution", "warning"),
                    "Suspicious": ("🚨 Suspicious", "error"),
                }
                label, color = verdict_display.get(
                    result.verdict, ("⚠️ Needs Caution", "warning")
                )
                getattr(st, color)(f"**Verdict: {label}**")

                # --- Warning signs ---
                if result.warning_signs_found:
                    st.subheader("⚠️ Warning Signs Detected")
                    for sign in result.warning_signs_found:
                        st.markdown(f"- {sign}")
                else:
                    st.markdown("*No specific warning sign patterns detected by local scan.*")

                # --- Explanation ---
                st.subheader("📋 Explanation")
                st.write(result.explanation)

                # --- Safe next steps ---
                if result.safe_next_steps:
                    st.subheader("✅ Recommended Actions")
                    for i, step in enumerate(result.safe_next_steps, 1):
                        st.markdown(f"{i}. {step}")

                # --- Confidence note ---
                st.caption(result.confidence_note)

            except InvalidInputError as e:
                st.warning(str(e), icon="✏️")
            except AIServiceError as e:
                st.error(str(e), icon="🤖")


# ===========================================================================
# TAB 2 — Password Safety Advisor
# ===========================================================================
with tab_password:
    st.header("🔑 Password Safety Advisor")
    st.write(
        "Enter a password to check how strong it is. "
        "Your password is checked locally — it is **never sent anywhere** or stored."
    )

    password_input = st.text_input(
        label="Enter a password to check",
        type="password",   # Characters are masked — not displayed back to the user
        placeholder="Type a password here...",
        key="password_input",
    )

    check_button = st.button("🔑 Check Strength", type="primary", key="check_btn")

    if check_button:
        advisor = PasswordAdvisor()
        try:
            result = advisor.evaluate(password_input)

            # --- Strength rating ---
            rating_icons = {"Weak": "🔴", "Moderate": "🟡", "Strong": "🟢"}
            icon = rating_icons.get(result.strength_rating, "🟡")
            getattr(st, result.color)(
                f"**{icon} Strength: {result.strength_rating}** (Score: {result.score}/100)"
            )

            # --- Progress bar ---
            st.progress(result.score / 100)

            # --- Issues ---
            if result.issues_found:
                st.subheader("⚠️ Issues Found")
                for issue in result.issues_found:
                    st.markdown(f"- {issue}")

            # --- Tips ---
            if result.tips:
                st.subheader("💡 How to Improve")
                for tip in result.tips:
                    st.markdown(f"- {tip}")

            # --- Privacy notice ---
            st.caption(result.privacy_notice)

        except InvalidInputError as e:
            st.warning(str(e), icon="✏️")


# ===========================================================================
# TAB 3 — Cyber Awareness Chatbot
# ===========================================================================
with tab_chatbot:
    st.header("💬 Cyber Awareness Chatbot")
    st.write(
        "Ask any beginner cybersecurity question — phishing, 2FA, safe passwords, "
        "suspicious links, privacy, and more."
    )

    # --- Clear chat button ---
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()

    # --- Display existing conversation ---
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg.role):
            st.write(msg.content)

    # --- Chat input ---
    user_input = st.chat_input("Ask a cybersecurity question...")

    if user_input:
        ai_client = get_ai_client()

        if ai_client is None:
            st.error(
                "⚠️ AI service is not configured. "
                "Please add your GOOGLE_API_KEY to the .env file. "
                "See README.md for instructions.",
                icon="🔑",
            )
        else:
            chatbot = get_chatbot(ai_client)

            # Show the user's message immediately
            with st.chat_message("user"):
                st.write(user_input)

            # Append user message to history
            st.session_state["chat_history"].append(
                ChatMessage(role="user", content=user_input)
            )

            try:
                with st.spinner("Thinking..."):
                    response = chatbot.chat(
                        user_input,
                        st.session_state["chat_history"],
                    )

                # Show assistant response
                with st.chat_message("assistant"):
                    st.write(response.content)

                # Append assistant response to history
                st.session_state["chat_history"].append(response)

            except InvalidInputError as e:
                st.warning(str(e), icon="✏️")
            except AIServiceError as e:
                st.error(str(e), icon="🤖")

            st.rerun()
