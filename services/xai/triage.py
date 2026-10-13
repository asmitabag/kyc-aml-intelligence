from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.triage import TriageResponse
# from services.xai.explanation import generate_feature_explanations
from services.xai.shap_explainer import explain_risk

from services.xai.uncertainty import (
    calculate_uncertainty,
    requires_human_review
)
from services.model_adapters.contracts import InferenceResult
from services.model_adapters.risk import RiskComponent, fuse_available_scores


def calculate_fused_risk(kyc_risk: float, aml_risk: float) -> float:
    return round(0.4 * kyc_risk + 0.6 * aml_risk, 4)


def fuse_component_scores(
    kyc_result: InferenceResult[object],
    aml_result: InferenceResult[object],
) -> float | None:
    return fuse_available_scores(
        [
            RiskComponent("kyc", kyc_result, 0.4),
            RiskComponent("aml", aml_result, 0.6),
        ]
    )


def alert_required(score: float | None, threshold: float = 0.8) -> bool:
    """Return whether a valid fused score reaches the inclusive threshold."""

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Alert threshold must be between 0 and 1")
    return score is not None and score >= threshold


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

    # uncertainty = calculate_uncertainty(
    #     kyc.kyc_risk,
    #     aml.aml_risk
    # )

    uncertainty = calculate_uncertainty(
    kyc.kyc_risk,
    aml.aml_risk
)

    human_review = requires_human_review(
        fused_risk,
        uncertainty
    )

    explanations = explain_risk(
        kyc.kyc_risk,
        aml.aml_risk
    )

    return TriageResponse(
        case_id=aml.case_id,
        fused_risk=fused_risk,
        uncertainty=uncertainty,
        priority=priority,
        human_review_required=human_review,
        shap_features=explanations,
        graph_explanation=aml.explanation_subgraph
    )