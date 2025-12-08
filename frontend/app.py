import streamlit as st

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
if prompt := st.chat_input("Ask me about vegan nutrition..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        response = "I'm here to help with vegan nutrition questions. Please ask me anything about plant-based diets, recipes, or nutrition."
        st.markdown(response)
    
    # Add assistant's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Limit chat history
    if len(st.session_state.messages) > 10:
        st.session_state.messages = st.session_state.messages[-10:]