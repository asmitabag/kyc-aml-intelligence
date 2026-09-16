from shared.schemas.case import CaseResponse
from services.sar.service import generate_sar


def test_generate_sar():
    case = CaseResponse(
        case_id="CASE001",
        customer_id="CUST001",
        kyc_risk=0.70,
        aml_risk=0.91,
        fused_risk=0.826,
        uncertainty=0.21,
        priority="HIGH",
        human_review_required=True,
        suspected_typology="layering",
        shap_features=[
            {
                "feature": "aml_risk",
                "value": 0.91,
                "importance": 0.246,
            }
        ],
        graph_explanation={
            "nodes": ["A001", "A002"],
            "edges": [
                {
                    "source": "A001",
                    "target": "A002",
                    "transaction_id": "T001",
                    "importance": 0.87,
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

    assert result.case_id == "CASE001"
    assert "CASE001" in result.sar_draft
    assert "CUST001" in result.sar_draft
    assert "layering" in result.sar_draft
    assert "T001" in result.evidence_ids_used
    assert "aml_risk" in result.evidence_ids_used
    assert "transaction_amount" in result.evidence_ids_used
    assert result.validation_status == "VALID"
    assert result.unsupported_claims == []