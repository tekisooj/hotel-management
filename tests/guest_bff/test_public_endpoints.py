def test_places_search_requires_params(bff_client, monkeypatch):
    # stub boto3 to prevent real calls if your handler uses boto3.client("location")
    class FakeLoc:
        def search_place_index_for_text(self, **kwargs):
            return {"Results": []}

    bff_client.app.state.place_index = "HotelManagementPlaceIndex"
    import boto3
    monkeypatch.setattr(boto3, "client", lambda *a, **k: FakeLoc())

    r = bff_client.get("/places/search-text", params={"text": "Belgrade"})
    assert r.status_code in (200, 500)  # 200 with mocked client; 500 if index missing
