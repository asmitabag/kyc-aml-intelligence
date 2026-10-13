from dataclasses import dataclass
from datetime import datetime
from typing import Any


RUNTIME_CONTRACT_VERSION = "aml-runtime.v1"

@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    account_type: str | None = None
    currency: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    transaction_id: str
    source_account_id: str
    target_account_id: str | None
    amount: float
    currency: str
    timestamp: datetime


@dataclass(frozen=True)
class GNNRuntimeInput:
    contract_version: str
    customer_id: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    numeric_features: dict[str, float]


@dataclass(frozen=True)
class XGBoostRuntimeInput:
    contract_version: str
    customer_id: str
    numeric_features: dict[str, float]


def build_xgboost_features(
    *,
    account_count: int,
    transaction_count: int,
    debit_total: float,
    credit_total: float,
    mean_amount: float,
    max_amount: float,
    distinct_counterparties: int,
) -> dict[str, float]:
    """Return documented aggregates, not a claim of trained-model compatibility."""

    return {
        "account_count": float(account_count),
        "transaction_count": float(transaction_count),
        "debit_total": debit_total,
        "credit_total": credit_total,
        "mean_amount": mean_amount,
        "max_amount": max_amount,
        "distinct_counterparties": float(distinct_counterparties),
    }
