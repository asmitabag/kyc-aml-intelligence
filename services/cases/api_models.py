from pydantic import BaseModel, Field
from typing import Literal


class CustomerCreate(BaseModel):
    customer_id: str | None = None
    full_name: str
    email: str | None = None
    phone: str | None = None
    customer_type: Literal["INDIVIDUAL", "BUSINESS"] = "INDIVIDUAL"
    data_origin: Literal["SYNTHETIC", "CONSENTED_DEMO", "IMPORTED"] = "CONSENTED_DEMO"


class AccountCreate(BaseModel):
    account_id: str | None = None
    customer_id: str | None = None
    account_type: str = "CHECKING"
    status: str = "ACTIVE"
    balance: float = 0.0
    currency: str = "USD"


class TransactionCreate(BaseModel):
    transaction_id: str | None = None
    account_id: str
    direction: Literal["DEBIT", "CREDIT"]
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    description: str | None = None
    counterparty: str | None = None
    status: str = "COMPLETED"


class AlertUpdate(BaseModel):
    status: str = "OPEN"
    severity: str | None = None
    narrative: str | None = None


class RiskAssessmentCreate(BaseModel):
    assessment_id: str | None = None
    customer_id: str
    case_id: str | None = None
    kyc_risk: float = Field(ge=0.0, le=1.0)
    aml_risk: float = Field(ge=0.0, le=1.0)
    fused_risk: float = Field(ge=0.0, le=1.0)
    uncertainty: float | None = None
    priority: str | None = None
    human_review_required: bool = False
    suspected_typology: str | None = None
    status: str = "OPEN"
    gnn_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    xgboost_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    final_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_level: str | None = None
    top_risk_factors: list[str] | None = None
    gnn_model_version: str | None = None
    xgboost_model_version: str | None = None


class KYCSubmit(BaseModel):
    document_tamper_probability: float = Field(..., ge=0.0, le=1.0)
    liveness_probability: float = Field(..., ge=0.0, le=1.0)
    deepfake_probability: float = Field(..., ge=0.0, le=1.0)
    kyc_risk: float = Field(..., ge=0.0, le=1.0)
    document_fingerprint: str
    evidence_ids: list[str] = Field(default_factory=list)
    model_version: str = "unavailable"


class AlertCreate(BaseModel):
    alert_id: str | None = None
    customer_id: str
    assessment_id: str | None = None
    alert_type: str = "TRANSACTION_PATTERN"
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    status: Literal["OPEN", "UNDER_REVIEW", "CLOSED"] = "OPEN"
    narrative: str | None = None
    account_id: str | None = None
    case_id: str | None = None
    reason_code: str | None = None


class SARDraftCreate(BaseModel):
    alert_id: str | None = None
    case_id: str | None = None
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
    alert_id: str | None = None
    assessment_id: str | None = None
    decision: Literal["CONFIRMED", "FALSE_POSITIVE", "NEEDS_MORE_INVESTIGATION"]
    rationale: str | None = None
    model_versions: dict[str, str] = Field(default_factory=dict)
