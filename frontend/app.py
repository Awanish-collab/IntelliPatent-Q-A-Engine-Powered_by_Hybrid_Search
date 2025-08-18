import os
import requests
import streamlit as st
from datetime import datetime
import time

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/search")

# Page configuration with custom styling
st.set_page_config(
    page_title="IntelliPatent Q&A Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 1.2rem 1.8rem;
        border-radius: 18px 18px 4px 18px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 3px 12px rgba(99, 102, 241, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.2rem 1.8rem;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 0;
        color: #1e293b;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Status indicators */
    .status-success {
        background-color: #f0f9ff;
        border: 1px solid #0ea5e9;
        color: #0c4a6e;
        padding: 0.875rem 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border-left: 4px solid #0ea5e9;
    }
    
    .status-info {
        background-color: #fefce8;
        border: 1px solid #eab308;
        color: #713f12;
        padding: 0.875rem 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border-left: 4px solid #eab308;
    }
    
    .status-warning {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        color: #7f1d1d;
        padding: 0.875rem 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border-left: 4px solid #ef4444;
    }
    
    /* Patent result cards */
    .patent-card {
        background: white;
        border: 1px solid #e1e8ed;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .patent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .patent-title {
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .patent-number {
        color: #7f8c8d;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .loading-text {
        margin-left: 1rem;
        color: #667eea;
        font-weight: 500;
    }
    
    /* Statistics container */
    .stats-container {
        display: flex;
        justify-content: space-around;
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()

# Header section
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🔍 IntelliPatent Q&A Engine</h1>
    <p class="header-subtitle">Intelligent Patent Search & Analysis Platform</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with enhanced styling
with st.sidebar:
    st.markdown("### ⚙️ Search Configuration")
    
    # Search options
    hybrid = st.checkbox(
        "🔄 Enable Hybrid Search", 
        value=True,
        help="Combines keyword and semantic search for better results"
    )
    
    summary = st.checkbox(
        "📝 Generate Final Summary", 
        value=True,
        help="Creates a comprehensive summary of search results"
    )
    
    st.markdown("---")
    
    # Session statistics
    st.markdown("### 📊 Session Stats")
    session_duration = datetime.now() - st.session_state.session_start
    duration_minutes = int(session_duration.total_seconds() / 60)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", st.session_state.query_count)
    with col2:
        st.metric("Duration", f"{duration_minutes}m")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.history = []
        st.session_state.query_count = 0
        st.session_state.session_start = datetime.now()
        st.rerun()
    
    # API status
    # API status
    st.markdown("### 🔗 API Status")
    try:
        # Try to connect to the base server (root endpoint)
        base_url = API_URL.replace("/search", "")
        test_response = requests.get(base_url, timeout=3)
        
        if test_response.status_code == 200:
            st.success("✅ API Connected")
        elif test_response.status_code in [404, 405]:
            # Server is running but endpoint doesn't exist - that's fine
            st.success("✅ API Connected")
        else:
            st.warning(f"⚠️ API Responding (Status: {test_response.status_code})")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ API Unreachable")
    except requests.exceptions.Timeout:
        st.warning("⚠️ API Timeout")
    except Exception as e:
        st.error(f"❌ API Error: {str(e)}")

# Main chat interface
chat_container = st.container()

# Display chat history with Streamlit's native chat components
with chat_container:
    for i, turn in enumerate(st.session_state.history):
        with st.chat_message(turn["role"]):
            if turn["role"] == "user":
                st.markdown(f"**You:** {turn['content']}")
            else:
                st.markdown(turn["content"])

# Chat input
query = st.chat_input("💬 Enter your patent-related question here...")

# Process user query
if query:
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": query})
    st.session_state.query_count += 1

    # Prepare API history (Q/A pairs)
    api_history = []
    last_user_q = None
    for turn in st.session_state.history[:-1]:  # Exclude the current query
        if turn["role"] == "user":
            last_user_q = turn["content"]
        elif turn["role"] == "assistant" and last_user_q:
            api_history.append({"question": last_user_q, "answer": turn["content"]})
            last_user_q = None

    # Show loading spinner with custom styling
    with st.spinner("🔍 Analyzing patents and generating response..."):
        try:
            # Prepare API payload
            payload = {
                "query": query,
                "history": api_history,
                "hybrid": hybrid,
                "summary": summary
            }
            
            # Make API request
            response = requests.post(API_URL, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                reply_parts = []

                # Process response data
                # Related/unrelated indicator (only for follow-up queries)
                if len(api_history) > 0 and "related" in data:
                    if data["related"]:
                        reply_parts.append("🔗 **Follow-up Query Detected:** This question is related to your previous query and will build upon the context.")
                    else:
                        reply_parts.append("ℹ️ **New Topic Detected:** This appears to be a new question unrelated to previous queries.")

                # Add notes if present
                if "note" in data and data["note"]:
                    reply_parts.append(f"📋 **Note:** {data['note']}")

                # Handle different response types
                if "message" in data and "not relevant" in data["message"].lower():
                    reply_parts.append(f"🚫 **Query Not Relevant:** {data['message']}")
                elif "generic_answer" in data:
                    if "message" in data:
                        reply_parts.append(f"📋 **System Message:** {data['message']}")
                    reply_parts.append(f"🤖 **Response:** {data['generic_answer']}")
                elif summary and "live_summary" in data and data["live_summary"]:
                    reply_parts.append(f"📄 **Comprehensive Summary:**\n\n{data['live_summary']}")
                elif "results" in data and data["results"]:
                    reply_parts.append("🔍 **Patent Search Results:**\n")
                    for idx, doc in enumerate(data["results"], 1):
                        result_text = f"**#{idx} {doc.get('title', 'Untitled Patent')}**\n"
                        result_text += f"*Patent Number: {doc.get('patent_number', 'N/A')}*\n\n"
                        result_text += f"{doc.get('detailed_summary', 'No summary available.')}\n"
                        reply_parts.append(result_text)
                else:
                    reply_parts.append("🤔 **No Results Found:** No relevant patents were found for your query. Try rephrasing or using different keywords.")

                # Combine response parts
                reply_text = "\n\n".join([p for p in reply_parts if p.strip()])
                
                # Display the response with proper formatting
                with st.chat_message("assistant"):
                    st.markdown(reply_text)
                
                # Add to history
                st.session_state.history.append({"role": "assistant", "content": reply_text})

            else:
                error_msg = f"⚠️ **API Error**\n\nStatus Code: {response.status_code}\n\nDetails: {response.text}"
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.session_state.history.append({"role": "assistant", "content": error_msg})

        except requests.exceptions.Timeout:
            timeout_msg = "⏱️ **Request Timeout:** The search is taking longer than expected. Please try again or simplify your query."
            with st.chat_message("assistant"):
                st.warning(timeout_msg)
            st.session_state.history.append({"role": "assistant", "content": timeout_msg})
            
        except requests.exceptions.ConnectionError:
            connection_msg = "🔌 **Connection Error:** Unable to connect to the patent search API. Please check your connection and try again."
            with st.chat_message("assistant"):
                st.error(connection_msg)
            st.session_state.history.append({"role": "assistant", "content": connection_msg})
            
        except Exception as e:
            error_msg = f"❌ **Unexpected Error:** An unexpected error occurred: {str(e)}\n\nPlease try again or contact support if the issue persists."
            with st.chat_message("assistant"):
                st.error(error_msg)
            st.session_state.history.append({"role": "assistant", "content": error_msg})

    # Auto-scroll to bottom (trigger rerun to show new messages)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; font-size: 0.9rem; padding: 1rem;">
    🔍 <strong>IntelliPatent Q&A Engine</strong> | Powered by Advanced AI • Built for Patent Professionals
</div>
""", unsafe_allow_html=True)