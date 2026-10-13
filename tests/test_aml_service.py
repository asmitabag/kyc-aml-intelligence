from services.aml_gnn.service import run_aml_analysis
from services.model_adapters.contracts import ModelStatus


def test_aml_service_is_explicitly_unavailable_without_adapter():
    result = run_aml_analysis({"case_id": "CASE001"})

    assert result.status is ModelStatus.UNAVAILABLE
    assert result.score is None
    assert result.output is None