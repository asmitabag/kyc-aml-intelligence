def selective_prediction(
    fused_risk: float,
    uncertainty: float,
    uncertainty_threshold: float = 0.2
) -> dict:
    """
    Decide whether the system should make an automatic decision
    or defer to human review.
    """

    if uncertainty >= uncertainty_threshold:
        return {
            "decision": "DEFER",
            "human_review_required": True
        }

    if fused_risk >= 0.8:
        return {
            "decision": "DEFER",
            "human_review_required": True
        }

    return {
        "decision": "AUTO",
        "human_review_required": False
    }