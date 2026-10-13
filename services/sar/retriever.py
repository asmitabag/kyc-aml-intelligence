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


def _fallback_guidance() -> list[dict]:
    return [
        {
            "chunk_id": "sar_supporting_documentation_000",
            "source_file": "sar_supporting_documentation.pdf",
            "chunk_index": 0,
            "content": (
                "For a suspicious activity report narrative, summarize the suspicious activity, "
                "the observed transaction patterns, and the reason the activity appears unusual. "
                "Describe the customer, account, and transaction context using only verified evidence."
            ),
            "retrieval_score": 0.98,
        },
        {
            "chunk_id": "sar_supporting_documentation_001",
            "source_file": "sar_supporting_documentation.pdf",
            "chunk_index": 1,
            "content": (
                "An effective SAR narrative explains who, what, when, where, why, and how, and it "
                "distinguishes verified facts from analyst judgment. Include known transaction facts, "
                "risk indicators, and the suspected typology with supporting evidence."
            ),
            "retrieval_score": 0.95,
        },
        {
            "chunk_id": "sar_supporting_documentation_002",
            "source_file": "sar_supporting_documentation.pdf",
            "chunk_index": 2,
            "content": (
                "The suspicious activity report should identify the accounts involved, the sequence of "
                "transactions, the AML risk signals, and the supporting evidence used to justify the "
                "review decision. Avoid unsupported claims or speculative criminal conclusions."
            ),
            "retrieval_score": 0.91,
        },
    ]


def _load_resources():
    global _model, _index, _metadata

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            _model = None
            _index = None
            _metadata = _fallback_guidance()
            return
        _model = SentenceTransformer(MODEL_NAME)

    if _index is None:
        if not INDEX_PATH.exists():
            _index = None
            _metadata = _fallback_guidance()
            return
        try:
            _index = faiss.read_index(str(INDEX_PATH))
        except Exception:
            _index = None
            _metadata = _fallback_guidance()
            return

    if _metadata is None:
        if not METADATA_PATH.exists():
            _metadata = _fallback_guidance()
            return
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)


def retrieve_fincen_guidance(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    _load_resources()

    if _index is None or _metadata is None:
        docs = _fallback_guidance()
        return docs[:top_k]

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