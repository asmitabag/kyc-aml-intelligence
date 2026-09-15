from shared.schemas.kyc import KYCResponse
from shared.schemas.triage import TriageResponse

from services.aml_gnn.service import run_aml_analysis
from services.xai.triage import create_triage


def run_case_triage(
    case_id: str,
    kyc: KYCResponse
) -> TriageResponse:

    # Step 1: Run AML analysis
    aml = run_aml_analysis(case_id)

    # Step 2: Combine KYC + AML into triage
    triage = create_triage(kyc, aml)

    return triage