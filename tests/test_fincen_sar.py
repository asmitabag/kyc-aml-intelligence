from shared.schemas.case import CaseResponse
from services.sar.service import generate_sar


def test_sar_uses_fincen_guidance():
    case = CaseResponse(
        case_id="CASE_RAG_001",
        customer_id="CUST_RAG_001",
        kyc_risk=0.70,
        aml_risk=0.91,
        fused_risk=0.826,
        uncertainty=0.21,
        priority="HIGH",
        human_review_required=True,
        suspected_typology="layering",
        shap_features=[
            {"feature": "aml_risk", "value": 0.91, "importance": 0.246}
        ],
        graph_explanation={
            "edges": [
                {
                    "source": "A001",
                    "target": "A002",
                    "transaction_id": "T001",
                    "importance": 0.92,
                }
            ],
            "important_features": [
                {
                    "feature": "transaction_amount",
                    "importance": 0.91,
                }
            ],
        },
        status="OPEN",
    )

    result = generate_sar(case)

    assert result.fincen_sources_used
    assert "sar_supporting_documentation.pdf" in result.fincen_sources_used
    assert result.sar_draft
    assert result.validation_status == "VALID"
    assert result.unsupported_claims == []