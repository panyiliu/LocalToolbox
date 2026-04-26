from unittest.mock import patch


def test_index_page_ok(client):
    response = client.get("/")
    assert response.status_code == 200


def test_tool_page_not_found(client):
    response = client.get("/tool/not-exists")
    assert response.status_code == 404
    body = response.get_json()
    assert body["success"] is False
    assert body["message"] == "工具不存在"


def test_api_tool_not_found(client):
    response = client.post("/api/not-exists")
    assert response.status_code == 404
    body = response.get_json()
    assert body["success"] is False
    assert "工具不存在" in body["message"]


def test_api_registry_failure_returns_not_found(client):
    with patch("core.tool_registry.import_module", side_effect=Exception("boom")):
        response = client.post("/api/html2image")
    assert response.status_code == 404
    body = response.get_json()
    assert body["success"] is False
    assert body["message"] == "工具不存在或加载失败"
