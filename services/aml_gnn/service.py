from typing import Any

from shared.schemas.aml import AMLResponse
from services.model_adapters.contracts import InferenceResult
from services.model_adapters.gnn import GNNAdapter, UnavailableGNNAdapter


def run_aml_analysis(
    graph: dict[str, Any] | None = None,
    adapter: GNNAdapter | None = None,
) -> InferenceResult[AMLResponse]:
    """Run the configured GNN adapter without fabricating a prediction.

    The default adapter is explicitly unavailable until Saloni's runtime
    interface and trained artifact are supplied.
    """

    selected_adapter = adapter or UnavailableGNNAdapter()
    return selected_adapter.analyze(graph or {})
