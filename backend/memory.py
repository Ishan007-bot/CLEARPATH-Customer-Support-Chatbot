
import uuid
from config import MAX_MEMORY_TURNS

# In-memory conversation store
conversation_store = {}


def get_or_create_conversation(conversation_id=None):
    """
    Get existing conversation history or create a new one.
    Returns (conversation_id, history_list).
    """
    if conversation_id and conversation_id in conversation_store:
        return conversation_id, conversation_store[conversation_id]

    # Create new conversation
    new_id = conversation_id or str(uuid.uuid4())
    conversation_store[new_id] = []
    return new_id, conversation_store[new_id]


def add_message(conversation_id, role, content):
    """Add a message to the conversation history."""
    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = []

    conversation_store[conversation_id].append({
        "role": role,
        "content": content
    })

    # Trim to last N turns (each turn = 1 user + 1 assistant message)
    max_messages = MAX_MEMORY_TURNS * 2
    if len(conversation_store[conversation_id]) > max_messages:
        conversation_store[conversation_id] = conversation_store[conversation_id][-max_messages:]


def get_history(conversation_id):
    """Get conversation history for a given ID."""
    return conversation_store.get(conversation_id, [])
