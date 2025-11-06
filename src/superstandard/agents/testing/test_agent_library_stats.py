import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_stats_keys_are_serialized(client):
    resp = client.get("/api/agent-library/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data.get("by_status"), dict)
    assert isinstance(data.get("by_category"), dict)

    for name in ("by_status", "by_category"):
        for k in data[name].keys():
            assert isinstance(k, str)
            assert "." not in k
            assert "Agent" not in k

    # Ensure counters align with serialized keys
    by_status = data["by_status"]
    prod = by_status.get("production", 0)
    dev = by_status.get("development", 0)
    templ = by_status.get("template", 0)

    assert data.get("production_ready") == prod
    assert data.get("in_development") == dev
    assert data.get("templates_available") == templ
