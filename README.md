# IntelliPatent Q\&A Engine (Hybrid Search + Gemini)

A production-ready Patent Q\&A system that combines:

* **Hybrid retrieval** with **Pinecone** (dense + optional sparse)
* **SQLite** for rich metadata (titles, patent numbers, summaries)
* **Gemini** for classification, summarization, and answers
* **Follow-up chat UX** (Streamlit)
* **Backend on Render**, **Frontend on Hugging Face Spaces**

---

## ✨ Features

* **Query classification**

  * `irrelevant` → blocked with a friendly message
  * `generic` → answered directly by Gemini (short, structured)
  * `specific` → routed to Pinecone (semantic or hybrid)

* **Hybrid / semantic search**

  * Dense embeddings: **Gemini Embedding** (1536 dims)
  * (Optional) Sparse embeddings: `pinecone-sparse-english-v0` with proper `input_type`

* **DB-backed metadata**

  * We store chunk metadata (title, patent number, detailed summary) in **SQLite**
  * Vector IDs from Pinecone map back to rows in SQLite

* **Smart follow-ups**

  * Conversation context kept in UI
  * Follow-up relevance is re-checked
  * If possible, reuse already-retrieved results; otherwise do a fresh search

* **Two deployment targets**

  * **Backend**: Render (FastAPI + Uvicorn)
  * **Frontend**: Hugging Face **Spaces** (Streamlit)

---

## 🧱 Architecture & Flow

```
User → Streamlit UI (HF Space)
            │
            ▼
      FastAPI Backend (Render)
            │
   ┌────────┴───────────┐
   ▼                    ▼
Gemini (classify/summarize)   Pinecone (query vectors)
                                   │
                                   ▼
                             SQLite metadata
```

1. UI sends the question to `/search` with flags (`hybrid`, `summary`).
2. Backend classifies the query (`irrelevant | generic | specific`).
3. For `specific`, it generates dense (and optional sparse) embeddings, queries Pinecone, then fetches metadata from SQLite using the vector IDs.
4. For `summary=true`, Gemini merges/structures the results.
5. UI maintains chat history and conversation context for follow-ups.

---

## 🗂️ Repo Structure (example)

```
.
├── api_server.py            # FastAPI app (Render)
├── gemini_helper.py         # Gemini: embeddings, classify, generic answers, summaries
├── pinecone_helper.py       # (Optional) Sparse embedding wrapper
├── app.py                   # Streamlit UI (HF Spaces)
├── requirements.txt         # (single-file works; see split option below)
├── .env                     # Local dev env vars (never commit real keys)
└── (optional) Dockerfile
```

---

## 🔑 Environment Variables

Set these on **Render** (backend) and **HF Space** (frontend) as needed:

**Backend (Render):**

* `GOOGLE_API_KEY` – Gemini API key
* `PINECONE_API_KEY1` – Pinecone key
* `PINECONE_INDEX_NAME` – e.g. `intellipatent-hybrid-search-index`
* `SQLITE_DB_PATH` – e.g. `patent_data.db`
* `SQLITE_DB_URL` – **public** or **export** link to your DB (Google Drive, S3, etc.)

  * Used to download `patent_data.db` on first boot if the file isn’t present
* (Optional) `PORT` – Render provides one; Uvicorn listens on `8000` by default and Render maps it.

**Frontend (HF Space):**

* `API_URL` – your Render URL, e.g.
  `https://intellipatent-q-a-engine-powered-by.onrender.com`

---

## 🧪 Local Development

1. Create a virtual env & install:

```bash
pip install -r requirements.txt
```

2. Create `.env` (local only):

```env
GOOGLE_API_KEY=your_gemini_key
PINECONE_API_KEY1=your_pinecone_key
PINECONE_INDEX_NAME=intellipatent-hybrid-search-index
SQLITE_DB_PATH=patent_data.db
SQLITE_DB_URL=https://.../download  # optional if DB is already in repo
```

3. Start backend:

```bash
uvicorn api_server:app --reload --port 8000
```

4. Start UI:

```bash
streamlit run app.py
```

---

## 🧠 Gemini Usage

* **Embeddings**: `gemini-embedding-001` with `output_dimensionality=1536`
  → **Make sure** your Pinecone index dimension is **1536**.

* **Classification** (`classify_query_type`)
  Returns exactly one of: `irrelevant | generic | specific`

* **Summaries** (`generate_summary`)
  Renders a 4-section structured output: Overview, Key Features, Claims, Applications

* **Generic Answers** (`generate_generic_answer`)
  Short, accurate, and clearly labeled in UI as general knowledge (not from DB).

---

## 📦 Pinecone Notes (Hybrid)

* **Metric**: `dotproduct` (recommended for Gemini embeddings)
* **Dimension**: must match your dense embedding size (**1536**)
* **Hybrid Query**:

  * Dense vector: from Gemini
  * Sparse vector: (optional) `pinecone-sparse-english-v0`

    * `input_type="passage"` for documents
    * `input_type="query"` for user queries
    * When upserting/querying, pass the **dict** shape:
      `{"indices": [...], "values": [...]}`
      (Do **not** pass the raw `SparseEmbedding` object)

---

## 💬 Follow-Ups (UI)

* The UI keeps:

  * **chat history**
  * **conversation\_context**
  * **last top-K docs + last live summary**

* Follow-up routing:

  1. Classify again (irrelevant → block; generic → short Gemini answer)
  2. If relevant and **answerable from cached docs/summary**, avoid Pinecone
  3. Otherwise, run hybrid/semantic search again

* For off-topic follow-ups (“who is prime minister…”), the UI clearly says:
  **“🚫 Query Not Relevant: Your question is not relevant to patents or IP.”**

---

## 🔐 Security & Privacy

* Never commit real keys to Git.
* Use **Render Env Vars** and **HF Space Secrets**.
* SQLite contains only patent metadata; no user PII is stored.

---

## 🧾 Requirements

If you’re keeping one file (works fine):

`requirements.txt` (example)

```
fastapi
uvicorn
python-dotenv
pinecone-client
google-generativeai
google-genai
requests
streamlit
```

> **Tip:** You can split into `requirements-backend.txt` and `requirements-frontend.txt` if you want Render to avoid installing Streamlit.

---

## 🐳 Optional: Docker

`Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

On Render, choose **Docker** runtime and they’ll use this Dockerfile.

---

## 🔭 Roadmap

* Add RAG citations per sentence/snippet
* Add re-ranking for better top-K
* Persist conversation state server-side
* Switch sparse to token-aware BM25 style with boosts
* Optional: move metadata from SQLite to a managed DB (Postgres)

---

## 🔗 Live URLs (fill in)

* **Live App:**
  `https://awanish17-intellipatent-ui.hf.space`

---

