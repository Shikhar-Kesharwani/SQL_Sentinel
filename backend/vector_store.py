import json
import uuid
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

STORE_PATH = Path(__file__).parent / "context_store.json"

# Load embedding model (same one used in hallucination detector)
try:
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    # If the model download fails due to network issues, handle gracefully later
    embedder = None


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
    """Add a new training example (SQL query or Documentation)."""
    if embedder is None:
        raise RuntimeError("Embedding model failed to load.")
        
    store = load_store()
    
    # Text to encode: if SQL, encode the question. If docs, encode the doc.
    text_to_encode = question if type == "sql" else doc_text
    
    emb = embedder.encode(text_to_encode).tolist()
    
    record = {
        "id": str(uuid.uuid4())[:8],
        "type": type,
        "question": question,
        "sql": sql,
        "doc_text": doc_text,
        "embedding": emb
    }
    
    store.append(record)
    save_store(store)
    return record["id"]


def remove_training_data(record_id: str):
    store = load_store()
    new_store = [r for r in store if r["id"] != record_id]
    save_store(new_store)


def get_relevant_context(query: str, top_k: int = 3):
    """Retrieve the top K most similar training examples to the query."""
    if embedder is None:
        return []
        
    store = load_store()
    if not store:
        return []

    # Create tensor of all embeddings
    query_emb = embedder.encode(query, convert_to_tensor=True)
    
    scored_results = []
    for record in store:
        # Convert list back to tensor for cosine similarity
        doc_emb = embedder.encode(record["question"] if record["type"] == "sql" else record["doc_text"], convert_to_tensor=True)
        score = util.cos_sim(query_emb, doc_emb).item()
        scored_results.append((score, record))
        
    # Sort by descending score
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # Filter out low-confidence matches (threshold 0.4) and return top_k
    top_matches = [r[1] for r in scored_results if r[0] > 0.4][:top_k]
    
    return top_matches

if __name__ == "__main__":
    # Test
    add_training_data("What are the top 5 artists by track count?", "SELECT ar.Name, COUNT(t.TrackId) FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId JOIN Track t ON al.AlbumId = t.AlbumId GROUP BY ar.Name ORDER BY COUNT(t.TrackId) DESC LIMIT 5", type="sql")
    print(get_relevant_context("Who are the best selling musicians?"))
