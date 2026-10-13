import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api_gateway.database import SessionLocal
from services.cases import models

db = SessionLocal()

try:
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.customer_id == "CUST-BD57BAC875FD")
        .first()
    )

    if customer is None:
        print("Customer not found.")
    else:
        accounts = (
            db.query(models.Account)
            .filter(models.Account.customer_id == customer.customer_id)
            .all()
        )
        account_ids = {account.account_id for account in accounts}

        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.account_id.in_(account_ids))
            .all()
        )

        print("Customer:", customer.customer_id)
        print("Owned account IDs:", sorted(account_ids))

        for tx in transactions:
            recipient_exists = (
                db.query(models.Account)
                .filter(models.Account.account_id == tx.to_account_id)
                .first()
            ) is not None if tx.to_account_id is not None else False

            print({
                "transaction_id": tx.transaction_id,
                "source_account_id": tx.account_id,
                "target_account_id": tx.to_account_id,
                "target_is_owned": tx.to_account_id in account_ids,
                "target_exists_in_database": recipient_exists,
                "amount": float(tx.amount),
                "currency": tx.currency,
            })
finally:
    db.close()
