from typing import Any

from pydantic import BaseModel, Field


class TriageResponse(BaseModel):
    case_id: str

    fused_risk: float = Field(ge=0.0, le=1.0)

    uncertainty: float = Field(ge=0.0, le=1.0)

    priority: str

    human_review_required: bool

    shap_features: list[dict[str, Any]]

    graph_explanation: dict[str, Any]