import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.model_adapters.runtime import (
    GNNRuntimeInput,
    GraphEdge,
    GraphNode,
    RUNTIME_CONTRACT_VERSION,
)
from services.model_adapters.account_gnn_adapter import AccountGNNAdapter

customer_id = "SYNTHETIC-GNN-TEST"

nodes = (
    GraphNode("TEST-A", "account", "checking", "USD"),
    GraphNode("TEST-B", "account", "savings", "EUR"),
    GraphNode("TEST-C", "account", "business", "GBP"),
)

now = datetime.now(timezone.utc)

edges = (
    GraphEdge("TEST-TXN-1", "TEST-A", "TEST-B", 125.0, "USD", now),
    GraphEdge("TEST-TXN-2", "TEST-B", "TEST-C", 250.0, "EUR", now),
    GraphEdge("TEST-TXN-3", "TEST-C", "TEST-A", 75.0, "GBP", now),
)

graph = GNNRuntimeInput(
    contract_version=RUNTIME_CONTRACT_VERSION,
    customer_id=customer_id,
    nodes=nodes,
    edges=edges,
    numeric_features={
        "account_count": 3.0,
        "transaction_count": 3.0,
        "total_amount": 450.0,
    },
)

adapter = AccountGNNAdapter()
result = adapter.analyze(graph)

print("Graph contract:", graph.contract_version)
print("Synthetic accounts:", len(nodes))
print("Input transactions:", len(edges))
print("Model status:", result.status.value)
print("Model version:", result.model_version)
print("Score:", result.score)
print("Error:", result.error)
print("Explanation:", result.explanation)

if result.output is not None:
    print("Output graph features:", result.output.graph_features)

if result.status.value == "available" and result.output is not None:
    actual_edges = result.output.graph_features.get("transaction_edge_count")
    assert actual_edges == 3, f"Expected 3 usable edges, got {actual_edges}"
    assert result.score is not None and 0.0 <= result.score <= 1.0
    print("PASS: GNN inference succeeded with 3 connected edges.")
else:
    raise SystemExit("FAIL: GNN inference did not return an available result.")
