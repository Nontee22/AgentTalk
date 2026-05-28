import uuid


def test_create_world(client):
    resp = client.post("/api/worlds", json={"name": "Test World", "tags": ["fantasy"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test World"
    assert data["tags"] == ["fantasy"]
    assert "id" in data


def test_create_world_missing_name(client):
    resp = client.post("/api/worlds", json={})
    assert resp.status_code == 422


def test_list_worlds(client):
    client.post("/api/worlds", json={"name": "World A", "tags": ["sci-fi"]})
    client.post("/api/worlds", json={"name": "World B", "tags": ["fantasy"]})
    resp = client.get("/api/worlds")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert "page" in data
    assert "page_size" in data


def test_list_worlds_with_tag_filter(client):
    client.post("/api/worlds", json={"name": "Fantasy World", "tags": ["fantasy"]})
    client.post("/api/worlds", json={"name": "Sci-fi World", "tags": ["sci-fi"]})
    resp = client.get("/api/worlds", params={"tag": "fantasy"})
    data = resp.json()
    for item in data["items"]:
        assert "fantasy" in item["tags"]


def test_list_worlds_with_search(client):
    client.post("/api/worlds", json={"name": "Hogwarts", "description": "Magic school"})
    resp = client.get("/api/worlds", params={"search": "Hogwarts"})
    data = resp.json()
    assert any(item["name"] == "Hogwarts" for item in data["items"])


def test_list_worlds_pagination(client):
    for i in range(5):
        client.post("/api/worlds", json={"name": f"Page World {i}"})
    resp = client.get("/api/worlds", params={"page": 1, "page_size": 2})
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_world(client):
    create_resp = client.post(
        "/api/worlds",
        json={"name": "Detail World", "setting": "A test setting"},
    )
    world_id = create_resp.json()["id"]
    resp = client.get(f"/api/worlds/{world_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Detail World"
    assert data["setting"] == "A test setting"
    assert data["character_count"] == 0


def test_get_world_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.get(f"/api/worlds/{fake_id}")
    assert resp.status_code == 404


def test_update_world(client):
    create_resp = client.post("/api/worlds", json={"name": "Old Name"})
    world_id = create_resp.json()["id"]
    resp = client.put(f"/api/worlds/{world_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_update_world_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.put(f"/api/worlds/{fake_id}", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_world(client):
    create_resp = client.post("/api/worlds", json={"name": "To Delete"})
    world_id = create_resp.json()["id"]
    resp = client.delete(f"/api/worlds/{world_id}")
    assert resp.status_code == 204
    get_resp = client.get(f"/api/worlds/{world_id}")
    assert get_resp.status_code == 404


def test_delete_world_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.delete(f"/api/worlds/{fake_id}")
    assert resp.status_code == 404


def test_world_character_count(client):
    create_resp = client.post("/api/worlds", json={"name": "Counted World"})
    world_id = create_resp.json()["id"]
    client.post(f"/api/worlds/{world_id}/characters", json={"name": "Char 1"})
    client.post(f"/api/worlds/{world_id}/characters", json={"name": "Char 2"})
    resp = client.get(f"/api/worlds/{world_id}")
    assert resp.json()["character_count"] == 2
