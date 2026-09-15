from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.sar import SARResponse
from shared.schemas.triage import TriageResponse
from shared.schemas.case import (
    CaseResponse,
    CaseStatusUpdate,
    CaseFeedback
)

from services.aml_gnn.service import run_aml_analysis
from services.xai.triage import create_triage
from services.xai.orchestrator import run_case_triage

from apps.api_gateway.database import get_db, Base, engine
from services.cases import models
from services.cases.service import (
    create_case,
    get_cases,
    get_case,
    update_case_status,
    add_case_feedback
)


app = FastAPI(
    title="KYC-AML Intelligence Platform",
    version="0.1.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# TEST ENDPOINTS
# --------------------------------------------------

@app.post("/test/kyc", response_model=KYCResponse)
def test_kyc(data: KYCResponse):
    return data


@app.post("/test/aml", response_model=AMLResponse)
def test_aml(data: AMLResponse):
    return data


@app.post("/test/triage", response_model=TriageResponse)
def test_triage(data: TriageResponse):
    return data


@app.post("/test/sar", response_model=SARResponse)
def test_sar(data: SARResponse):
    return data


# --------------------------------------------------
# TRIAGE
# --------------------------------------------------

@app.post("/triage", response_model=TriageResponse)
def triage(kyc: KYCResponse, aml: AMLResponse):
    return create_triage(kyc, aml)


@app.post("/aml/{case_id}", response_model=AMLResponse)
def aml_analysis(case_id: str):
    return run_aml_analysis(case_id)


@app.post("/triage/{case_id}", response_model=TriageResponse)
def triage_case(case_id: str, kyc: KYCResponse):
    return run_case_triage(case_id, kyc)


# --------------------------------------------------
# CASE MANAGEMENT
# --------------------------------------------------

@app.post("/cases", response_model=CaseResponse)
def create_new_case(
    kyc: KYCResponse,
    db: Session = Depends(get_db)
):
    aml = run_aml_analysis(kyc.customer_id)

    triage = create_triage(
        kyc,
        aml
    )

    return create_case(
        db=db,
        kyc=kyc,
        aml=aml,
        triage=triage
    )


@app.get("/cases", response_model=list[CaseResponse])
def list_cases(
    db: Session = Depends(get_db)
):
    return get_cases(db)


@app.get("/cases/{case_id}", response_model=CaseResponse)
def get_case_by_id(
    case_id: str,
    db: Session = Depends(get_db)
):
    case = get_case(
        db,
        case_id
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case

@app.patch("/cases/{case_id}/status", response_model=CaseResponse)
def update_status(
    case_id: str,
    data: CaseStatusUpdate,
    db: Session = Depends(get_db)
):
    case = update_case_status(
        db,
        case_id,
        data.status
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case

@app.post("/cases/{case_id}/feedback", response_model=CaseResponse)
def submit_feedback(
    case_id: str,
    feedback: CaseFeedback,
    db: Session = Depends(get_db)
):
    case = add_case_feedback(
        db=db,
        case_id=case_id,
        analyst_decision=feedback.analyst_decision,
        comment=feedback.comment
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case