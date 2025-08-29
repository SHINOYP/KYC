"""
Query the FAISS index for possible matches and display results in a table.
"""

import sys, json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from tabulate import tabulate  # pip install tabulate

INDEX_DIR = Path("data/index")
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def load_index():
    """Load FAISS index + corresponding records."""
    index = faiss.read_index(str(INDEX_DIR / "kyc.index"))
    with open(INDEX_DIR / "records.json", "r", encoding="utf-8") as f:
        records = json.load(f)
    return index, records

def search(query: str, top_k: int = 5):
    """Search a query string in the FAISS index."""
    index, records = load_index()
    emb = MODEL.encode([query], convert_to_numpy=True).astype("float32")
    D, I = index.search(emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        rec = records[idx]
        rec["distance"] = float(score)   # lower = better match
        results.append(rec)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m kyc_guardian.query '<name>'")
        sys.exit(1)

    q = sys.argv[1]
    results = search(q)

    print(f"\n🔎 Top matches for '{q}':\n")

    # Format results as a clean table
    table = []
    for r in results:
        table.append([
            r.get("source", ""),
            r.get("name", ""),
            r.get("dob", "").strip(),
            r.get("citizenship", "").strip(),
            round(r.get("distance", 3))
        ])

    headers = ["Source", "Name", "DOB", "Citizenship", "Distance"]
    print(tabulate(table, headers=headers, tablefmt="grid"))
