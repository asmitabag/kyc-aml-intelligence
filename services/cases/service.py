from sqlalchemy.orm import Session

from services.cases.models import Case
from shared.schemas.triage import TriageResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.aml import AMLResponse


def create_case(
    db: Session,
    kyc: KYCResponse,
    aml: AMLResponse,
    triage: TriageResponse
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

        status="OPEN"
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
    status: str
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
    comment: str | None = None
):
    case = get_case(db, case_id)

    if case is None:
        return None

    case.status = analyst_decision

    db.commit()
    db.refresh(case)

    return case