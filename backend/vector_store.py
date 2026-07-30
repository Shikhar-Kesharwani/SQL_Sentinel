import json
import uuid
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

load_dotenv()

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

STORE_PATH = Path(__file__).parent / "context_store.json"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "sql-sentinel")

try:
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    embedder = None

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
    if embedder is None:
        raise RuntimeError("Embedding model failed to load.")
        
    text_to_encode = question if type == "sql" else doc_text
    emb = embedder.encode(text_to_encode).tolist()
    record_id = str(uuid.uuid4())[:8]
    
    if is_pinecone() and index is not None:
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
        index.delete(ids=[record_id])
        return

    store = load_store()
    new_store = [r for r in store if r["id"] != record_id]
    save_store(new_store)


def get_relevant_context(query: str, top_k: int = 3):
    if embedder is None:
        return []
        
    query_emb = embedder.encode(query).tolist()
    
    if is_pinecone() and index is not None:
        res = index.query(vector=query_emb, top_k=top_k, include_metadata=True)
        top_matches = []
        for match in res.get("matches", []):
            if match.get("score", 0) > 0.4:
                top_matches.append(match.get("metadata"))
        return top_matches

    store = load_store()
    if not store:
        return []

    query_tensor = embedder.encode(query, convert_to_tensor=True)
    scored_results = []
    for record in store:
        doc_emb = embedder.encode(record["question"] if record["type"] == "sql" else record["doc_text"], convert_to_tensor=True)
        score = util.cos_sim(query_tensor, doc_emb).item()
        scored_results.append((score, record))
        
    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_matches = [r[1] for r in scored_results if r[0] > 0.4][:top_k]
    
    return top_matches

if __name__ == "__main__":
    # Test
    add_training_data("What are the top 5 artists by track count?", "SELECT ar.Name, COUNT(t.TrackId) FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId JOIN Track t ON al.AlbumId = t.AlbumId GROUP BY ar.Name ORDER BY COUNT(t.TrackId) DESC LIMIT 5", type="sql")
    print(get_relevant_context("Who are the best selling musicians?"))
