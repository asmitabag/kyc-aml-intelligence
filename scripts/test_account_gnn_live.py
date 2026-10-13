import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from apps.api_gateway.database import SessionLocal
from services.cases import models
from services.aml_runtime import AMLRuntimeOrchestrator
from services.model_adapters.account_gnn_adapter import AccountGNNAdapter

db = SessionLocal()
adapter = AccountGNNAdapter()
orchestrator = AMLRuntimeOrchestrator()

try:
    customers = db.query(models.Customer).all()
    selected = None

    for customer in customers:
        accounts = (
            db.query(models.Account)
            .filter(models.Account.customer_id == customer.customer_id)
            .all()
        )
        account_ids = {account.account_id for account in accounts}

        if not account_ids:
            continue

        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.account_id.in_(account_ids))
            .order_by(models.Transaction.occurred_at.asc())
            .all()
        )

        if transactions:
            selected = (customer, accounts, account_ids, transactions)
            break

    if selected is None:
        print("NO_TEST_DATA: No customer with accounts and transactions was found.")
    else:
        customer, accounts, account_ids, transactions = selected

        graph = orchestrator._build_graph(
            customer.customer_id,
            account_ids,
            transactions,
            accounts=accounts,
        )

        print("Customer ID:", customer.customer_id)
        print("Account count:", len(accounts))
        print("Transaction count:", len(transactions))
        print("Graph contract:", graph.contract_version)

        result = adapter.analyze(graph)

        print("Model status:", result.status.value)
        print("Model version:", result.model_version)
        print("Score:", result.score)
        print("Error:", result.error)
        print("Explanation:", result.explanation)

        if result.output is not None:
            print("Output model:", result.output.explanation_subgraph.get("model"))
            print("Experimental:", result.output.explanation_subgraph.get("experimental"))

finally:
    db.close()
