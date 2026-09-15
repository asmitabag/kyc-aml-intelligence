from services.xai.calibration import calculate_ece


def test_ece_perfect_calibration():
    probabilities = [0.0, 1.0, 0.0, 1.0]
    labels = [0, 1, 0, 1]

    ece = calculate_ece(probabilities, labels)

    assert ece == 0.0