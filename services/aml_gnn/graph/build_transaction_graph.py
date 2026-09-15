from pathlib import Path

import polars as pl


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FEATURE_DIR = PROJECT_ROOT / "data" / "processed" / "features"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "graph"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Columns required for the transaction graph
# ---------------------------------------------------------

GRAPH_COLUMNS = [
    "Sender_account",
    "Receiver_account",
    "Amount",
    "log_amount",
    "timestamp",
    "Payment_type",
    "is_cross_border",
    "currency_changed",
    "Is_laundering",
]


# ---------------------------------------------------------
# Build graph for one split
# ---------------------------------------------------------

def build_transaction_graph(split: str):

    input_path = FEATURE_DIR / f"{split}_features.parquet"
    output_path = OUTPUT_DIR / f"{split}_transaction_graph.parquet"

    print(f"\nBuilding transaction graph: {split}")
    print(f"Input: {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {input_path}"
        )

    df = pl.read_parquet(input_path)

    print(f"Transactions loaded: {df.height:,}")

    # -----------------------------------------------------
    # Validate required columns
    # -----------------------------------------------------

    missing_columns = [
        col for col in GRAPH_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # -----------------------------------------------------
    # Keep only graph-relevant information
    # -----------------------------------------------------

    graph = df.select(GRAPH_COLUMNS)

    # -----------------------------------------------------
    # Convert account IDs to strings
    #
    # This is important because later our heterogeneous
    # graph will contain IDs such as:
    #
    # A123
    # C123
    # D123
    # ADDR123
    # DOC123
    # -----------------------------------------------------

    graph = graph.with_columns([
        pl.col("Sender_account")
        .cast(pl.Utf8)
        .alias("source_account"),

        pl.col("Receiver_account")
        .cast(pl.Utf8)
        .alias("target_account"),
    ])

    # -----------------------------------------------------
    # Add a unique transaction ID
    # -----------------------------------------------------

    graph = graph.with_row_index(
        name="transaction_id",
        offset=0,
    )

    # -----------------------------------------------------
    # Reorder columns
    # -----------------------------------------------------

    graph = graph.select([
        "transaction_id",
        "source_account",
        "target_account",
        "Amount",
        "log_amount",
        "timestamp",
        "Payment_type",
        "is_cross_border",
        "currency_changed",
        "Is_laundering",
    ])

    # -----------------------------------------------------
    # Basic validation
    # -----------------------------------------------------

    null_counts = graph.null_count()

    print("\nNull values:")
    print(null_counts)

    # Self-transfers are allowed to exist in raw data, but
    # we flag them instead of silently deleting them.
    graph = graph.with_columns(
        (
            pl.col("source_account")
            == pl.col("target_account")
        ).alias("is_self_transfer")
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    graph.write_parquet(output_path)

    print(f"\nSaved: {output_path}")
    print(f"Rows: {graph.height:,}")

    print("\nSample:")
    print(graph.head(5))

    return graph


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    for split in ["train", "validation", "test"]:
        build_transaction_graph(split)

    print("\nTransaction graph construction complete.")