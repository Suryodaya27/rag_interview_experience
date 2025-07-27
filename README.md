# 🧠 LeetCode + GFG Post Intelligence

A Streamlit-based intelligent search system that scrapes interview and coding-related discussions from LeetCode and GeeksForGeeks, converts them into embeddings, and retrieves the most relevant content for user queries using a Retrieval-Augmented Generation (RAG) approach.

---

## 🚀 Features

- 🔍 **Company-aware scraping**: Accepts a company name and checks for cached data locally before scraping fresh content.
- 🧼 **Data preprocessing**: Extracts post content and converts it into clean, meaningful chunks.
- 🧠 **Embedding generation**: Embeds each content chunk using an LLM-compatible model (via Ollama).
- 🧮 **Semantic search**: Stores embeddings in a vector database (PostgreSQL with pgvector) for efficient similarity querying.
- 🤖 **Contextual Q&A**: Accepts user questions, retrieves top relevant chunks, and feeds them along with the question into an LLM to generate answers.
- ⚡ **Streamlit frontend**: Interactive user interface for entering company names and questions.

---

## 🛠️ Tech Stack

- **Language**: Python
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend / Embeddings**: [Ollama](https://ollama.com/)
- **Database**: PostgreSQL + [pgvector](https://github.com/pgvector/pgvector)
- **Containerization**: Docker

---

## 🧩 Workflow

```text
1. User enters a company name.
2. System checks for existing cache (links and data).
3. If not cached:
   - Scrape posts from LeetCode and GeeksForGeeks.
   - Chunk post content.
   - Convert chunks into embeddings via Ollama.
   - Store in pgvector (PostgreSQL).
4. User enters a question.
5. Convert question into embedding.
6. Query pgvector for top-k similar chunks.
7. Feed top-k chunks + question into LLM.
8. Display final response to user.
