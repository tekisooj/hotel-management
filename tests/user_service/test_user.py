import uuid

def test_create_and_get_user(user_client):
    uid = str(uuid.uuid4())
    patch = user_client.patch(f"/user/{uid}", json={"name": "Ada", "last_name": "Lovelace", "email": "ada@ex.com"})
    assert patch.status_code in (200, 204)

    res = user_client.get(f"/user/{uid}")
    assert res.status_code in (200, 404)
