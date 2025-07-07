import streamlit as st
import requests
import json
import time
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="VentureBots - AI Entrepreneurship Coach",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, modern CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #2563eb;
        --primary-light: #3b82f6;
        --success: #10b981;
        --error: #ef4444;
        --warning: #f59e0b;
        --background: #0f172a;
        --surface: #1e293b;
        --surface-light: #334155;
        --text: #f8fafc;
        --text-muted: #64748b;
        --border: #334155;
        --shadow: rgba(0, 0, 0, 0.25);
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: var(--background);
        color: var(--text);
    }
    
    .stApp > header, #MainMenu, footer {
        display: none !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--primary), var(--success));
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px var(--shadow);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
    }
    
    .status-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .status-connected {
        border-left: 4px solid var(--success);
    }
    
    .status-error {
        border-left: 4px solid var(--error);
    }
    
    .stChatMessage {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 2px 8px var(--shadow) !important;
    }
    
    .stChatMessage[data-testid="stChatMessage-user"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
        border: none !important;
        margin-left: 2rem !important;
    }
    
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background: var(--surface) !important;
        border-left: 4px solid var(--success) !important;
        margin-right: 2rem !important;
    }
    
    .stChatMessage p,
    .stChatMessage div,
    .stChatMessage span {
        color: var(--text) !important;
        line-height: 1.6;
    }
    
    .stChatMessage[data-testid="stChatMessage-user"] p,
    .stChatMessage[data-testid="stChatMessage-user"] div,
    .stChatMessage[data-testid="stChatMessage-user"] span {
        color: white !important;
    }
    
    div[data-testid="stChatInput"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px var(--shadow) !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        background: var(--surface) !important;
        border: none !important;
        color: var(--text) !important;
        font-size: 1rem !important;
        padding: 1rem !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.8 !important;
    }
    
    div[data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--primary-light) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px var(--shadow) !important;
    }
    
    .stSidebar {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    .stSidebar .stMarkdown {
        color: var(--text) !important;
    }
    
    .stSuccess {
        background: var(--success) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    .stError {
        background: var(--error) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    .stWarning {
        background: var(--warning) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    .stInfo {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    .loading-dots {
        display: inline-block;
        position: relative;
        width: 64px;
        height: 20px;
    }
    
    .loading-dots div {
        position: absolute;
        top: 6px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary);
        animation: loading 1.2s linear infinite;
    }
    
    .loading-dots div:nth-child(1) { left: 8px; animation-delay: 0s; }
    .loading-dots div:nth-child(2) { left: 28px; animation-delay: -0.4s; }
    .loading-dots div:nth-child(3) { left: 48px; animation-delay: -0.8s; }
    
    @keyframes loading {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .stChatMessage {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        
        .stChatMessage[data-testid="stChatMessage-user"] {
            margin-left: 0.5rem !important;
        }
        
        .stChatMessage[data-testid="stChatMessage-assistant"] {
            margin-right: 0.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Configuration
ADK_SERVER_URL = os.getenv("ADK_BACKEND_URL", "http://localhost:8000")
APP_NAME = "manager"

def create_session(user_id, session_id):
    """Create a new ADK session"""
    initial_state = {
        "initialized": True,
        "timestamp": datetime.now().isoformat()
    }
    
    url = f"{ADK_SERVER_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"
    payload = {"state": initial_state}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code in [200, 201, 409]:
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
            "parts": [{"text": message}]
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

def show_connection_status():
    """Show connection status"""
    try:
        response = requests.get(f"{ADK_SERVER_URL}/docs", timeout=5)
        if response.status_code == 200:
            return "🟢 Connected", True
        else:
            return "🟡 Connection Issues", False
    except:
        return "🔴 Disconnected", False

def initialize_session():
    """Initialize session state"""
    if "session_created" not in st.session_state:
        st.session_state.session_created = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"

def main():
    # Initialize session
    initialize_session()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 VentureBots</h1>
        <p>AI Entrepreneurship Coach</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection status
    connection_status, is_connected = show_connection_status()
    status_class = "status-connected" if is_connected else "status-error"
    
    st.markdown(f"""
    <div class="status-card {status_class}">
        <div>{connection_status}</div>
        <div style="margin-left: auto; font-size: 0.9rem; color: var(--text-muted);">
            Session: {st.session_state.session_id[-6:]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create session if not already created
    if not st.session_state.session_created:
        with st.container():
            st.markdown("""
            <div class="status-card">
                <div class="loading-dots">
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                <div>Initializing your coaching session...</div>
            </div>
            """, unsafe_allow_html=True)
            
            success, message = create_session(st.session_state.user_id, st.session_state.session_id)
            
            if success:
                st.session_state.session_created = True
                
                # Send initial greeting
                success, response = send_message_stream(
                    st.session_state.user_id,
                    st.session_state.session_id,
                    "hi"
                )
                
                if success:
                    # Process onboarding response
                    streaming_text = ""
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
                    
                    # Add onboarding message
                    if streaming_text.strip():
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": streaming_text.strip(),
                            "timestamp": datetime.now()
                        })
                
                st.rerun()
            else:
                st.error(f"❌ Connection failed: {message}")
                if st.button("🔄 Retry"):
                    st.rerun()
                st.stop()
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input(
        "Share your entrepreneurship ideas or ask for coaching guidance...",
        disabled=not st.session_state.session_created
    ):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Send message and get response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # Show loading
            response_placeholder.markdown("""
            <div class="loading-dots">
                <div></div>
                <div></div>
                <div></div>
            </div>
            """, unsafe_allow_html=True)
            
            success, response = send_message_stream(
                st.session_state.user_id,
                st.session_state.session_id,
                prompt
            )
            
            if success:
                streaming_text = ""
                first_content = False
                
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            if event_data.get("content") and event_data["content"].get("parts"):
                                for part in event_data["content"]["parts"]:
                                    if part.get("text") and event_data["content"].get("role") == "model":
                                        new_text = part["text"]
                                        
                                        if not first_content:
                                            first_content = True
                                            response_placeholder.empty()
                                        
                                        if event_data.get("partial", False):
                                            streaming_text += new_text
                                        else:
                                            streaming_text = new_text
                                            
                                        response_placeholder.write(streaming_text)
                        except json.JSONDecodeError:
                            continue
                
                # Add response to messages
                final_response = streaming_text.strip() if streaming_text.strip() else "I processed your request but have no text response."
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response,
                    "timestamp": datetime.now()
                })
                
            else:
                response_placeholder.error(f"❌ Error: {response}")
                if st.button("🔄 Retry"):
                    st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎓 Session Info")
        st.write(f"**User ID:** `{st.session_state.user_id}`")
        st.write(f"**Session:** `{st.session_state.session_id}`")
        
        if st.session_state.messages:
            user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
            ai_msgs = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            st.write(f"**Messages:** {user_msgs} sent, {ai_msgs} received")
        
        st.divider()
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_created = False
            st.session_state.user_id = f"user_{int(time.time())}"
            st.session_state.session_id = f"session_{int(time.time())}"
            st.rerun()
        
        if st.button("💾 Export Chat", use_container_width=True):
            if st.session_state.messages:
                export_text = "\n".join([
                    f"**{msg['role'].title()}:** {msg['content']}\n"
                    for msg in st.session_state.messages
                ])
                st.download_button(
                    label="📥 Download",
                    data=export_text,
                    file_name=f"venturebot_chat_{st.session_state.session_id}.txt",
                    mime="text/plain"
                )
            else:
                st.info("No messages to export")

if __name__ == "__main__":
    main()