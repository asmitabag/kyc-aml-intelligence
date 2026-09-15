from typing import Any
from pydantic import BaseModel


class CaseResponse(BaseModel):
    case_id: str
    customer_id: str | None = None
    kyc_risk: float | None = None
    aml_risk: float | None = None
    fused_risk: float | None = None
    uncertainty: float | None = None
    priority: str | None = None
    human_review_required: bool = False
    suspected_typology: str | None = None
    shap_features: list[dict[str, Any]] | None = None
    graph_explanation: dict[str, Any] | None = None
    status: str

    class Config:
        from_attributes = True


class CaseStatusUpdate(BaseModel):
    status: str

class CaseFeedback(BaseModel):
    analyst_decision: str
    comment: str | None = None