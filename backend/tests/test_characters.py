import uuid


def test_create_character(client):
    world_resp = client.post("/api/worlds", json={"name": "Char Test World"})
    world_id = world_resp.json()["id"]
    resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Hero", "identity": "Warrior", "personality": "Brave"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Hero"
    assert data["world_id"] == world_id
    assert data["identity"] == "Warrior"


def test_create_character_world_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.post(
        f"/api/worlds/{fake_id}/characters",
        json={"name": "Nobody"},
    )
    assert resp.status_code == 404


def test_create_character_missing_name(client):
    world_resp = client.post("/api/worlds", json={"name": "No Name World"})
    world_id = world_resp.json()["id"]
    resp = client.post(f"/api/worlds/{world_id}/characters", json={})
    assert resp.status_code == 422


def test_list_characters(client):
    world_resp = client.post("/api/worlds", json={"name": "List Char World"})
    world_id = world_resp.json()["id"]
    client.post(f"/api/worlds/{world_id}/characters", json={"name": "A"})
    client.post(f"/api/worlds/{world_id}/characters", json={"name": "B"})
    resp = client.get(f"/api/worlds/{world_id}/characters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all("personality" not in c for c in data)


def test_get_character(client):
    world_resp = client.post("/api/worlds", json={"name": "Get Char World"})
    world_id = world_resp.json()["id"]
    create_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={
            "name": "Detailed Char",
            "personality": "Smart",
            "greeting": "Hello!",
        },
    )
    char_id = create_resp.json()["id"]
    resp = client.get(f"/api/characters/{char_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Detailed Char"
    assert data["personality"] == "Smart"
    assert data["greeting"] == "Hello!"


def test_get_character_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.get(f"/api/characters/{fake_id}")
    assert resp.status_code == 404


def test_update_character(client):
    world_resp = client.post("/api/worlds", json={"name": "Update Char World"})
    world_id = world_resp.json()["id"]
    create_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Old Char"},
    )
    char_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/characters/{char_id}",
        json={"name": "New Char", "personality": "Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Char"
    assert resp.json()["personality"] == "Updated"


def test_update_character_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.put(f"/api/characters/{fake_id}", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_character(client):
    world_resp = client.post("/api/worlds", json={"name": "Delete Char World"})
    world_id = world_resp.json()["id"]
    create_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "To Delete"},
    )
    char_id = create_resp.json()["id"]
    resp = client.delete(f"/api/characters/{char_id}")
    assert resp.status_code == 204
    get_resp = client.get(f"/api/characters/{char_id}")
    assert get_resp.status_code == 404


def test_delete_character_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.delete(f"/api/characters/{fake_id}")
    assert resp.status_code == 404


def test_cascade_delete_world_deletes_characters(client):
    world_resp = client.post("/api/worlds", json={"name": "Cascade World"})
    world_id = world_resp.json()["id"]
    create_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Will be deleted"},
    )
    char_id = create_resp.json()["id"]
    client.delete(f"/api/worlds/{world_id}")
    get_resp = client.get(f"/api/characters/{char_id}")
    assert get_resp.status_code == 404
