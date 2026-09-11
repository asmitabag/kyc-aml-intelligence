from pathlib import Path
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path(
    "data/processed/samld_cleaned.parquet"
)

OUTPUT_DIR = Path(
    "data/processed/splits"
)


# ============================================================
# Split configuration
# ============================================================

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("SAML-D CHRONOLOGICAL SPLIT")
    print("=" * 70)

    # --------------------------------------------------------
    # Load cleaned data
    # --------------------------------------------------------

    print("\nLoading cleaned dataset...")

    df = pd.read_parquet(INPUT_FILE)

    print(f"Rows loaded: {len(df):,}")

    # --------------------------------------------------------
    # Ensure chronological order
    # --------------------------------------------------------

    df = df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Calculate split boundaries
    # --------------------------------------------------------

    total_rows = len(df)

    train_end = int(
        total_rows * TRAIN_RATIO
    )

    validation_end = int(
        total_rows * (TRAIN_RATIO + VALIDATION_RATIO)
    )

    # --------------------------------------------------------
    # Create splits
    # --------------------------------------------------------

    train_df = df.iloc[:train_end].copy()

    validation_df = df.iloc[
        train_end:validation_end
    ].copy()

    test_df = df.iloc[
        validation_end:
    ].copy()

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save splits
    # --------------------------------------------------------

    train_file = OUTPUT_DIR / "train.parquet"
    validation_file = OUTPUT_DIR / "validation.parquet"
    test_file = OUTPUT_DIR / "test.parquet"

    train_df.to_parquet(
        train_file,
        index=False
    )

    validation_df.to_parquet(
        validation_file,
        index=False
    )

    test_df.to_parquet(
        test_file,
        index=False
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SPLIT SUMMARY")
    print("=" * 70)

    print(
        f"\nTrain:      {len(train_df):,} rows"
    )

    print(
        f"Validation: {len(validation_df):,} rows"
    )

    print(
        f"Test:       {len(test_df):,} rows"
    )

    print("\nDate ranges:")

    print(
        "Train:"
        f"      {train_df['timestamp'].min()}"
        f" → {train_df['timestamp'].max()}"
    )

    print(
        "Validation:"
        f" {validation_df['timestamp'].min()}"
        f" → {validation_df['timestamp'].max()}"
    )

    print(
        "Test:"
        f"       {test_df['timestamp'].min()}"
        f" → {test_df['timestamp'].max()}"
    )

    # --------------------------------------------------------
    # AML distribution
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("AML LABEL DISTRIBUTION")
    print("=" * 70)

    for name, split in [
        ("TRAIN", train_df),
        ("VALIDATION", validation_df),
        ("TEST", test_df),
    ]:

        laundering = int(
            split["Is_laundering"].sum()
        )

        normal = len(split) - laundering

        rate = (
            laundering / len(split) * 100
            if len(split) > 0
            else 0
        )

        print(
            f"\n{name}"
        )

        print(
            f"  Normal:     {normal:,}"
        )

        print(
            f"  Laundering: {laundering:,}"
        )

        print(
            f"  Rate:       {rate:.4f}%"
        )

    print("\n" + "=" * 70)
    print("FILES SAVED")
    print("=" * 70)

    print(train_file)
    print(validation_file)
    print(test_file)

    print("\nSplit complete.")


if __name__ == "__main__":
    main()