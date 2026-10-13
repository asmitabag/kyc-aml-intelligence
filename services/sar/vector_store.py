import json
from pathlib import Path

import faiss
import numpy as np


EMBEDDINGS_PATH = Path("data/fincen/chunks/fincen_embeddings.json")
INDEX_DIR = Path("data/fincen/index")

INDEX_PATH = INDEX_DIR / "fincen.index"
METADATA_PATH = INDEX_DIR / "metadata.json"


def build_faiss_index() -> None:
    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        raise ValueError("No embeddings found.")

    embeddings = np.array(
        [chunk["embedding"] for chunk in chunks],
        dtype=np.float32,
    )

    # Embeddings were normalized during generation,
    # so inner product = cosine similarity.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    metadata = []

    for chunk in chunks:
        metadata.append(
            {
                "chunk_id": chunk["chunk_id"],
                "source_file": chunk["source_file"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
            }
        )

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Indexed chunks: {index.ntotal}")
    print(f"Vector dimension: {index.d}")
    print(f"Index saved to: {INDEX_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")


if __name__ == "__main__":
    build_faiss_index()