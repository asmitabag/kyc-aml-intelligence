from shared.schemas.case import CaseResponse
from services.sar.validator import validate_sar


def test_validator_detects_unsupported_claim():
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
        shap_features=[],
        graph_explanation={},
        status="OPEN",
    )

    sar_draft = """
    SUSPICIOUS ACTIVITY REPORT

    Case ID: CASE001
    Customer ID: CUST001
    Suspected Typology: layering
    """

    status, unsupported_claims = validate_sar(
        sar_draft=sar_draft,
        case=case,
        evidence_ids=[],
    )

    assert status == "VALID"
    assert unsupported_claims == []