from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar


OutputT = TypeVar("OutputT")


class ModelStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class InferenceResult(Generic[OutputT]):
    """Result envelope for model integrations.

    A score is present only when the adapter produced a valid inference. An
    unavailable or error result must retain ``score=None``.
    """

    model_name: str
    status: ModelStatus
    score: float | None = None
    output: OutputT | None = None
    model_version: str | None = None
    explanation: dict[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ValueError(f"{self.model_name} score must be between 0 and 1")
        if self.status is not ModelStatus.AVAILABLE and self.score is not None:
            raise ValueError("Unavailable or error results cannot contain a score")
        if self.status is ModelStatus.AVAILABLE and self.score is None:
            raise ValueError("Available results must contain a score")
