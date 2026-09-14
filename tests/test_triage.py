from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from services.xai.triage import create_triage


def test_high_risk_triage():

    kyc = KYCResponse(
        customer_id="C001",
        document_tamper_probability=0.20,
        liveness_probability=0.95,
        deepfake_probability=0.05,
        kyc_risk=0.70,
        document_fingerprint="DOC001",
        evidence_ids=["E001"]
    )

    aml = AMLResponse(
        case_id="CASE001",
        aml_risk=0.91,
        suspected_typology="layering",
        suspicious_transaction_ids=["T001"],
        suspicious_account_ids=["A001"],
        explanation_subgraph={"nodes": ["A001", "A002"]},
        graph_features={"degree": 12}
    )

    result = create_triage(kyc, aml)

    assert result.case_id == "CASE001"
    assert result.fused_risk == 0.826
    assert result.priority == "HIGH"
    assert result.human_review_required is True