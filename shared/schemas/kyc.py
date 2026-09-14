from pydantic import BaseModel, Field


class KYCResponse(BaseModel):
    customer_id: str

    document_tamper_probability: float = Field(ge=0.0, le=1.0)
    liveness_probability: float = Field(ge=0.0, le=1.0)
    deepfake_probability: float = Field(ge=0.0, le=1.0)

    kyc_risk: float = Field(ge=0.0, le=1.0)

    document_fingerprint: str

    tamper_mask_path: str | None = None

    evidence_ids: list[str]