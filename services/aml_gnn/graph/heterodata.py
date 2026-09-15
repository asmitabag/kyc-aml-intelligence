from pathlib import Path

import torch
from torch_geometric.data import HeteroData
import polars as pl


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

GRAPH_DIR = PROJECT_ROOT / "data" / "processed" / "graph"
HETERO_DIR = GRAPH_DIR / "heterogeneous"

OUTPUT_DIR = GRAPH_DIR / "pyg"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# Load node IDs
# =========================================================

def load_node_ids():

    node_files = {
        "customer": "customer_nodes.parquet",
        "account": "account_nodes.parquet",
        "device": "device_nodes.parquet",
        "address": "address_nodes.parquet",
        "document": "document_nodes.parquet",
    }

    node_ids = {}

    for node_type, filename in node_files.items():

        path = HETERO_DIR / filename

        df = pl.read_parquet(path)

        # Every node needs a stable integer index for PyG
        ids = df.get_column(
            df.columns[0]
        ).cast(pl.Utf8).to_list()

        node_ids[node_type] = ids

        print(
            f"{node_type:10s}: {len(ids):,} nodes"
        )

    return node_ids


# =========================================================
# Create ID -> integer index mappings
# =========================================================

def create_mappings(node_ids):

    mappings = {}

    for node_type, ids in node_ids.items():

        mappings[node_type] = {
            node_id: index
            for index, node_id in enumerate(ids)
        }

    return mappings


# =========================================================
# Add identity edges
# =========================================================

def add_identity_edges(
    data,
    mappings,
):

    identity_edges = {
        "owns": (
            "customer",
            "account",
            "owns_edges.parquet",
            "customer_id",
            "account_id",
        ),
        "uses": (
            "customer",
            "device",
            "uses_edges.parquet",
            "customer_id",
            "device_id",
        ),
        "lives_at": (
            "customer",
            "address",
            "lives_at_edges.parquet",
            "customer_id",
            "address_id",
        ),
        "submitted": (
            "customer",
            "document",
            "submitted_edges.parquet",
            "customer_id",
            "document_id",
        ),
    }

    for edge_type, (
        source_type,
        target_type,
        filename,
        source_column,
        target_column,
    ) in identity_edges.items():

        path = HETERO_DIR / filename

        df = pl.read_parquet(path)

        source_ids = df.get_column(
            source_column
        ).cast(pl.Utf8).to_list()

        target_ids = df.get_column(
            target_column
        ).cast(pl.Utf8).to_list()

        source_indices = [
            mappings[source_type][node_id]
            for node_id in source_ids
        ]

        target_indices = [
            mappings[target_type][node_id]
            for node_id in target_ids
        ]

        edge_index = torch.tensor(
            [
                source_indices,
                target_indices,
            ],
            dtype=torch.long,
        )

        data[
            source_type,
            edge_type,
            target_type
        ].edge_index = edge_index

        print(
            f"{edge_type:12s}: "
            f"{edge_index.shape[1]:,} edges"
        )


# =========================================================
# Add transaction edges
# =========================================================

def add_transaction_edges(
    data,
    mappings,
    split,
):

    path = (
        GRAPH_DIR
        / f"{split}_transaction_graph.parquet"
    )

    df = pl.read_parquet(path)

    print(
        f"\nLoading {split} transactions: "
        f"{df.height:,}"
    )

    source_ids = (
        df
        .get_column("source_account")
        .cast(pl.Utf8)
        .to_list()
    )

    target_ids = (
        df
        .get_column("target_account")
        .cast(pl.Utf8)
        .to_list()
    )

    # -----------------------------------------------------
    # Convert account IDs into PyG node indices
    # -----------------------------------------------------

    source_indices = [
        mappings["account"][account_id]
        for account_id in source_ids
    ]

    target_indices = [
        mappings["account"][account_id]
        for account_id in target_ids
    ]

    edge_index = torch.tensor(
        [
            source_indices,
            target_indices,
        ],
        dtype=torch.long,
    )

    # -----------------------------------------------------
    # Transaction edge features
    # -----------------------------------------------------

    edge_features = df.select([
        "Amount",
        "log_amount",
        "is_cross_border",
        "currency_changed",
    ]).to_numpy()

    edge_attr = torch.tensor(
        edge_features,
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # Transaction labels
    # -----------------------------------------------------

    labels = torch.tensor(
        df
        .get_column("Is_laundering")
        .to_numpy(),
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # Store in HeteroData
    # -----------------------------------------------------

    relation = (
        "account",
        "transfers",
        "account",
    )

    data[relation].edge_index = edge_index

    data[relation].edge_attr = edge_attr

    data[relation].edge_label = labels

    print(
        f"Transaction edges: "
        f"{edge_index.shape[1]:,}"
    )

    print(
        f"Edge features: "
        f"{edge_attr.shape}"
    )

    print(
        f"Laundering labels: "
        f"{labels.sum().item():,.0f}"
    )


# =========================================================
# Build PyG graph
# =========================================================

def build_graph(split):

    print("\n" + "=" * 60)
    print(f"BUILDING PyG GRAPH: {split.upper()}")
    print("=" * 60)

    # -----------------------------------------------------
    # Load node IDs
    # -----------------------------------------------------

    node_ids = load_node_ids()

    mappings = create_mappings(node_ids)

    # -----------------------------------------------------
    # Create HeteroData
    # -----------------------------------------------------

    data = HeteroData()

    # -----------------------------------------------------
    # Add nodes
    # -----------------------------------------------------

    for node_type, ids in node_ids.items():

        # Initial node feature:
        # one-dimensional constant feature.
        #
        # Later we will replace this with meaningful
        # account/KYC/identity features.

        data[node_type].x = torch.ones(
            (len(ids), 1),
            dtype=torch.float32,
        )

    # -----------------------------------------------------
    # Identity relationships
    # -----------------------------------------------------

    add_identity_edges(
        data,
        mappings,
    )

    # -----------------------------------------------------
    # Transaction relationships
    # -----------------------------------------------------

    add_transaction_edges(
        data,
        mappings,
        split,
    )

    # -----------------------------------------------------
    # Print graph summary
    # -----------------------------------------------------

    print("\nGraph summary:")
    print(data)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / f"{split}_heterodata.pt"
    )

    torch.save(
        data,
        output_path,
    )

    print(
        f"\nSaved: {output_path}"
    )

    return data


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    for split in [
        "train",
        "validation",
        "test",
    ]:

        build_graph(split)

    print("\n" + "=" * 60)
    print("ALL PyG HETEROGENEOUS GRAPHS CREATED")
    print("=" * 60)