import streamlit as st
from datetime import datetime
from config import Config
from openai import OpenAI

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
if prompt := st.chat_input("Ask me anything about vegan nutrition..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Generate response using the model
        try:
            response = client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a knowledgeable and friendly Vegan Nutritionist Assistant. 
                        Provide helpful, accurate information about vegan nutrition, meal planning, 
                        and answer questions about plant-based diets. Be concise but thorough in your responses.
                        If asked about specific foods, include nutritional information when relevant.
                        If the question is not related to veganism or nutrition, politely decline to answer."""
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