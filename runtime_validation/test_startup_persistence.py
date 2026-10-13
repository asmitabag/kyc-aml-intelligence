import json
import os
from urllib.request import urlopen


BASE_URL = os.getenv("AML_BASE_URL", "http://127.0.0.1:8000")


def test_health_reports_real_model_availability():
    with urlopen(f"{BASE_URL}/api/v1/health", timeout=10) as response:
        health = json.loads(response.read())
    assert response.status == 200
    assert health["status"] == "degraded"
    assert health["models"] == {"gnn": "unavailable", "xgboost": "unavailable"}


def test_unauthenticated_and_missing_resource_paths_are_explicit():
    try:
        urlopen(f"{BASE_URL}/api/v1/customers/does-not-exist", timeout=10)
    except Exception as exc:
        assert exc.code == 404
    else:
        raise AssertionError("missing customer unexpectedly returned success")
