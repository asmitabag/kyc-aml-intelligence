from typing import Any, Optional

from pydantic import BaseModel


class CaseResponse(BaseModel):
    case_id: str
    customer_id: Optional[str] = None
    kyc_risk: Optional[float] = None
    aml_risk: Optional[float] = None
    fused_risk: Optional[float] = None
    uncertainty: Optional[float] = None
    priority: Optional[str] = None
    human_review_required: bool = False
    suspected_typology: Optional[str] = None
    shap_features: Optional[list[dict[str, Any]]] = None
    graph_explanation: Optional[dict[str, Any]] = None
    status: str

    class Config:
        from_attributes = True


class CaseStatusUpdate(BaseModel):
    status: str


class CaseFeedback(BaseModel):
    analyst_decision: str
    comment: Optional[str] = None