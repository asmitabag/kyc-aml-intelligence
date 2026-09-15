from services.xai.selective_prediction import selective_prediction


def test_defer_high_uncertainty():
    result = selective_prediction(0.6, 0.3)

    assert result["decision"] == "DEFER"
    assert result["human_review_required"] is True


def test_defer_high_risk():
    result = selective_prediction(0.9, 0.05)

    assert result["decision"] == "DEFER"
    assert result["human_review_required"] is True


def test_auto_low_risk():
    result = selective_prediction(0.4, 0.05)

    assert result["decision"] == "AUTO"
    assert result["human_review_required"] is False