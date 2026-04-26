import io
import os
from unittest.mock import patch


def test_html2image_requires_file(client):
    response = client.post("/api/html2image", data={})
    assert response.status_code == 400
    assert response.get_json()["message"] == "请上传 HTML 文件"


def test_html2image_success_download(client, tmp_path):
    output_file = tmp_path / "out.jpg"
    output_file.write_bytes(b"fake-jpg")

    with patch("tools.html2image.check_playwright_chromium") as mocked_check, patch("tools.html2image.convert", return_value=str(output_file)):
        mocked_check.return_value.ok = True
        response = client.post(
            "/api/html2image",
            data={
                "html_file": (io.BytesIO(b"<html></html>"), "index.html"),
                "format": "JPEG",
                "quality": "95",
            },
            content_type="multipart/form-data",
        )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/jpeg")
    assert "attachment" in response.headers["Content-Disposition"]


def test_html2image_invalid_quality_fallback(client, tmp_path):
    output_file = tmp_path / "out.png"
    output_file.write_bytes(b"fake-png")

    with patch("tools.html2image.check_playwright_chromium") as mocked_check, patch("tools.html2image.convert", return_value=str(output_file)) as mocked:
        mocked_check.return_value.ok = True
        response = client.post(
            "/api/html2image",
            data={
                "html_file": (io.BytesIO(b"<html></html>"), "index.html"),
                "format": "PNG",
                "quality": "abc",
            },
            content_type="multipart/form-data",
        )
    assert response.status_code == 200
    _, _, quality = mocked.call_args[0]
    assert quality == 95
