import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("data/fincen/chunks/fincen_chunks.json")
EMBEDDINGS_PATH = Path("data/fincen/chunks/fincen_embeddings.json")

MODEL_NAME = "all-MiniLM-L6-v2"


def generate_embeddings() -> None:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        raise ValueError("No chunks found.")

    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["content"] for chunk in chunks]

    print(f"Generating embeddings for {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    output = []

    for chunk, embedding in zip(chunks, embeddings):
        output.append(
            {
                **chunk,
                "embedding": embedding.tolist(),
            }
        )

    with open(EMBEDDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Saved embeddings to: {EMBEDDINGS_PATH}")
    print(f"Embedding dimension: {len(embeddings[0])}")


if __name__ == "__main__":
    generate_embeddings()