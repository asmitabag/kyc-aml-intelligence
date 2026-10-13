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

    # Fields whose values must come directly from verified case data.
    factual_fields = (
        "Case ID:",
        "Customer ID:",
        "KYC Risk:",
        "AML Risk:",
        "Fused Risk:",
        "Uncertainty:",
        "Priority:",
        "Suspected Typology:",
        "Human Review Required:",
    )

    for line in sar_draft.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        field, value = line.split(":", 1)
        field = field.strip() + ":"
        value = value.strip()

        if field not in factual_fields:
            continue

        if not value or value == "UNKNOWN":
            continue

        if value not in supported_values:
            unsupported_claims.append(
                f"{field} {value}"
            )

    status = "VALID" if not unsupported_claims else "INVALID"

    return status, unsupported_claims