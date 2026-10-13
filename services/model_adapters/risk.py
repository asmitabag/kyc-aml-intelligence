from dataclasses import dataclass

from services.model_adapters.contracts import InferenceResult, ModelStatus


@dataclass(frozen=True)
class RiskComponent:
    name: str
    result: InferenceResult[object]
    weight: float


def fuse_available_scores(components: list[RiskComponent]) -> float | None:
    """Return a normalized weighted score from available components only.

    Missing or unavailable components are excluded and their weights are
    renormalized. If no component is available, return ``None``; callers must
    keep the assessment pending or explicitly unavailable.
    """

    available = [
        component
        for component in components
        if component.result.status is ModelStatus.AVAILABLE
    ]
    if not available:
        return None
    total_weight = sum(component.weight for component in available)
    if total_weight <= 0:
        raise ValueError("At least one available component must have positive weight")
    return round(
        sum(component.result.score * component.weight for component in available)
        / total_weight,
        4,
    )
