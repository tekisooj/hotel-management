import uuid

def test_add_and_list_reviews(review_client):
    property_uuid = str(uuid.uuid4())
    body = {
        "uuid": str(uuid.uuid4()),
        "property_uuid": property_uuid,
        "user_uuid": str(uuid.uuid4()),
        "rating": 4.5,
        "comment": "Great stay",
    }
    add = review_client.post(f"/review/{property_uuid}", json=body)
    assert add.status_code == 200

    lst = review_client.get(f"/reviews/{property_uuid}")
    assert lst.status_code == 200
    items = lst.json()
    assert items and items[0]["comment"] == "Great stay"
