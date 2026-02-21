# Clearpath Customer Support Chatbot

A production-grade RAG-based customer support chatbot for the **Clearpath** SaaS platform. Built with FastAPI, FAISS, sentence-transformers, and Groq LLM.

## Architecture

```
User Query → Classification (simple/complex)
           → Embedding → FAISS Retrieval (top-5 chunks)
           → Groq LLM (llama-3.1-8b / llama-3.3-70b)
           → Evaluator (refusal / no_context / conflicting_sources)
           → JSON Response
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, FastAPI |
| Vector Store | FAISS |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq API (Llama 3.1 8B + Llama 3.3 70B) |
| PDF Processing | pdfplumber |
| Frontend | Streamlit |

## Project Structure

```
├── README.md
├── Written_answers.md
├── docs/                    # 30 Clearpath PDF documents
├── backend/
│   ├── config.py            # All configuration constants
│   ├── ingest.py            # PDF → chunks → embeddings → FAISS index
│   ├── retriever.py         # Query → top-K chunk retrieval
│   ├── router.py            # Rule-based query classification
│   ├── llm.py               # Groq API integration
│   ├── evaluator.py         # Output quality flags
│   ├── memory.py            # Conversation history store
│   ├── main.py              # FastAPI app (/query endpoint)
│   ├── eval_harness.py      # Test suite
│   └── requirements.txt     # Dependencies
└── frontend/
    └── app.py               # Streamlit chat UI
```

## Setup & Run

### 1. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Set Groq API key

```bash
# Linux/Mac
export GROQ_API_KEY="your-key-here"

# Windows PowerShell
$env:GROQ_API_KEY="your-key-here"
```

Get a free key at [console.groq.com](https://console.groq.com)

### 3. Build the FAISS index (one-time)

```bash
cd backend
python ingest.py
```

This processes all 30 PDFs and creates `faiss_index.bin` + `metadata.pkl`.

### 4. Start the backend

```bash
cd backend
python main.py
```

API runs at `http://localhost:8000`

### 5. Start the frontend

```bash
cd frontend
streamlit run app.py
```

UI runs at `http://localhost:8501`

### 6. Run evaluation tests

```bash
cd backend
python eval_harness.py
```

## API Contract

### POST /query

**Request:**
```json
{
  "question": "How do I set up custom workflows?",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "To set up custom workflows in Clearpath...",
  "metadata": {
    "model_used": "llama-3.3-70b-versatile",
    "classification": "complex",
    "tokens": {
      "input": 1250,
      "output": 180
    },
    "latency_ms": 1340,
    "chunks_retrieved": 5,
    "evaluator_flags": []
  },
  "sources": [
    {
      "document": "12_Custom_Workflows_Tutorial.pdf",
      "page": 2,
      "relevance_score": 0.7832
    }
  ],
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## Key Features

- **Deterministic routing**: Rule-based classification (no LLM for routing)
- **Dual model strategy**: Fast 8B model for simple queries, powerful 70B for complex ones
- **Evaluator flags**: Detects refusals, hallucination risk, and conflicting sources
- **Conversation memory**: Maintains last 5 turns per conversation
- **Source tracking**: Every answer cites document name, page, and relevance score
- **Request logging**: All queries logged to `logs.json` with full metadata
