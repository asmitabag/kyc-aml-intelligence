from pydantic import BaseModel


class SARResponse(BaseModel):
    case_id: str

    sar_draft: str

    evidence_ids_used: list[str]

    validation_status: str

    unsupported_claims: list[str]