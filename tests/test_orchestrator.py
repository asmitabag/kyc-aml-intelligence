from shared.schemas.kyc import KYCResponse
from services.xai.orchestrator import run_case_triage


def test_case_triage_orchestration():

    kyc = KYCResponse(
        customer_id="C001",
        document_tamper_probability=0.20,
        liveness_probability=0.95,
        deepfake_probability=0.05,
        kyc_risk=0.70,
        document_fingerprint="DOC001",
        evidence_ids=["E001"]
    )

    result = run_case_triage("CASE001", kyc)

    assert result.case_id == "CASE001"
    assert result.fused_risk == 0.826
    assert result.priority == "HIGH"
    assert result.human_review_required is True