import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer




PROC = Path("data/processed")
INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def build_index():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Load normalized data
    path = PROC / "all.jsonl"
    if not path.exists():
        print("!! no processed data found. Run normalize first.")
        return

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    texts = [r.get("name", "") + " " + str(r.get("dob", "")) for r in records]
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")

    # Create FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index + records
    faiss.write_index(index, str(INDEX_DIR / "kyc.index"))
    with open(INDEX_DIR / "records.json", "w", encoding="utf-8") as f:
        json.dump(records, f)

    print(f"Built FAISS index with {len(records)} records, dim={dim}")
    print(f"Saved to {INDEX_DIR}")

if __name__ == "__main__":
    build_index()
