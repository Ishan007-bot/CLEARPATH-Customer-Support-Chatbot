# 🧭 Clearpath Customer Support Chatbot

A production-grade, high-performance RAG-based customer support assistant for the **Clearpath** enterprise platform. 

This system uses a **dual-model strategy** and a **rule-based deterministic router** to provide fast, cost-effective, and highly accurate responses derived exclusively from internal PDF documentation.

---

## 🏗️ Architecture

```text
User Query → Rule-Based Router (Simple/Complex)
           → Vector Retrieval (FAISS + all-MiniLM-L6-v2) | Top-10 Chunks
           → Groq LLM (Llama 3.1 8B / Llama 3.3 70B)
           → Real-time Evaluator (Safety + Quality Flags)
           → Professional Streamlit UI / FastAPI JSON Response
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Vector Engine** | FAISS (Facebook AI Similarity Search) |
| **LLM Inference** | **Groq Cloud API** (Ultra-low latency inference) |
| **Embedding Model**| `sentence-transformers/all-MiniLM-L6-v2` |
| **Frontend** | Streamlit (Custom Professional Theme) |
| **PDF Extraction**| `pdfplumber` |

---

## 🚀 Getting Started

### 1. Requirements
*   Python 3.10+
*   Groq API Key (Free at [console.groq.com](https://console.groq.com))
*   ~4GB RAM (To load the embedding model locally)

### 2. Installation
```bash
# Clone the repo and navigate to project root
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Step 1: Document Ingestion (One-time)
Place your PDFs in the `docs/` folder and run:
```bash
cd backend
python ingest.py
```
*Creates `faiss_index.bin` and `metadata.pkl` in the backend folder.*

### 5. Step 2: Start Services
**Start Backend (Terminal 1):**
```bash
cd backend
python main.py
```
*API runs at `http://localhost:8000`*

**Start Frontend (Terminal 2):**
```bash
cd frontend
streamlit run app.py
```
*UI runs at `http://localhost:8501`*

### 6. Run Evaluation Tests
```bash
cd backend
python eval_harness.py
```

---

## 🧠 Groq Model Strategy

| Query Type | Model Used | Logic |
|------------|------------|-------|
| **Simple** | `llama-3.1-8b-instant` | Greetings, basic facts, short context. Focus on speed (<400ms). |
| **Complex**| `llama-3.3-70b-versatile`| Technical "How-to", comparisons, pricing, long multi-document context. |

---

## 🏆 Bonus Challenges Attempted

1.  **Conversation Memory**: Full multi-turn support via `memory.py`. Managed token-cost tradeoffs by limiting turns and reasoning about design in `Written_answers.md`.
2.  **Token-by-Token Streaming**: Implemented real-time response streaming in both the FastAPI backend (`/query_stream`) and Streamlit frontend for a premium user experience.
3.  **Custom Evaluation Harness**: Developed a standalone test suite (`eval_harness.py`) with 8 pre-defined queries covering multiple intent categories to verify system accuracy.
4.  **High-Fidelity Project UI**: Engineered a unique glassmorphism interface with real-time telemetry, model detection, and interactive source citations.
5.  **Deterministic Hybrid Routing**: Optimized for cost and speed by using a rule-based engine in `router.py` instead of an LLM for classification.

---

## ⚠️ Known Issues & Limitations

1.  **Cold Start Latency**: The very first query of a session may take 10-15 seconds longer because the `all-MiniLM-L6-v2` embedding model must be loaded into local RAM. Subsequent queries are near-instant.
2.  **RAM Consumption**: The embedding process requires approximately 2-4GB of available RAM. On low-memory systems, we have reduced the batch size to `8` in `ingest.py` to prevent crashes.
3.  **PDF-Only**: Currently supports `.pdf` files. `.docx` or `.txt` files in the docs folder will be ignored.
4.  **Deterministic Router**: While fast, the router depends on keywords. Highly nuanced "middle-ground" queries might occasionally be categorized as 'simple' when they require 'complex' reasoning.

---

## 📡 API Contract

### `POST /query`
**Request:**
```json
{
  "question": "What is the Clearpath SLA?",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "Clearpath provides a 99.9% uptime guarantee...",
  "metadata": {
    "model_used": "llama-3.3-70b-versatile",
    "classification": "complex",
    "tokens": { "input": 1450, "output": 210 },
    "latency_ms": 1120,
    "chunks_retrieved": 10,
    "evaluator_flags": []
  },
  "sources": [
    { "document": "SLA_Policy.pdf", "page": 1, "relevance_score": 0.89 }
  ],
  "conversation_id": "7488-abcd-..."
}
```
