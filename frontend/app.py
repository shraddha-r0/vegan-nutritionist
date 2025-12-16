import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from config import Config
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

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
                        with st.expander("Details"):
                            st.json(message["metadata"])
        if st.session_state.generating_response:
            with st.chat_message("assistant"):
                assistant_placeholder = st.empty()
                assistant_placeholder.caption("Analyzing your request...")

    if st.session_state.generating_response:
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful vegan nutritionist assistant. "
                "You help users track and understand their nutritional intake. "
                "Be concise and focus on providing accurate, actionable advice.\n\n"
                "Database schema:\n"
                f"{Config.load_database_schema_text()}\n\n"
                "Nutrition profile:\n"
                f"{Config.load_nutrition_profile_text()}"
            )
        }
        
        api_messages = [system_message] + [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.messages 
            if msg["role"] != "system"
        ][-MAX_HISTORY:]

        response = get_chat_completion(api_messages)
        if assistant_placeholder is not None:
            assistant_placeholder.markdown(response)
        else:
            with st.chat_message("assistant"):
                st.markdown(response)
        
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        }
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
