import pandas as pd


TRANSACTIONS_PATH = "data/synthetic/transactions.csv"
FEATURES_PATH = "data/synthetic/account_features.csv"
OUTPUT_PATH = "data/synthetic/account_features.csv"


def label_accounts():

    transactions = pd.read_csv(TRANSACTIONS_PATH)
    features = pd.read_csv(FEATURES_PATH)

    suspicious = transactions[
        transactions["is_suspicious"] == 1
    ]

    suspicious_accounts = set(
        suspicious["sender_account"]
    ) | set(
        suspicious["receiver_account"]
    )

    features["is_suspicious"] = (
        features["account_id"]
        .isin(suspicious_accounts)
        .astype(int)
    )

    features.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"Suspicious accounts: "
        f"{features['is_suspicious'].sum()}"
    )

    print(
        f"Normal accounts: "
        f"{(features['is_suspicious'] == 0).sum()}"
    )


if __name__ == "__main__":
    label_accounts()