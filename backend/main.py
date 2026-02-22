import time
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from typing import Optional

from retriever import retrieve
from router import classify_query
from llm import call_llm, call_llm_stream

from evaluator import evaluate
from memory import get_or_create_conversation, add_message, get_history
from config import LOGS_PATH, FAISS_INDEX_PATH

app = FastAPI(title="Clearpath Support Chatbot API")


# --- Request/Response Models ---

class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class TokenInfo(BaseModel):
    input: int
    output: int


class MetadataInfo(BaseModel):
    model_used: str
    classification: str
    tokens: TokenInfo
    latency_ms: int
    chunks_retrieved: int
    evaluator_flags: list


class SourceInfo(BaseModel):
    document: str
    page: int
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    metadata: MetadataInfo
    sources: list
    conversation_id: str


# --- Logging ---

def log_request(entry):
    """Append a log entry to logs.json"""
    logs = []
    if os.path.exists(LOGS_PATH):
        try:
            with open(LOGS_PATH, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs = []

    logs.append(entry)

    with open(LOGS_PATH, "w") as f:
        json.dump(logs, f, indent=2)


# --- Health Check ---

@app.get("/health")
def health():
    index_exists = os.path.exists(FAISS_INDEX_PATH)
    return {
        "status": "ok",
        "faiss_index_ready": index_exists
    }


# --- Main Endpoint ---

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    start_time = time.time()

    # Validate input
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    question = req.question.strip()

    try:
        # Get or create conversation
        conv_id, _ = get_or_create_conversation(req.conversation_id)

        # Classify the query (simple or complex)
        route = classify_query(question)
        classification = route["classification"]
        model_used = route["model_used"]
        requires_context = route.get("requires_context", True)

        # Retrieve relevant chunks ONLY if required
        chunks = []
        if requires_context:
            try:
                chunks = retrieve(question)
            except FileNotFoundError:
                chunks = []
        
        chunks_retrieved = len(chunks)

        # Get conversation history for context
        history = get_history(conv_id)

        # Call LLM
        llm_result = call_llm(question, chunks, model_used, history)
        answer = llm_result["answer"]
        tokens_input = llm_result["tokens_input"]
        tokens_output = llm_result["tokens_output"]

        # Evaluate the response
        flags = evaluate(answer, chunks, chunks_retrieved)

        # Format sources from retrieved chunks
        sources = []
        for chunk in chunks:
            sources.append({
                "document": chunk["document"],
                "page": chunk["page"],
                "relevance_score": chunk["relevance_score"]
            })

        # Save conversation history
        add_message(conv_id, "user", question)
        add_message(conv_id, "assistant", answer)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Log the request
        log_entry = {
            "query": question,
            "classification": classification,
            "model_used": model_used,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "latency_ms": latency_ms
        }
        log_request(log_entry)

        # Build response matching the exact API contract
        return QueryResponse(
            answer=answer,
            metadata=MetadataInfo(
                model_used=model_used,
                classification=classification,
                tokens=TokenInfo(input=tokens_input, output=tokens_output),
                latency_ms=latency_ms,
                chunks_retrieved=chunks_retrieved,
                evaluator_flags=flags
            ),
            sources=sources,
            conversation_id=conv_id
        )

    except HTTPException:
        raise
    except Exception as e:
        # Catch-all: return a safe response instead of crashing
        latency_ms = int((time.time() - start_time) * 1000)
        conv_id = req.conversation_id or "error"
        return QueryResponse(
            answer=f"Sorry, something went wrong: {str(e)}",
            metadata=MetadataInfo(
                model_used="none",
                classification="simple",
                tokens=TokenInfo(input=0, output=0),
                latency_ms=latency_ms,
                chunks_retrieved=0,
                evaluator_flags=[]
            ),
            sources=[],
            conversation_id=conv_id
        )


# --- Streaming Endpoint ---

@app.post("/query_stream")
def query_stream(req: QueryRequest):
    """
    Streaming version of the query endpoint.
    Yields tokens as they are generated.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    question = req.question.strip()
    conv_id, _ = get_or_create_conversation(req.conversation_id)
    route = classify_query(question)
    model_used = route["model_used"]
    requires_context = route.get("requires_context", True)
    
    chunks = []
    if requires_context:
        try:
            chunks = retrieve(question)
        except:
            chunks = []
    
    history = get_history(conv_id)

    def stream_generator():
        full_answer = ""
        for token in call_llm_stream(question, chunks, model_used, history):
            full_answer += token
            yield token
        
        # After streaming completes, we add to memory
        add_message(conv_id, "user", question)
        add_message(conv_id, "assistant", full_answer)

    return StreamingResponse(stream_generator(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
