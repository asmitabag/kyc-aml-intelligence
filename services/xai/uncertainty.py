def calculate_uncertainty(
    kyc_risk: float,
    aml_risk: float
) -> float:
    """
    Estimate uncertainty from disagreement between KYC and AML risk.
    """

    disagreement = abs(kyc_risk - aml_risk)

    # Maximum disagreement = 1.0
    uncertainty = disagreement

    return round(float(uncertainty), 4)


def requires_human_review(
    fused_risk: float,
    uncertainty: float,
    risk_threshold: float = 0.8,
    uncertainty_threshold: float = 0.2
) -> bool:
    """
    Send high-risk or highly uncertain cases to human review.
    """

    return (
        fused_risk >= risk_threshold
        or uncertainty >= uncertainty_threshold
    )