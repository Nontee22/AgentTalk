def test_health_endpoint_responds(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_has_required_fields(client):
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


def test_health_status_is_valid_value(client):
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
