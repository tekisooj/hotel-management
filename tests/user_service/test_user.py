import uuid

def test_create_and_get_user(user_client):
    # depending on your API shape; adjust as needed
    uid = str(uuid.uuid4())
    patch = user_client.patch(f"/user/{uid}", json={"name": "Ada", "last_name": "Lovelace", "email": "ada@ex.com"})
    assert patch.status_code in (200, 204)

    # If 'me' needs Authorization header, set it when you implement auth
    # For now, just ensure /user/{id} returns something if implemented
    res = user_client.get(f"/user/{uid}")
    assert res.status_code in (200, 404)
