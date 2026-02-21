import time
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from retriever import retrieve
from router import classify_query
from llm import call_llm
from evaluator import evaluate
from memory import get_or_create_conversation, add_message, get_history
from config import LOGS_PATH

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


# --- Main Endpoint ---

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    start_time = time.time()

    # Validate input
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    question = req.question.strip()

    # Step 1: Get or create conversation
    conv_id, _ = get_or_create_conversation(req.conversation_id)

    # Step 2: Classify the query (simple or complex)
    route = classify_query(question)
    classification = route["classification"]
    model_used = route["model_used"]

    # Step 3: Retrieve relevant chunks
    try:
        chunks = retrieve(question)
    except FileNotFoundError:
        # FAISS index not built yet
        chunks = []

    chunks_retrieved = len(chunks)

    # Step 4: Get conversation history for context
    history = get_history(conv_id)

    # Step 5: Call LLM
    llm_result = call_llm(question, chunks, model_used, history)
    answer = llm_result["answer"]
    tokens_input = llm_result["tokens_input"]
    tokens_output = llm_result["tokens_output"]

    # Step 6: Evaluate the response
    flags = evaluate(answer, chunks, chunks_retrieved)

    # Step 7: Format sources from retrieved chunks
    sources = []
    for chunk in chunks:
        sources.append({
            "document": chunk["document"],
            "page": chunk["page"],
            "relevance_score": chunk["relevance_score"]
        })

    # Step 8: Save conversation history
    add_message(conv_id, "user", question)
    add_message(conv_id, "assistant", answer)

    # Step 9: Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Step 10: Log the request
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
