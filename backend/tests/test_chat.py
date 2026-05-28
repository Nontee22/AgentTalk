import uuid


def test_start_chat(client):
    world_resp = client.post("/api/worlds", json={"name": "Chat World"})
    world_id = world_resp.json()["id"]
    char_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Chat Char", "greeting": "Hello there!"},
    )
    char_id = char_resp.json()["id"]

    resp = client.post(
        "/api/chat/start",
        json={"character_id": char_id, "world_id": world_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "conversation_id" in data
    assert data["greeting_message"]["content"] == "Hello there!"
    assert data["greeting_message"]["role"] == "assistant"


def test_start_chat_no_greeting(client):
    world_resp = client.post("/api/worlds", json={"name": "No Greet World"})
    world_id = world_resp.json()["id"]
    char_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Silent Char"},
    )
    char_id = char_resp.json()["id"]

    resp = client.post(
        "/api/chat/start",
        json={"character_id": char_id, "world_id": world_id},
    )
    assert resp.status_code == 201
    assert resp.json()["greeting_message"] is None


def test_start_chat_invalid_character(client):
    world_resp = client.post("/api/worlds", json={"name": "Invalid Char World"})
    world_id = world_resp.json()["id"]
    fake_id = str(uuid.uuid4())

    resp = client.post(
        "/api/chat/start",
        json={"character_id": fake_id, "world_id": world_id},
    )
    assert resp.status_code == 404


def test_list_conversations(client):
    world_resp = client.post("/api/worlds", json={"name": "Conv List World"})
    world_id = world_resp.json()["id"]
    char_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "List Char", "greeting": "Hi"},
    )
    char_id = char_resp.json()["id"]

    client.post(
        "/api/chat/start",
        json={"character_id": char_id, "world_id": world_id},
    )

    resp = client.get("/api/chat/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["character_name"] == "List Char"


def test_get_conversation_messages(client):
    world_resp = client.post("/api/worlds", json={"name": "Msg World"})
    world_id = world_resp.json()["id"]
    char_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Msg Char", "greeting": "Welcome!"},
    )
    char_id = char_resp.json()["id"]

    start_resp = client.post(
        "/api/chat/start",
        json={"character_id": char_id, "world_id": world_id},
    )
    conv_id = start_resp.json()["conversation_id"]

    resp = client.get(f"/api/chat/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["content"] == "Welcome!"


def test_delete_conversation(client):
    world_resp = client.post("/api/worlds", json={"name": "Del Conv World"})
    world_id = world_resp.json()["id"]
    char_resp = client.post(
        f"/api/worlds/{world_id}/characters",
        json={"name": "Del Char"},
    )
    char_id = char_resp.json()["id"]

    start_resp = client.post(
        "/api/chat/start",
        json={"character_id": char_id, "world_id": world_id},
    )
    conv_id = start_resp.json()["conversation_id"]

    resp = client.delete(f"/api/chat/{conv_id}")
    assert resp.status_code == 204


def test_delete_conversation_not_found(client):
    fake_id = uuid.uuid4()
    resp = client.delete(f"/api/chat/{fake_id}")
    assert resp.status_code == 404
