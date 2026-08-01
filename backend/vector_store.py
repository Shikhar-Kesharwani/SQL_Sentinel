import json
import uuid
import os
import math
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

STORE_PATH = Path(__file__).parent / "context_store.json"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "sql-sentinel")

_embedder = None

def get_embedding(text: str) -> list:
    """Generate vector embedding for text without requiring PyTorch/heavy dependencies."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            res = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            if "embedding" in res:
                return res["embedding"]
        except Exception:
            pass

    # Fallback to SentenceTransformer if installed (local mode)
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _embedder = False
            
    if _embedder:
        try:
            return _embedder.encode(text).tolist()
        except Exception:
            pass

    # Basic frequency vector fallback (dimension 384)
    import hashlib
    vec = [0.0] * 384
    words = text.lower().split()
    for w in words:
        idx = int(hashlib.md5(w.encode()).hexdigest(), 16) % 384
        vec[idx] += 1.0
    return vec

def cosine_similarity(v1: list, v2: list) -> float:
    if not v1 or not v2:
        return 0.0
    min_len = min(len(v1), len(v2))
    v1 = v1[:min_len]
    v2 = v2[:min_len]
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def is_pinecone() -> bool:
    return bool(PINECONE_API_KEY and Pinecone)

pc = None
index = None
if is_pinecone():
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Warning: Failed to connect to Pinecone: {e}")

def load_store():
    if not STORE_PATH.exists():
        return []
    try:
        with open(STORE_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_store(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_training_data(question: str, sql: str = None, doc_text: str = None, type: str = "sql"):
    text_to_encode = question if type == "sql" else doc_text
    emb = get_embedding(text_to_encode)
    record_id = str(uuid.uuid4())[:8]
    
    if is_pinecone() and index is not None:
        try:
            index.upsert([{
                "id": record_id,
                "values": emb,
                "metadata": {
                    "type": type,
                    "question": question,
                    "sql": sql or "",
                    "doc_text": doc_text or ""
                }
            }])
            return record_id
        except Exception as e:
            print(f"Pinecone upsert error: {e}")

    store = load_store()
    record = {
        "id": record_id,
        "type": type,
        "question": question,
        "sql": sql,
        "doc_text": doc_text,
        "embedding": emb
    }
    store.append(record)
    save_store(store)
    return record_id

def remove_training_data(record_id: str):
    if is_pinecone() and index is not None:
        try:
            index.delete(ids=[record_id])
            return
        except Exception:
            pass

    store = load_store()
    new_store = [r for r in store if r["id"] != record_id]
    save_store(new_store)

def get_relevant_context(query: str, top_k: int = 3):
    query_emb = get_embedding(query)
    
    if is_pinecone() and index is not None:
        try:
            res = index.query(vector=query_emb, top_k=top_k, include_metadata=True)
            top_matches = []
            for match in res.get("matches", []):
                if match.get("score", 0) > 0.4:
                    top_matches.append(match.get("metadata"))
            return top_matches
        except Exception as e:
            print(f"Pinecone query error: {e}")

    store = load_store()
    if not store:
        return []

    scored_results = []
    for record in store:
        doc_text = record["question"] if record["type"] == "sql" else record["doc_text"]
        doc_emb = record.get("embedding") or get_embedding(doc_text)
        score = cosine_similarity(query_emb, doc_emb)
        scored_results.append((score, record))
        
    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_matches = [r[1] for r in scored_results if r[0] > 0.4][:top_k]
    
    return top_matches

if __name__ == "__main__":
    add_training_data("What are the top 5 artists by track count?", "SELECT ar.Name, COUNT(t.TrackId) FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId JOIN Track t ON al.AlbumId = t.AlbumId GROUP BY ar.Name ORDER BY COUNT(t.TrackId) DESC LIMIT 5", type="sql")
    print(get_relevant_context("Who are the best selling musicians?"))
