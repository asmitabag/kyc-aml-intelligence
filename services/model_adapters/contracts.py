from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, Optional, TypeVar


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
    score: Optional[float] = None
    output: Optional[OutputT] = None
    model_version: Optional[str] = None
    explanation: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ValueError(f"{self.model_name} score must be between 0 and 1")
        if self.status is not ModelStatus.AVAILABLE and self.score is not None:
            raise ValueError("Unavailable or error results cannot contain a score")
        if self.status is ModelStatus.AVAILABLE and self.score is None:
            raise ValueError("Available results must contain a score")
