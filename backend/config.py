import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_index.bin")
METADATA_PATH = os.path.join(BASE_DIR, "metadata.pkl")
LOGS_PATH = os.path.join(BASE_DIR, "logs.json")

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking settings
CHUNK_SIZE = 400        # target words per chunk
CHUNK_OVERLAP = 50      # overlap in words between chunks
MIN_CHUNK_SIZE = 50     # ignore tiny chunks

# Retrieval settings
TOP_K = 5               # number of chunks to retrieve

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SIMPLE_MODEL = "llama-3.1-8b-instant"
COMPLEX_MODEL = "llama-3.3-70b-versatile"

# Conversation memory
MAX_MEMORY_TURNS = 5    # keep last 5 exchanges in memory
