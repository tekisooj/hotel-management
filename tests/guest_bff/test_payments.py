import json
from uuid import uuid4
from httpx import Response, Request
import pytest

def _fake_async_client(monkeypatch, responses: list[Response]):

    class FakeRespCtx:
        def __init__(self):
            self._idx = 0
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, **kwargs):
            # oauth or capture/order requests
            resp = responses[self._idx]
            self._idx += 1
            return resp
        async def get(self, url, **kwargs):
            resp = responses[self._idx]
            self._idx += 1
            return resp

    import bffs.guest_bff.app.handlers as handlers

    class FakeAsyncClient:
        def __init__(self, *a, **kw): ...
        async def __aenter__(self): return FakeRespCtx()
        async def __aexit__(self, exc_type, exc, tb): return False

    monkeypatch.setattr(handlers, "AsyncClient", FakeAsyncClient)


def test_create_payment_order_success(bff_client, monkeypatch):

    room_uuid = str(uuid4())
    room_payload = {"uuid": room_uuid, "name": "Nice Room", "price_per_night": 120, "currency_code": "USD"}

    def fake_get(url, *a, **kw):
        class R:
            status_code = 200
            def json(self):
                return room_payload
            text = "OK"
        return R()

    app_state = bff_client.app.state
    app_state.property_service_client = type("C", (), {"get": fake_get})

    oauth_json = {"access_token": "TOKEN"}
    order_json = {"id": "ORDER123", "status": "CREATED"}

    from httpx import Response, Request
    responses = [
        Response(200, request=Request("POST", "https://api-m.sandbox.paypal.com/v1/oauth2/token"),
                 json=oauth_json),
        Response(201, request=Request("POST", "https://api-m.sandbox.paypal.com/v2/checkout/orders"),
                 json=order_json),
    ]
    _fake_async_client(monkeypatch, responses)

    body = {
        "room_uuid": room_uuid,
        "check_in": "2025-10-12",
        "check_out": "2025-10-14",
        "guests": 2
    }
    r = bff_client.post("/booking/payment/order", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["order_id"] == "ORDER123"
    assert data["amount"]["currency_code"] == "USD"
    assert data["nightly_rate"] == "120.00"
    assert data["nights"] == 2


def test_capture_payment_success(bff_client, monkeypatch):
    room_uuid = str(uuid4())
    room_payload = {"uuid": room_uuid, "name": "Room", "price_per_night": 100, "currency_code": "USD"}

    def fake_get_room(url, *a, **kw):
        class R:
            status_code = 200
            def json(self): return room_payload
            text = "OK"
        return R()

    def fake_post_booking(path, json=None, *a, **kw):
        class R:
            status_code = 200
            def json(self): return json["uuid"]
            text = "OK"
        return R()

    app_state = bff_client.app.state
    app_state.property_service_client = type("P", (), {"get": fake_get_room})
    app_state.booking_service_client = type("B", (), {"post": fake_post_booking})

    oauth_json = {"access_token": "TOKEN"}
    capture_json = {
        "status": "COMPLETED",
        "purchase_units": [
            {"payments": {"captures": [{"status": "COMPLETED", "amount": {"currency_code": "USD", "value": "200.00"}}]}}
        ],
    }
    responses = [
        Response(200, request=Request("POST", "https://api-m.sandbox.paypal.com/v1/oauth2/token"),
                 json=oauth_json),
        Response(201, request=Request("POST", "https://api-m.sandbox.paypal.com/v2/checkout/orders/ORDER123/capture"),
                 json=capture_json),
    ]
    _fake_async_client(monkeypatch, responses)

    body = {
        "order_id": "ORDER123",
        "room_uuid": room_uuid,
        "check_in": "2025-10-12",
        "check_out": "2025-10-14",
        "guests": 2
    }
    r = bff_client.post("/booking/payment/capture", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["payment_status"] == "COMPLETED"
    assert data["amount"]["value"] == "200.00"
