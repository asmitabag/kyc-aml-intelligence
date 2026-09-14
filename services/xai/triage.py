from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.triage import TriageResponse


def calculate_fused_risk(kyc_risk: float, aml_risk: float) -> float:
    return round(0.4 * kyc_risk + 0.6 * aml_risk, 4)


def determine_priority(fused_risk: float) -> str:
    if fused_risk >= 0.8:
        return "HIGH"
    if fused_risk >= 0.5:
        return "MEDIUM"
    return "LOW"


def calculate_uncertainty(kyc_risk: float, aml_risk: float) -> float:
    return round(abs(kyc_risk - aml_risk), 4)


def create_triage(
    kyc: KYCResponse,
    aml: AMLResponse
) -> TriageResponse:

    fused_risk = calculate_fused_risk(
        kyc.kyc_risk,
        aml.aml_risk
    )

    priority = determine_priority(fused_risk)

    uncertainty = calculate_uncertainty(
        kyc.kyc_risk,
        aml.aml_risk
    )

    return TriageResponse(
        case_id=aml.case_id,
        fused_risk=fused_risk,
        uncertainty=uncertainty,
        priority=priority,
        human_review_required=priority == "HIGH",
        shap_features=[],
        graph_explanation=aml.explanation_subgraph
    )