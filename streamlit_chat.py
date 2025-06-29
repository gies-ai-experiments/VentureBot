import streamlit as st
import requests
import json
import time
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="ADK Agent Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
# Use environment variable for backend URL, fallback to localhost
ADK_SERVER_URL = os.getenv("ADK_BACKEND_URL", "http://localhost:8000")

APP_NAME = "managerA"

def create_session(user_id, session_id, initial_state=None):
    """Create a new ADK session"""
    if initial_state is None:
        initial_state = {
            "initialized": True,
            "timestamp": datetime.now().isoformat()
        }
    
    url = f"{ADK_SERVER_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"
    payload = {"state": initial_state}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code in [200, 201, 409]:  # 409 means session already exists
            return True, "Session created successfully"
        else:
            return False, f"Failed to create session: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def send_message_stream(user_id, session_id, message):
    """Send a message to the ADK agent using streaming SSE"""
    url = f"{ADK_SERVER_URL}/run_sse"
    payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "body": message,
        "new_message": {
            "role": "user",
            "parts": [{
                "text": message
            }]
        },
        "streaming": True
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        if response.status_code == 200:
            return True, response
        else:
            return False, f"API Error: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def parse_sse_stream(response):
    """Parse Server-Sent Events stream"""
    events = []
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                events.append(event_data)
            except json.JSONDecodeError:
                continue
    return events

def parse_agent_response(events):
    """Parse ADK events to extract agent response"""
    agent_response = ""
    function_calls = []
    
    for event in events:
        if event.get("content") and event["content"].get("parts"):
            for part in event["content"]["parts"]:
                # Extract text responses from model
                if part.get("text") and event["content"].get("role") == "model":
                    agent_response += part["text"]
                
                # Track function calls
                elif part.get("functionCall"):
                    func_call = part["functionCall"]
                    function_calls.append(f"🔧 Called: {func_call.get('name')}({json.dumps(func_call.get('args', {}))})")
    
    return agent_response.strip(), function_calls

def initialize_session():
    """Initialize session state variables"""
    if "session_created" not in st.session_state:
        st.session_state.session_created = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"

def main():
    st.title("🤖 Venture Bot")
    
    # Initialize session
    initialize_session()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        st.write(f"**Server:** {ADK_SERVER_URL}")
        st.write(f"**Agent:** {APP_NAME}")
        st.write(f"**User ID:** {st.session_state.user_id}")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.session_state.session_created = False
            st.session_state.user_id = f"user_{int(time.time())}"
            st.session_state.session_id = f"session_{int(time.time())}"
            st.rerun()
        
        # Session status
        if st.session_state.session_created:
            st.success("✅ Session Active")
        else:
            st.warning("⏳ Creating Session...")
    
    # Create session if not already created
    if not st.session_state.session_created:
        with st.spinner("Creating session and connecting to Venture Bot..."):
            success, message = create_session(st.session_state.user_id, st.session_state.session_id)
            if success:
                st.session_state.session_created = True
                
                # Send greeting to trigger onboarding agent
                success, response = send_message_stream(
                    st.session_state.user_id,
                    st.session_state.session_id,
                    "hi"  # Send greeting to trigger onboarding
                )
                
                if success:
                    # Process the onboarding response
                    streaming_text = ""
                    try:
                        for line in response.iter_lines(decode_unicode=True):
                            if line.startswith('data: '):
                                try:
                                    event_data = json.loads(line[6:])
                                    if event_data.get("content") and event_data["content"].get("parts"):
                                        for part in event_data["content"]["parts"]:
                                            if part.get("text") and event_data["content"].get("role") == "model":
                                                new_text = part["text"]
                                                if event_data.get("partial", False):
                                                    streaming_text += new_text
                                                else:
                                                    streaming_text = new_text
                                except json.JSONDecodeError:
                                    continue
                        
                        # Add onboarding response to messages
                        if streaming_text.strip():
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": streaming_text.strip(),
                                "timestamp": datetime.now()
                            })
                    except Exception as e:
                        st.error(f"Failed to get onboarding response: {str(e)}")
                
                st.rerun()
            else:
                st.error(f"Failed to create session: {message}")
                st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here...", disabled=not st.session_state.session_created):
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        }
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Send message to ADK agent with streaming
        with st.chat_message("assistant"):
            # Create placeholder for streaming response
            response_placeholder = st.empty()
            
            success, response = send_message_stream(
                st.session_state.user_id,
                st.session_state.session_id,
                prompt
            )
            
            if success:
                # Initialize streaming response
                streaming_text = ""
                response_placeholder.write("🤔 Agent is thinking...")
                
                try:
                    # Process SSE stream in real-time
                    for line in response.iter_lines(decode_unicode=True):
                        if line.startswith('data: '):
                            try:
                                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                                
                                # Extract text from the event
                                if event_data.get("content") and event_data["content"].get("parts"):
                                    for part in event_data["content"]["parts"]:
                                        if part.get("text") and event_data["content"].get("role") == "model":
                                            new_text = part["text"]
                                            # For partial responses, append; for complete responses, use as-is
                                            if event_data.get("partial", False):
                                                streaming_text += new_text
                                            else:
                                                streaming_text = new_text  # Complete response
                                            # Update the display in real-time
                                            response_placeholder.write(streaming_text)
                                            
                            except json.JSONDecodeError:
                                continue
                    
                    # Final response
                    final_response = streaming_text.strip() if streaming_text.strip() else "I processed your request but have no text response."
                    response_placeholder.write(final_response)
                    
                    # Add assistant message to history
                    assistant_message = {
                        "role": "assistant",
                        "content": final_response,
                        "timestamp": datetime.now()
                    }
                    st.session_state.messages.append(assistant_message)
                    
                except Exception as e:
                    error_msg = f"❌ Streaming Error: {str(e)}"
                    response_placeholder.error(error_msg)
                    
                    # Add error message to history
                    error_message = {
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now()
                    }
                    st.session_state.messages.append(error_message)
            
            else:
                error_msg = f"❌ Error: {response}"
                st.error(error_msg)
                
                # Add error message to history
                error_message = {
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now()
                }
                st.session_state.messages.append(error_message)

if __name__ == "__main__":
    main() 