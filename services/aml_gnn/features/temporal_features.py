from pathlib import Path

import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "graph"
OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "temporal"
)


def calculate_temporal_features(split: str) -> None:
    input_path = INPUT_DIR / f"{split}_transaction_graph.parquet"
    output_path = OUTPUT_DIR / f"{split}_temporal_features.parquet"

    print("\n" + "=" * 60)
    print(f"TEMPORAL FEATURES: {split.upper()}")
    print("=" * 60)

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------

    print(f"Loading: {input_path}")

    df = pl.read_parquet(
        input_path,
        columns=[
            "transaction_id",
            "source_account",
            "target_account",
            "Amount",
            "timestamp",
        ],
    )

    print(f"Transactions: {df.height:,}")

    # Make sure timestamp is Datetime
    df = df.with_columns(
        pl.col("timestamp").cast(pl.Datetime)
    )

    # ---------------------------------------------------------
    # OUTGOING TRANSACTIONS
    # ---------------------------------------------------------

    print("Preparing outgoing transactions...")

    outgoing = (
        df.select(
            [
                "transaction_id",
                pl.col("source_account").alias("account_id"),
                "timestamp",
                pl.col("Amount").alias("amount"),
            ]
        )
        .sort(["account_id", "timestamp"])
        .with_columns(
            pl.lit(1).alias("txn")
        )
    )

    print("Calculating outgoing temporal features...")

    outgoing = outgoing.with_columns(
        [
            # Number of previous outgoing transactions in 1 hour
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="1h",
                closed="left",
            )
            .over("account_id")
            .alias("sender_txn_count_1h"),

            # Number of previous outgoing transactions in 24 hours
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="24h",
                closed="left",
            )
            .over("account_id")
            .alias("sender_txn_count_24h"),

            # Number of previous outgoing transactions in 7 days
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="7d",
                closed="left",
            )
            .over("account_id")
            .alias("sender_txn_count_7d"),

            # Previous outgoing amount in 1 hour
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="1h",
                closed="left",
            )
            .over("account_id")
            .alias("sender_amount_1h"),

            # Previous outgoing amount in 24 hours
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="24h",
                closed="left",
            )
            .over("account_id")
            .alias("sender_amount_24h"),

            # Previous outgoing amount in 7 days
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="7d",
                closed="left",
            )
            .over("account_id")
            .alias("sender_amount_7d"),
        ]
    )

    outgoing = outgoing.select(
        [
            "transaction_id",
            "sender_txn_count_1h",
            "sender_txn_count_24h",
            "sender_txn_count_7d",
            "sender_amount_1h",
            "sender_amount_24h",
            "sender_amount_7d",
        ]
    )

    # ---------------------------------------------------------
    # INCOMING TRANSACTIONS
    # ---------------------------------------------------------

    print("Preparing incoming transactions...")

    incoming = (
        df.select(
            [
                "transaction_id",
                pl.col("target_account").alias("account_id"),
                "timestamp",
                pl.col("Amount").alias("amount"),
            ]
        )
        .sort(["account_id", "timestamp"])
        .with_columns(
            pl.lit(1).alias("txn")
        )
    )

    print("Calculating incoming temporal features...")

    incoming = incoming.with_columns(
        [
            # Number of previous incoming transactions in 1 hour
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="1h",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_txn_count_1h"),

            # Number of previous incoming transactions in 24 hours
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="24h",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_txn_count_24h"),

            # Number of previous incoming transactions in 7 days
            pl.col("txn")
            .rolling_sum_by(
                by="timestamp",
                window_size="7d",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_txn_count_7d"),

            # Previous incoming amount in 1 hour
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="1h",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_amount_1h"),

            # Previous incoming amount in 24 hours
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="24h",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_amount_24h"),

            # Previous incoming amount in 7 days
            pl.col("amount")
            .rolling_sum_by(
                by="timestamp",
                window_size="7d",
                closed="left",
            )
            .over("account_id")
            .alias("receiver_amount_7d"),
        ]
    )

    incoming = incoming.select(
        [
            "transaction_id",
            "receiver_txn_count_1h",
            "receiver_txn_count_24h",
            "receiver_txn_count_7d",
            "receiver_amount_1h",
            "receiver_amount_24h",
            "receiver_amount_7d",
        ]
    )

    # ---------------------------------------------------------
    # JOIN
    # ---------------------------------------------------------

    print("Joining outgoing and incoming features...")

    result = (
        df.select("transaction_id")
        .join(
            outgoing,
            on="transaction_id",
            how="left",
        )
        .join(
            incoming,
            on="transaction_id",
            how="left",
        )
        .fill_null(0)
    )

    # ---------------------------------------------------------
    # VELOCITY FEATURES
    # ---------------------------------------------------------

    print("Creating velocity features...")

    result = result.with_columns(
        [
            (
                pl.col("sender_txn_count_1h")
                / pl.col("sender_txn_count_24h").clip(
                    lower_bound=1
                )
            ).alias("sender_velocity_1h_24h"),

            (
                pl.col("receiver_txn_count_1h")
                / pl.col("receiver_txn_count_24h").clip(
                    lower_bound=1
                )
            ).alias("receiver_velocity_1h_24h"),

            (
                pl.col("sender_amount_1h")
                / pl.col("sender_amount_24h").clip(
                    lower_bound=1
                )
            ).alias("sender_amount_velocity_1h_24h"),

            (
                pl.col("receiver_amount_1h")
                / pl.col("receiver_amount_24h").clip(
                    lower_bound=1
                )
            ).alias("receiver_amount_velocity_1h_24h"),
        ]
    )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    print("Validating...")

    # Check row count
    assert result.height == df.height, (
        f"Row count mismatch: "
        f"{result.height:,} != {df.height:,}"
    )

    # Check transaction IDs
    assert result["transaction_id"].n_unique() == df.height, (
        "Duplicate transaction IDs detected."
    )

    # All temporal feature columns
    numeric_columns = [
        c
        for c in result.columns
        if c != "transaction_id"
    ]

    # Check null values
    null_count = (
        result
        .select(
            pl.sum_horizontal(
                [
                    pl.col(c)
                    .is_null()
                    .cast(pl.UInt64)
                    for c in numeric_columns
                ]
            ).sum()
        )
        .item()
    )

    assert null_count == 0, (
        f"Found {null_count:,} null values."
    )

    # Temporal counts and amounts cannot be negative
    for column in numeric_columns:
        minimum = result[column].min()

        assert minimum >= 0, (
            f"Negative value found in {column}: {minimum}"
        )

    # Check for infinite values
    for column in numeric_columns:
        infinite_count = (
            result
            .select(
                pl.col(column)
                .is_infinite()
                .sum()
            )
            .item()
        )

        assert infinite_count == 0, (
            f"Infinite value found in {column}: "
            f"{infinite_count:,}"
        )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.write_parquet(output_path)

    print("\nValidation PASSED")
    print(f"Rows: {result.height:,}")
    print(f"Columns: {result.width}")
    print(f"Saved: {output_path}")

    print("\nGenerated features:")

    for column in result.columns:
        print(f"  - {column}")


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    for split in [
        "train",
        "validation",
        "test",
    ]:
        calculate_temporal_features(split)

    print("\n" + "=" * 60)
    print("TEMPORAL FEATURE ENGINEERING COMPLETE")
    print("=" * 60)