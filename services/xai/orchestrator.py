from shared.schemas.kyc import KYCResponse
from shared.schemas.triage import TriageResponse

from services.aml_gnn.service import run_aml_analysis
from services.xai.triage import create_triage
from services.model_adapters.contracts import ModelStatus


def run_case_triage(
    case_id: str,
    kyc: KYCResponse
) -> TriageResponse:

    # Step 1: Run AML analysis
    aml_result = run_aml_analysis({"case_id": case_id})
    if aml_result.status is not ModelStatus.AVAILABLE or aml_result.output is None:
        raise RuntimeError(aml_result.error or "GNN AML inference is unavailable")

    # Step 2: Combine KYC + AML into triage
    triage = create_triage(kyc, aml_result.output)

    return triage