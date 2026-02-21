import streamlit as st
import requests
import time

API_URL = "http://localhost:8000/query"

# --- Page Config ---
st.set_page_config(
    page_title="Clearpath Support",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for unique dark theme ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        background: linear-gradient(145deg, #0a0a0f 0%, #111127 50%, #0d1117 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Hide default streamlit stuff */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Title area */
    .hero-title {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }

    .hero-sub {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
        font-weight: 300;
    }

    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    /* Message bubbles */
    .user-msg {
        background: linear-gradient(135deg, #1e3a5f, #1e2a4a);
        border: 1px solid #2d4a6f;
        border-radius: 18px 18px 4px 18px;
        padding: 14px 20px;
        margin: 8px 0;
        color: #e2e8f0;
        font-size: 0.92rem;
        line-height: 1.6;
        max-width: 85%;
        margin-left: auto;
        animation: slideInRight 0.3s ease;
    }

    .bot-msg {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #1f2937;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 20px;
        margin: 8px 0;
        color: #d1d5db;
        font-size: 0.92rem;
        line-height: 1.6;
        max-width: 85%;
        animation: slideInLeft 0.3s ease;
    }

    .msg-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        display: block;
    }

    .user-label { color: #60a5fa; }
    .bot-label { color: #a78bfa; }

    /* Debug panel */
    .debug-card {
        background: rgba(15, 15, 30, 0.8);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 6px 0;
        backdrop-filter: blur(10px);
    }

    .debug-title {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }

    .debug-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }

    .debug-key {
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 500;
    }

    .debug-val {
        font-size: 0.82rem;
        font-weight: 600;
    }

    .val-blue { color: #60a5fa; }
    .val-purple { color: #a78bfa; }
    .val-green { color: #34d399; }
    .val-amber { color: #fbbf24; }
    .val-red { color: #f87171; }

    /* Flag badges */
    .flag-badge {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #f87171;
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 20px;
        margin: 2px 4px 2px 0;
        font-weight: 500;
    }

    .no-flags {
        color: #34d399;
        font-size: 0.82rem;
    }

    /* Source cards */
    .source-card {
        background: rgba(30, 30, 50, 0.5);
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        font-size: 0.8rem;
    }

    .source-doc { color: #60a5fa; font-weight: 500; }
    .source-detail { color: #64748b; }

    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(15, 15, 35, 0.9) !important;
        border: 1px solid #2d3748 !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 14px 18px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.15) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #475569 !important;
    }

    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 28px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }

    /* Animations */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Divider */
    .subtle-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #1f2937, transparent);
        margin: 1rem 0;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34d399;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    .status-text {
        color: #64748b;
        font-size: 0.78rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: transparent !important;
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "debug_data" not in st.session_state:
    st.session_state.debug_data = []

# --- Header ---
st.markdown('<div class="hero-title">🧭 Clearpath Support</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">AI-powered assistant · Ask anything about Clearpath</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)

# --- Layout: Chat (left) + Debug (right) ---
chat_col, debug_col = st.columns([3, 1.2])

with chat_col:
    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f'''
                <div class="user-msg">
                    <span class="msg-label user-label">You</span>
                    {msg["content"]}
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div class="bot-msg">
                    <span class="msg-label bot-label">Clearpath AI</span>
                    {msg["content"]}
                </div>
            ''', unsafe_allow_html=True)

    st.markdown('<div style="height: 20px"></div>', unsafe_allow_html=True)

    # Input area
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Ask about Clearpath features, pricing, workflows...",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        # Call API
        payload = {"question": user_input.strip()}
        if st.session_state.conversation_id:
            payload["conversation_id"] = st.session_state.conversation_id

        try:
            response = requests.post(API_URL, json=payload, timeout=30)
            data = response.json()

            answer = data.get("answer", "No response received.")
            st.session_state.conversation_id = data.get("conversation_id")

            # Add bot response
            st.session_state.messages.append({"role": "assistant", "content": answer})

            # Store debug info
            metadata = data.get("metadata", {})
            sources = data.get("sources", [])
            st.session_state.debug_data.append({
                "query": user_input.strip(),
                "model": metadata.get("model_used", "—"),
                "classification": metadata.get("classification", "—"),
                "tokens_in": metadata.get("tokens", {}).get("input", 0),
                "tokens_out": metadata.get("tokens", {}).get("output", 0),
                "latency": metadata.get("latency_ms", 0),
                "chunks": metadata.get("chunks_retrieved", 0),
                "flags": metadata.get("evaluator_flags", []),
                "sources": sources
            })

        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ Cannot connect to the backend. Make sure the FastAPI server is running on port 8000."
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Error: {str(e)}"
            })

        st.rerun()

# --- Debug Panel ---
with debug_col:
    st.markdown(f'''
        <div style="padding-top: 8px;">
            <span class="status-dot"></span>
            <span class="status-text">Backend {'connected' if st.session_state.conversation_id else 'waiting'}</span>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.debug_data:
        latest = st.session_state.debug_data[-1]

        st.markdown(f'''
            <div class="debug-card">
                <div class="debug-title">Latest Request</div>
                <div class="debug-row">
                    <span class="debug-key">Model</span>
                    <span class="debug-val val-blue">{latest["model"]}</span>
                </div>
                <div class="debug-row">
                    <span class="debug-key">Classification</span>
                    <span class="debug-val val-purple">{latest["classification"]}</span>
                </div>
                <div class="debug-row">
                    <span class="debug-key">Latency</span>
                    <span class="debug-val val-green">{latest["latency"]} ms</span>
                </div>
                <div class="debug-row">
                    <span class="debug-key">Chunks</span>
                    <span class="debug-val val-blue">{latest["chunks"]}</span>
                </div>
                <div class="debug-row">
                    <span class="debug-key">Tokens In</span>
                    <span class="debug-val val-amber">{latest["tokens_in"]}</span>
                </div>
                <div class="debug-row">
                    <span class="debug-key">Tokens Out</span>
                    <span class="debug-val val-amber">{latest["tokens_out"]}</span>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # Evaluator flags
        flags = latest["flags"]
        if flags:
            flags_html = "".join([f'<span class="flag-badge">{f}</span>' for f in flags])
            st.markdown(f'''
                <div class="debug-card">
                    <div class="debug-title">Evaluator Flags</div>
                    {flags_html}
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div class="debug-card">
                    <div class="debug-title">Evaluator Flags</div>
                    <span class="no-flags">✓ No flags raised</span>
                </div>
            ''', unsafe_allow_html=True)

        # Sources
        sources = latest["sources"]
        if sources:
            sources_html = ""
            for s in sources:
                sources_html += f'''
                    <div class="source-card">
                        <span class="source-doc">📄 {s["document"]}</span><br>
                        <span class="source-detail">Page {s["page"]} · Score: {s["relevance_score"]}</span>
                    </div>
                '''
            st.markdown(f'''
                <div class="debug-card">
                    <div class="debug-title">Sources</div>
                    {sources_html}
                </div>
            ''', unsafe_allow_html=True)

    else:
        st.markdown('''
            <div class="debug-card">
                <div class="debug-title">Debug Panel</div>
                <div style="color: #475569; font-size: 0.82rem; padding: 8px 0;">
                    Send a message to see request details here.
                </div>
            </div>
        ''', unsafe_allow_html=True)

# --- Footer ---
st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)
st.markdown('''
    <div style="text-align: center; padding: 0.5rem 0;">
        <span style="color: #334155; font-size: 0.72rem;">
            Clearpath Support AI · Powered by Groq + FAISS + sentence-transformers
        </span>
    </div>
''', unsafe_allow_html=True)
