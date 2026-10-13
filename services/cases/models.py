from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
)
from sqlalchemy.orm import relationship

from apps.api_gateway.database import Base

import secrets
from sqlalchemy import UniqueConstraint

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    customer_type = Column(String, default="INDIVIDUAL", nullable=False)
    data_origin = Column(String, default="CONSENTED_DEMO", nullable=False)
    kyc_status = Column(String, default="PENDING")
    onboarding_status = Column(String, default="IN_PROGRESS")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    assessments = relationship("RiskAssessment", back_populates="customer", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="customer", cascade="all, delete-orphan")
    kyc_results = relationship("KYCResult", back_populates="customer", cascade="all, delete-orphan")
    sar_drafts = relationship("SARDraft", back_populates="customer")
    documents = relationship("KYCDocument", back_populates="customer", cascade="all, delete-orphan")


class KYCResult(Base):
    __tablename__ = "kyc_results"

    kyc_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    document_tamper_probability = Column(Float, nullable=False)
    liveness_probability = Column(Float, nullable=False)
    deepfake_probability = Column(Float, nullable=False)
    kyc_risk = Column(Float, nullable=False)
    document_fingerprint = Column(String, nullable=False)
    evidence_ids = Column(JSON, default=list)
    model_version = Column(String, default="unavailable", nullable=False)
    status = Column(String, default="REVIEW", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="kyc_results")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    document_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)
    document_fingerprint = Column(String, nullable=True)
    status = Column(String, default="RECEIVED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="documents")


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    account_type = Column(String, default="CHECKING")
    status = Column(String, default="ACTIVE")
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.account_id",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    alerts = relationship("Alert", back_populates="account", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    to_account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True, index=True)
    direction = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    amount_decimal = Column(Numeric(18, 2), nullable=True)
    currency = Column(String, default="USD")
    description = Column(String, nullable=True)
    counterparty = Column(String, nullable=True)
    status = Column(String, default="COMPLETED")
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_origin = Column(String, default="SYNTHETIC", nullable=False)

    account = relationship(
        "Account",
        foreign_keys=[account_id],
        back_populates="transactions",
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    case_id = Column(String, nullable=True)
    kyc_risk = Column(Float, nullable=False)
    aml_risk = Column(Float, nullable=False)
    fused_risk = Column(Float, nullable=False)
    gnn_risk = Column(Float, nullable=True)
    xgboost_risk = Column(Float, nullable=True)
    final_risk = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    top_risk_factors = Column(JSON, nullable=True)
    gnn_model_version = Column(String, nullable=True)
    xgboost_model_version = Column(String, nullable=True)
    uncertainty = Column(Float, nullable=True)
    priority = Column(String, nullable=True)
    human_review_required = Column(Boolean, default=False)
    suspected_typology = Column(String, nullable=True)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="assessments")
    alerts = relationship("Alert", back_populates="assessment")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True, index=True)
    case_id = Column(String, nullable=True, index=True)
    assessment_id = Column(String, ForeignKey("risk_assessments.assessment_id"), nullable=True, index=True)
    reason_code = Column(String, nullable=True, index=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, default="MEDIUM")
    status = Column(String, default="OPEN")
    narrative = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    customer = relationship("Customer", back_populates="alerts")
    account = relationship("Account", back_populates="alerts")
    assessment = relationship("RiskAssessment", back_populates="alerts")
    sar_drafts = relationship("SARDraft", back_populates="alert")


class SARDraft(Base):
    __tablename__ = "sar_drafts"

    sar_id = Column(String, primary_key=True, index=True)
    case_id = Column(String, nullable=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=True, index=True)
    alert_id = Column(String, ForeignKey("alerts.alert_id"), nullable=True, index=True)
    narrative = Column(Text, nullable=False)
    evidence_ids_used = Column(JSON, nullable=True)
    fincen_sources_used = Column(JSON, nullable=True)
    validation_status = Column(String, default="VALID")
    review_status = Column(String, default="DRAFT", nullable=False)
    unsupported_claims = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    customer = relationship("Customer", back_populates="sar_drafts")
    alert = relationship("Alert", back_populates="sar_drafts")


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    feedback_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    alert_id = Column(String, ForeignKey("alerts.alert_id"), nullable=False, index=True)
    assessment_id = Column(String, nullable=True, index=True)
    decision = Column(String, nullable=False)
    rationale = Column(Text, nullable=True)
    model_versions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, index=True)

    customer_id = Column(String, nullable=True)

    kyc_risk = Column(Float, nullable=True)
    aml_risk = Column(Float, nullable=True)
    fused_risk = Column(Float, nullable=True)

    uncertainty = Column(Float, nullable=True)

    priority = Column(String, nullable=True)

    human_review_required = Column(Boolean, default=False)

    suspected_typology = Column(String, nullable=True)

    shap_features = Column(JSON, nullable=True)
    graph_explanation = Column(JSON, nullable=True)

    status = Column(String, default="OPEN")

    feedback = relationship(
        "CaseFeedback",
        back_populates="case",
        cascade="all, delete-orphan"
    )

class CaseFeedback(Base):
    __tablename__ = "case_feedback"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        String,
        ForeignKey("cases.case_id"),
        nullable=False
    )

    analyst_decision = Column(String, nullable=False)

    comment = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    case = relationship("Case", back_populates="feedback")

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="customer")
    customer_id = Column(
        String,
        ForeignKey("customers.customer_id"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer")