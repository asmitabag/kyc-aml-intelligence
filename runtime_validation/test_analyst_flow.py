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
            return payload
    except Exception as exc:
        if hasattr(exc, "code"):
            payload = json.loads(exc.read())
            assert exc.code in expected, (exc.code, payload)
            return payload
        raise


def test_alert_sar_review_feedback_and_persistence():
    suffix = uuid.uuid4().hex[:10].upper()
    customer = call("POST", "/api/v1/customers", {
        "full_name": f"Analyst Runtime {suffix}",
        "email": f"analyst-{suffix.lower()}@example.test",
    }, expected=(200, 201))
    customer_id = customer["customer_id"]
    alert = call("POST", "/api/v1/alerts", {
        "customer_id": customer_id,
        "alert_type": "RUNTIME_VALIDATION",
        "reason_code": "TEST_REVIEW",
        "severity": "HIGH",
        "narrative": "Runtime validation alert",
    }, expected=(200, 201))
    alert_id = alert["alert_id"]

    alerts = call("GET", "/api/v1/alerts")
    assert any(item["alert_id"] == alert_id for item in alerts)

    updated = call("PATCH", f"/api/v1/alerts/{alert_id}/status", {
        "status": "UNDER_REVIEW",
    })
    assert updated["status"] == "UNDER_REVIEW"

    sar = call("POST", "/api/v1/sar-drafts", {
        "alert_id": alert_id,
        "customer_id": customer_id,
        "narrative": "Runtime SAR draft based on the alert record.",
        "validation_status": "NEEDS_REVIEW",
        "review_status": "DRAFT",
    }, expected=(200, 201))
    sar_id = sar["sar_id"]
    assert sar["alert_id"] == alert_id

    reviewed = call("PATCH", f"/api/v1/sar-drafts/{sar_id}/status", {
        "status": "IN_REVIEW",
    })
    assert reviewed["review_status"] == "IN_REVIEW"
    persisted_sar = call("GET", f"/api/v1/sar-drafts/{sar_id}")
    assert persisted_sar["review_status"] == "IN_REVIEW"

    feedback = call("POST", f"/api/v1/alerts/{alert_id}/feedback", {
        "customer_id": customer_id,
        "alert_id": alert_id,
        "decision": "NEEDS_MORE_INVESTIGATION",
        "rationale": "Runtime validation feedback",
    }, expected=(200, 201))
    assert feedback["alert_id"] == alert_id
    dataset = call("GET", "/api/v1/feedback/dataset")
    assert any(item.get("feedback_id") == feedback["feedback_id"] for item in dataset)
