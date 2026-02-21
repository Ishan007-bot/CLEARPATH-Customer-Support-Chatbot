"""
Retriever Module
================
Handles query-to-chunk retrieval using FAISS.

On each query:
1. Convert query text to an embedding
2. Search the FAISS index for top-K similar chunks
3. Return chunk text, document name, page number, and similarity score
"""

import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, METADATA_PATH, EMBEDDING_MODEL, TOP_K


# Load model, index, and metadata once at module level
_model = None
_index = None
_metadata = None


def _load_resources():
    """Lazy-load the FAISS index, metadata, and embedding model."""
    global _model, _index, _metadata

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    if _index is None:
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}. Run ingest.py first.")
        _index = faiss.read_index(FAISS_INDEX_PATH)

    if _metadata is None:
        if not os.path.exists(METADATA_PATH):
            raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}. Run ingest.py first.")
        with open(METADATA_PATH, "rb") as f:
            _metadata = pickle.load(f)


def retrieve(query, top_k=TOP_K):
    """
    Retrieve top-K relevant chunks for a given query.

    Returns a list of dicts:
    [
        {
            "text": "chunk content...",
            "document": "filename.pdf",
            "page": 3,
            "relevance_score": 0.85
        },
        ...
    ]
    """
    _load_resources()

    # Convert query to embedding
    query_embedding = _model.encode([query])
    query_embedding = np.array(query_embedding, dtype="float32")

    # Search FAISS index (returns L2 distances, lower = more similar)
    distances, indices = _index.search(query_embedding, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue  # FAISS returns -1 if fewer results than top_k

        chunk_meta = _metadata[idx]
        distance = float(distances[0][i])

        # Convert L2 distance to a similarity score (0 to 1)
        # Lower distance = higher similarity
        relevance_score = round(1.0 / (1.0 + distance), 4)

        results.append({
            "text": chunk_meta["text"],
            "document": chunk_meta["document"],
            "page": chunk_meta["page"],
            "relevance_score": relevance_score
        })

    return results
