import pandas as pd


INPUT_PATH = "data/synthetic/transactions.csv"
OUTPUT_PATH = "data/synthetic/account_features.csv"


def build_account_features():

    df = pd.read_csv(INPUT_PATH)

    sent = (
        df.groupby("sender_account")
        .agg(
            sent_transaction_count=("transaction_id", "count"),
            total_sent_amount=("amount", "sum"),
            avg_sent_amount=("amount", "mean")
        )
        .reset_index()
        .rename(columns={"sender_account": "account_id"})
    )

    received = (
        df.groupby("receiver_account")
        .agg(
            received_transaction_count=("transaction_id", "count"),
            total_received_amount=("amount", "sum"),
            avg_received_amount=("amount", "mean")
        )
        .reset_index()
        .rename(columns={"receiver_account": "account_id"})
    )

    accounts = pd.DataFrame({
        "account_id": sorted(
            set(df["sender_account"]) |
            set(df["receiver_account"])
        )
    })

    features = (
        accounts
        .merge(sent, on="account_id", how="left")
        .merge(received, on="account_id", how="left")
        .fillna(0)
    )

    features["total_transaction_count"] = (
        features["sent_transaction_count"] +
        features["received_transaction_count"]
    )

    features["total_flow_amount"] = (
        features["total_sent_amount"] +
        features["total_received_amount"]
    )

    features["net_flow"] = (
        features["total_received_amount"] -
        features["total_sent_amount"]
    )

    features.to_csv(OUTPUT_PATH, index=False)

    print(
        f"Generated account features for "
        f"{len(features)} accounts."
    )


if __name__ == "__main__":
    build_account_features()