"""
Evaluation Harness
Runs test queries against the API and prints PASS/FAIL results.
"""

import requests
import time

API_URL = "http://localhost:8000/query"

# Test cases: each has a query and expected keywords in the answer
tests = [
    {
        "query": "hi",
        "expected_keywords": ["hello", "help", "assist", "hi"],
        "expected_classification": "simple"
    },
    {
        "query": "What is Clearpath?",
        "expected_keywords": ["clearpath"],
        "expected_classification": "simple"
    },
    {
        "query": "How do I set up custom workflows in Clearpath?",
        "expected_keywords": ["workflow", "custom", "create", "set"],
        "expected_classification": "complex"
    },
    {
        "query": "What are the pricing plans?",
        "expected_keywords": ["pric", "plan", "enterprise", "cost"],
        "expected_classification": "complex"
    },
    {
        "query": "Explain the data security policy",
        "expected_keywords": ["security", "data", "privacy", "policy"],
        "expected_classification": "complex"
    },
    {
        "query": "thanks",
        "expected_keywords": ["welcome", "help", "glad", "assist"],
        "expected_classification": "simple"
    },
    {
        "query": "How do I integrate third-party tools with Clearpath?",
        "expected_keywords": ["integrat", "api", "connect", "tool"],
        "expected_classification": "complex"
    },
    {
        "query": "What is the SLA response time?",
        "expected_keywords": ["sla", "response", "time", "support"],
        "expected_classification": "complex"
    },
]


def check_keywords(answer, keywords):
    """Check if any expected keyword appears in the answer."""
    answer_lower = answer.lower()
    for kw in keywords:
        if kw.lower() in answer_lower:
            return True
    return False


def run_tests():
    print("=" * 80)
    print("Clearpath RAG - Evaluation Harness")
    print("=" * 80)
    print(f"Running {len(tests)} test queries against {API_URL}\n")

    passed = 0
    failed = 0
    errors = 0

    for i, test in enumerate(tests, 1):
        query = test["query"]
        expected_kw = test["expected_keywords"]
        expected_class = test["expected_classification"]

        try:
            start = time.time()
            resp = requests.post(API_URL, json={"question": query}, timeout=30)
            elapsed = int((time.time() - start) * 1000)

            if resp.status_code != 200:
                print(f"  [{i}] FAIL (HTTP {resp.status_code})")
                print(f"      Query: {query}")
                print(f"      Error: {resp.text}\n")
                failed += 1
                continue

            data = resp.json()
            answer = data.get("answer", "")
            classification = data.get("metadata", {}).get("classification", "")
            model = data.get("metadata", {}).get("model_used", "")

            # Check keyword match
            kw_match = check_keywords(answer, expected_kw)

            # Check classification
            class_match = classification == expected_class

            # Overall result
            result = "PASS" if (kw_match and class_match) else "FAIL"

            if result == "PASS":
                passed += 1
            else:
                failed += 1

            print(f"  [{i}] {result} | {elapsed}ms | {classification} -> {model}")
            print(f"      Query:    {query}")
            print(f"      Answer:   {answer[:120]}...")
            if not kw_match:
                print(f"      ⚠ Keywords not found: {expected_kw}")
            if not class_match:
                print(f"      ⚠ Expected '{expected_class}', got '{classification}'")
            print()

        except requests.exceptions.ConnectionError:
            print(f"  [{i}] ERROR - Cannot connect to backend")
            print(f"      Query: {query}\n")
            errors += 1
        except Exception as e:
            print(f"  [{i}] ERROR - {str(e)}")
            print(f"      Query: {query}\n")
            errors += 1

    print("=" * 80)
    print(f"Results: {passed} PASSED | {failed} FAILED | {errors} ERRORS")
    print(f"Total:   {len(tests)} tests")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
