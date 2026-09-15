from shared.schemas.kyc import KYCResponse
from shared.schemas.aml import AMLResponse


def generate_feature_explanations(
    kyc: KYCResponse,
    aml: AMLResponse
) -> list[dict]:

    features = []

    features.append({
        "feature": "aml_risk",
        "value": aml.aml_risk,
        "importance": round(0.6 * aml.aml_risk, 4)
    })

    features.append({
        "feature": "kyc_risk",
        "value": kyc.kyc_risk,
        "importance": round(0.4 * kyc.kyc_risk, 4)
    })

    features.append({
        "feature": "document_tamper_probability",
        "value": kyc.document_tamper_probability,
        "importance": round(
            0.4 * kyc.document_tamper_probability,
            4
        )
    })

    features.append({
        "feature": "liveness_probability",
        "value": kyc.liveness_probability,
        "importance": round(
            0.4 * (1 - kyc.liveness_probability),
            4
        )
    })

    features.append({
        "feature": "deepfake_probability",
        "value": kyc.deepfake_probability,
        "importance": round(
            0.4 * kyc.deepfake_probability,
            4
        )
    })

    return sorted(
        features,
        key=lambda x: x["importance"],
        reverse=True
    )