
import os
from groq import Groq
from config import GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are an expert Clearpath customer support assistant. "
    "Your goal is to answer questions using the provided context and conversation history. "
    "MANDATORY: If the user uses pronouns like 'it', 'them', or 'those', or says 'tell me more', "
    "look at the conversation history to identify what topic they are referring to. "
    "If the context is empty, rely on the history to provide a detailed continuation. "
    "If the answer is neither in the context nor the history, politely state you don't have that information. "
    "Be professional, technical, and concise."
)


def build_messages(question, chunks, conversation_history=None):
    """
    Build the message list for the Groq API call.
    Includes system prompt, conversation history, context, and the question.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history if available (for multi-turn context)
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Build context from retrieved chunks
    if chunks:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['document']}, Page {chunk['page']}]\n{chunk['text']}"
            )
        context_text = "\n\n".join(context_parts)
    else:
        context_text = "No relevant context found."

    # User message with context
    user_message = f"CONTEXT:\n{context_text}\n\nQUESTION:\n{question}"
    messages.append({"role": "user", "content": user_message})

    return messages


def call_llm(question, chunks, model, conversation_history=None):
    """
    Call Groq API with the given question, context chunks, and model.
    
    Returns:
        dict with 'answer', 'tokens_input', 'tokens_output'
    """
    messages = build_messages(question, chunks, conversation_history)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024
        )

        answer = response.choices[0].message.content
        tokens_input = response.usage.prompt_tokens
        tokens_output = response.usage.completion_tokens

        return {
            "answer": answer,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output
        }

    except Exception as e:
        return {
            "answer": f"Sorry, I encountered an error: {str(e)}",
            "tokens_input": 0,
            "tokens_output": 0
        }


def call_llm_stream(question, chunks, model, conversation_history=None):
    """
    Call Groq API with streaming enabled.
    Yields tokens one by one.
    """
    messages = build_messages(question, chunks, conversation_history)

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f" [Error during streaming: {str(e)}]"
