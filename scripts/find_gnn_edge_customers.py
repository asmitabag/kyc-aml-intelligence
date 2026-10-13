import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from apps.api_gateway.database import SessionLocal
from services.cases import models

db = SessionLocal()

try:
    accounts = db.query(models.Account).all()
    account_lookup = {a.account_id: a for a in accounts}
    customers = db.query(models.Customer).all()

    candidates = []

    for customer in customers:
        owned = {
            a.account_id
            for a in accounts
            if a.customer_id == customer.customer_id
        }

        if not owned:
            continue

        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.account_id.in_(owned))
            .all()
        )

        usable_edges = [
            tx for tx in transactions
            if tx.to_account_id in account_lookup
        ]

        if usable_edges:
            candidates.append(
                (customer.customer_id, len(owned), len(transactions), len(usable_edges))
            )

    candidates.sort(key=lambda x: (x[3], x[2]), reverse=True)

    print("Customers with usable transaction edges:", len(candidates))
    for customer_id, account_count, transaction_count, edge_count in candidates[:10]:
        print({
            "customer_id": customer_id,
            "account_count": account_count,
            "transaction_count": transaction_count,
            "usable_edges": edge_count,
        })

finally:
    db.close()
