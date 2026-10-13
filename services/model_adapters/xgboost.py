from typing import Any, Protocol

from services.model_adapters.contracts import InferenceResult
from services.model_adapters.runtime import XGBoostRuntimeInput


class XGBoostAdapter(Protocol):
    """Runtime contract for an XGBoost risk model."""

    def predict(self, features: XGBoostRuntimeInput) -> InferenceResult[dict[str, Any]]:
        ...


class UnavailableXGBoostAdapter:
    def predict(self, features: XGBoostRuntimeInput) -> InferenceResult[dict[str, Any]]:
        from services.model_adapters.contracts import ModelStatus

        return InferenceResult(
            model_name="xgboost",
            status=ModelStatus.UNAVAILABLE,
            error="XGBoost model artifact and runtime adapter are not available",
        )
