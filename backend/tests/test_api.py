from datetime import date, timedelta
import pytest


def test_health_endpoints(client):
    assert client.get("/health/live").json() == {"status": "alive"}
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_create_and_list_aircraft(client):
    payload = {
        "registration": "D-AIXX",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
        "status": "operational",
    }
    created = client.post("/api/v1/aircraft", json=payload)
    assert created.status_code == 201
    assert created.json()["registration"] == "D-AIXX"
    assert len(client.get("/api/v1/aircraft").json()) == 1


def test_duplicate_aircraft_registration_returns_conflict(client):
    payload = {"registration": "D-AIXX", "aircraft_type": "A320neo", "manufacturer": "Airbus"}
    assert client.post("/api/v1/aircraft", json=payload).status_code == 201
    duplicate = client.post("/api/v1/aircraft", json=payload)
    assert duplicate.status_code == 409


def test_create_work_order_and_filter_overdue(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AIZZ", "aircraft_type": "A350-900", "manufacturer": "Airbus"
    }).json()
    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect landing gear assembly",
        "priority": "high",
        "status": "open",
        "due_date": (date.today() - timedelta(days=1)).isoformat(),
    })
    assert work_order.status_code == 201
    assert work_order.json()["work_order_number"] == f"WO-{date.today().year}-0001"
    overdue = client.get("/api/v1/work-orders", params={"overdue_only": "true"})
    assert len(overdue.json()) == 1


def test_work_order_rejects_unknown_aircraft(client):
    response = client.post("/api/v1/work-orders", json={
        "aircraft_id": 999,
        "title": "Inspect cabin pressure system",
        "due_date": date.today().isoformat(),
    })
    assert response.status_code == 404

def test_update_work_order_status_and_priority(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AIYY",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect engine assembly",
        "priority": "normal",
        "status": "open",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.patch(
        f"/api/v1/work-orders/{work_order['id']}",
        json={"status": "in_progress", "priority": "critical"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["priority"] == "critical"


def test_update_unknown_work_order_returns_404(client):
    response = client.patch(
        "/api/v1/work-orders/999",
        json={"status": "in_progress"},
    )

    assert response.status_code == 404


def test_update_work_order_rejects_invalid_status(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AIZZ",
        "aircraft_type": "A350-900",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect landing gear",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.patch(
        f"/api/v1/work-orders/{work_order['id']}",
        json={"status": "invalid_status"},
    )

    assert response.status_code == 422


def test_update_work_order_rejects_empty_payload(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AIWW",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect cabin systems",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.patch(
        f"/api/v1/work-orders/{work_order['id']}",
        json={},
    )

    assert response.status_code == 422


def test_work_order_rejects_invalid_status_transition(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AI11",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect engine assembly",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.patch(
        f"/api/v1/work-orders/{work_order['id']}",
        json={"status": "completed"},
    )

    assert response.status_code == 409
    assert "Cannot transition" in response.json()["detail"]


def test_work_order_allows_valid_status_transitions(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AI12",
        "aircraft_type": "A350-900",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect landing gear",
        "due_date": date.today().isoformat(),
    }).json()

    assert work_order["work_order_number"] == f"WO-{date.today().year}-0001"

    work_order_id = work_order["id"]
    for next_status in ["in_progress", "blocked", "in_progress", "completed"]:
        response = client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": next_status},
        )
        assert response.status_code == 200
        assert response.json()["status"] == next_status


def test_completed_work_order_cannot_be_reopened(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AI13",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect cabin systems",
        "due_date": date.today().isoformat(),
    }).json()

    work_order_id = work_order["id"]

    client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": "in_progress"},
    )

    client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": "completed"},
    )

    response = client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": "in_progress"},
    )

    assert response.status_code == 409


def test_priority_can_be_updated_without_status_change(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-AI14",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Inspect hydraulic system",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.patch(
        f"/api/v1/work-orders/{work_order['id']}",
        json={"priority": "critical"},
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "critical"
    assert response.json()["status"] == "open"

def test_get_work_order_by_id(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-GET01",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Test individual work order retrieval",
        "due_date": date.today().isoformat(),
    }).json()

    response = client.get(
        f"/api/v1/work-orders/{work_order['id']}"
    )

    assert response.status_code == 200
    assert response.json()["work_order_number"] == f"WO-{date.today().year}-{work_order['id']:04d}"
    assert response.json()["status"] == "open"


def test_get_unknown_work_order_returns_404(client):
    response = client.get("/api/v1/work-orders/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found"

def test_work_order_pagination(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-PAGE01",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    for due_date in ["2027-01-10", "2027-01-20", "2027-01-30"]:
        client.post("/api/v1/work-orders", json={
            "aircraft_id": aircraft["id"],
            "title": "Pagination test",
            "due_date": due_date,
        })

    response = client.get(
        "/api/v1/work-orders",
        params={"limit": 2, "offset": 1},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert [
        item["work_order_number"] for item in response.json()
    ] == [f"WO-{date.today().year}-0002", f"WO-{date.today().year}-0003"]


def test_work_order_sorting_descending(client):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-SORT01",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    for _ in range(3):
        client.post("/api/v1/work-orders", json={
            "aircraft_id": aircraft["id"],
            "title": "Sorting test",
            "due_date": "2027-02-01",
        })

    response = client.get(
        "/api/v1/work-orders",
        params={
            "sort_by": "work_order_number",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200
    assert [
        item["work_order_number"] for item in response.json()
    ] == [f"WO-{date.today().year}-0003", f"WO-{date.today().year}-0002", f"WO-{date.today().year}-0001"]


def test_work_order_pagination_rejects_invalid_limit(client):
    response = client.get(
        "/api/v1/work-orders",
        params={"limit": 101},
    )

    assert response.status_code == 422


def test_work_order_sorting_rejects_invalid_field(client):
    response = client.get(
        "/api/v1/work-orders",
        params={"sort_by": "invalid_field"},
    )

    assert response.status_code == 422



@pytest.mark.parametrize(
    ("initial_status", "next_status"),
    [
        ("open", "cancelled"),
        ("in_progress", "cancelled"),
        ("blocked", "cancelled"),
    ],
)
def test_work_order_allows_cancellation(
    client, initial_status, next_status
):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-CANCEL01",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Test work-order cancellation",
        "due_date": date.today().isoformat(),
    }).json()

    work_order_id = work_order["id"]

    if initial_status != "open":
        response = client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200

    if initial_status == "blocked":
        response = client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": "blocked"},
        )
        assert response.status_code == 200

    response = client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": next_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == next_status


@pytest.mark.parametrize(
    ("initial_status", "next_status"),
    [
        ("cancelled", "in_progress"),
        ("cancelled", "completed"),
        ("completed", "in_progress"),
        ("completed", "cancelled"),
    ],
)
def test_terminal_work_order_status_cannot_be_changed(
    client, initial_status, next_status
):
    aircraft = client.post("/api/v1/aircraft", json={
        "registration": "D-TERMINAL01",
        "aircraft_type": "A320neo",
        "manufacturer": "Airbus",
    }).json()

    work_order = client.post("/api/v1/work-orders", json={
        "aircraft_id": aircraft["id"],
        "title": "Test terminal work-order status",
        "due_date": date.today().isoformat(),
    }).json()

    work_order_id = work_order["id"]

    if initial_status == "completed":
        client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": "in_progress"},
        )
        response = client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": "completed"},
        )
        assert response.status_code == 200
    else:
        response = client.patch(
            f"/api/v1/work-orders/{work_order_id}",
            json={"status": "cancelled"},
        )
        assert response.status_code == 200

    response = client.patch(
        f"/api/v1/work-orders/{work_order_id}",
        json={"status": next_status},
    )

    assert response.status_code == 409