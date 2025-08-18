import os
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from pinecone import Pinecone
from dotenv import load_dotenv
from gemini_helper import (
    generate_dense_embedding,
    generate_summary,
    classify_query_type,
    generate_generic_answer,
    gemini_model,
    generation_config
)
from pinecone_helper import generate_sparse_embedding
import requests

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "intellipatent-hybrid-search-index")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "patent_data.db")

DB_PATH = os.getenv("SQLITE_DB_PATH", "patent_data.db")
DB_URL = os.getenv("SQLITE_DB_URL")

app = FastAPI(title="IntelliPatent Q&A Engine API", version="1.4.3")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


class ConversationTurn(BaseModel):
    question: str
    answer: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    history: Optional[List[ConversationTurn]] = Field(default_factory=list)
    top_k: int = 5
    hybrid: bool = False
    summary: bool = False


def fetch_metadata_from_sqlite(vector_ids: List[str]):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in vector_ids)
    cursor.execute(
        f"""SELECT vector_id, patent_number, title, detailed_summary 
            FROM patent_chunks 
            WHERE vector_id IN ({placeholders})""",
        vector_ids
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "vector_id": row[0],
            "patent_number": row[1],
            "title": row[2],
            "detailed_summary": row[3]
        }
        for row in rows
    ]


def check_followup_relevance_multi(relevant_turns: List[ConversationTurn], new_question: str) -> dict:
    """
    Check if new question is related to ANY of the previous relevant queries
    Returns: {
        'is_related': bool,
        'related_to_index': int or None,  # Index of the related query
        'related_turn': ConversationTurn or None  # The actual related turn
    }
    """
    for i, turn in enumerate(reversed(relevant_turns)):
        prompt = f"""
        Previous question: {turn.question}
        Previous answer: {turn.answer or ''}
        New follow-up question: {new_question}

        Is the new follow-up question relevant to the previous question and its answer?
        Consider topics, themes, technical domains, and conceptual relationships.
        Respond only with 'yes' or 'no'.
        """
        try:
            resp = gemini_model.generate_content(prompt, generation_config=generation_config)
            if not resp or not hasattr(resp, "text"):
                continue
            text = resp.text.strip().lower()
            if text.startswith("yes") or text.startswith("y"):
                return {
                    'is_related': True,
                    'related_to_index': len(relevant_turns) - 1 - i,  # Convert back to original index
                    'related_turn': turn
                }
        except Exception as e:
            print(f"⚠ Follow-up relevance check error for turn {i}: {e}")
            continue
    
    return {'is_related': False, 'related_to_index': None, 'related_turn': None}

@app.post("/search")
async def search_patents(request: SearchRequest):
    try:
        query_text = (request.query or "").strip()
        history = request.history or []

        # ---- Extract ALL relevant turns (ignore irrelevant queries completely) ----
        relevant_turns = []
        for turn in history:
            if turn.answer and "not relevant to patents" not in turn.answer.lower():
                relevant_turns.append(turn)
        
        # ---- FIRST QUERY detection (no relevant context found) ----
        if not relevant_turns:
            print(f"🔍 First relevant query (no previous context): {query_text}")
            query_type = classify_query_type(query_text)
            technical_terms = ["microprocessor", "pipeline", "semiconductor", "AI", "neural", "cache", "encryption", "robotics", "sensor", "optics"]
            force_specific = any(term.lower() in query_text.lower() for term in technical_terms)

            if query_type == "irrelevant" and not force_specific:
                return {"results": [], "message": "Your query is not relevant to patents or intellectual property."}

            if query_type == "generic" and not force_specific:
                answer = generate_generic_answer(query_text)
                return {"results": [], "message": "Your query is patent-related but too general; here's a direct answer.", "generic_answer": answer}

            # Process as specific/relevant query
            dense_emb = generate_dense_embedding(query_text)
            if not dense_emb:
                return {"error": "Failed to generate dense embedding."}

            if request.hybrid:
                sparse_emb = generate_sparse_embedding(query_text)
                pinecone_results = index.query(vector=dense_emb, sparse_vector=sparse_emb, top_k=request.top_k, include_metadata=False)
            else:
                pinecone_results = index.query(vector=dense_emb, top_k=request.top_k, include_metadata=False)

            vector_ids = [match["id"] for match in pinecone_results.get("matches", [])]
            if not vector_ids:
                fallback_answer = generate_generic_answer(query_text)
                return {"results": [], "message": "No relevant matches found; here's a direct Gemini answer.", "generic_answer": fallback_answer}

            results = fetch_metadata_from_sqlite(vector_ids)
            if request.summary:
                combined_text = " ".join([r["detailed_summary"] for r in results if r.get("detailed_summary")])
                live_summary = generate_summary(query_text, combined_text) if combined_text.strip() else "No content available for summary."
                return {"results": results, "live_summary": live_summary}

            return {"results": results}

        # ---- FOLLOW-UP QUERIES (relevant context exists) ----
        print(f"🔗 Follow-up query with {len(relevant_turns)} relevant context(s)")
        
        # ---- PRIORITY CHECK: Summary Keywords (before irrelevance check) ----
        lowered = query_text.lower()
        summary_keywords = ["summary", "summarize", "explain", "details", "list", "points", "highlight", "brief", "short", "lines", "bullet"]
        is_summary_request = any(word in lowered for word in summary_keywords)
        
        if is_summary_request:
            print(f"📄 Summary request detected: '{query_text}'")
            # Use the most recent relevant context for summary
            last_relevant_turn = relevant_turns[-1]
            summary_text = generate_summary(query_text, last_relevant_turn.answer or "")
            return {
                "results": [], 
                "live_summary": summary_text, 
                "related": True,
                "note": f"Summary of previous response (Query #{len(relevant_turns)})"
            }
        
        # ---- Check if current query is irrelevant ----
        current_query_type = classify_query_type(query_text)
        technical_terms = ["microprocessor", "pipeline", "semiconductor", "AI", "neural", "cache", "encryption", "robotics", "sensor", "optics"]
        force_specific = any(term.lower() in query_text.lower() for term in technical_terms)
        
        if current_query_type == "irrelevant" and not force_specific:
            # Current query is irrelevant, but preserve previous relevant context
            return {"results": [], "message": "Your query is not relevant to patents or intellectual property.", "related": False}

        # ---- Smart Multi-Context Check ----
        # Check against ALL previous relevant queries to find the best match
        relevance_result = check_followup_relevance_multi(relevant_turns, query_text)
        
        if not relevance_result['is_related']:
            # Unrelated to ALL previous contexts, treat as NEW first query
            print(f"🆕 Unrelated to all previous contexts, treating as new query")
            
            if current_query_type == "generic" and not force_specific:
                generic_answer = generate_generic_answer(query_text)
                return {
                    "results": [],
                    "message": "This is a new topic unrelated to previous queries.",
                    "generic_answer": generic_answer,
                    "related": False
                }

            # Process as new specific query
            dense_emb = generate_dense_embedding(query_text)
            if not dense_emb:
                return {"error": "Failed to generate dense embedding."}

            if request.hybrid:
                sparse_emb = generate_sparse_embedding(query_text)
                pinecone_results = index.query(vector=dense_emb, sparse_vector=sparse_emb, top_k=request.top_k, include_metadata=False)
            else:
                pinecone_results = index.query(vector=dense_emb, top_k=request.top_k, include_metadata=False)

            vector_ids = [match["id"] for match in pinecone_results.get("matches", [])]
            if not vector_ids:
                fallback_answer = generate_generic_answer(query_text)
                return {"results": [], "message": "No relevant matches found for this new topic.", "generic_answer": fallback_answer, "related": False}

            results = fetch_metadata_from_sqlite(vector_ids)
            if request.summary:
                combined_text = " ".join([r["detailed_summary"] for r in results if r.get("detailed_summary")])
                live_summary = generate_summary(query_text, combined_text) if combined_text.strip() else "No content available for summary."
                return {"results": results, "live_summary": live_summary, "related": False}

            return {"results": results, "related": False}

        # ---- RELATED FOLLOW-UP (found matching context) ----
        related_turn = relevance_result['related_turn']
        related_index = relevance_result['related_to_index']
        
        print(f"✅ Related follow-up to query #{related_index + 1}: '{related_turn.question[:50]}...'")
        
        # Create augmented query with the MOST RELEVANT context
        augmented_query = f"Previous Question: {related_turn.question}\nPrevious Answer: {related_turn.answer or ''}\nFollow-up Question: {query_text}"
        
        # Check if follow-up is generic
        followup_query_type = classify_query_type(augmented_query)
        if followup_query_type == "generic":
            generic_answer = generate_generic_answer(augmented_query)
            return {
                "results": [], 
                "message": "This follow-up is relevant but generic.", 
                "generic_answer": generic_answer, 
                "related": True,
                "note": f"Based on context from query #{related_index + 1}"
            }

        # Process specific follow-up with BEST matching context
        dense_emb = generate_dense_embedding(augmented_query)
        if not dense_emb:
            return {"error": "Failed to generate dense embedding."}

        if request.hybrid:
            sparse_emb = generate_sparse_embedding(augmented_query)
            pinecone_results = index.query(vector=dense_emb, sparse_vector=sparse_emb, top_k=request.top_k, include_metadata=False)
        else:
            pinecone_results = index.query(vector=dense_emb, top_k=request.top_k, include_metadata=False)

        vector_ids = [match["id"] for match in pinecone_results.get("matches", [])]
        if not vector_ids:
            fallback_answer = generate_generic_answer(augmented_query)
            return {
                "results": [], 
                "message": "No relevant matches found for this follow-up.", 
                "generic_answer": fallback_answer, 
                "related": True,
                "note": f"Based on context from query #{related_index + 1}"
            }

        results = fetch_metadata_from_sqlite(vector_ids)
        if request.summary:
            combined_text = " ".join([r["detailed_summary"] for r in results if r.get("detailed_summary")])
            live_summary = generate_summary(augmented_query, combined_text) if combined_text.strip() else "No content available for summary."
            return {
                "results": results, 
                "live_summary": live_summary, 
                "related": True,
                "note": f"Results based on context from query #{related_index + 1}"
            }

        return {
            "results": results, 
            "related": True,
            "note": f"Results based on context from query #{related_index + 1}"
        }

    except Exception as e:
        print(f"⚠ API error: {e}")
        return {"error": str(e)}

# Add this endpoint to your api_server.py file, after your existing imports and before the /search endpoint

@app.get("/health")
async def health_check():
    """Health check endpoint for API status monitoring"""
    try:
        # Optional: Test database connection
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        # Optional: Test Pinecone connection
        index.describe_index_stats()
        
        return {
            "status": "healthy",
            "timestamp": os.popen('date').read().strip(),
            "version": "1.4.3",
            "services": {
                "database": "connected",
                "pinecone": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": os.popen('date').read().strip()
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "IntelliPatent Q&A Engine API", "version": "1.4.3", "status": "running"}


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


def ensure_db_file():
    if not os.path.exists(DB_PATH):
        if not DB_URL:
            raise RuntimeError("Database not found locally and SQLITE_DB_URL not set")
        print(f"📥 Downloading DB from {DB_URL}...")
        response = requests.get(DB_URL)
        response.raise_for_status()
        with open(DB_PATH, "wb") as f:
            f.write(response.content)
        print("✅ Database downloaded and saved locally.")
    else:
        print("✔ Database already exists locally, skipping download.")

# Call it before using DB
ensure_db_file()


