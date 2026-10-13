from typing import Literal, Optional

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    customer_id: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    customer_type: Literal["INDIVIDUAL", "BUSINESS"] = "INDIVIDUAL"
    data_origin: Literal["SYNTHETIC", "CONSENTED_DEMO", "IMPORTED"] = "CONSENTED_DEMO"


class AccountCreate(BaseModel):
    account_id: Optional[str] = None
    customer_id: Optional[str] = None
    account_type: str = "CHECKING"
    status: str = "ACTIVE"
    balance: float = 0.0
    currency: str = "USD"


class TransactionCreate(BaseModel):
    transaction_id: Optional[str] = None
    account_id: str
    direction: Literal["DEBIT", "CREDIT"]
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    description: Optional[str] = None
    counterparty: Optional[str] = None
    status: str = "COMPLETED"


class AlertUpdate(BaseModel):
    status: str = "OPEN"
    severity: Optional[str] = None
    narrative: Optional[str] = None


class RiskAssessmentCreate(BaseModel):
    assessment_id: Optional[str] = None
    customer_id: str
    case_id: Optional[str] = None
    kyc_risk: float = Field(ge=0.0, le=1.0)
    aml_risk: float = Field(ge=0.0, le=1.0)
    fused_risk: float = Field(ge=0.0, le=1.0)
    uncertainty: Optional[float] = None
    priority: Optional[str] = None
    human_review_required: bool = False
    suspected_typology: Optional[str] = None
    status: str = "OPEN"
    gnn_risk: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    xgboost_risk: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    final_risk: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[str] = None
    top_risk_factors: Optional[list[str]] = None
    gnn_model_version: Optional[str] = None
    xgboost_model_version: Optional[str] = None


class KYCSubmit(BaseModel):
    document_tamper_probability: float = Field(..., ge=0.0, le=1.0)
    liveness_probability: float = Field(..., ge=0.0, le=1.0)
    deepfake_probability: float = Field(..., ge=0.0, le=1.0)
    kyc_risk: float = Field(..., ge=0.0, le=1.0)
    document_fingerprint: str
    evidence_ids: list[str] = Field(default_factory=list)
    model_version: str = "unavailable"


class AlertCreate(BaseModel):
    alert_id: Optional[str] = None
    customer_id: str
    assessment_id: Optional[str] = None
    alert_type: str = "TRANSACTION_PATTERN"
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    status: Literal["OPEN", "UNDER_REVIEW", "CLOSED"] = "OPEN"
    narrative: Optional[str] = None
    account_id: Optional[str] = None
    case_id: Optional[str] = None
    reason_code: Optional[str] = None


class SARDraftCreate(BaseModel):
    alert_id: Optional[str] = None
    case_id: Optional[str] = None
    customer_id: str
    narrative: str
    evidence_ids_used: list[str] = Field(default_factory=list)
    fincen_sources_used: list[str] = Field(default_factory=list)
    validation_status: Literal["VALID", "INVALID", "NEEDS_REVIEW"] = "VALID"
    unsupported_claims: list[str] = Field(default_factory=list)
    review_status: Literal["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"] = "DRAFT"


class SARStatusUpdate(BaseModel):
    status: Literal["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"]


class FeedbackCreate(BaseModel):
    customer_id: str
    alert_id: Optional[str] = None
    assessment_id: Optional[str] = None
    decision: Literal["CONFIRMED", "FALSE_POSITIVE", "NEEDS_MORE_INVESTIGATION"]
    rationale: Optional[str] = None
    model_versions: dict[str, str] = Field(default_factory=dict)
