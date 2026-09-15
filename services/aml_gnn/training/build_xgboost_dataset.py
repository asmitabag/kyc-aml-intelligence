from pathlib import Path

import polars as pl


BASE_DIR = Path(__file__).resolve().parents[3]

GRAPH_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "graph"
)

TRANSACTION_FEATURE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
)

TEMPORAL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "temporal"
)

ACCOUNT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "scaled"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "xgboost"
)


SPLITS = [
    "train",
    "validation",
    "test",
]


ACCOUNT_ID = "account_id"
TRANSACTION_ID = "transaction_id"


# ============================================================
# Account-level features
# ============================================================

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


# ============================================================
# Transaction-level features
# ============================================================

TRANSACTION_FEATURES = [
    "Amount",
    "log_amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_cross_border",
    "currency_changed",
]


# ============================================================
# Temporal features
# ============================================================

TEMPORAL_FEATURES = [
    "sender_txn_count_1h",
    "sender_txn_count_24h",
    "sender_txn_count_7d",
    "sender_amount_1h",
    "sender_amount_24h",
    "sender_amount_7d",
    "receiver_txn_count_1h",
    "receiver_txn_count_24h",
    "receiver_txn_count_7d",
    "receiver_amount_1h",
    "receiver_amount_24h",
    "receiver_amount_7d",
    "sender_velocity_1h_24h",
    "receiver_velocity_1h_24h",
    "sender_amount_velocity_1h_24h",
    "receiver_amount_velocity_1h_24h",
]


# ============================================================
# Load transaction graph
# ============================================================

def load_transaction_graph(split: str) -> pl.DataFrame:

    path = (
        GRAPH_DIR
        / f"{split}_transaction_graph.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Transaction graph file not found:\n{path}"
        )

    df = pl.read_parquet(path)

    required_columns = [
        TRANSACTION_ID,
        "source_account",
        "target_account",
        "Is_laundering",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{split}: missing transaction graph columns:\n"
            f"{missing}"
        )

    df = df.select(required_columns)

    if df.height == 0:
        raise ValueError(
            f"{split}: transaction graph is empty."
        )

    if (
        df[TRANSACTION_ID].n_unique()
        != df.height
    ):
        raise ValueError(
            f"{split}: duplicate transaction IDs "
            f"in transaction graph."
        )

    return df


# ============================================================
# Load transaction features
# ============================================================

def load_transaction_features(
    split: str,
) -> pl.DataFrame:

    path = (
        TRANSACTION_FEATURE_DIR
        / f"{split}_features.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Transaction feature file not found:\n{path}"
        )

    df = pl.read_parquet(path)

    required_columns = TRANSACTION_FEATURES

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{split}: missing transaction feature columns:\n"
            f"{missing}"
        )

    # --------------------------------------------------------
    # transaction_features.parquet was created before
    # transaction_id existed.
    #
    # build_transaction_graph.py subsequently created
    # transaction_id using the row index.
    #
    # Reconstruct the same ID from the feature-file row order.
    # --------------------------------------------------------

    df = df.select(required_columns)

    df = df.with_row_index(
        name=TRANSACTION_ID,
        offset=0,
    )

    return df


# ============================================================
# Load account features
# ============================================================

def load_account_features(
    split: str,
) -> pl.DataFrame:

    path = (
        ACCOUNT_DIR
        / f"{split}_account_features_scaled.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Account feature file not found:\n{path}"
        )

    df = pl.read_parquet(path)

    required_columns = (
        [ACCOUNT_ID]
        + ACCOUNT_FEATURES
    )

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{split}: missing account feature columns:\n"
            f"{missing}"
        )

    df = df.select(required_columns)

    if (
        df[ACCOUNT_ID].n_unique()
        != df.height
    ):
        raise ValueError(
            f"{split}: duplicate account IDs."
        )

    return df


# ============================================================
# Load temporal features
# ============================================================

def load_temporal_features(
    split: str,
) -> pl.DataFrame:

    path = (
        TEMPORAL_DIR
        / f"{split}_temporal_features.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Temporal feature file not found:\n{path}"
        )

    df = pl.read_parquet(path)

    required_columns = (
        [TRANSACTION_ID]
        + TEMPORAL_FEATURES
    )

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{split}: missing temporal feature columns:\n"
            f"{missing}"
        )

    df = df.select(required_columns)

    if (
        df[TRANSACTION_ID].n_unique()
        != df.height
    ):
        raise ValueError(
            f"{split}: duplicate transaction IDs "
            f"in temporal features."
        )

    return df


# ============================================================
# Build XGBoost dataset
# ============================================================

def build_dataset(split: str) -> pl.DataFrame:

    print(f"\n{'=' * 60}")
    print(f"Building {split.upper()} XGBoost dataset")
    print(f"{'=' * 60}")

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    transactions = load_transaction_graph(split)

    transaction_features = (
        load_transaction_features(split)
    )

    temporal = load_temporal_features(split)

    accounts = load_account_features(split)

    print(
        f"Transaction graph:     {transactions.shape}"
    )

    print(
        f"Transaction features:  {transaction_features.shape}"
    )

    print(
        f"Temporal features:     {temporal.shape}"
    )

    print(
        f"Account features:      {accounts.shape}"
    )

    # --------------------------------------------------------
    # Validate transaction row counts
    # --------------------------------------------------------

    if (
        transactions.height
        != transaction_features.height
    ):
        raise ValueError(
            f"{split}: transaction graph and "
            f"transaction feature row counts differ:\n"
            f"Graph: {transactions.height:,}\n"
            f"Features: {transaction_features.height:,}"
        )

    if (
        transactions.height
        != temporal.height
    ):
        raise ValueError(
            f"{split}: transaction graph and "
            f"temporal feature row counts differ:\n"
            f"Graph: {transactions.height:,}\n"
            f"Temporal: {temporal.height:,}"
        )

    # --------------------------------------------------------
    # Validate transaction ID alignment
    # --------------------------------------------------------

    print("\nValidating transaction ID alignment...")

    graph_ids = (
        transactions[TRANSACTION_ID]
        .to_list()
    )

    feature_ids = (
        transaction_features[TRANSACTION_ID]
        .to_list()
    )

    temporal_ids = (
        temporal[TRANSACTION_ID]
        .to_list()
    )

    if graph_ids != feature_ids:
        raise ValueError(
            f"{split}: transaction feature IDs "
            f"do not match transaction graph IDs."
        )

    if graph_ids != temporal_ids:
        raise ValueError(
            f"{split}: temporal transaction IDs "
            f"do not match transaction graph IDs."
        )

    print(
        "  Transaction IDs aligned successfully."
    )

    # --------------------------------------------------------
    # Join transaction features
    # --------------------------------------------------------

    print(
        "\nJoining transaction features..."
    )

    result = transactions.join(
        transaction_features,
        on=TRANSACTION_ID,
        how="left",
    )

    if result.height != transactions.height:
        raise ValueError(
            f"{split}: transaction feature join "
            f"changed row count:\n"
            f"{transactions.height} -> {result.height}"
        )

    print(
        "  Transaction feature join successful."
    )

    # --------------------------------------------------------
    # Prepare sender account features
    # --------------------------------------------------------

    sender_rename = {
        ACCOUNT_ID: "source_account"
    }

    sender_rename.update(
        {
            feature: f"sender_{feature}"
            for feature in ACCOUNT_FEATURES
        }
    )

    sender_accounts = accounts.rename(
        sender_rename
    )

    # --------------------------------------------------------
    # Prepare receiver account features
    # --------------------------------------------------------

    receiver_rename = {
        ACCOUNT_ID: "target_account"
    }

    receiver_rename.update(
        {
            feature: f"receiver_{feature}"
            for feature in ACCOUNT_FEATURES
        }
    )

    receiver_accounts = accounts.rename(
        receiver_rename
    )

    # --------------------------------------------------------
    # Join sender features
    # --------------------------------------------------------

    print(
        "Joining sender account features..."
    )

    result = result.join(
        sender_accounts,
        on="source_account",
        how="left",
    )

    if result.height != transactions.height:
        raise ValueError(
            f"{split}: sender join changed row count:\n"
            f"{transactions.height} -> {result.height}"
        )

    print(
        "  Sender join successful."
    )

    # --------------------------------------------------------
    # Join receiver features
    # --------------------------------------------------------

    print(
        "Joining receiver account features..."
    )

    result = result.join(
        receiver_accounts,
        on="target_account",
        how="left",
    )

    if result.height != transactions.height:
        raise ValueError(
            f"{split}: receiver join changed row count:\n"
            f"{transactions.height} -> {result.height}"
        )

    print(
        "  Receiver join successful."
    )

    # --------------------------------------------------------
    # Join temporal features
    # --------------------------------------------------------

    print(
        "Joining temporal features..."
    )

    result = result.join(
        temporal,
        on=TRANSACTION_ID,
        how="left",
    )

    if result.height != transactions.height:
        raise ValueError(
            f"{split}: temporal join changed row count:\n"
            f"{transactions.height} -> {result.height}"
        )

    print(
        "  Temporal join successful."
    )

    # --------------------------------------------------------
    # Define final feature columns
    # --------------------------------------------------------

    sender_features = [
        f"sender_{feature}"
        for feature in ACCOUNT_FEATURES
    ]

    receiver_features = [
        f"receiver_{feature}"
        for feature in ACCOUNT_FEATURES
    ]

    feature_columns = (
        TRANSACTION_FEATURES
        + sender_features
        + receiver_features
        + TEMPORAL_FEATURES
    )

    expected_feature_count = 71

    print(
        f"\nTotal ML features: "
        f"{len(feature_columns)}"
    )

    if (
        len(feature_columns)
        != expected_feature_count
    ):
        raise ValueError(
            f"Expected {expected_feature_count} "
            f"features, got {len(feature_columns)}."
        )

    # --------------------------------------------------------
    # Check feature existence
    # --------------------------------------------------------

    missing = [
        column
        for column in feature_columns
        if column not in result.columns
    ]

    if missing:
        raise ValueError(
            f"{split}: missing final feature columns:\n"
            f"{missing}"
        )

    # --------------------------------------------------------
    # Check missing values
    # --------------------------------------------------------

    print(
        "\nChecking missing values..."
    )

    null_counts = (
        result
        .select(feature_columns)
        .null_count()
        .to_dicts()[0]
    )

    null_columns = {
        column: count
        for column, count in null_counts.items()
        if count > 0
    }

    if null_columns:

        print(
            f"  Found missing values in "
            f"{len(null_columns)} columns."
        )

        for column, count in null_columns.items():
            print(
                f"    {column}: {count:,}"
            )

        print(
            "\n  Filling missing feature values with 0."
        )

        result = result.with_columns(
            [
                pl.col(column).fill_null(0)
                for column in null_columns
            ]
        )

    else:

        print(
            "  No missing feature values."
        )

    # --------------------------------------------------------
    # Final null validation
    # --------------------------------------------------------

    remaining_nulls = (
        result
        .select(feature_columns)
        .null_count()
        .sum_horizontal()
        .item()
    )

    if remaining_nulls > 0:
        raise ValueError(
            f"{split}: {remaining_nulls} null values "
            f"remain after filling."
        )

    # --------------------------------------------------------
    # Select final dataset
    # --------------------------------------------------------

    result = result.select(
        [
            TRANSACTION_ID
        ]
        + feature_columns
        + ["Is_laundering"]
    )

    # --------------------------------------------------------
    # Validate final row count
    # --------------------------------------------------------

    if result.height != transactions.height:
        raise ValueError(
            f"{split}: final row count mismatch."
        )

    # --------------------------------------------------------
    # Validate transaction uniqueness
    # --------------------------------------------------------

    if (
        result[TRANSACTION_ID].n_unique()
        != result.height
    ):
        raise ValueError(
            f"{split}: duplicate transaction IDs "
            f"in final dataset."
        )

    # --------------------------------------------------------
    # Validate labels
    # --------------------------------------------------------

    laundering_count = int(
        result["Is_laundering"].sum()
    )

    normal_count = (
        result.height
        - laundering_count
    )

    laundering_rate = (
        laundering_count
        / result.height
    )

    print("\nFinal dataset:")

    print(
        f"  Rows:            {result.height:,}"
    )

    print(
        f"  Features:        {len(feature_columns)}"
    )

    print(
        f"  Normal:          {normal_count:,}"
    )

    print(
        f"  Laundering:      {laundering_count:,}"
    )

    print(
        f"  Laundering rate: "
        f"{laundering_rate:.6%}"
    )

    # --------------------------------------------------------
    # Numerical validation
    # --------------------------------------------------------

    print(
        "\nValidating numerical features..."
    )

    numeric_dtypes = {
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
        pl.Float32,
        pl.Float64,
    }

    for column in feature_columns:

        dtype = result[column].dtype

        if dtype not in numeric_dtypes:
            raise ValueError(
                f"{split}: feature '{column}' "
                f"has non-numeric dtype {dtype}."
            )

    print(
        "  Numerical validation passed."
    )

    return result


# ============================================================
# Main
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 60)
    print("XGBOOST DATASET BUILDER")
    print("=" * 60)

    for split in SPLITS:

        dataset = build_dataset(split)

        output_path = (
            OUTPUT_DIR
            / f"{split}_xgboost_dataset.parquet"
        )

        dataset.write_parquet(
            output_path,
            compression="zstd",
        )

        print(
            f"\nSaved {split} dataset:"
        )

        print(output_path)

    print("\n" + "=" * 60)
    print(
        "ALL XGBOOST DATASETS CREATED SUCCESSFULLY"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()