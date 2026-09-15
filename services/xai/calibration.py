import numpy as np


def calculate_ece(
    probabilities: list[float],
    labels: list[int],
    n_bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE).

    probabilities: predicted probabilities for the positive class
    labels: actual binary labels
    """

    probabilities = np.asarray(probabilities)
    labels = np.asarray(labels)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]

        if i == n_bins - 1:
            mask = (probabilities >= lower) & (probabilities <= upper)
        else:
            mask = (probabilities >= lower) & (probabilities < upper)

        if not np.any(mask):
            continue

        confidence = probabilities[mask].mean()
        accuracy = labels[mask].mean()

        ece += (
            np.sum(mask) / len(probabilities)
        ) * abs(accuracy - confidence)

    return round(float(ece), 4)