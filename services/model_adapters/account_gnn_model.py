
from __future__ import annotations

import torch
from torch import nn


class AccountGNN(nn.Module):
    """Architecture matching the account_gnn_v1 training checkpoint."""

    def __init__(
        self,
        in_features: int = 11,
        hidden: int = 64,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()

        self.input_layer = nn.Linear(in_features, hidden)
        self.message_layer1 = nn.Linear(hidden * 2, hidden)
        self.message_layer2 = nn.Linear(hidden * 2, hidden)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    @staticmethod
    def aggregate(
        h: torch.Tensor,
        source: torch.Tensor,
        target: torch.Tensor,
    ) -> torch.Tensor:
        agg = torch.zeros_like(h)
        count = torch.zeros(
            (h.shape[0], 1),
            dtype=h.dtype,
            device=h.device,
        )

        agg.index_add_(0, target, h[source])
        count.index_add_(
            0,
            target,
            torch.ones(
                (len(target), 1),
                dtype=h.dtype,
                device=h.device,
            ),
        )
        return agg / count.clamp(min=1)

    def forward(
        self,
        x: torch.Tensor,
        source: torch.Tensor,
        target: torch.Tensor,
        customer_nodes: list[torch.Tensor],
    ) -> torch.Tensor:
        h = torch.relu(self.input_layer(x))
        h = self.dropout(h)

        incoming = self.aggregate(h, source, target)
        outgoing = self.aggregate(h, target, source)
        h = torch.relu(
            self.message_layer1(
                torch.cat([h, incoming + outgoing], dim=1)
            )
        )
        h = self.dropout(h)

        incoming2 = self.aggregate(h, source, target)
        outgoing2 = self.aggregate(h, target, source)
        h = torch.relu(
            self.message_layer2(
                torch.cat([h, incoming2 + outgoing2], dim=1)
            )
        )

        mean_pooled = torch.stack(
            [h[idx].mean(dim=0) for idx in customer_nodes]
        )
        max_pooled = torch.stack(
            [h[idx].max(dim=0).values for idx in customer_nodes]
        )

        graph_repr = torch.cat([mean_pooled, max_pooled], dim=1)
        return self.classifier(graph_repr).squeeze(1)
