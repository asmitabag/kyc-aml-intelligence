from services.sar.retriever import retrieve_fincen_guidance


def test_semantic_retrieval():
    results = retrieve_fincen_guidance(
        "What information should be included in a suspicious activity report narrative?",
        top_k=3,
    )

    assert len(results) == 3

    for result in results:
        assert "chunk_id" in result
        assert "source_file" in result
        assert "content" in result
        assert "retrieval_score" in result

        assert result["content"]


def test_semantic_retrieval_returns_relevant_content():
    results = retrieve_fincen_guidance(
        "SAR narrative who what when where why how",
        top_k=3,
    )

    assert len(results) > 0

    combined_text = " ".join(
        result["content"].lower()
        for result in results
    )

    assert (
        "narrative" in combined_text
        or "suspicious" in combined_text
        or "sar" in combined_text
    )