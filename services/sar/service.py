from shared.schemas.sar import SARResponse
from shared.schemas.case import CaseResponse
from services.sar.validator import validate_sar
from services.sar.retriever import retrieve_fincen_guidance
from services.sar.generator import generate_grounded_sar


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

    # Retrieve relevant FinCEN guidance
    query = (
        f"suspicious activity report "
        f"{case.suspected_typology or ''} "
        f"transaction evidence narrative"
    )

    fincen_guidance = retrieve_fincen_guidance(query)

    fincen_sources = list(
        dict.fromkeys(
            document["source_file"]
            for document in fincen_guidance
        )
    )

    grounding_context = "\n".join(
        f"[Source: {document['source_file']} | "
        f"Chunk: {document['chunk_id']} | "
        f"Score: {document['retrieval_score']}]\n"
        f"{document['content']}"
        for document in fincen_guidance
    )

    # Build case-specific evidence for Gemini
    case_context = f"""
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

Evidence IDs:
{", ".join(evidence_ids) if evidence_ids else "No evidence identifiers available."}

SHAP Features:
{case.shap_features or "No SHAP features available."}

Graph Explanation:
{case.graph_explanation or "No graph explanation available."}
""".strip()

    # Generate the SAR narrative using case evidence + retrieved FinCEN guidance
    sar_draft = generate_grounded_sar(
        case_context=case_context,
        fincen_context=(
            grounding_context
            if grounding_context
            else "No relevant FinCEN guidance retrieved."
        ),
    )

    # Validate the generated SAR against the known case evidence
    validation_status, unsupported_claims = validate_sar(
        sar_draft=sar_draft,
        case=case,
        evidence_ids=evidence_ids,
    )

    return SARResponse(
        case_id=case.case_id,
        sar_draft=sar_draft,
        evidence_ids_used=evidence_ids,
        fincen_sources_used=fincen_sources,
        validation_status=validation_status,
        unsupported_claims=unsupported_claims,
    )