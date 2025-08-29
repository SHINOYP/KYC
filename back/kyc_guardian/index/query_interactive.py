"""
Query the FAISS index for possible matches.
"""

import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

INDEX_DIR = Path("data/index")
MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def load_index():
    index = faiss.read_index(str(INDEX_DIR / "kyc.index"))
    with open(INDEX_DIR / "records.json", "r", encoding="utf-8") as f:
        records = json.load(f)
    return index, records

def search(query: str, top_k: int = 5):
    index, records = load_index()
    emb = MODEL.encode([query], convert_to_numpy=True)
    D, I = index.search(emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        rec = records[idx]
        rec["similarity"] = float(score)
        results.append(rec)
    return results

if __name__ == "__main__":
    q = input("Enter a name to search: ")
    results = search(q)
    for r in results:
        print(r["source"], r["name"], "-> similarity:", r["similarity"])
