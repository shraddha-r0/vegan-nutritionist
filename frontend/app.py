import streamlit as st
from datetime import datetime
from config import Config
from openai import OpenAI
import requests
from typing import List, Dict, Any, Optional
import json

# Initialize the OpenAI client with Hugging Face router
client = OpenAI(
    base_url=Config.HUGGINGFACE_BASE_URL,
    api_key=Config.HUGGINGFACE_API_KEY
)

# Set page config
st.set_page_config(
    page_title="🍽️ Vegan Nutritionist Assistant",
    page_icon="🥗",
    layout="wide"
)

# Initialize API call history
if "api_calls" not in st.session_state:
    st.session_state.api_calls = []

def call_meal_api(endpoint: str, method: str = "get", data: dict = None) -> Optional[Dict[str, Any]]:
    """Helper function to make API calls to the FastAPI backend"""
    url = f"{Config.FASTAPI_URL}{endpoint}"
    api_call = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "endpoint": endpoint,
        "method": method.upper(),
        "request": data,
        "response": None,
        "status": "success"
    }
    
    try:
        if method.lower() == "get":
            response = requests.get(url, params=data)
        elif method.lower() == "post":
            response = requests.post(url, json=data)
        response.raise_for_status()
        
        api_call["response"] = response.json()
        return api_call["response"]
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        api_call["status"] = "error"
        api_call["response"] = {"error": error_msg}
        st.error(f"Error calling API: {error_msg}")
        return None
    finally:
        # Add the API call to the session state (keep last 10 calls)
        st.session_state.api_calls = [api_call] + st.session_state.api_calls[:9]

# Debug panel in the sidebar
with st.sidebar:
    st.header("🔧 API Debug Panel")
    
    if st.checkbox("Show API Calls", value=False):
        st.subheader("Recent API Calls")
        
        if not st.session_state.api_calls:
            st.info("No API calls have been made yet.")
        else:
            for i, call in enumerate(st.session_state.api_calls):
                with st.expander(f"{call['timestamp']} - {call['method']} {call['endpoint']} ({call['status']})", expanded=False):
                    st.write("**Request Body:**")
                    st.json(call.get("request") or {})
                    
                    st.write("**Response:")
                    st.json(call.get("response") or {})
                    
                    if call["status"] == "error":
                        st.error("This call resulted in an error")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi there! I'm your Vegan Nutritionist Assistant. How can I help you with your vegan diet today?"
        }
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
# Update the chat interface section
if prompt := st.chat_input("Ask me anything about your meals or nutrition..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if the user is asking about their meals
    is_meal_query = any(keyword in prompt.lower() for keyword in 
                       ["my meals", "what i ate", "meal history", "what did i eat"])
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            if is_meal_query:
                # Get meal data from the API
                meals = call_meal_api("/meals/", "get")
                
                if meals:
                    # Format the meal data
                    formatted_meals = []
                    for meal in meals:
                        date = meal.get('date', 'Unknown date')
                        meal_type = meal.get('meal_type', 'meal').capitalize()
                        desc = meal.get('description', 'No description')
                        cals = meal.get('calories', 0)
                        formatted_meals.append(
                            f"**{date} - {meal_type}**: {desc} ({cals} calories)"
                        )
                    
                    if formatted_meals:
                        full_response = "Here are your recent meals:\n\n" + "\n\n".join(formatted_meals)
                    else:
                        full_response = "I couldn't find any meals in your history."
                else:
                    full_response = "I couldn't retrieve your meal history. The meal service might be unavailable."
                
                message_placeholder.markdown(full_response)
            else:
                # Regular chat response for non-meal queries
                response = client.chat.completions.create(
                    model=Config.MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a knowledgeable and friendly Vegan Nutritionist Assistant. 
                            Provide helpful, accurate information about vegan nutrition, meal planning, 
                            and answer questions about plant-based diets. Be concise but thorough in your responses.
                            If asked about specific foods, include nutritional information when relevant.
                            If the question is not related to veganism or nutrition, politely decline to answer.
                            If the user asks about their meal history, let them know you can show their recent meals."""
                        }
                    ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Stream the response
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
        except Exception as e:
            full_response = f"Sorry, I encountered an error: {str(e)}"
            message_placeholder.error(full_response)
    
    # Add assistant's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Limit chat history to avoid context window issues
    if len(st.session_state.messages) > 10:
        st.session_state.messages = st.session_state.messages[-10:]