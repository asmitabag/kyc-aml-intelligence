from pathlib import Path

import numpy as np
import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[3]

ACCOUNT_FEATURE_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "account_features"
)

GRAPH_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "graph"
    / "heterogeneous"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "aligned"
)


ACCOUNT_FEATURE_COLUMNS = [
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


def load_global_accounts() -> pl.DataFrame:
    """
    Load the global account-node list used by the heterogeneous graph.

    This establishes one consistent account ordering across
    train, validation, and test.
    """

    path = GRAPH_DIR / "account_nodes.parquet"

    print(f"Loading global account nodes: {path}")

    accounts = pl.read_parquet(path)

    if "account_id" not in accounts.columns:
        raise ValueError(
            "account_nodes.parquet must contain 'account_id'."
        )

    accounts = accounts.select("account_id")

    # Match the string representation used by the graph builder.
    accounts = accounts.with_columns(
        pl.col("account_id").cast(pl.String)
    )

    if accounts["account_id"].n_unique() != accounts.height:
        raise ValueError(
            "Duplicate account IDs found in global account nodes."
        )

    print(
        f"Global accounts: {accounts.height:,}"
    )

    return accounts


def align_split(
    split: str,
    global_accounts: pl.DataFrame,
) -> None:

    input_path = (
        ACCOUNT_FEATURE_DIR
        / f"{split}_account_features.parquet"
    )

    output_path = (
        OUTPUT_DIR
        / f"{split}_account_features_aligned.parquet"
    )

    print("\n" + "=" * 60)
    print(f"ALIGNING ACCOUNT FEATURES: {split.upper()}")
    print("=" * 60)

    print(f"Loading: {input_path}")

    features = pl.read_parquet(input_path)

    print(
        f"Input accounts: {features.height:,}"
    )

    # ---------------------------------------------------------
    # Validate input schema
    # ---------------------------------------------------------

    required_columns = [
        "account_id",
        *ACCOUNT_FEATURE_COLUMNS,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in features.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in {split}: {missing_columns}"
        )

    features = features.select(required_columns)

    # Ensure consistent account ID type
    features = features.with_columns(
        pl.col("account_id").cast(pl.String)
    )

    # Check duplicate account IDs
    duplicate_count = (
        features
        .select(
            pl.col("account_id").n_unique()
        )
        .item()
    )

    if duplicate_count != features.height:
        raise ValueError(
            f"Duplicate account IDs detected in {split}."
        )

    # ---------------------------------------------------------
    # Align to GLOBAL account ordering
    # ---------------------------------------------------------

    aligned = (
        global_accounts
        .join(
            features,
            on="account_id",
            how="left",
        )
    )

    print(
        f"Aligned accounts: {aligned.height:,}"
    )

    # ---------------------------------------------------------
    # Missing accounts
    # ---------------------------------------------------------

    missing_accounts = (
        aligned
        .filter(
            pl.col(ACCOUNT_FEATURE_COLUMNS[0]).is_null()
        )
        .height
    )

    print(
        f"Accounts without activity in {split}: "
        f"{missing_accounts:,}"
    )

    # These accounts have no observed activity in the split.
    # Zero is therefore the appropriate default for count,
    # amount, ratio, and log-aggregate features.
    aligned = aligned.with_columns(
        [
            pl.col(column)
            .fill_null(0)
            .cast(pl.Float64)
            .alias(column)
            for column in ACCOUNT_FEATURE_COLUMNS
        ]
    )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    assert aligned.height == global_accounts.height, (
        f"Row count mismatch: "
        f"{aligned.height:,} != "
        f"{global_accounts.height:,}"
    )

    assert (
        aligned["account_id"].n_unique()
        == global_accounts.height
    ), "Duplicate account IDs after alignment."

    null_count = (
        aligned
        .select(
            pl.sum_horizontal(
                [
                    pl.col(column)
                    .is_null()
                    .cast(pl.UInt64)
                    for column in ACCOUNT_FEATURE_COLUMNS
                ]
            ).sum()
        )
        .item()
    )

    assert null_count == 0, (
        f"Found {null_count:,} null feature values."
    )

    # Check for negative values.
    # Transaction counts and amounts should never be negative.
    non_negative_columns = [
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
        "cross_border_count",
        "cross_border_ratio",
        "log_incoming_total",
        "log_outgoing_total",
        "log_total_transaction_amount",
    ]

    for column in non_negative_columns:
        minimum = aligned[column].min()

        assert minimum >= 0, (
            f"Negative value found in "
            f"{column}: {minimum}"
        )

    # Ratios should be non-negative
    for column in [
        "incoming_outgoing_amount_ratio",
        "incoming_outgoing_count_ratio",
    ]:
        minimum = aligned[column].min()

        assert minimum >= 0, (
            f"Negative ratio found in "
            f"{column}: {minimum}"
        )

    print("\nValidation PASSED")

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    aligned.write_parquet(output_path)

    print(f"Saved: {output_path}")

    print(
        f"Features per account: "
        f"{len(ACCOUNT_FEATURE_COLUMNS)}"
    )


def main() -> None:

    global_accounts = load_global_accounts()

    for split in [
        "train",
        "validation",
        "test",
    ]:
        align_split(
            split,
            global_accounts,
        )

    print("\n" + "=" * 60)
    print("ACCOUNT FEATURE ALIGNMENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()