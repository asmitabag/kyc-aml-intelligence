from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from services.cases.models import (
    Account,
    Alert,
    Case,
    CaseFeedback,
    Customer,
    RiskAssessment,
    SARDraft,
    Transaction,
)
from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.triage import TriageResponse


def create_case(
    db: Session,
    kyc: KYCResponse,
    aml: AMLResponse,
    triage: TriageResponse,
):
    case = Case(
        case_id=triage.case_id,
        customer_id=kyc.customer_id,
        kyc_risk=kyc.kyc_risk,
        aml_risk=aml.aml_risk,
        fused_risk=triage.fused_risk,
        uncertainty=triage.uncertainty,
        priority=triage.priority,
        human_review_required=triage.human_review_required,
        suspected_typology=aml.suspected_typology,
        shap_features=triage.shap_features,
        graph_explanation=triage.graph_explanation.model_dump(),
        status="OPEN",
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return case


def get_cases(db: Session):
    return db.query(Case).all()


def get_case(db: Session, case_id: str):
    return db.query(Case).filter(Case.case_id == case_id).first()


def update_case_status(
    db: Session,
    case_id: str,
    status: str,
):
    case = get_case(db, case_id)

    if case is None:
        return None

    case.status = status

    db.commit()
    db.refresh(case)

    return case


def add_case_feedback(
    db: Session,
    case_id: str,
    analyst_decision: str,
    comment: Optional[str] = None,
):
    case = get_case(db, case_id)

    if case is None:
        return None

    feedback = CaseFeedback(
        case_id=case_id,
        analyst_decision=analyst_decision,
        comment=comment,
    )

    db.add(feedback)
    db.commit()
    db.refresh(case)

    return case


def create_customer(
    db: Session,
    customer_id: str,
    full_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    customer_type: str = "INDIVIDUAL",
    data_origin: str = "CONSENTED_DEMO",
):
    existing = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if existing:
        return existing

    customer = Customer(
        customer_id=customer_id,
        full_name=full_name,
        email=email,
        phone=phone,
        customer_type=customer_type,
        data_origin=data_origin,
        kyc_status="PENDING",
        onboarding_status="IN_PROGRESS",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: str):
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()


def create_account(
    db: Session,
    account_id: str,
    customer_id: str,
    account_type: str = "CHECKING",
    status: str = "ACTIVE",
    balance: float = 0.0,
    currency: str = "USD",
):
    customer = get_customer(db, customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    account = Account(
        account_id=account_id,
        customer_id=customer_id,
        account_type=account_type,
        status=status,
        balance=balance,
        currency=currency,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_transaction(
    db: Session,
    transaction_id: str,
    account_id: str,
    direction: str,
    amount: float,
    description: Optional[str] = None,
    counterparty: Optional[str] = None,
    currency: str = "USD",
    status: str = "COMPLETED",
    to_account_id: Optional[str] = None,
    data_origin: str = "SYNTHETIC",
):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if account is None:
        raise ValueError("Account not found")

    transaction = Transaction(
        transaction_id=transaction_id,
        account_id=account_id,
        direction=direction,
        amount=amount,
        amount_decimal=Decimal(str(amount)),
        description=description,
        counterparty=counterparty,
        currency=currency,
        status=status,
        occurred_at=datetime.utcnow(),
        to_account_id=to_account_id,
        data_origin=data_origin,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def create_risk_assessment(
    db: Session,
    assessment_id: str,
    customer_id: str,
    kyc_risk: float,
    aml_risk: float,
    fused_risk: float,
    uncertainty: Optional[float] = None,
    priority: Optional[str] = None,
    human_review_required: bool = False,
    suspected_typology: Optional[str] = None,
    case_id: Optional[str] = None,
    gnn_risk: Optional[float] = None,
    xgboost_risk: Optional[float] = None,
    final_risk: Optional[float] = None,
    risk_level: Optional[str] = None,
    top_risk_factors: Optional[list[str]] = None,
    gnn_model_version: Optional[str] = None,
    xgboost_model_version: Optional[str] = None,
):
    customer = get_customer(db, customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    assessment = RiskAssessment(
        assessment_id=assessment_id,
        customer_id=customer_id,
        case_id=case_id,
        kyc_risk=kyc_risk,
        aml_risk=aml_risk,
        fused_risk=fused_risk,
        gnn_risk=gnn_risk,
        xgboost_risk=xgboost_risk,
        final_risk=final_risk if final_risk is not None else fused_risk,
        risk_level=risk_level,
        top_risk_factors=top_risk_factors,
        gnn_model_version=gnn_model_version,
        xgboost_model_version=xgboost_model_version,
        uncertainty=uncertainty,
        priority=priority,
        human_review_required=human_review_required,
        suspected_typology=suspected_typology,
        status="OPEN",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def create_alert(
    db: Session,
    alert_id: str,
    customer_id: str,
    alert_type: str,
    severity: str = "MEDIUM",
    status: str = "OPEN",
    narrative: Optional[str] = None,
    account_id: Optional[str] = None,
    case_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
    reason_code: Optional[str] = None,
):
    customer = get_customer(db, customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    alert = Alert(
        alert_id=alert_id,
        customer_id=customer_id,
        account_id=account_id,
        case_id=case_id,
        assessment_id=assessment_id,
        reason_code=reason_code,
        alert_type=alert_type,
        severity=severity,
        status=status,
        narrative=narrative,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def create_sar_draft(
    db: Session,
    sar_id: str,
    case_id: str,
    customer_id: str,
    narrative: str,
    evidence_ids_used: Optional[list[str]] = None,
    fincen_sources_used: Optional[list[str]] = None,
    validation_status: str = "VALID",
    unsupported_claims: Optional[list[str]] = None,
    alert_id: Optional[str] = None,
    review_status: str = "DRAFT",
):
    sar = SARDraft(
        sar_id=sar_id,
        case_id=case_id,
        customer_id=customer_id,
        narrative=narrative,
        evidence_ids_used=evidence_ids_used or [],
        fincen_sources_used=fincen_sources_used or [],
        validation_status=validation_status,
        review_status=review_status,
        alert_id=alert_id,
        unsupported_claims=unsupported_claims or [],
    )
    db.add(sar)
    db.commit()
    db.refresh(sar)
    return sar


def get_alerts(db: Session):
    return db.query(Alert).all()


def get_alert(db: Session, alert_id: str):
    return db.query(Alert).filter(Alert.alert_id == alert_id).first()


def update_alert(
    db: Session,
    alert_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    narrative: Optional[str] = None,
):
    alert = get_alert(db, alert_id)
    if alert is None:
        return None

    if status is not None:
        alert.status = status
    if severity is not None:
        alert.severity = severity
    if narrative is not None:
        alert.narrative = narrative

    db.commit()
    db.refresh(alert)
    return alert