
import re

# Phrases that indicate the model is refusing to answer
REFUSAL_PHRASES = [
    "i don't know",
    "i do not know",
    "not mentioned",
    "cannot find",
    "can't find",
    "no information",
    "not found in",
    "not available in",
    "doesn't mention",
    "does not mention",
    "not specified",
    "no relevant"
]


def check_refusal(answer):
    """Check if the answer is a refusal (model says it doesn't know)."""
    answer_lower = answer.lower()
    for phrase in REFUSAL_PHRASES:
        if phrase in answer_lower:
            return True
    return False


def check_no_context(chunks_retrieved, answer):
    """
    Flag if no chunks were retrieved but the model still gave an answer
    (instead of refusing). This means it might be hallucinating.
    """
    if chunks_retrieved == 0 and not check_refusal(answer):
        return True
    return False


def check_conflicting_sources(chunks):
    """
    Check if retrieved chunks contain conflicting numeric or factual info.
    For example, different pricing numbers or contradicting statements.
    
    Looks for numbers (like prices, percentages, counts) across chunks
    and flags if the same type of number appears with different values.
    """
    if len(chunks) < 2:
        return False

    # Extract all numbers with their surrounding context (5 words before)
    number_contexts = []
    for chunk in chunks:
        text = chunk["text"].lower()
        # Find patterns like "$99", "99%", "99 users", numbers with context
        matches = re.finditer(r'(\w+\s+){0,3}(\$[\d,.]+|[\d,.]+%|[\d,.]+)', text)
        for match in matches:
            full = match.group().strip()
            number_contexts.append(full)

    # Compare numbers that share context words (simple heuristic)
    # Group by the non-numeric prefix
    groups = {}
    for ctx in number_contexts:
        # Split into context words and the number
        parts = ctx.split()
        if len(parts) >= 2:
            key = " ".join(parts[:-1])  # context words as key
            value = parts[-1]           # the number
            if key not in groups:
                groups[key] = set()
            groups[key].add(value)

    # If any context group has multiple different numbers, flag it
    for key, values in groups.items():
        if len(values) > 1:
            return True

    return False


def evaluate(answer, chunks, chunks_retrieved):
    """
    Run all evaluator checks and return a list of flags.
    
    Returns:
        list of flag strings, e.g. ["refusal"] or ["no_context", "multiple_conflicting_sources"]
    """
    flags = []

    if check_refusal(answer):
        flags.append("refusal")

    if check_no_context(chunks_retrieved, answer):
        flags.append("no_context")

    if check_conflicting_sources(chunks):
        flags.append("multiple_conflicting_sources")

    return flags
