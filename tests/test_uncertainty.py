from services.xai.uncertainty import (
    calculate_uncertainty,
    requires_human_review
)


def test_uncertainty():
    assert calculate_uncertainty(0.7, 0.9) == 0.2


def test_human_review_high_risk():
    assert requires_human_review(
        fused_risk=0.85,
        uncertainty=0.05
    ) is True


def test_human_review_high_uncertainty():
    assert requires_human_review(
        fused_risk=0.6,
        uncertainty=0.25
    ) is True


def test_no_human_review():
    assert requires_human_review(
        fused_risk=0.4,
        uncertainty=0.05
    ) is False