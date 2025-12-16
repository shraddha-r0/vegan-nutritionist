import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import Config
from openai import OpenAI
from sql_assistant import LLMSQLAssistant, AssistantResponse
from meal_logger import MealLogger

# Initialize clients/helpers
client = OpenAI(api_key=Config.OPENAI_API_KEY)
sql_assistant = LLMSQLAssistant()
meal_logger = MealLogger()

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

def classify_user_request(message: str) -> str:
    """Determine if the user wants to log a meal, query past meals, or ask a general question."""
    if not message.strip():
        return "GENERAL"

    prompt = (
        "You are an intent classifier for a vegan nutrition assistant. "
        "Return exactly one label:\n"
        "- LOG: the user is describing food they ate or explicitly wants to add a meal to the log.\n"
        "- QUERY: the user is asking about previously logged meals, totals, comparisons, or needs SQL-style analysis.\n"
        "- GENERAL: anything else such as general advice, meal ideas, or non-database questions.\n"
        "Prefer LOG only when the user clearly provides new meal information to record. "
        "Prefer QUERY when they ask questions like 'What did I eat yesterday?' or 'How many grams of protein last week?'."
    )
    try:
        response = client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message.strip()},
            ],
            temperature=0,
            max_tokens=5,
        )
        decision = response.choices[0].message.content.strip().upper()
        if "LOG" in decision:
            return "LOG"
        if "QUERY" in decision or "SQL" in decision:
            return "QUERY"
        return "GENERAL"
    except Exception:
        return "GENERAL"


def is_meal_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    confirm_keywords = ["confirm", "save", "looks good", "log it", "ship it"]
    return any(keyword in normalized for keyword in confirm_keywords)


def is_meal_cancellation(text: str) -> bool:
    normalized = text.strip().lower()
    cancel_keywords = ["cancel", "stop", "don't log", "discard", "nope"]
    return any(keyword in normalized for keyword in cancel_keywords)

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
                        meal_entry = metadata.get("meal_entry")
                        if meal_entry:
                            with st.expander("Meal Entry Details"):
                                df = pd.DataFrame([meal_entry])
                                st.dataframe(df, use_container_width=True)
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
                                    if k not in {"sql", "rows", "meal_entry"}
                                }
                                if extras:
                                    st.markdown("**Additional Details**")
                                    st.json(extras)
                        else:
                            remaining = {
                                k: v for k, v in metadata.items() if k != "meal_entry"
                            }
                            if remaining:
                                with st.expander("Details"):
                                    st.json(remaining)
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
        pending_meal = st.session_state.get("pending_meal_entry")

        def complete_response(text: str, metadata: Optional[Dict[str, Any]] = None):
            if assistant_placeholder is not None:
                assistant_placeholder.markdown(text)
            else:
                with st.chat_message("assistant"):
                    st.markdown(text)
            assistant_message = {
                "role": "assistant",
                "content": text,
                "timestamp": datetime.now().isoformat()
            }
            if metadata:
                assistant_message["metadata"] = metadata
            st.session_state.messages.append(assistant_message)
            st.session_state.generating_response = False
            _save_chat_history()
            st.rerun()

        if pending_meal:
            stage = pending_meal.get("stage")
            if stage == "awaiting_details":
                if is_meal_cancellation(question_text):
                    st.session_state.pop("pending_meal_entry", None)
                    complete_response("Okay, I won't log that meal.")
                    return
                result = meal_logger.build_entry(
                    pending_meal.get("description", ""),
                    question_text
                )
                if result.error or not result.row:
                    complete_response(
                        f"I'm still missing some details: {result.error or 'Please provide amounts and timing.'}"
                    )
                else:
                    st.session_state.pending_meal_entry = {
                        "stage": "awaiting_confirmation",
                        "description": pending_meal.get("description", ""),
                        "entry": result.row,
                        "summary": result.summary,
                    }
                    preview_msg = (
                        f"{result.summary}\n\n"
                        "Please review the meal details. Reply **confirm meal entry** to save it "
                        "or **cancel meal entry** to discard."
                    )
                    complete_response(preview_msg, metadata={"meal_entry": result.row})
            elif stage == "awaiting_confirmation":
                if is_meal_confirmation(question_text):
                    entry = pending_meal.get("entry") or {}
                    try:
                        meal_logger.insert_entry(entry)
                    except Exception as exc:
                        complete_response(f"I couldn't save that meal: {exc}")
                        return
                    st.session_state.pop("pending_meal_entry", None)
                    confirmation_text = (
                        "Meal saved to your log! Let me know if you'd like to add anything else."
                    )
                    complete_response(confirmation_text, metadata={"meal_entry": entry})
                elif is_meal_cancellation(question_text):
                    st.session_state.pop("pending_meal_entry", None)
                    complete_response("No problem—I've discarded that meal entry.")
                else:
                    complete_response(
                        "I still need a clear **confirm meal entry** or **cancel meal entry** before proceeding."
                    )
            return

        intent = classify_user_request(question_text) if question_text else "GENERAL"

        if intent == "LOG":
            st.session_state.pending_meal_entry = {
                "stage": "awaiting_details",
                "description": question_text,
            }
            complete_response(meal_logger.clarification_prompt())
            return

        if intent == "QUERY":
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

        complete_response(response_text, metadata)

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
        st.session_state.pop("pending_meal_entry", None)
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
