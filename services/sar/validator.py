from shared.schemas.case import CaseResponse


def validate_sar(
    sar_draft: str,
    case: CaseResponse,
    evidence_ids: list[str],
) -> tuple[str, list[str]]:
    unsupported_claims = []

    supported_values = {
        case.case_id,
        case.customer_id,
        case.suspected_typology,
        str(case.kyc_risk),
        str(case.aml_risk),
        str(case.fused_risk),
        str(case.uncertainty),
        str(case.priority),
        str(case.human_review_required),
    }

    for evidence_id in evidence_ids:
        supported_values.add(evidence_id)

    # Check whether the draft contains unsupported factual identifiers/values.
    # This is intentionally conservative; the LLM/RAG validator will be added later.
    for line in sar_draft.splitlines():
        line = line.strip()

        if not line:
            continue

        if ":" not in line:
            continue

        value = line.split(":", 1)[1].strip()

        if not value:
            continue

        if value == "UNKNOWN":
            continue

        if value.startswith("-"):
            value = value[1:].strip()

        if value not in supported_values and line.startswith(
            (
                "Case ID:",
                "Customer ID:",
                "Suspected Typology:",
            )
        ):
            unsupported_claims.append(value)

    status = "VALID" if not unsupported_claims else "INVALID"

    return status, unsupported_claims