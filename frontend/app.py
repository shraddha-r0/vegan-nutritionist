import pandas as pd
import streamlit as st

from config import Config
from sql_assistant import LLMSQLAssistant

st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
)

WELCOME_MESSAGE = (
    "Hi there! I'm your Vegan Nutritionist Assistant. "
    "Ask me about your meals, macros, or micronutrients and I'll query the data for you."
)
MAX_HISTORY = 15


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    if "assistant" not in st.session_state and "assistant_error" not in st.session_state:
        try:
            st.session_state.assistant = LLMSQLAssistant()
            st.session_state.assistant_error = None
        except Exception as exc:  # pragma: no cover - Streamlit handles display
            st.session_state.assistant_error = str(exc)


def render_sidebar():
    st.sidebar.header("How it works")
    st.sidebar.markdown(
        "1. Enter any natural-language nutrition question.\n"
        "2. The LLM writes a safe SQL query over your meals table.\n"
        "3. Results are grounded in the SQLite database and summarized."
    )
    st.sidebar.caption(f"Database: `{Config.DB_PATH}`")


def render_message(message: dict):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_metadata(message)


def render_metadata(message: dict):
    if message.get("error"):
        st.warning(message["error"])
    if message.get("sql"):
        confidence = message.get("confidence")
        if confidence is not None:
            st.caption(f"SQL confidence: {confidence:.0%}")
        with st.expander("LLM generated SQL + results", expanded=False):
            st.code(message["sql"], language="sql")
            rows = message.get("rows")
            if rows is None:
                st.info("No query was executed.")
            elif not rows:
                st.info("The query returned no rows.")
            else:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
        if message.get("reasoning"):
            st.caption(f"Why this query: {message['reasoning']}")


def clamp_history():
    if len(st.session_state.messages) > MAX_HISTORY:
        st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]


def main():
    init_session()
    render_sidebar()

    assistant_error = st.session_state.get("assistant_error")
    if assistant_error:
        st.error(f"Setup error: {assistant_error}")
        return

    st.title(Config.APP_TITLE)
    st.caption("Grounded SQL answers for your vegan meals and nutrients.")

    for message in st.session_state.messages:
        render_message(message)

    prompt = st.chat_input("Ask me about your meals, macros, or micronutrients...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    assistant = st.session_state.get("assistant")
    response = assistant.answer_question(prompt)
    assistant_message = {
        "role": "assistant",
        "content": response.message,
        "sql": response.sql,
        "rows": response.rows,
        "reasoning": response.reasoning,
        "confidence": response.confidence,
        "error": response.error,
    }

    with st.chat_message("assistant"):
        st.markdown(response.message)
        render_metadata(assistant_message)

    st.session_state.messages.append(assistant_message)
    clamp_history()


if __name__ == "__main__":
    main()
