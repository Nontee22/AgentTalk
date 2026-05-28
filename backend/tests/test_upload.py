import io


def test_upload_image(client):
    file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = client.post(
        "/api/upload",
        params={"category": "covers"},
        files={"file": ("test.png", file, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"].startswith("covers/")
    assert data["path"].endswith(".png")


def test_upload_avatar(client):
    file = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    resp = client.post(
        "/api/upload",
        params={"category": "avatars"},
        files={"file": ("avatar.jpg", file, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["path"].startswith("avatars/")


def test_upload_invalid_type(client):
    file = io.BytesIO(b"not an image")
    resp = client.post(
        "/api/upload",
        params={"category": "covers"},
        files={"file": ("test.txt", file, "text/plain")},
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]


def test_upload_invalid_category(client):
    file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = client.post(
        "/api/upload",
        params={"category": "invalid"},
        files={"file": ("test.png", file, "image/png")},
    )
    assert resp.status_code == 422


def test_upload_too_large(client):
    file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * (6 * 1024 * 1024))
    resp = client.post(
        "/api/upload",
        params={"category": "covers"},
        files={"file": ("big.png", file, "image/png")},
    )
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()
