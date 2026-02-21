"""
Document Ingestion Script
=========================
This script handles the full RAG ingestion pipeline:
1. Load PDFs from the /docs folder
2. Extract text page by page using pdfplumber
3. Chunk the text into 300-500 word pieces with 50-word overlap
4. Generate embeddings using sentence-transformers
5. Build and save a FAISS index + metadata

WHY CHUNKING?
- LLMs have limited context windows. We can't feed entire documents.
- Smaller chunks allow the retriever to find the MOST relevant passage
  instead of returning a huge document where the answer is buried.
- Typical chunk size of 300-500 words is a sweet spot: big enough to carry
  meaning, small enough to be precise in retrieval.

WHY OVERLAP?
- Without overlap, a sentence at the boundary of two chunks gets split.
- The answer could be half in chunk A and half in chunk B.
- 50-word overlap ensures boundary content appears in both chunks,
  so we don't lose context at the edges.
"""

import os
import pickle
import pdfplumber
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import (
    DOCS_DIR, FAISS_INDEX_PATH, METADATA_PATH,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE
)


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file page by page.
    Returns a list of (page_number, text) tuples.
    """
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    # Clean up common PDF artifacts
                    text = text.replace("\x00", "")      # null bytes
                    text = " ".join(text.split())         # collapse whitespace
                    pages.append((i + 1, text))           # 1-indexed page numbers
    except Exception as e:
        print(f"  [ERROR] Failed to read {pdf_path}: {e}")
    return pages


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into chunks of ~chunk_size words with overlap.
    
    We split on word boundaries and try to break at sentence endings
    (periods) when possible, to preserve semantic meaning.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        # If we're not at the end, try to break at a sentence boundary
        if end < len(words):
            # Look backwards from 'end' for a period to break at
            best_break = end
            for j in range(end, max(start + chunk_size // 2, start), -1):
                if words[j - 1].endswith(('.', '!', '?')):
                    best_break = j
                    break
            end = best_break

        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        if len(chunk_words) >= MIN_CHUNK_SIZE:
            chunks.append(chunk_text_str)

        # Move forward by (chunk length - overlap) words
        start = start + (end - start) - overlap
        if start >= len(words):
            break

    return chunks


def load_all_documents():
    """
    Load all PDFs from the docs directory.
    Returns a list of chunk dicts with text, document name, and page number.
    """
    if not os.path.exists(DOCS_DIR):
        print(f"[ERROR] Docs directory not found: {DOCS_DIR}")
        return []

    pdf_files = sorted([f for f in os.listdir(DOCS_DIR) if f.lower().endswith(".pdf")])
    if not pdf_files:
        print("[ERROR] No PDF files found in docs/")
        return []

    print(f"Found {len(pdf_files)} PDF files in {DOCS_DIR}")

    all_chunks = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(DOCS_DIR, pdf_file)
        print(f"  Processing: {pdf_file}")

        pages = extract_text_from_pdf(pdf_path)
        doc_chunk_count = 0

        for page_num, page_text in pages:
            chunks = chunk_text(page_text)
            for chunk in chunks:
                all_chunks.append({
                    "text": chunk,
                    "document": pdf_file,
                    "page": page_num
                })
                doc_chunk_count += 1

        print(f"    -> {doc_chunk_count} chunks from {len(pages)} pages")

    print(f"\nTotal chunks: {len(all_chunks)}")
    return all_chunks


def build_faiss_index(chunks):
    """
    Generate embeddings for all chunks and build a FAISS index.
    Saves:
      - faiss_index.bin  (the vector index)
      - metadata.pkl     (chunk text + document + page for each vector)
    """
    if not chunks:
        print("[ERROR] No chunks to index.")
        return

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Extract just the text for embedding
    texts = [c["text"] for c in chunks]

    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype="float32")

    # Build FAISS index (L2 distance, simple flat index — works great for <100k vectors)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"FAISS index built: {index.ntotal} vectors, dimension={dimension}")

    # Save index
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Saved FAISS index to {FAISS_INDEX_PATH}")

    # Save metadata (text, document, page for each chunk)
    metadata = [{"text": c["text"], "document": c["document"], "page": c["page"]} for c in chunks]
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)
    print(f"Saved metadata to {METADATA_PATH}")

    print("\n✅ Ingestion complete!")


if __name__ == "__main__":
    print("=" * 60)
    print("Clearpath RAG - Document Ingestion")
    print("=" * 60)

    chunks = load_all_documents()
    if chunks:
        build_faiss_index(chunks)
    else:
        print("No chunks generated. Check your docs/ folder.")
