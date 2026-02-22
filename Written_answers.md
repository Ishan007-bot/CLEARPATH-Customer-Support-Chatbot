# Written Answers

### Q1 — Routing Logic

My router works on a set of deterministic rules to decide which model gets the query. For **Simple** classification, I look for common greetings, very short "Yes/No" style questions (under 10 words), and anything that doesn't trigger my "complex" keyword list. The query gets pushed to **Complex** (using the Llama 3.3 70B model) if it’s more than 10 words long, contains multiple questions, or hits specific technical triggers like "pricing," "security," "workflows," or "integration."

I drew the boundary at 10 words and keyword triggers because it creates a clear split between "admin" talk and actual knowledge retrieval. Short queries are usually just noise or simple fact checks that the 8B model handles instantly. However, once a user starts using more words or specific technical terms, they are usually looking for a synthesis of multiple documents, which is where the 70B model really shines.

One query that the router misclassified was: *"Check the pricing for me."* 
Because it was only 5 words and I hadn't initially included "pricing" as a complex keyword, it went straight to the 8B model. The 8B model gives a decent answer, but it lacks the nuance of the retrieval-heavy 70B model. This happened because the word count was too low to hit the length trigger. 

To improve this without an LLM, I’d implement a **TF-IDF or Ngram-based classifier**. Instead of just looking for exact word matches, I could look for the "semantic density" of technical terms. This would help catch things like "what's the damage" or "setup help" which feel complex but don't always use the exact "workflow" keywords I have listed.


### Q2 — Retrieval Failures

A classic failure case I ran into was with the query: *"How do I authenticate with the Clearpath API and what are the rate limits?"*

Even though I had the exact document for this (`26_API_Documentation_v2.1.pdf`), the system initially failed to retrieve the correct technical chunk. Instead, it pulled a bunch of general "Getting Started" chunks and even some pricing details because they mentioned the word "API" frequently. The system basically returned a "generic" help answer or claimed it didn't know the exact steps, even though the data was in the index.

The retrieval failed primarily because of **low top-K precision**. When the index contains 30+ documents, general keywords like "API" create a lot of mathematical "noise." The specific chunk containing the Bearer Token and Rate Limit info was sitting at rank #7 or #8 in terms of similarity score, but my system was only looking at the top 5 (`TOP_K=5`). Because the general documents were longer and used the word "API" more often, they "pushed out" the more technical, shorter chunk that actually had the secrets.

To fix this, I increased the retrieval window to `TOP_K=10`. This simple change gave the "technical" chunk enough room to make it into the context window. Once the AI saw it—even as the 7th match—it was smart enough to ignore the 6 irrelevant chunks and extract the exact auth steps. If I wanted to be even more robust, I’d add a **Re-ranker (like Cohere or a Cross-Encoder)**. That way, I could pull 20 chunks roughly, and then use a second, smarter model to re-order them based on actual semantic relevance before sending them to the LLM.


### Q3 — Cost and Scale

Scaling this system to 5,000 queries a day changes the math quite a bit. Based on what I've seen in the logs, a "Simple" query typically uses ~250 tokens (input + output), while a "Complex" RAG query can easily hit 2,500+ tokens because of those 10 retrieved chunks. Assuming a 40/60 split between simple and complex traffic:

*   **Simple (8B Model):** 2,000 queries × 250 tokens ≈ 0.5 Million tokens/day.
*   **Complex (70B Model):** 3,000 queries × 2,700 tokens (avg) ≈ 8.1 Million tokens/day.
*   **Total daily footprint:** ~8.6 Million tokens.

The absolute **biggest cost driver** isn't the AI's "thinking" (the output)—it’s the **Input Context**. Every time we attach 10 chunks of PDF text to a prompt, we're basically sending a small essay to the LLM. With the 70B model being significantly more expensive per token than the 8B, those massive RAG context windows are where the budget goes.

The single **highest-ROI change** to cut costs without killing quality would be **Context Pruning or Summarization**. Instead of dumping 10 full chunks into the prompt, I could use a much smaller, cheaper model to quickly summarize those chunks or just extract the relevant sentences. Reducing the input context by 50% would almost halve the 70B model's bill without losing the core information needed for the answer.

One optimization I'd **definitely avoid** is cutting down the conversation memory too aggressively. It’s tempting to save tokens by only remembering the last one or two messages, but and from a user perspective, that’s a nightmare. If a customer has to repeat their account ID or the error they just described three messages ago, the "AI" suddenly feels like a broken phone tree. I’d rather pay for the extra input tokens to keep the conversation feeling human and continuous than save a few cents and frustrate every user.


### Q4 — What Is Broken

If I’m being honest, the most significant flaw in this system is the **rule-based deterministic router**. Right now, it relies on word counts and a hardcoded list of keywords like "pricing" or "workflow" to decide if a query is complex. 

This is a huge liability for a real deployment because language is messy. If a user asks, *"My setup is acting weird, can you look at my logs?"*—it might get classified as "simple" just because it doesn't hit a specific keyword or length trigger. If it goes to the simple 8B model without any retrieved context, the AI will just say it doesn't know, even if the answer is sitting right there in the docs. 

I shipped with it anyway because, for a prototype, it’s **lightning fast**. It has zero latency and zero token cost. In a timed assessment where every millisecond counts for the UI experience, a rule-based router is the best way to keep the app feeling snappy. It handles 90% of cases perfectly, and I felt that for this scale, the speed bonus outweighed the edge-case errors.

If I had more time, I wouldn't use an LLM for routing—that's too slow. Instead, I’d train a **small, local classifier (like a DistilBERT model)** specifically on the Clearpath documentation. This model would be small enough to run on the same CPU as the backend but smart enough to understand the *intent* behind a question. It wouldn't care if the user said "cost" or "pricing" or "how much dough"; it would recognize the intent of "Commercial Inquiry" and route it to the 70B model with the right retrieval chunks every single time.


### AI Usage

I used AI as a companion to help me move faster through specific technical hurdles and debugging sessions. Here are a few of the exact prompts I used when I got stuck on implementation details:

- "I'm using pdfplumber to extract text from these enterprise docs, but some pages are returning null bytes and weird whitespace that's causing issues with my FAISS encoding. Can you show me a robust way to clean/strip these characters in Python before I chunk the text?"

- "I have made the .env file and set the Groq API key however the config.py file is not able to read the API key and access it. Suggest me a fix ?"

- "FAISS is returning L2 distances for my RAG chunks. How do I mathematically convert these distances into a percentage-based 'Relevance Score' (0 to 1) that I can display to users in a UI?"

- "I'm using st.chat_input in Streamlit. How do I properly structure st.session_state to store a chat history that persists through reruns and also keep track of a unique conversation_id for my backend logging?"
