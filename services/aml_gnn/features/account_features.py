from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

SPLIT_DIR = BASE_DIR / "data" / "processed" / "features"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "account_features"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ACCOUNT FEATURE CREATION
# ============================================================

def create_account_features(split_name: str):

    input_path = SPLIT_DIR / f"{split_name}_features.parquet"
    output_path = OUTPUT_DIR / f"{split_name}_account_features.parquet"

    print("\n" + "=" * 70)
    print(f"PROCESSING {split_name.upper()}")
    print("=" * 70)

    print(f"Loading: {input_path}")

    df = pd.read_parquet(input_path)

    print(f"Rows: {len(df):,}")

    # --------------------------------------------------------
    # Make sure timestamp is datetime
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --------------------------------------------------------
    # Create directional transaction tables
    # --------------------------------------------------------

    sender = df[
        [
            "Sender_account",
            "Receiver_account",
            "Amount",
            "is_cross_border",
            "Payment_type",
        ]
    ].copy()

    receiver = df[
        [
            "Receiver_account",
            "Sender_account",
            "Amount",
            "is_cross_border",
            "Payment_type",
        ]
    ].copy()

    # ========================================================
    # OUTGOING FEATURES
    # ========================================================

    outgoing = (
        sender
        .groupby("Sender_account")
        .agg(
            outgoing_count=("Amount", "size"),
            outgoing_total=("Amount", "sum"),
            outgoing_mean=("Amount", "mean"),
            outgoing_std=("Amount", "std"),
            outgoing_max=("Amount", "max"),
            outgoing_cross_border_count=("is_cross_border", "sum"),
        )
        .reset_index()
        .rename(columns={"Sender_account": "account_id"})
    )

    # ========================================================
    # INCOMING FEATURES
    # ========================================================

    incoming = (
        receiver
        .groupby("Receiver_account")
        .agg(
            incoming_count=("Amount", "size"),
            incoming_total=("Amount", "sum"),
            incoming_mean=("Amount", "mean"),
            incoming_std=("Amount", "std"),
            incoming_max=("Amount", "max"),
            incoming_cross_border_count=("is_cross_border", "sum"),
        )
        .reset_index()
        .rename(columns={"Receiver_account": "account_id"})
    )

    # ========================================================
    # UNIQUE COUNTERPARTIES
    # ========================================================

    outgoing_counterparties = (
        sender
        .groupby("Sender_account")["Receiver_account"]
        .nunique()
        .reset_index()
        .rename(
            columns={
                "Sender_account": "account_id",
                "Receiver_account": "unique_outgoing_counterparties",
            }
        )
    )

    incoming_counterparties = (
        receiver
        .groupby("Receiver_account")["Sender_account"]
        .nunique()
        .reset_index()
        .rename(
            columns={
                "Receiver_account": "account_id",
                "Sender_account": "unique_incoming_counterparties",
            }
        )
    )

    # ========================================================
    # COMBINE FEATURES
    # ========================================================

    account_features = pd.merge(
        outgoing,
        incoming,
        on="account_id",
        how="outer",
    )

    account_features = pd.merge(
        account_features,
        outgoing_counterparties,
        on="account_id",
        how="left",
    )

    account_features = pd.merge(
        account_features,
        incoming_counterparties,
        on="account_id",
        how="left",
    )

    # ========================================================
    # FILL MISSING VALUES
    # ========================================================

    numeric_columns = account_features.select_dtypes(
        include=[np.number]
    ).columns

    account_features[numeric_columns] = (
        account_features[numeric_columns].fillna(0)
    )

    # ========================================================
    # DERIVED BEHAVIORAL FEATURES
    # ========================================================

    account_features["total_transaction_count"] = (
        account_features["incoming_count"]
        + account_features["outgoing_count"]
    )

    account_features["total_transaction_amount"] = (
        account_features["incoming_total"]
        + account_features["outgoing_total"]
    )

    account_features["total_unique_counterparties"] = (
        account_features["unique_incoming_counterparties"]
        + account_features["unique_outgoing_counterparties"]
    )

    # Incoming / outgoing amount ratio
    account_features["incoming_outgoing_amount_ratio"] = (
        account_features["incoming_total"]
        / (account_features["outgoing_total"] + 1e-9)
    )

    # Incoming / outgoing transaction ratio
    account_features["incoming_outgoing_count_ratio"] = (
        account_features["incoming_count"]
        / (account_features["outgoing_count"] + 1e-9)
    )

    # Cross-border transaction ratio
    account_features["cross_border_count"] = (
        account_features["incoming_cross_border_count"]
        + account_features["outgoing_cross_border_count"]
    )

    account_features["cross_border_ratio"] = (
        account_features["cross_border_count"]
        / (account_features["total_transaction_count"] + 1e-9)
    )

    # ========================================================
    # LOG TRANSFORMATIONS
    # ========================================================

    account_features["log_incoming_total"] = np.log1p(
        account_features["incoming_total"]
    )

    account_features["log_outgoing_total"] = np.log1p(
        account_features["outgoing_total"]
    )

    account_features["log_total_transaction_amount"] = np.log1p(
        account_features["total_transaction_amount"]
    )

    # ========================================================
    # CLEAN NUMERIC VALUES
    # ========================================================

    account_features = account_features.replace(
        [np.inf, -np.inf],
        0,
    )

    # ========================================================
    # SAVE
    # ========================================================

    account_features.to_parquet(
        output_path,
        index=False,
    )

    print(f"Accounts: {len(account_features):,}")
    print(f"Features: {len(account_features.columns):,}")
    print(f"Saved: {output_path}")

    print("\nSample:")
    print(account_features.head())

    return account_features


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    for split in ["train", "validation", "test"]:
        create_account_features(split)

    print("\n" + "=" * 70)
    print("ACCOUNT FEATURE CREATION COMPLETE")
    print("=" * 70)