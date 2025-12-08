import os
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
FASTAPI_URL = "http://localhost:8000"  # Update if your FastAPI server is running elsewhere

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Set page config
st.set_page_config(
    page_title="🍽️ Vegan Nutritionist Assistant",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("🍽️ Vegan Nutritionist Assistant")
st.markdown("""
Ask me anything about your meals or request to add new ones! For example:
- "Show me all meals from yesterday"
- "Add a breakfast with 2 bananas and oatmeal"
- "What did I eat for dinner last Friday?"
- "Show me my nutrition summary for this week"
""")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Configuration
    st.subheader("API Settings")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Get your API key from https://platform.openai.com/account/api-keys"
    )
    
    # Model Configuration
    st.subheader("Model Settings")
    model_name = st.selectbox(
        "Model",
        ["gpt-3.5-turbo", "gpt-4"],
        index=0,
        help="Choose the OpenAI model to use"
    )
    
    # Temperature slider for creativity
    temperature = st.slider(
        "Creativity",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make the output more random, lower values more deterministic"
    )
    
    # FastAPI URL
    st.subheader("Backend Settings")
    fastapi_url = st.text_input(
        "FastAPI URL",
        value=FASTAPI_URL,
        help="URL where your FastAPI backend is running"
    )
    
    # Health check
    if st.button("Check Backend Connection"):
        try:
            response = requests.get(f"{fastapi_url}/health")
            if response.status_code == 200:
                st.success("✅ Backend is connected and healthy!")
            else:
                st.error(f"❌ Backend returned status code: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Could not connect to backend: {str(e)}")

# Function to call FastAPI backend
def call_fastapi_endpoint(endpoint: str, method: str = "get", data: dict = None) -> Optional[Dict[str, Any]]:
    """Helper function to make API calls to the FastAPI backend"""
    url = f"{FASTAPI_URL}{endpoint}"
    try:
        if method.lower() == "get":
            response = requests.get(url, params=data)
        elif method.lower() == "post":
            response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def generate_sql(natural_language: str, schema_info: str) -> str:
    """
    Generate SQL from natural language using OpenAI's API
    
    Args:
        natural_language: The user's query in natural language
        schema_info: Information about the database schema
        
    Returns:
        str: Generated SQL query
    """
    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar")
        return ""
        
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_api_key)
    
    prompt = f"""
    You are a helpful AI assistant that converts natural language to SQL.
    
    Database schema:
    {schema_info}
    
    Important notes:
    - Use SQLite syntax
    - Always use parameterized queries
    - Only query tables and columns that exist in the schema
    - For dates, use the 'date' function for comparisons
    - For times, use the 'time' function for comparisons
    
    Convert the following natural language query to SQL:
    ""{natural_language}""
    
    Return ONLY the SQL query, nothing else. Do not include any explanations or markdown formatting.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts natural language to SQL."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return ""

def handle_natural_language_query(query: str) -> str:
    """
    Process a natural language query and return results
    """
    # Database schema information
    schema_info = """
    Table: meals
    - id: int (primary key)
    - date: date (format: YYYY-MM-DD)
    - time: time (format: HH:MM:SS)
    - meal_type: str (e.g., "Breakfast", "Lunch", "Dinner", "Snack")
    - description: str
    - calories: float
    - protein_g: float
    - carbs_g: float
    - fat_g: float
    - fiber_g: float
    - sugar_g: float
    - sodium_mg: float
    - cholesterol_mg: float
    - meal_source: str (e.g., "Home", "Restaurant")
    - notes: str
    """
    
    # Generate SQL from natural language
    with st.spinner("Analyzing your request..."):
        sql_query = generate_sql(query, schema_info)
        
        if not sql_query:
            return "I couldn't generate a valid query for your request. Please try rephrasing."
        
        # Execute the query
        result = call_fastapi_endpoint(
            "/query",
            "post",
            {"query": sql_query}
        )
        
        if not result:
            return "I couldn't get any results for your query. Please try again."
            
        # Convert to DataFrame for better display
        if isinstance(result, list):
            df = pd.DataFrame(result)
            
            # If we have date and time columns, combine them for better display
            if 'date' in df.columns and 'time' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                df = df.sort_values('datetime', ascending=False)
                
                # Show a time series chart for numeric columns
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                if len(numeric_cols) > 0 and 'datetime' in df.columns:
                    st.subheader("📊 Nutrition Over Time")
                    for col in numeric_cols:
                        if col != 'id':  # Skip ID column
                            fig = px.line(
                                df, 
                                x='datetime', 
                                y=col,
                                title=f"{col} Over Time",
                                labels={'datetime': 'Date', col: col}
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            # Show the data in a table
            st.subheader("📋 Query Results")
            st.dataframe(df, use_container_width=True)
            
            # Add some basic statistics
            if not df.empty:
                st.subheader("📊 Summary Statistics")
                st.dataframe(df.describe(), use_container_width=True)
                
                # Show a pie chart of meal types if available
                if 'meal_type' in df.columns:
                    st.subheader("🍽️ Meal Type Distribution")
                    fig = px.pie(
                        df,
                        names='meal_type',
                        title="Meal Type Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            return f"Found {len(df)} results for your query."
        else:
            # If the result isn't a list, just return it as a string
            return str(result)

# Function to add a new meal
def add_meal_ui():
    """UI for adding a new meal"""
    with st.expander("➕ Add New Meal", expanded=False):
        with st.form("add_meal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                meal_date = st.date_input("Date", value=datetime.now())
                meal_time = st.time_input("Time", value=datetime.now().time())
                meal_type = st.selectbox(
                    "Meal Type",
                    ["Breakfast", "Lunch", "Dinner", "Snack", "Other"]
                )
                meal_source = st.selectbox(
                    "Source",
                    ["Home", "Restaurant", "Takeout", "Other"]
                )
            
            with col2:
                description = st.text_area("Description", placeholder="What did you eat?")
                notes = st.text_area("Notes (Optional)", placeholder="Any additional notes...")
            
            # Nutrition Information
            st.subheader("Nutrition Information")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                calories = st.number_input("Calories", min_value=0.0, step=1.0, value=0.0)
                protein = st.number_input("Protein (g)", min_value=0.0, step=0.1, value=0.0)
            with col2:
                carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.1, value=0.0)
                fat = st.number_input("Fat (g)", min_value=0.0, step=0.1, value=0.0)
            with col3:
                fiber = st.number_input("Fiber (g)", min_value=0.0, step=0.1, value=0.0)
                sugar = st.number_input("Sugar (g)", min_value=0.0, step=0.1, value=0.0)
            with col4:
                sodium = st.number_input("Sodium (mg)", min_value=0, step=1, value=0)
                cholesterol = st.number_input("Cholesterol (mg)", min_value=0, step=1, value=0)
            
            submitted = st.form_submit_button("Save Meal")
            
            if submitted:
                meal_data = {
                    "date": str(meal_date),
                    "time": str(meal_time),
                    "meal_type": meal_type,
                    "description": description,
                    "calories": calories,
                    "protein_g": protein,
                    "carbs_g": carbs,
                    "fat_g": fat,
                    "fiber_g": fiber,
                    "sugar_g": sugar,
                    "sodium_mg": sodium,
                    "cholesterol_mg": cholesterol,
                    "meal_source": meal_source,
                    "notes": notes
                }
                
                # Call the API to add the meal
                result = call_fastapi_endpoint("/meals", "post", meal_data)
                
                if result:
                    st.success("✅ Meal added successfully!")
                else:
                    st.error("❌ Failed to add meal. Please try again.")

# Main app layout
def main():
    # Add a new meal section
    add_meal_ui()
    
    # Chat interface
    st.subheader("💬 Chat with your Nutrition Assistant")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask me about your meals..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process the query and get response
        with st.chat_message("assistant"):
            response = handle_natural_language_query(user_input)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
