
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import torch

from shared.schemas.aml import AMLResponse
from services.model_adapters.account_gnn_model import AccountGNN
from services.model_adapters.contracts import InferenceResult, ModelStatus
from services.model_adapters.runtime import GNNRuntimeInput


DEFAULT_ARTIFACT_DIR = Path("artifacts/account_gnn_v1")

EXPECTED_FEATURES = [
    "type_business",
    "type_checking",
    "type_savings",
    "currency_EUR",
    "currency_GBP",
    "currency_INR",
    "currency_USD",
    "out_count_log",
    "in_count_log",
    "out_amount_log_sum",
    "in_amount_log_sum",
]


class AccountGNNAdapter:
    """Experimental account-level GNN adapter for synthetic AML data."""

    def __init__(
        self,
        artifact_dir: Union[str, Path] = DEFAULT_ARTIFACT_DIR,
    ) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.model: Optional[AccountGNN] = None
        self.metadata: Optional[dict[str, Any]] = None
        self.load_error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        try:
            metadata_path = self.artifact_dir / "metadata.json"
            checkpoint_path = self.artifact_dir / "account_gnn.pt"

            with metadata_path.open("r", encoding="utf-8") as file:
                metadata = json.load(file)

            if metadata.get("model") != "account_gnn_v1":
                raise ValueError("Unexpected account GNN model identifier")

            if metadata.get("feature_columns") != EXPECTED_FEATURES:
                raise ValueError("Account GNN feature order does not match")

            mean = metadata.get("scaler_mean")
            scale = metadata.get("scaler_scale")
            if not isinstance(mean, list) or not isinstance(scale, list):
                raise ValueError("Scaler metadata is missing")
            if len(mean) != 4 or len(scale) != 4:
                raise ValueError("Expected four scaler values")

            checkpoint = torch.load(
                checkpoint_path,
                map_location="cpu",
                weights_only=True,
            )

            if not isinstance(checkpoint, dict) or "state_dict" not in checkpoint:
                raise ValueError("Invalid account GNN checkpoint format")

            input_features = int(checkpoint["input_features"])
            hidden_features = int(checkpoint["hidden_features"])
            dropout = float(checkpoint["dropout"])

            if input_features != len(EXPECTED_FEATURES):
                raise ValueError(
                    f"Expected {len(EXPECTED_FEATURES)} input features, "
                    f"checkpoint has {input_features}"
                )

            model = AccountGNN(
                in_features=input_features,
                hidden=hidden_features,
                dropout=dropout,
            )
            model.load_state_dict(checkpoint["state_dict"], strict=True)
            model.eval()

            self.metadata = metadata
            self.model = model
        except Exception as exc:
            self.load_error = f"{type(exc).__name__}: {exc}"
            self.metadata = None
            self.model = None

    def analyze(self, graph: GNNRuntimeInput) -> InferenceResult[AMLResponse]:
        if self.model is None or self.metadata is None:
            return InferenceResult(
                model_name="account_gnn",
                status=ModelStatus.UNAVAILABLE,
                error=self.load_error or "Account GNN artifacts are unavailable",
            )

        try:
            account_nodes = [
                node for node in graph.nodes
                if node.node_type == "account"
            ]
            account_ids = [node.node_id for node in account_nodes]

            if not account_ids:
                raise ValueError("Graph contains no account nodes")

            index = {account_id: i for i, account_id in enumerate(account_ids)}
            n = len(account_ids)

            out_count = np.zeros(n, dtype=np.float64)
            in_count = np.zeros(n, dtype=np.float64)
            out_amount = np.zeros(n, dtype=np.float64)
            in_amount = np.zeros(n, dtype=np.float64)

            edge_sources: list[int] = []
            edge_targets: list[int] = []

            for edge in graph.edges:
                source = index.get(edge.source_account_id)
                target = index.get(edge.target_account_id or "")
                if source is None or target is None:
                    continue

                amount = float(edge.amount)
                if not math.isfinite(amount):
                    raise ValueError("Graph contains a non-finite transaction amount")
                amount_log = math.log1p(max(amount, 0.0))

                edge_sources.append(source)
                edge_targets.append(target)

                out_count[source] += 1.0
                in_count[target] += 1.0
                out_amount[source] += amount_log
                in_amount[target] += amount_log

            type_columns = {
                "type_business": "business",
                "type_checking": "checking",
                "type_savings": "savings",
            }
            currency_columns = {
                "currency_EUR": "EUR",
                "currency_GBP": "GBP",
                "currency_INR": "INR",
                "currency_USD": "USD",
            }

            feature_matrix = np.zeros((n, len(EXPECTED_FEATURES)), dtype=np.float32)

            for i, node in enumerate(account_nodes):
                account_type = (node.account_type or "").strip().lower()
                currency = (node.currency or "").strip().upper()

                for column, category in type_columns.items():
                    feature_matrix[i, EXPECTED_FEATURES.index(column)] = float(
                        account_type == category
                    )

                for column, category in currency_columns.items():
                    feature_matrix[i, EXPECTED_FEATURES.index(column)] = float(
                        currency == category
                    )

            feature_matrix[:, 7] = np.log1p(out_count)
            feature_matrix[:, 8] = np.log1p(in_count)
            feature_matrix[:, 9] = np.log1p(out_amount)
            feature_matrix[:, 10] = np.log1p(in_amount)

            mean = np.asarray(self.metadata["scaler_mean"], dtype=np.float32)
            scale = np.asarray(self.metadata["scaler_scale"], dtype=np.float32)
            if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(scale)):
                raise ValueError("Scaler values must be finite")
            if np.any(scale <= 0):
                raise ValueError("Scaler scales must be positive")

            feature_matrix[:, -4:] = (
                feature_matrix[:, -4:] - mean
            ) / scale

            x = torch.tensor(feature_matrix, dtype=torch.float32)
            edge_index = torch.tensor(
                [edge_sources, edge_targets],
                dtype=torch.long,
            )

            source = torch.tensor(edge_sources, dtype=torch.long)
            target = torch.tensor(edge_targets, dtype=torch.long)

            # The runtime graph contains accounts for one customer.
            # The training model expects a list of node-index groups, one per customer.
            customer_nodes = [torch.arange(n, dtype=torch.long)]

            with torch.no_grad():
                logits = self.model(
                    x,
                    source,
                    target,
                    customer_nodes,
                )
                score = float(torch.sigmoid(logits.reshape(-1)[0]).item())

            if not math.isfinite(score) or not 0.0 <= score <= 1.0:
                raise ValueError("Account GNN returned an invalid score")

            output = AMLResponse(
                case_id=graph.customer_id,
                aml_risk=score,
                suspected_typology="unknown",
                suspicious_transaction_ids=[],
                suspicious_account_ids=[],
                explanation_subgraph={
                    "model": "account_gnn_v1",
                    "experimental": True,
                    "warning": (
                        "Trained on synthetic data; score is not calibrated "
                        "for real-world AML decisions."
                    ),
                },
                graph_features={
                    "account_count": n,
                    "transaction_edge_count": len(edge_sources),
                },
            )

            return InferenceResult(
                model_name="account_gnn",
                status=ModelStatus.AVAILABLE,
                score=score,
                output=output,
                model_version="account_gnn_v1_synthetic",
                explanation={
                    "experimental": True,
                    "account_count": n,
                    "transaction_edge_count": len(edge_sources),
                    "warning": (
                        "Synthetic benchmark only; not evidence of "
                        "real-world detection performance."
                    ),
                },
            )

        except Exception as exc:
            return InferenceResult(
                model_name="account_gnn",
                status=ModelStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
            )
