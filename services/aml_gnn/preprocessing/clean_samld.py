from pathlib import Path
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path("data/raw/samld/SAML-D.csv")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "samld_cleaned.parquet"


# ============================================================
# Required columns
# ============================================================

REQUIRED_COLUMNS = [
    "Time",
    "Date",
    "Sender_account",
    "Receiver_account",
    "Amount",
    "Payment_currency",
    "Received_currency",
    "Sender_bank_location",
    "Receiver_bank_location",
    "Payment_type",
    "Is_laundering",
    "Laundering_type",
]


# ============================================================
# Load dataset
# ============================================================

def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path.resolve()}"
        )

    print(f"Loading dataset from: {path}")

    df = pd.read_csv(path)

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    return df


# ============================================================
# Validate schema
# ============================================================

def validate_schema(df: pd.DataFrame) -> None:
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Schema validation: PASSED")


# ============================================================
# Clean and transform
# ============================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    # --------------------------------------------------------
    # Remove exact duplicate transactions
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates().copy()

    removed = before - len(df)

    print(f"Duplicate rows removed: {removed:,}")


    # --------------------------------------------------------
    # Clean string columns
    # --------------------------------------------------------

    string_columns = [
        "Payment_currency",
        "Received_currency",
        "Sender_bank_location",
        "Receiver_bank_location",
        "Payment_type",
        "Laundering_type",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string").str.strip()


    # --------------------------------------------------------
    # Convert account IDs
    # --------------------------------------------------------

    df["Sender_account"] = pd.to_numeric(
        df["Sender_account"],
        errors="coerce"
    )

    df["Receiver_account"] = pd.to_numeric(
        df["Receiver_account"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Convert amount
    # --------------------------------------------------------

    df["Amount"] = pd.to_numeric(
        df["Amount"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Convert AML label
    # --------------------------------------------------------

    df["Is_laundering"] = pd.to_numeric(
        df["Is_laundering"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Combine Date + Time
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["Date"].astype(str)
        + " "
        + df["Time"].astype(str),
        errors="coerce"
    )


    # --------------------------------------------------------
    # Validate transaction values
    # --------------------------------------------------------

    invalid_accounts = (
        df["Sender_account"].isna()
        | df["Receiver_account"].isna()
    )

    invalid_amounts = (
        df["Amount"].isna()
        | (df["Amount"] <= 0)
    )

    invalid_labels = ~df["Is_laundering"].isin([0, 1])

    invalid_timestamps = df["timestamp"].isna()


    invalid_rows = (
        invalid_accounts
        | invalid_amounts
        | invalid_labels
        | invalid_timestamps
    )

    print(f"Invalid rows found: {invalid_rows.sum():,}")


    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    df = df.loc[~invalid_rows].copy()


    # --------------------------------------------------------
    # Convert types
    # --------------------------------------------------------

    df["Sender_account"] = df["Sender_account"].astype("int64")
    df["Receiver_account"] = df["Receiver_account"].astype("int64")
    df["Is_laundering"] = df["Is_laundering"].astype("int8")


    # --------------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------------

    df = df.sort_values(
        "timestamp"
    ).reset_index(drop=True)


    # --------------------------------------------------------
    # Add useful temporal features
    # --------------------------------------------------------

    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["day"] = df["timestamp"].dt.day
    df["hour"] = df["timestamp"].dt.hour
    df["minute"] = df["timestamp"].dt.minute
    df["second"] = df["timestamp"].dt.second

    df["day_of_week"] = df["timestamp"].dt.dayofweek

    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype("int8")


    # --------------------------------------------------------
    # Log transaction amount
    # --------------------------------------------------------

    df["log_amount"] = (
        df["Amount"].clip(lower=0).apply(
            lambda x: __import__("math").log1p(x)
        )
    )


    # --------------------------------------------------------
    # Final column ordering
    # --------------------------------------------------------

    preferred_columns = [
        "timestamp",
        "Sender_account",
        "Receiver_account",
        "Amount",
        "log_amount",
        "Payment_currency",
        "Received_currency",
        "Sender_bank_location",
        "Receiver_bank_location",
        "Payment_type",
        "Is_laundering",
        "Laundering_type",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "day_of_week",
        "is_weekend",
    ]

    df = df[preferred_columns]


    return df


# ============================================================
# Save
# ============================================================

def save_data(df: pd.DataFrame, path: Path) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        path,
        index=False
    )

    print(f"\nCleaned dataset saved to:")
    print(path.resolve())


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("SAML-D CLEANING PIPELINE")
    print("=" * 70)

    df = load_data(INPUT_FILE)

    validate_schema(df)

    df = clean_data(df)

    print("\n" + "=" * 70)
    print("CLEANED DATASET SUMMARY")
    print("=" * 70)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nAML label distribution:")

    print(
        df["Is_laundering"]
        .value_counts()
        .sort_index()
    )

    print("\nTimestamp range:")

    print("Start:", df["timestamp"].min())
    print("End:  ", df["timestamp"].max())

    save_data(
        df,
        OUTPUT_FILE
    )

    print("\nCleaning complete.")


if __name__ == "__main__":
    main()