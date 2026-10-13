from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import pytest

from apps.api_gateway.database import Base, get_db
from apps.api_gateway.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)


def override_db():
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def test_customer_to_alert_feedback_workflow(client):
    customer = client.post("/api/v1/customers", json={"full_name": "Demo Customer"})
    assert customer.status_code == 200
    customer_id = customer.json()["customer_id"]

    account = client.post(
        "/api/v1/accounts",
        json={"customer_id": customer_id, "currency": "USD"},
    )
    assert account.status_code == 201
    account_id = account.json()["account_id"]

    transaction = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"account_id": account_id, "direction": "DEBIT", "amount": 125.50},
    )
    assert transaction.status_code == 200
    assert transaction.json()["account_id"] == account_id

    kyc = client.post(
        f"/api/v1/customers/{customer_id}/kyc",
        json={
            "document_tamper_probability": 0.01,
            "liveness_probability": 0.02,
            "deepfake_probability": 0.01,
            "kyc_risk": 0.1,
            "document_fingerprint": "demo-fingerprint",
        },
    )
    assert kyc.status_code == 200
    assert client.get(f"/api/v1/customers/{customer_id}/kyc/latest").status_code == 200

    alert = client.post(
        "/api/v1/alerts",
        json={"customer_id": customer_id, "account_id": account_id},
    )
    assert alert.status_code == 201
    alert_id = alert.json()["alert_id"]

    status = client.patch(
        f"/api/v1/alerts/{alert_id}/status",
        json={"status": "UNDER_REVIEW"},
    )
    assert status.status_code == 200
    assert status.json()["status"] == "UNDER_REVIEW"

    feedback = client.post(
        f"/api/v1/alerts/{alert_id}/feedback",
        json={
            "customer_id": customer_id,
            "decision": "NEEDS_MORE_INVESTIGATION",
            "rationale": "Review transaction context",
        },
    )
    assert feedback.status_code == 201, feedback.text
    assert feedback.json()["alert_id"] == alert_id

    sar = client.post(
        "/api/v1/sar-drafts",
        json={
            "customer_id": customer_id,
            "alert_id": alert_id,
            "narrative": "Reviewable draft",
            "validation_status": "VALID",
        },
    )
    assert sar.status_code == 200, sar.text
    sar_id = sar.json()["sar_id"]
    updated_sar = client.patch(
        f"/api/v1/sar-drafts/{sar_id}/status",
        json={"status": "IN_REVIEW"},
    )
    assert updated_sar.status_code == 200
    assert updated_sar.json()["review_status"] == "IN_REVIEW"
    assert updated_sar.json()["validation_status"] == "VALID"
