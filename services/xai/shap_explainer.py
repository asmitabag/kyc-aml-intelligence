import numpy as np
import shap


FEATURE_NAMES = [
    "kyc_risk",
    "aml_risk",
]


def triage_model(X):
    """
    X columns:
    [kyc_risk, aml_risk]

    Returns fused risk.
    """

    kyc_risk = X[:, 0]
    aml_risk = X[:, 1]

    return 0.4 * kyc_risk + 0.6 * aml_risk


def explain_risk(
    kyc_risk: float,
    aml_risk: float
) -> list[dict]:

    background = np.array([
        [0.0, 0.0],
        [0.5, 0.5],
        [1.0, 1.0],
    ])

    sample = np.array([
        [kyc_risk, aml_risk]
    ])

    explainer = shap.Explainer(
        triage_model,
        background,
        feature_names=FEATURE_NAMES
    )

    explanation = explainer(sample)

    values = explanation.values[0]

    results = []

    for name, value, shap_value in zip(
        FEATURE_NAMES,
        sample[0],
        values
    ):
        results.append({
            "feature": name,
            "value": round(float(value), 4),
            "importance": round(float(shap_value), 4)
        })

    return sorted(
        results,
        key=lambda x: abs(x["importance"]),
        reverse=True
    )