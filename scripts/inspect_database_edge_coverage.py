import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from apps.api_gateway.database import SessionLocal
from services.cases import models

db = SessionLocal()

try:
    accounts = db.query(models.Account).all()
    transactions = db.query(models.Transaction).all()
    account_ids = {a.account_id for a in accounts}

    missing_targets = sum(t.to_account_id is None for t in transactions)
    existing_targets = sum(
        t.to_account_id is not None and t.to_account_id in account_ids
        for t in transactions
    )
    unknown_targets = sum(
        t.to_account_id is not None and t.to_account_id not in account_ids
        for t in transactions
    )

    print("Customers:", db.query(models.Customer).count())
    print("Accounts:", len(accounts))
    print("Transactions:", len(transactions))
    print("Transactions with no recipient:", missing_targets)
    print("Recipients matching an account:", existing_targets)
    print("Non-null recipients not matching an account:", unknown_targets)

    print("\nSample account IDs:")
    for account in accounts[:5]:
        print(repr(account.account_id))

    print("\nSample transactions:")
    for tx in transactions[:10]:
        print({
            "transaction_id": tx.transaction_id,
            "source": tx.account_id,
            "target": tx.to_account_id,
        })

finally:
    db.close()
