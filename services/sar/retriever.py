import json
from pathlib import Path

import faiss
import numpy as np


INDEX_PATH = Path("data/fincen/index/fincen.index")
METADATA_PATH = Path("data/fincen/index/metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"


_model = None
_index = None
_metadata = None


def _load_resources():
    global _model, _index, _metadata

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise RuntimeError(
                "FinCEN retrieval is unavailable because the embedding runtime "
                "could not be loaded."
            ) from exc
        _model = SentenceTransformer(MODEL_NAME)

    if _index is None:
        _index = faiss.read_index(str(INDEX_PATH))

    if _metadata is None:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)


def retrieve_fincen_guidance(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    _load_resources()

    query_embedding = _model.encode(
        [query],
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32,
    )

    scores, indices = _index.search(
        query_embedding,
        top_k,
    )

    results = []

    for score, index in zip(scores[0], indices[0]):
        if index < 0:
            continue

        document = _metadata[index]

        results.append(
            {
                "chunk_id": document["chunk_id"],
                "source_file": document["source_file"],
                "chunk_index": document["chunk_index"],
                "content": document["content"],
                "retrieval_score": round(float(score), 4),
            }
        )

    return results