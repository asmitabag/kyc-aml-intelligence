from shared.schemas.kyc import KYCResponse
from shared.schemas.aml import AMLResponse
from shared.schemas.triage import TriageResponse
from shared.schemas.sar import SARResponse


def test_kyc_schema():
    data = KYCResponse(
        customer_id="C001",
        document_tamper_probability=0.12,
        liveness_probability=0.95,
        deepfake_probability=0.04,
        kyc_risk=0.15,
        document_fingerprint="DOC001",
        evidence_ids=["E001", "E002"]
    )

    assert data.customer_id == "C001"


def test_aml_schema():
    data = AMLResponse(
        case_id="CASE001",
        aml_risk=0.91,
        suspected_typology="layering",
        suspicious_transaction_ids=["T001", "T002"],
        suspicious_account_ids=["A001", "A002"],
        explanation_subgraph={},
        graph_features={}
    )

    assert data.aml_risk == 0.91


def test_triage_schema():
    data = TriageResponse(
        case_id="CASE001",
        fused_risk=0.94,
        uncertainty=0.08,
        priority="HIGH",
        human_review_required=True,
        shap_features=[],
        graph_explanation={
            "nodes": [],
            "edges": [],
            "important_features": []
        }
    )

    assert data.human_review_required is True


def test_sar_schema():
    data = SARResponse(
        case_id="CASE001",
        sar_draft="Suspicious activity was observed.",
        evidence_ids_used=["E001"],
        validation_status="PASS",
        unsupported_claims=[]
    )

    assert data.validation_status == "PASS"