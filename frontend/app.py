import streamlit as st
import requests
import uuid
import time

# --- Page Config ---
st.set_page_config(
    page_title="Clearpath Assistant",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Configuration ---
API_URL = "http://localhost:8000/query"

# --- Custom Styling (The WOW Factor) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;600&display=swap');

    :root {
        --bg-color: #0d0e12;
        --card-bg: rgba(23, 25, 35, 0.7);
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --border-color: rgba(255, 255, 255, 0.08);
    }

    /* Global Overrides */
    .stApp {
        background: radial-gradient(circle at top right, #1a1b26, #0d0e12);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    [data-testid="stHeader"] { background: transparent; }

    /* Custom Header */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .brand-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Message Bubbles */
    .chat-bubble {
        padding: 1rem 1.25rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 85%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid var(--border-color);
        animation: fadeIn 0.4s ease-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-bubble {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        align-self: flex-end;
        margin-left: auto;
        color: white;
        border-bottom-right-radius: 4px;
    }

    .assistant-bubble {
        background: var(--card-bg);
        border-bottom-left-radius: 4px;
        backdrop-filter: blur(12px);
    }

    .bubble-header {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
        opacity: 0.8;
    }

    /* Debug Cards */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(20px);
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stat-value {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .tag-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }
    .tag-purple { background: rgba(139, 92, 246, 0.15); color: #a78bfa; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }
    .tag-green { background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }

    /* Hide standard chat elements for custom look */
    .stChatMessage { display: none !important; }

</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# --- Main UI ---
st.markdown('''
<div class="header-container">
    <div class="brand-title">🧭 CLEARPATH</div>
    <div style="display: flex; gap: 1rem; align-items: center;">
        <span class="tag-green">● SYSTEM LIVE</span>
        <span style="color: #64748b; font-size: 0.8rem;">Build 2.0.4</span>
    </div>
</div>
''', unsafe_allow_html=True)

col1, col2 = st.columns([2.5, 1], gap="large")

with col1:
    # Message Display
    chat_placeholder = st.container()
    
    with chat_placeholder:
        for msg in st.session_state.messages:
            bubble_type = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
            label = "Human" if msg["role"] == "user" else "Assistant"
            
            st.markdown(f'''
            <div class="chat-bubble {bubble_type}">
                <div class="bubble-header">{label}</div>
                {msg["content"]}
            </div>
            ''', unsafe_allow_html=True)

    # Simple space to keep input at bottom
    st.markdown('<div style="height: 100px"></div>', unsafe_allow_html=True)

    # Modern Chat Input
    if prompt := st.chat_input("Ask about enterprise compliance, service logs, or workflows..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display immediately
        with chat_placeholder:
             st.markdown(f'''
            <div class="chat-bubble user-bubble">
                <div class="bubble-header">Human</div>
                {prompt}
            </div>
            ''', unsafe_allow_html=True)

        with st.spinner("Processing deep retrieval..."):
            try:
                payload = {
                    "question": prompt,
                    "conversation_id": st.session_state.conversation_id
                }
                response = requests.post(API_URL, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.last_response = data
                    answer = data["answer"]
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.rerun()
                else:
                    st.error(f"API Error: {response.status_code}")
            except Exception as e:
                st.error(f"Gateway Error: {str(e)}")

with col2:
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-title" style="font-size: 1.2rem; margin-bottom: 1rem;">INSIGHTS</div>', unsafe_allow_html=True)
    
    if st.session_state.last_response:
        res = st.session_state.last_response
        meta = res["metadata"]
        
        # Performance Card
        st.markdown(f'''
        <div class="glass-card">
            <div class="stat-label">Model Engine</div>
            <div class="stat-value">{meta['model_used']}</div>
            <div style="display: flex; gap: 0.5rem;">
                <span class="tag-blue">{meta['classification'].upper()}</span>
                <span class="tag-purple">{meta['latency_ms']} MS</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Context Card
        st.markdown(f'''
        <div class="glass-card">
            <div class="stat-label">Token Consumption</div>
            <div class="stat-value">Σ {meta['tokens']['input'] + meta['tokens']['output']}</div>
            <div style="font-size: 0.8rem; color: #64748b;">
                Input: {meta['tokens']['input']} | Output: {meta['tokens']['output']}
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # RAG Sources
        with st.expander("📚 SOURCE CITATIONS", expanded=True):
            if res["sources"]:
                for s in res["sources"]:
                    st.markdown(f"""
                    <div style="padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 8px;">
                        <span style="color: #60a5fa; font-weight: 600; font-size: 0.85rem;">{s['document']}</span><br/>
                        <span style="color: #94a3b8; font-size: 0.75rem;">Page {s['page']} · Relevance: {int(s['relevance_score']*100)}%</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No external sources cited for this response.")

        # Evaluator Flags
        if meta.get("evaluator_flags"):
            st.markdown('<div class="stat-label" style="margin-top: 1rem;">SAFETY ALERTS</div>', unsafe_allow_html=True)
            for flag in meta["evaluator_flags"]:
                st.error(f"⚠️ {flag.replace('_', ' ').upper()}")
    else:
        st.markdown('''
        <div class="glass-card" style="opacity: 0.5;">
            <div class="stat-label">Telemetry Offline</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 5px;">
                Citations and engine metadata will populate here once active.
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown('''
<div style="position: fixed; bottom: 10px; right: 20px; color: #475569; font-size: 0.7rem; letter-spacing: 0.1em;">
    CLEARPATH V2.0 // RAG OPS // AI MODULES ACTIVE
</div>
''', unsafe_allow_html=True)
