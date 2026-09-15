import csv
import random
from datetime import datetime, timedelta


random.seed(42)


NUM_ACCOUNTS = 50
NUM_TRANSACTIONS = 300


def generate_accounts():
    return [f"A{i:03d}" for i in range(1, NUM_ACCOUNTS + 1)]


def generate_transactions(accounts):
    transactions = []

    start_time = datetime(2026, 1, 1)

    for i in range(1, NUM_TRANSACTIONS + 1):

        sender = random.choice(accounts)
        receiver = random.choice(accounts)

        while receiver == sender:
            receiver = random.choice(accounts)

        amount = round(random.uniform(100, 10000), 2)

        timestamp = start_time + timedelta(
            minutes=random.randint(0, 60 * 24 * 30)
        )

        transactions.append({
            "transaction_id": f"T{i:04d}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "is_suspicious": 0
        })

    return transactions


def inject_layering_pattern(transactions, accounts):

    suspicious_accounts = random.sample(accounts, 4)

    for i in range(10):
        sender = suspicious_accounts[i % 4]
        receiver = suspicious_accounts[(i + 1) % 4]

        transactions.append({
            "transaction_id": f"S{i + 1:04d}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": round(random.uniform(15000, 30000), 2),
            "timestamp": (
                datetime(2026, 1, 15) +
                timedelta(minutes=i * 10)
            ).isoformat(),
            "is_suspicious": 1
        })

    return transactions


def save_transactions(transactions):

    with open(
        "data/synthetic/transactions.csv",
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "transaction_id",
                "sender_account",
                "receiver_account",
                "amount",
                "timestamp",
                "is_suspicious"
            ]
        )

        writer.writeheader()
        writer.writerows(transactions)


def main():

    accounts = generate_accounts()

    transactions = generate_transactions(accounts)

    transactions = inject_layering_pattern(
        transactions,
        accounts
    )

    save_transactions(transactions)

    print(
        f"Generated {len(accounts)} accounts "
        f"and {len(transactions)} transactions."
    )


if __name__ == "__main__":
    main()