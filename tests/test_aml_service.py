from services.aml_gnn.service import run_aml_analysis


def test_mock_aml_service():

    result = run_aml_analysis("CASE001")

    assert result.case_id == "CASE001"
    assert 0.0 <= result.aml_risk <= 1.0
    assert result.suspected_typology == "layering"
    assert len(result.suspicious_transaction_ids) > 0
    assert len(result.suspicious_account_ids) > 0