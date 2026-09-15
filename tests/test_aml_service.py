from services.aml_gnn.service import run_aml_analysis


def test_aml_service():
    result = run_aml_analysis("CASE001")

    assert result.case_id == "CASE001"
    assert result.aml_risk == 0.91

    assert "nodes" in result.explanation_subgraph
    assert "edges" in result.explanation_subgraph
    assert "important_features" in result.explanation_subgraph