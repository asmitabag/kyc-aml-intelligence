from typing import Protocol

from shared.schemas.aml import AMLResponse
from services.model_adapters.contracts import InferenceResult, ModelStatus
from services.model_adapters.runtime import GNNRuntimeInput


class GNNAdapter(Protocol):
    """Runtime contract for Saloni's graph model.

    The training pipeline and artifact loading remain owned by the model
    owner. This interface accepts a constructed runtime graph and returns
    explicit availability rather than a synthetic prediction.
    """

    def analyze(self, graph: GNNRuntimeInput) -> InferenceResult[AMLResponse]:
        ...


class UnavailableGNNAdapter:
    def analyze(self, graph: GNNRuntimeInput) -> InferenceResult[AMLResponse]:
        return InferenceResult(
            model_name="gnn",
            status=ModelStatus.UNAVAILABLE,
            error="GNN model artifact and runtime adapter are not available",
        )
