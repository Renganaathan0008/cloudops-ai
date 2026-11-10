"""API tests for the target service; simulations use bounded workloads."""

import time

import pytest
from app.main import app
from app.routes.items import item_store
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Provide a clean in-memory store and close app lifespan
    after each test.
    """

    item_store.clear()
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "CloudOps AI Target Service"
    assert "reset when the app restarts" in response.json()["data_storage"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "target-service"}


def test_create_item(client: TestClient) -> None:
    response = client.post(
        "/items",
        json={"name": "Monitor", "description": "Demo item", "price": 12.5},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Monitor",
        "description": "Demo item",
        "price": 12.5,
    }


def test_retrieve_all_items(client: TestClient) -> None:
    client.post("/items", json={"name": "One", "price": 1})
    client.post("/items", json={"name": "Two", "price": 2})

    response = client.get("/items")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["One", "Two"]


def test_retrieve_one_item(client: TestClient) -> None:
    created = client.post("/items", json={"name": "One", "price": 1}).json()

    response = client.get(f"/items/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "One"


def test_update_item(client: TestClient) -> None:
    created = client.post("/items", json={"name": "Old", "price": 1}).json()

    response = client.put(
        f"/items/{created['id']}",
        json={"name": "New", "description": "Updated", "price": 2.5},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["price"] == 2.5


def test_delete_item(client: TestClient) -> None:
    created = client.post("/items", json={"name": "Remove", "price": 1}).json()

    response = client.delete(f"/items/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/items/{created['id']}").status_code == 404


def test_missing_and_invalid_item_ids(client: TestClient) -> None:
    assert client.get("/items/999").status_code == 404
    assert client.get("/items/not-an-integer").status_code == 422


def test_variable_latency_endpoint(client: TestClient) -> None:
    response = client.get("/simulate/latency", params={"delay_seconds": 0.01})

    assert response.status_code == 200
    assert response.json()["configured_delay_seconds"] == 0.01
    assert response.json()["actual_elapsed_seconds"] >= 0.01


def test_cpu_simulation_validates_duration(client: TestClient) -> None:
    assert (
        client.get(
            "/simulate/cpu-load",
            params={"duration_seconds": 3},
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/simulate/cpu-load",
            params={"duration_seconds": 0},
        ).status_code
        == 422
    )


def test_cpu_simulation_runs_bounded_workload(client: TestClient) -> None:
    response = client.get(
        "/simulate/cpu-load",
        params={"duration_seconds": 0.02},
    )

    assert response.status_code == 200
    assert response.json()["requested_duration_seconds"] == 0.02
    assert response.json()["actual_execution_seconds"] >= 0.02
    assert response.json()["iterations"] > 0


def test_memory_simulation_can_be_enabled_and_disabled(
    client: TestClient,
) -> None:
    enabled = client.post(
        "/simulate/memory-leak",
        json={
            "enabled": True,
            "allocation_interval_seconds": 0.05,
            "allocation_bytes_per_interval": 1_024,
        },
    )
    time.sleep(0.12)
    status_response = client.get("/simulate/memory-leak/status")

    assert enabled.status_code == 200
    assert status_response.json()["enabled"] is True
    assert 0 < status_response.json()["allocated_bytes"] <= 8 * 1024 * 1024

    disabled = client.post("/simulate/memory-leak", json={"enabled": False})
    time.sleep(0.12)
    stopped_status = client.get("/simulate/memory-leak/status").json()

    assert disabled.status_code == 200
    assert stopped_status["enabled"] is False
    assert stopped_status["allocated_bytes"] == 0


def test_memory_simulation_rejects_unsafe_allocation(
    client: TestClient,
) -> None:
    response = client.post(
        "/simulate/memory-leak",
        json={"enabled": True, "allocation_bytes_per_interval": 2_000_000},
    )

    assert response.status_code == 422


def test_error_rate_validates_probability_and_controls_outcome(
    client: TestClient,
) -> None:
    invalid = client.get(
        "/simulate/error-rate",
        params={"probability": 1.1},
    )
    assert invalid.status_code == 422

    success = client.get("/simulate/error-rate", params={"probability": 0})
    failure = client.get("/simulate/error-rate", params={"probability": 1})

    assert success.status_code == 200
    assert success.json() == {"probability": 0.0, "outcome": "success"}
    assert failure.status_code == 503
    assert failure.json()["detail"] == {
        "probability": 1.0,
        "outcome": "failure",
    }


def test_prometheus_metrics_include_requests_and_real_system_gauges(
    client: TestClient,
) -> None:
    client.get("/health")
    response = client.get("/metrics")
    body = response.text

    assert response.status_code == 200
    assert "cloudops_target_http_requests_total" in body
    assert "cloudops_target_http_request_duration_seconds" in body
    assert "cloudops_target_system_cpu_percent" in body
    assert "cloudops_target_process_memory_rss_bytes" in body
    assert "cloudops_target_system_memory_available_bytes" in body
    assert "cloudops_target_active_items" in body
