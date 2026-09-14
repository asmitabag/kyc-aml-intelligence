from fastapi import FastAPI

from shared.schemas.aml import AMLResponse
from shared.schemas.kyc import KYCResponse
from shared.schemas.sar import SARResponse
from shared.schemas.triage import TriageResponse


app = FastAPI(
    title="KYC-AML Intelligence Platform",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


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