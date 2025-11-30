import streamlit as st
import requests
import uuid

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/chat"
APP_TITLE = "Intelligent Calendar Assistant 📅"

st.set_page_config(page_title=APP_TITLE)
st.title(APP_TITLE)

# --- 1. Session Initialization and Memory ---
# Streamlit's session_state acts as the memory for the app.

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I am your Calendar Manager. How can I help you with your schedule?"}
    ]

# Initialize a unique session ID for the backend
# This ties the frontend conversation to the correct memory in your FastAPI agent.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())


# --- 2. Display Chat Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- 3. Handle User Input and Backend API Call ---

if prompt := st.chat_input("Ask me about scheduling or availability..."):
    # 3a. Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3b. Prepare the payload for the backend API
    payload = {
        "session_id": st.session_state["session_id"],
        "prompt": prompt
    }

    # 3c. Call the FastAPI backend
    with st.spinner("Thinking..."):
        try:
            response = requests.post(BACKEND_URL, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            # Extract the AI's response text
            assistant_response = response.json().get("response", "An unknown error occurred.")
            
        except requests.exceptions.ConnectionError:
            assistant_response = "Error: Could not connect to the backend API. Make sure your FastAPI server is running at **http://127.0.0.1:8000**."
        except requests.exceptions.RequestException as e:
            assistant_response = f"An API request error occurred: {e}"
        
    # 3d. Add assistant message to state and display
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Rerun the app to display the latest message
    st.rerun()