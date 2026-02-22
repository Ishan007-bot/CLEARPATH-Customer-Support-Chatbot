"""
Model Router (Deterministic)
============================
Rule-based classification of queries into "simple" or "complex".
NO LLM is used for routing — this is purely deterministic.

Rules:
  simple:
    - Less than 10 words
    - OR is a greeting (hi, hello, thanks, etc.)
    - OR is a yes/no question

  complex:
    - Contains keywords: how, why, explain, compare, steps
    - OR has multiple question marks
    - OR 10+ words

Mapping:
  simple  → llama-3.1-8b-instant
  complex → llama-3.3-70b-versatile
"""

from config import SIMPLE_MODEL, COMPLEX_MODEL

# Greetings and simple phrases
GREETINGS = {"hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye", "ok", "okay", "sure", "yes", "no"}

# Keywords that signal a complex query
COMPLEX_KEYWORDS = {"how", "why", "explain", "compare", "steps", "difference", "describe", "elaborate", "pricing", "plans", "cost"}

# Words that start yes/no questions
YES_NO_STARTERS = {"is", "are", "was", "were", "do", "does", "did", "can", "could", "will", "would", "should", "has", "have", "had"}


def classify_query(question):
    """
    Classify a query as 'simple' or 'complex' using rule-based logic.

    Returns:
        dict with 'classification', 'model_used', and 'requires_context'
    """
    text = question.strip().lower()
    words = text.split()
    word_count = len(words)

    # List of queries that specifically DON'T need retrieval (Identity/Greetings)
    PERSONAL_QUERIES = {"who are you", "what is your name", "what's your name", "identify yourself", "what are you"}

    # Check if it's a greeting
    clean_text = text.rstrip("!?.,")
    if clean_text in GREETINGS or any(q in text for q in PERSONAL_QUERIES):
        return {"classification": "simple", "model_used": SIMPLE_MODEL, "requires_context": False}

    # Check for yes/no question (starts with yes/no starter words)
    if words and words[0] in YES_NO_STARTERS and text.endswith("?"):
        if word_count < 10:
            return {"classification": "simple", "model_used": SIMPLE_MODEL}

    for word in words:
        stripped = word.rstrip("?!.,")
        if stripped in COMPLEX_KEYWORDS:
            return {"classification": "complex", "model_used": COMPLEX_MODEL, "requires_context": True}

    # Check for multiple question marks (indicates complex/multi-part question)
    if text.count("?") >= 2:
        return {"classification": "complex", "model_used": COMPLEX_MODEL, "requires_context": True}

    # Check word count
    if word_count >= 10:
        return {"classification": "complex", "model_used": COMPLEX_MODEL, "requires_context": True}

    # Default: short simple queries
    return {"classification": "simple", "model_used": SIMPLE_MODEL, "requires_context": True}
