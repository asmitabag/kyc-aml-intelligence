from pathlib import Path

import polars as pl
import torch
from torch_geometric.data import HeteroData


# =========================================================
# PATHS
# =========================================================

GRAPH_DIR = Path("data/processed/graph/heterogeneous")
TRANSACTION_GRAPH_DIR = Path("data/processed/graph")
SCALED_FEATURE_DIR = Path("data/processed/features/scaled")
OUTPUT_DIR = Path("data/processed/graph/pyg")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# ACCOUNT FEATURES
# =========================================================

ACCOUNT_FEATURES = [
    "outgoing_count",
    "outgoing_total",
    "outgoing_mean",
    "outgoing_std",
    "outgoing_max",
    "outgoing_cross_border_count",

    "incoming_count",
    "incoming_total",
    "incoming_mean",
    "incoming_std",
    "incoming_max",
    "incoming_cross_border_count",

    "unique_outgoing_counterparties",
    "unique_incoming_counterparties",

    "total_transaction_count",
    "total_transaction_amount",
    "total_unique_counterparties",

    "incoming_outgoing_amount_ratio",
    "incoming_outgoing_count_ratio",

    "cross_border_count",
    "cross_border_ratio",

    "log_incoming_total",
    "log_outgoing_total",
    "log_total_transaction_amount",
]


# =========================================================
# NODE ID COLUMNS
# =========================================================

NODE_ID_COLUMNS = {
    "customer": "customer_id",
    "account": "account_id",
    "device": "device_id",
    "address": "address_id",
    "document": "document_id",
}


# =========================================================
# IDENTITY EDGE CONFIGURATION
# =========================================================

IDENTITY_EDGES = [
    {
        "file": "owns_edges.parquet",
        "source_type": "customer",
        "relation": "owns",
        "target_type": "account",
        "source_column": "customer_id",
        "target_column": "account_id",
    },
    {
        "file": "uses_edges.parquet",
        "source_type": "customer",
        "relation": "uses",
        "target_type": "device",
        "source_column": "customer_id",
        "target_column": "device_id",
    },
    {
        "file": "lives_at_edges.parquet",
        "source_type": "customer",
        "relation": "lives_at",
        "target_type": "address",
        "source_column": "customer_id",
        "target_column": "address_id",
    },
    {
        "file": "submitted_edges.parquet",
        "source_type": "customer",
        "relation": "submitted",
        "target_type": "document",
        "source_column": "customer_id",
        "target_column": "document_id",
    },
]


# =========================================================
# LOAD NODE TABLES
# =========================================================

def load_node_ids():

    node_tables = {}

    for node_type, id_column in NODE_ID_COLUMNS.items():

        file_path = (
            GRAPH_DIR
            / f"{node_type}_nodes.parquet"
        )

        df = pl.read_parquet(file_path)

        if id_column not in df.columns:

            raise ValueError(
                f"{id_column} not found in "
                f"{file_path}"
            )

        node_tables[node_type] = df

    return node_tables


# =========================================================
# CREATE ID → INTEGER INDEX MAPPING
# =========================================================

def create_index_mapping(df, column):

    ids = (
        df[column]
        .cast(pl.Utf8)
        .to_list()
    )

    return {
        value: index
        for index, value in enumerate(ids)
    }


# =========================================================
# ADD IDENTITY EDGES
# =========================================================

def add_identity_edges(
    data,
    edge_config,
    mappings,
):

    edge_file = edge_config["file"]

    source_type = edge_config["source_type"]
    relation = edge_config["relation"]
    target_type = edge_config["target_type"]

    source_column = edge_config["source_column"]
    target_column = edge_config["target_column"]

    edges = pl.read_parquet(
        GRAPH_DIR / edge_file
    )

    # -----------------------------------------------------
    # Validate columns
    # -----------------------------------------------------

    if source_column not in edges.columns:

        raise ValueError(
            f"{source_column} not found in "
            f"{edge_file}"
        )

    if target_column not in edges.columns:

        raise ValueError(
            f"{target_column} not found in "
            f"{edge_file}"
        )

    # -----------------------------------------------------
    # Convert IDs to strings
    # -----------------------------------------------------

    source_ids = (
        edges[source_column]
        .cast(pl.Utf8)
        .to_list()
    )

    target_ids = (
        edges[target_column]
        .cast(pl.Utf8)
        .to_list()
    )

    # -----------------------------------------------------
    # Check that all IDs exist
    # -----------------------------------------------------

    missing_sources = [
        x
        for x in source_ids
        if x not in mappings[source_type]
    ]

    missing_targets = [
        x
        for x in target_ids
        if x not in mappings[target_type]
    ]

    if missing_sources:

        raise ValueError(
            f"{len(missing_sources):,} source IDs from "
            f"{edge_file} are missing from "
            f"{source_type} nodes."
        )

    if missing_targets:

        raise ValueError(
            f"{len(missing_targets):,} target IDs from "
            f"{edge_file} are missing from "
            f"{target_type} nodes."
        )

    # -----------------------------------------------------
    # Convert IDs → integer node indices
    # -----------------------------------------------------

    source_indices = [
        mappings[source_type][x]
        for x in source_ids
    ]

    target_indices = [
        mappings[target_type][x]
        for x in target_ids
    ]

    edge_index = torch.tensor(
        [
            source_indices,
            target_indices,
        ],
        dtype=torch.long,
    )

    # -----------------------------------------------------
    # Add edge relation
    # -----------------------------------------------------

    data[
        source_type,
        relation,
        target_type
    ].edge_index = edge_index

    print(
        f"  {source_type} -[{relation}]-> "
        f"{target_type}: "
        f"{edge_index.shape[1]:,} edges"
    )


# =========================================================
# LOAD SCALED ACCOUNT FEATURES
# =========================================================

def load_account_features(
    account_mapping,
    split,
):

    feature_file = (
        SCALED_FEATURE_DIR
        / f"{split}_account_features_scaled.parquet"
    )

    print(
        f"\nLoading account features: "
        f"{feature_file}"
    )

    df = pl.read_parquet(feature_file)

    # -----------------------------------------------------
    # Ensure account IDs are strings
    # -----------------------------------------------------

    df = df.with_columns(
        pl.col("account_id")
        .cast(pl.Utf8)
    )

    # -----------------------------------------------------
    # Validate expected columns
    # -----------------------------------------------------

    required_columns = [
        "account_id"
    ] + ACCOUNT_FEATURES

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing account feature columns: "
            + str(missing_columns)
        )

    # -----------------------------------------------------
    # Create account → feature lookup
    # -----------------------------------------------------

    feature_lookup = {}

    selected = df.select(
        ["account_id"] + ACCOUNT_FEATURES
    )

    for row in selected.iter_rows():

        account_id = row[0]

        features = row[1:]

        feature_lookup[account_id] = features

    # -----------------------------------------------------
    # Align features to PyG node ordering
    # -----------------------------------------------------

    num_accounts = len(account_mapping)

    feature_matrix = []

    missing_count = 0

    ordered_accounts = sorted(
        account_mapping.items(),
        key=lambda x: x[1],
    )

    for account_id, node_index in ordered_accounts:

        if account_id in feature_lookup:

            feature_matrix.append(
                feature_lookup[account_id]
            )

        else:

            # Standardized feature space:
            # zero represents the neutral value.

            feature_matrix.append(
                [0.0] * len(ACCOUNT_FEATURES)
            )

            missing_count += 1

    # -----------------------------------------------------
    # Convert to tensor
    # -----------------------------------------------------

    x = torch.tensor(
        feature_matrix,
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    if x.shape[0] != num_accounts:

        raise ValueError(
            f"Account feature row mismatch: "
            f"{x.shape[0]} vs {num_accounts}"
        )

    if x.shape[1] != len(ACCOUNT_FEATURES):

        raise ValueError(
            f"Account feature column mismatch: "
            f"{x.shape[1]} vs "
            f"{len(ACCOUNT_FEATURES)}"
        )

    if not torch.isfinite(x).all():

        raise ValueError(
            "Account feature tensor contains "
            "NaN or infinite values."
        )

    print(
        f"{split.capitalize()} account features:"
    )

    print(
        f"  Shape: {tuple(x.shape)}"
    )

    print(
        f"  Features: {len(ACCOUNT_FEATURES)}"
    )

    print(
        f"  Missing accounts filled with zero: "
        f"{missing_count:,}"
    )

    return x


# =========================================================
# BUILD HETERODATA
# =========================================================

def build_heterodata(split):

    print("\n" + "=" * 70)

    print(
        f"BUILDING PYTORCH GEOMETRIC GRAPH: "
        f"{split.upper()}"
    )

    print("=" * 70)

    # =====================================================
    # LOAD NODE TABLES
    # =====================================================

    node_tables = load_node_ids()

    # =====================================================
    # CREATE NODE MAPPINGS
    # =====================================================

    mappings = {}

    for node_type, df in node_tables.items():

        mappings[node_type] = (
            create_index_mapping(
                df,
                NODE_ID_COLUMNS[node_type],
            )
        )

    # =====================================================
    # CREATE HETERODATA
    # =====================================================

    data = HeteroData()

    # =====================================================
    # NODE FEATURES
    # =====================================================

    # -----------------------------------------------------
    # CUSTOMER
    # -----------------------------------------------------

    data["customer"].x = torch.ones(
        (
            len(mappings["customer"]),
            1,
        ),
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # ACCOUNT
    #
    # 24 REAL SCALED BEHAVIORAL FEATURES
    # -----------------------------------------------------

    data["account"].x = load_account_features(
        mappings["account"],
        split,
    )

    # -----------------------------------------------------
    # DEVICE
    # -----------------------------------------------------

    data["device"].x = torch.ones(
        (
            len(mappings["device"]),
            1,
        ),
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # ADDRESS
    # -----------------------------------------------------

    data["address"].x = torch.ones(
        (
            len(mappings["address"]),
            1,
        ),
        dtype=torch.float32,
    )

    # -----------------------------------------------------
    # DOCUMENT
    # -----------------------------------------------------

    data["document"].x = torch.ones(
        (
            len(mappings["document"]),
            1,
        ),
        dtype=torch.float32,
    )

    # =====================================================
    # IDENTITY RELATIONSHIPS
    # =====================================================

    print("\nIdentity relationships:")

    for edge_config in IDENTITY_EDGES:

        add_identity_edges(
            data,
            edge_config,
            mappings,
        )

    # =====================================================
    # LOAD TRANSACTION GRAPH
    # =====================================================

    transaction_file = (
        TRANSACTION_GRAPH_DIR
        / f"{split}_transaction_graph.parquet"
    )

    print(
        f"\nLoading transactions: "
        f"{transaction_file}"
    )

    transactions = pl.read_parquet(
        transaction_file
    )

    # =====================================================
    # TRANSACTION ACCOUNT IDs
    # =====================================================

    source_ids = (
        transactions["source_account"]
        .cast(pl.Utf8)
        .to_list()
    )

    target_ids = (
        transactions["target_account"]
        .cast(pl.Utf8)
        .to_list()
    )

    # =====================================================
    # VALIDATE ACCOUNT IDs
    # =====================================================

    missing_sources = [
        x
        for x in source_ids
        if x not in mappings["account"]
    ]

    missing_targets = [
        x
        for x in target_ids
        if x not in mappings["account"]
    ]

    if missing_sources:

        raise ValueError(
            f"Found {len(missing_sources):,} "
            f"source accounts missing from "
            f"account nodes."
        )

    if missing_targets:

        raise ValueError(
            f"Found {len(missing_targets):,} "
            f"target accounts missing from "
            f"account nodes."
        )

    # =====================================================
    # MAP ACCOUNTS → NODE INDICES
    # =====================================================

    source_indices = [
        mappings["account"][x]
        for x in source_ids
    ]

    target_indices = [
        mappings["account"][x]
        for x in target_ids
    ]

    edge_index = torch.tensor(
        [
            source_indices,
            target_indices,
        ],
        dtype=torch.long,
    )

    # =====================================================
    # TRANSACTION EDGE FEATURES
    # =====================================================

    edge_feature_columns = [
        "Amount",
        "log_amount",
        "is_cross_border",
        "currency_changed",
    ]

    missing_edge_columns = [
        column
        for column in edge_feature_columns
        if column not in transactions.columns
    ]

    if missing_edge_columns:

        raise ValueError(
            "Missing transaction edge features: "
            + str(missing_edge_columns)
        )

    edge_attr = torch.tensor(
        transactions.select(
            edge_feature_columns
        ).to_numpy(),
        dtype=torch.float32,
    )

    # =====================================================
    # TRANSACTION LABELS
    # =====================================================

    if "Is_laundering" not in transactions.columns:

        raise ValueError(
            "Is_laundering column not found "
            "in transaction graph."
        )

    edge_label = torch.tensor(
        transactions[
            "Is_laundering"
        ].to_numpy(),
        dtype=torch.float32,
    )

    # =====================================================
    # ADD TRANSACTION RELATION
    # =====================================================

    data[
        "account",
        "transfers",
        "account"
    ].edge_index = edge_index

    data[
        "account",
        "transfers",
        "account"
    ].edge_attr = edge_attr

    data[
        "account",
        "transfers",
        "account"
    ].edge_label = edge_label

    # =====================================================
    # GRAPH SUMMARY
    # =====================================================

    print("\nGraph summary:")

    for node_type in data.node_types:

        print(
            f"  {node_type}: "
            f"{tuple(data[node_type].x.shape)}"
        )

    print(
        "\nTransaction edges:",
        tuple(
            data[
                "account",
                "transfers",
                "account"
            ].edge_index.shape
        ),
    )

    print(
        "Transaction edge features:",
        tuple(
            data[
                "account",
                "transfers",
                "account"
            ].edge_attr.shape
        ),
    )

    print(
        "Transaction labels:",
        tuple(
            data[
                "account",
                "transfers",
                "account"
            ].edge_label.shape
        ),
    )

    print(
        "Laundering transactions:",
        int(edge_label.sum().item()),
    )

    # =====================================================
    # FINAL VALIDATION
    # =====================================================

    transaction_type = (
        "account",
        "transfers",
        "account",
    )

    # Account feature validation

    if data["account"].x.shape[0] != len(
        mappings["account"]
    ):

        raise ValueError(
            "Account node count does not match "
            "account feature count."
        )

    if data["account"].x.shape[1] != 24:

        raise ValueError(
            "Account nodes should contain "
            "exactly 24 features."
        )

    # Transaction validation

    expected_transactions = len(
        transactions
    )

    actual_transactions = (
        data[transaction_type]
        .edge_index
        .shape[1]
    )

    if actual_transactions != expected_transactions:

        raise ValueError(
            "Transaction edge count mismatch."
        )

    if (
        data[transaction_type]
        .edge_attr
        .shape[0]
        != expected_transactions
    ):

        raise ValueError(
            "Transaction edge feature count mismatch."
        )

    if (
        data[transaction_type]
        .edge_label
        .shape[0]
        != expected_transactions
    ):

        raise ValueError(
            "Transaction label count mismatch."
        )

    # Check all tensors are finite

    if not torch.isfinite(
        data["account"].x
    ).all():

        raise ValueError(
            "Account features contain NaN "
            "or infinite values."
        )

    if not torch.isfinite(
        data[transaction_type].edge_attr
    ).all():

        raise ValueError(
            "Transaction edge features contain "
            "NaN or infinite values."
        )

    print(
        "\nValidation PASSED."
    )

    # =====================================================
    # SAVE
    # =====================================================

    output_file = (
        OUTPUT_DIR
        / f"{split}_heterodata.pt"
    )

    torch.save(
        data,
        output_file,
    )

    print(
        f"Saved: {output_file}"
    )

    return data


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    for split in [
        "train",
        "validation",
        "test",
    ]:

        build_heterodata(split)

    print("\n" + "=" * 70)

    print(
        "ALL HETERODATA GRAPHS "
        "BUILT SUCCESSFULLY"
    )

    print("=" * 70)