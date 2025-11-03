import uuid
from datetime import datetime, timedelta

def test_create_and_cancel_booking(booking_client):
    cid = datetime.utcnow().date()
    cod = (datetime.utcnow() + timedelta(days=2)).date()

    payload = {
        "uuid": str(uuid.uuid4()),
        "room_uuid": str(uuid.uuid4()),
        "user_uuid": str(uuid.uuid4()),
        "check_in": f"{cid}T00:00:00",
        "check_out": f"{cod}T00:00:00",
        "total_price": 200.00,
        "status": "PENDING",
    }

    create = booking_client.post("/booking", json=payload)
    assert create.status_code == 200
    bid = create.json()

    cancel = booking_client.patch(f"/booking/{bid}/cancel", json={"user_uuid": payload["user_uuid"]})
    assert cancel.status_code == 200
    assert cancel.json() == bid


def test_availability_batch(booking_client):
    body = {
        "room_uuids": [str(uuid.uuid4()), str(uuid.uuid4())],
        "check_in": "2025-10-01T00:00:00",
        "check_out": "2025-10-03T00:00:00",
    }
    r = booking_client.post("/availability/batch", json=body)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == set(body["room_uuids"])
