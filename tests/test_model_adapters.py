import pytest

from services.model_adapters.contracts import InferenceResult, ModelStatus
from services.model_adapters.gnn import UnavailableGNNAdapter
from services.model_adapters.risk import RiskComponent, fuse_available_scores
from services.model_adapters.xgboost import UnavailableXGBoostAdapter
from services.xai.triage import alert_required, fuse_component_scores


def available(name: str, score: float) -> InferenceResult[object]:
    return InferenceResult(name, ModelStatus.AVAILABLE, score=score)


def test_unavailable_adapters_preserve_null_score():
    gnn = UnavailableGNNAdapter().analyze({})
    xgb = UnavailableXGBoostAdapter().predict([])

    assert gnn.status is ModelStatus.UNAVAILABLE
    assert xgb.status is ModelStatus.UNAVAILABLE
    assert gnn.score is None
    assert xgb.score is None


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_inference_result_rejects_invalid_scores(score):
    with pytest.raises(ValueError, match="between 0 and 1"):
        InferenceResult("test", ModelStatus.AVAILABLE, score=score)


def test_fusion_renormalizes_available_components():
    result = fuse_component_scores(
        available("kyc", 0.5),
        InferenceResult("aml", ModelStatus.UNAVAILABLE),
    )
    assert result == 0.5

    result = fuse_available_scores(
        [
            RiskComponent("kyc", available("kyc", 0.5), 0.4),
            RiskComponent("aml", available("aml", 1.0), 0.6),
        ]
    )
    assert result == 0.8


def test_fusion_returns_none_when_no_component_is_available():
    assert fuse_available_scores(
        [RiskComponent("aml", InferenceResult("aml", ModelStatus.UNAVAILABLE), 0.6)]
    ) is None


@pytest.mark.parametrize(
    ("score", "threshold", "expected"),
    [(0.8, 0.8, True), (0.7999, 0.8, False), (None, 0.8, False)],
)
def test_alert_threshold_is_inclusive_and_configurable(score, threshold, expected):
    assert alert_required(score, threshold) is expected


def test_alert_threshold_must_be_in_range():
    with pytest.raises(ValueError, match="between 0 and 1"):
        alert_required(0.9, 1.1)
