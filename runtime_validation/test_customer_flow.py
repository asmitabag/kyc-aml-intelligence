import json
import os
import uuid
from urllib.request import Request, urlopen


BASE_URL = os.getenv("AML_BASE_URL", "http://127.0.0.1:8000")


def call(method, path, body=None, expected=(200,)):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
            assert response.status in expected, (response.status, payload)
            return response.status, payload
    except Exception as exc:
        if hasattr(exc, "code"):
            payload = json.loads(exc.read())
            assert exc.code in expected, (exc.code, payload)
            return exc.code, payload
        raise


def test_customer_registration_accounts_transactions_and_aml_unavailable():
    suffix = uuid.uuid4().hex[:10].upper()
    _, customer = call("POST", "/api/v1/customers", {
        "full_name": f"Runtime Customer {suffix}",
        "email": f"runtime-{suffix.lower()}@example.test",
        "data_origin": "CONSENTED_DEMO",
    }, expected=(200, 201))
    customer_id = customer["customer_id"]

    _, profile = call("GET", f"/api/v1/customers/{customer_id}")
    assert profile["customer_id"] == customer_id

    _, account = call("POST", f"/api/v1/customers/{customer_id}/accounts", {
        "customer_id": customer_id,
        "currency": "USD",
    }, expected=(200, 201))
    account_id = account["account_id"]

    _, transaction = call("POST", f"/api/v1/accounts/{account_id}/transactions", {
        "account_id": account_id,
        "direction": "DEBIT",
        "amount": 125.50,
        "currency": "USD",
        "description": "Runtime validation transaction",
    })
    assert transaction["account_id"] == account_id

    _, history = call("GET", f"/api/v1/customers/{customer_id}/transactions")
    assert any(item["transaction_id"] == transaction["transaction_id"] for item in history)

    call("POST", f"/api/v1/customers/{customer_id}/kyc", {
        "document_tamper_probability": 0.01,
        "liveness_probability": 0.01,
        "deepfake_probability": 0.01,
        "kyc_risk": 0.1,
        "document_fingerprint": f"runtime-{suffix}",
    })
    status, analysis = call(
        "POST",
        f"/api/v1/customers/{customer_id}/aml-analysis",
        expected=(503,),
    )
    assert status == 503
    assert analysis["status"] == "unavailable"
    assert analysis["assessment_id"] is None
    assert analysis["fused_risk"] is None
    assert set(analysis["model_statuses"]) >= {"gnn", "xgboost"}
