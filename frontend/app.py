import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from config import Config
from openai import OpenAI
from sql_assistant import LLMSQLAssistant, AssistantResponse

# Initialize the OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)
sql_assistant = LLMSQLAssistant()

# Constants
CHAT_HISTORY_KEY = "chat_history"
MAX_HISTORY = 20


# Set page config
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
)

WELCOME_MESSAGE = (
    "Hi there! I'm your Vegan Nutritionist Assistant. "
    "Ask me about your meals, macros, or micronutrients and I'll help you analyze your nutrition data."
)

def _save_chat_history():
    """Save chat history to session state"""
    if "messages" in st.session_state:
        # Only keep the last MAX_HISTORY messages
        recent_messages = st.session_state.messages[-MAX_HISTORY:]
        st.session_state[CHAT_HISTORY_KEY] = json.dumps([
            {k: v for k, v in msg.items() if k not in ["timestamp", "metadata"]}
            for msg in recent_messages
        ])

def init_session():
    """Initialize or load chat session"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Try to load from session state
        if st.session_state.get(f"{CHAT_HISTORY_KEY}_initialized", False) is False:
            try:
                if CHAT_HISTORY_KEY in st.session_state:
                    loaded_messages = json.loads(st.session_state[CHAT_HISTORY_KEY])
                    if isinstance(loaded_messages, list):
                        st.session_state.messages = loaded_messages
            except Exception as e:
                st.error(f"Error loading chat history: {e}")
                st.session_state.messages = []
            
            st.session_state[f"{CHAT_HISTORY_KEY}_initialized"] = True
        
        # Add welcome message if no messages exist
        if not st.session_state.messages:
            st.session_state.messages = [{
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "timestamp": datetime.now().isoformat()
            }]
            _save_chat_history()

def get_chat_completion(messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    """Get completion from OpenAI's Chat API"""
    try:
        response = client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting chat completion: {str(e)}")
        return "I'm sorry, I encountered an error processing your request."

def should_use_sql(question: str) -> bool:
    """Determine if a question should be routed to the SQL assistant."""
    classification_prompt = (
        "Decide whether the user message needs data from the meals database.\n"
        "Respond ONLY with 'SQL' if answering requires querying past or present meals, "
        "macros, or logs. Otherwise respond 'GENERAL'.\n"
        "Examples needing SQL: questions about what was eaten, nutrient totals over specific dates, "
        "comparisons based on logged meals.\n"
        "Examples not needing SQL: general nutrition advice, hypothetical questions, cooking tips."
    )
    try:
        response = client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": classification_prompt},
                {"role": "user", "content": question.strip()},
            ],
            temperature=0,
            max_tokens=5,
        )
        decision = response.choices[0].message.content.strip().lower()
        return "sql" in decision
    except Exception:
        return False

def handle_sql_question(question: str) -> AssistantResponse:
    """Generate SQL answer and return structured response."""
    return sql_assistant.answer_question(question)

def build_general_system_prompt() -> str:
    """Reuse the nutrition profile's system prompt with lightweight guardrails."""
    profile = Config.load_nutrition_profile()
    profile_prompt = profile.get(
        "system_prompt",
        "You are a knowledgeable and supportive vegan nutritionist assistant.",
    )
    profile_text = Config.load_nutrition_profile_text()
    return (
        f"{profile_prompt}\n\n"
        "When the user asks questions that do not require querying historic meal logs, "
        "answer using only the nutrition profile context below and general best practices. "
        "If the user is explicitly asking about their logged meals or historical data, let them know "
        "that you need to run a database analysis and encourage them to ask about specific meals so you can run SQL.\n\n"
        "Nutrition profile (YAML):\n"
        f"{profile_text}"
    )

def render_chat():
    """Render the chat interface using Streamlit's chat components."""
    if "generating_response" not in st.session_state:
        st.session_state.generating_response = False

    assistant_placeholder = None
    chat_history = st.container(height=520, border=False)
    with chat_history:
        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message.get("metadata"):
                        metadata = message["metadata"]
                        sql_present = isinstance(metadata, dict) and (
                            metadata.get("sql") or metadata.get("rows")
                        )
                        if sql_present:
                            with st.expander("SQL Analysis"):
                                if metadata.get("sql"):
                                    st.markdown("**Query**")
                                    st.code(metadata["sql"], language="sql")
                                if metadata.get("rows"):
                                    df = pd.DataFrame(metadata["rows"])
                                    if not df.empty:
                                        st.markdown("**Results**")
                                        st.dataframe(df, use_container_width=True)
                                extras = {
                                    k: v for k, v in metadata.items()
                                    if k not in {"sql", "rows"}
                                }
                                if extras:
                                    st.markdown("**Additional Details**")
                                    st.json(extras)
                        else:
                            with st.expander("Details"):
                                st.json(metadata)
        if st.session_state.generating_response:
            with st.chat_message("assistant"):
                assistant_placeholder = st.empty()
                assistant_placeholder.caption("Analyzing your request...")

    if st.session_state.generating_response:
        latest_user_message = next(
            (msg for msg in reversed(st.session_state.messages) if msg["role"] == "user"),
            None,
        )
        question_text = latest_user_message["content"] if latest_user_message else ""
        use_sql = bool(question_text and should_use_sql(question_text))

        if use_sql:
            sql_response = handle_sql_question(question_text)
            response_text = sql_response.message
            metadata: Dict[str, Any] = {}
            if sql_response.sql:
                metadata["sql"] = sql_response.sql
            if sql_response.rows is not None:
                metadata["rows"] = sql_response.rows
            if sql_response.reasoning:
                metadata["reasoning"] = sql_response.reasoning
            if sql_response.confidence is not None:
                metadata["confidence"] = sql_response.confidence
            if sql_response.error:
                metadata["error"] = sql_response.error
        else:
            system_message = {
                "role": "system",
                "content": build_general_system_prompt(),
            }
            api_messages = [system_message] + [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
                if msg["role"] != "system"
            ][-MAX_HISTORY:]
            response_text = get_chat_completion(api_messages)
            metadata = None

        if assistant_placeholder is not None:
            assistant_placeholder.markdown(response_text)
        else:
            with st.chat_message("assistant"):
                st.markdown(response_text)
        
        assistant_message = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            assistant_message["metadata"] = metadata
        st.session_state.messages.append(assistant_message)
        st.session_state.generating_response = False
        _save_chat_history()
        st.rerun()

    prompt = st.chat_input("Ask me about your meals, macros, or micronutrients...")
    
    if prompt:
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.messages.append(user_message)
        st.session_state.generating_response = True
        _save_chat_history()
        st.rerun()

def render_sidebar():
    """Render the sidebar"""
    st.sidebar.title("Chat Controls")
    
    if st.sidebar.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Chat history cleared. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        }]
        _save_chat_history()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This assistant helps you track and analyze your vegan nutrition. "
        "Ask about your meals, macros, or get nutritional advice."
    )

def main():
    """Main application function"""
    init_session()
    
    st.title(Config.APP_TITLE)
    st.caption("Your personal AI nutritionist for tracking and optimizing your vegan diet.")
    
    render_chat()
    render_sidebar()

if __name__ == "__main__":
    main()
