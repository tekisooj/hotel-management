import uuid


def test_add_and_get_property(property_client):
    payload = {
        "uuid": str(uuid.uuid4()),
        "user_uuid": str(uuid.uuid4()),
        "name": "Seaside House",
        "country": "US",
        "state": "CA",
        "city": "Santa Monica",
        "address": "123 Ocean Ave",
        "latitude": 34.01,
        "longitude": -118.49,
    }

    r = property_client.post("/property", json=payload)
    assert r.status_code == 200
    prop_uuid = r.json()
    assert prop_uuid == payload["uuid"]

    r2 = property_client.get(f"/property/{prop_uuid}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["uuid"] == payload["uuid"]
    assert body["name"] == payload["name"]


def test_properties_by_city(property_client):
    # list endpoint exists in your routes
    r = property_client.get("/properties/city", params={"country": "US", "city": "Santa Monica"})
    assert r.status_code in (200, 404, 200)  # allow empty list
    assert isinstance(r.json(), list)


def test_create_presigned_upload(property_client):
    r = property_client.post("/assets/upload-url", json={"filename": "photo.jpg", "content_type": "image/jpeg"})
    assert r.status_code == 200
    data = r.json()
    assert "url" in data and "fields" in data


def test_rooms_crud(property_client):
    # create property first
    import uuid
    prop_id = str(uuid.uuid4())
    property_client.post("/property", json={"uuid": prop_id, "name": "X", "country": "RS", "city": "Beograd"})

    room = {
        "uuid": str(uuid.uuid4()),
        "property_uuid": prop_id,
        "name": "Room 1",
        "capacity": 2,
        "price_per_night": 100,
        "currency_code": "USD",
    }

    add = property_client.post("/room", json=room)
    assert add.status_code == 200

    get = property_client.get(f"/room/{room['uuid']}")
    assert get.status_code == 200
    assert get.json()["name"] == "Room 1"

    list_rooms = property_client.get(f"/rooms/{prop_id}")
    assert list_rooms.status_code == 200
    assert any(r["uuid"] == room["uuid"] for r in list_rooms.json())

    delete = property_client.delete(f"/room/{room['uuid']}")
    assert delete.status_code == 200
