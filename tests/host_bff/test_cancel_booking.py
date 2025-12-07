import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from bffs.host_bff.app.main import create_app


class FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class DummyEventBus:
    def __init__(self):
        self.events: list[dict] = []

    def put_event(self, detail_type: str, source: str, detail: dict):
        self.events.append({"detail_type": detail_type, "source": source, "detail": detail})


@pytest.fixture
def host_app(monkeypatch):
    booking_uuid = str(uuid4())
    room_uuid = str(uuid4())
    property_uuid = str(uuid4())
    guest_uuid = str(uuid4())
    host_uuid = str(uuid4())

    booking_payload = {
        "uuid": booking_uuid,
        "user_uuid": guest_uuid,
        "room_uuid": room_uuid,
        "check_in": "2024-01-10T00:00:00Z",
        "check_out": "2024-01-12T00:00:00Z",
        "total_price": 123.0,
        "status": "confirmed",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    class FakeBookingClient:
        def __init__(self):
            self.cancel_payload = None

        async def get(self, path: str, headers=None):
            if path.startswith("booking/"):
                return FakeResponse(200, booking_payload)
            return FakeResponse(404, {})

        async def patch(self, path: str, json=None, headers=None):
            self.cancel_payload = json
            return FakeResponse(200, {**booking_payload, "status": "cancelled"})

    class FakePropertyClient:
        async def get(self, path: str, headers=None):
            if path.startswith("room/"):
                return FakeResponse(200, {"uuid": room_uuid, "property_uuid": property_uuid, "name": "Room"})
            if path.startswith("property/"):
                return FakeResponse(
                    200,
                    {"uuid": property_uuid, "user_uuid": host_uuid, "name": "Test Property", "address": "123 St"},
                )
            return FakeResponse(404, {})

    class FakeUserClient:
        async def get(self, path: str, headers=None):
            if path.startswith("user/"):
                return FakeResponse(
                    200,
                    {"uuid": guest_uuid, "email": "guest@example.com", "name": "Guest", "last_name": "User"},
                )
            return FakeResponse(404, {})

    os.environ.pop("EVENT_BUS_NAME", None)
    app = create_app()
    app.state.booking_service_client = FakeBookingClient()
    app.state.property_service_client = FakePropertyClient()
    app.state.user_service_client = FakeUserClient()
    dummy_bus = DummyEventBus()
    app.state.event_bus = dummy_bus
    app.dependency_overrides = {}
    return app, dummy_bus, booking_uuid, host_uuid


def test_host_can_cancel_booking_and_emits_event(host_app):
    app, event_bus, booking_uuid, host_uuid = host_app
    client = TestClient(app)

    resp = client.delete(f"/booking/{booking_uuid}", headers={"X-User-Id": host_uuid})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cancelled"

    assert event_bus.events, "Expected cancellation event to be published"
    event = event_bus.events[0]
    assert event["detail_type"] == "BookingCancelled"
    assert event["detail"]["guest_email"] == "guest@example.com"
    assert event["detail"]["booking_uuid"] == booking_uuid
