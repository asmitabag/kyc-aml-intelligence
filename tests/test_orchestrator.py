from shared.schemas.kyc import KYCResponse
from services.xai.orchestrator import run_case_triage
import pytest


def test_case_triage_requires_available_gnn():

    kyc = KYCResponse(
        customer_id="C001",
        document_tamper_probability=0.20,
        liveness_probability=0.95,
        deepfake_probability=0.05,
        kyc_risk=0.70,
        document_fingerprint="DOC001",
        evidence_ids=["E001"]
    )

    with pytest.raises(RuntimeError, match="GNN model artifact and runtime adapter are not available"):
        run_case_triage("CASE001", kyc)