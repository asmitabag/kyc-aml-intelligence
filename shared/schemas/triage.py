from typing import Any
from pydantic import BaseModel, Field


class GraphExplanation(BaseModel):
    nodes: list[str]
    edges: list[dict[str, Any]] = Field(default_factory=list)
    important_features: list[dict[str, Any]] = Field(default_factory=list)


class TriageResponse(BaseModel):
    case_id: str
    fused_risk: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    priority: str
    human_review_required: bool
    shap_features: list[dict[str, Any]]
    graph_explanation: GraphExplanation