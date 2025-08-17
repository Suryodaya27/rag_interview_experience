# 🧠 LeetCode + GFG Post Intelligence (Agentic RAG)

A Streamlit-based intelligent **Retrieval-Augmented Generation (RAG)** system that scrapes and processes interview/coding-related discussions from **LeetCode** and **GeeksForGeeks**, stores them in a **vector database**, and generates contextual answers to user queries.  

Now upgraded with an **Agentic RAG loop**, **company-aware responses**, and improved debugging/UX.

---

## 🚀 Features

- 🔍 **Company-aware scraping**  
  Accepts a company name and checks for cached data locally before scraping fresh content.  

- 🧼 **Data preprocessing & chunking**  
  Extracts raw post content, cleans it, and splits into semantically meaningful chunks.  

- 🧠 **Embedding generation**  
  Generates embeddings for each chunk using an LLM-compatible embedding model (via **Ollama**).  

- 🧮 **Semantic search**  
  Stores embeddings in **PostgreSQL + pgvector** for fast similarity querying.  

- 🤖 **Agentic RAG Q&A**  
  - Retrieves top relevant chunks for a user query.  
  - Runs a **multi-step agentic loop** (retries + self-checks).  
  - Ensures answers stay **company-specific** when relevant.  

- 🛠 **Debug Mode**  
  Optional toggle to view retrieved chunks (with links) for transparency.  

- ⚡ **Performance Tracking**  
  Shows query **response time** in the UI.  

- 🎨 **Streamlit Frontend**  
  - Clean chat-like interface.  
  - Debug + timing reset automatically for each new question.  
  - Cancel query option (planned).  

---

## 🛠️ Tech Stack

- **Language**: Python 
- **Scraping**: Playwright+BeautifulSoup 
- **Frontend**: [Streamlit](https://streamlit.io/)  
- **Embeddings / LLM**: [Ollama](https://ollama.com/) (local models, CPU/GPU supported)  
- **Database**: PostgreSQL + [pgvector](https://github.com/pgvector/pgvector)  
- **Containerization**: Docker  

---

## 🧩 Workflow

```text
1. User enters a company name.
2. System checks for existing cache (links and data).
3. If not cached:
   - Scrape posts from LeetCode & GeeksForGeeks.
   - Clean and chunk post content.
   - Generate embeddings via Ollama.
   - Store embeddings + metadata in pgvector (Postgres).
4. User enters a question.
5. Convert question → embeddings.
6. Query pgvector for top-k similar chunks.
7. Agentic RAG loop:
   - Retrieve + reason over chunks.
   - Retry/self-correct if answer is weak.
   - Ensure context is company-specific if query demands.
8. Final response displayed in Streamlit UI.
9. Debug info (retrieved chunks) & response time shown (optional).
```


⚡ Tip: For CPU-only environments, smaller parameter models (1.3B–3B) are recommended for faster response times.