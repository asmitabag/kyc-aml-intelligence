from shared.schemas.sar import SARResponse
from shared.schemas.case import CaseResponse
from services.sar.validator import validate_sar


def generate_sar(case: CaseResponse) -> SARResponse:
    evidence_ids = []

    # Collect evidence from the existing case
    if case.shap_features:
        evidence_ids.extend(
            feature["feature"]
            for feature in case.shap_features
            if "feature" in feature
        )

    if case.graph_explanation:
        for edge in case.graph_explanation.get("edges", []):
            transaction_id = edge.get("transaction_id")
            if transaction_id:
                evidence_ids.append(transaction_id)

        for feature in case.graph_explanation.get("important_features", []):
            feature_name = feature.get("feature")
            if feature_name:
                evidence_ids.append(feature_name)

    # Remove duplicates while preserving order
    evidence_ids = list(dict.fromkeys(evidence_ids))

    sar_draft = f"""
SUSPICIOUS ACTIVITY REPORT

Case ID: {case.case_id}
Customer ID: {case.customer_id or "UNKNOWN"}

Risk Assessment:
- KYC Risk: {case.kyc_risk}
- AML Risk: {case.aml_risk}
- Fused Risk: {case.fused_risk}
- Uncertainty: {case.uncertainty}
- Priority: {case.priority}

Suspected Typology:
{case.suspected_typology or "UNKNOWN"}

Human Review Required:
{case.human_review_required}

Evidence Used:
{", ".join(evidence_ids) if evidence_ids else "No evidence identifiers available."}

This SAR draft was generated from the structured case data currently available.
Additional factual details should be added only when supported by verified evidence.
""".strip()

    validation_status, unsupported_claims = validate_sar(
        sar_draft=sar_draft,
        case=case,
        evidence_ids=evidence_ids,
    )

    return SARResponse(
        case_id=case.case_id,
        sar_draft=sar_draft,
        evidence_ids_used=evidence_ids,
        validation_status=validation_status,
        unsupported_claims=unsupported_claims,
    )