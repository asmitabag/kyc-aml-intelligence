from pathlib import Path
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_DIR = Path("data/processed/splits")
OUTPUT_DIR = Path("data/processed/features")


# ============================================================
# Feature creation
# ============================================================

def create_transaction_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # --------------------------------------------------------
    # Transaction amount
    # --------------------------------------------------------

    df["log_amount"] = (
        pd.Series(df["Amount"])
        .clip(lower=0)
        .pipe(lambda x: x.map(lambda value: __import__("math").log1p(value)))
    )

    # --------------------------------------------------------
    # Time-based features
    # --------------------------------------------------------

    df["hour"] = df["timestamp"].dt.hour

    df["day_of_week"] = (
        df["timestamp"].dt.dayofweek
    )

    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype("int8")

    # --------------------------------------------------------
    # Cross-border transaction
    # --------------------------------------------------------

    df["is_cross_border"] = (
        df["Sender_bank_location"]
        != df["Receiver_bank_location"]
    ).astype("int8")

    # --------------------------------------------------------
    # Currency conversion / currency mismatch
    # --------------------------------------------------------

    df["currency_changed"] = (
        df["Payment_currency"]
        != df["Received_currency"]
    ).astype("int8")

    return df


# ============================================================
# Process one split
# ============================================================

def process_split(split_name: str):

    input_file = (
        INPUT_DIR / f"{split_name}.parquet"
    )

    output_file = (
        OUTPUT_DIR / f"{split_name}_features.parquet"
    )

    print("\n" + "=" * 70)
    print(f"PROCESSING {split_name.upper()}")
    print("=" * 70)

    print(f"Loading: {input_file}")

    df = pd.read_parquet(input_file)

    print(f"Rows: {len(df):,}")

    df = create_transaction_features(df)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        output_file,
        index=False
    )

    print(f"Saved: {output_file}")

    print("\nNew features:")

    print(
        df[
            [
                "log_amount",
                "hour",
                "day_of_week",
                "is_weekend",
                "is_cross_border",
                "currency_changed",
            ]
        ].head()
    )


# ============================================================
# Main
# ============================================================

def main():

    for split_name in [
        "train",
        "validation",
        "test",
    ]:

        process_split(split_name)

    print("\n" + "=" * 70)
    print("TRANSACTION FEATURE CREATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()