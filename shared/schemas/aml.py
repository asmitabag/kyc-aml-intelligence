from typing import Any

from pydantic import BaseModel, Field


class AMLResponse(BaseModel):
    case_id: str

    aml_risk: float = Field(ge=0.0, le=1.0)

    suspected_typology: str

    suspicious_transaction_ids: list[str]
    suspicious_account_ids: list[str]

    explanation_subgraph: dict[str, Any]
    graph_features: dict[str, Any]