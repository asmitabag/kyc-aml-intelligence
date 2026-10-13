from sqlalchemy.orm import Session

from services.cases.models import AnalystFeedback, Case, CaseFeedback


def get_feedback_dataset(db: Session) -> list[dict]:
    feedback_rows = (
        db.query(CaseFeedback, Case)
        .join(Case, Case.case_id == CaseFeedback.case_id)
        .all()
    )

    dataset = []

    for feedback, case in feedback_rows:
        dataset.append({
            "case_id": case.case_id,
            "customer_id": case.customer_id,
            "kyc_risk": case.kyc_risk,
            "aml_risk": case.aml_risk,
            "fused_risk": case.fused_risk,
            "uncertainty": case.uncertainty,
            "priority": case.priority,
            "suspected_typology": case.suspected_typology,
            "analyst_decision": feedback.analyst_decision,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        })

    canonical_rows = db.query(AnalystFeedback).all()
    for feedback in canonical_rows:
        dataset.append({
            "feedback_id": feedback.feedback_id,
            "alert_id": feedback.alert_id,
            "assessment_id": feedback.assessment_id,
            "customer_id": feedback.customer_id,
            "decision": feedback.decision,
            "rationale": feedback.rationale,
            "model_versions": feedback.model_versions or {},
            "created_at": feedback.created_at.isoformat(),
        })

    return dataset