import io
from unittest.mock import patch


def test_html2pdf_requires_file(client):
    response = client.post("/api/html2pdf", data={})
    assert response.status_code == 400
    assert response.get_json()["message"] == "请上传 HTML 文件"


def test_html2pdf_success_download(client, tmp_path):
    output_file = tmp_path / "resume.pdf"
    output_file.write_bytes(b"%PDF-1.4")

    with patch("tools.html2pdf.check_playwright_chromium") as mocked_check, patch("tools.html2pdf.convert", return_value=str(output_file)):
        mocked_check.return_value.ok = True
        response = client.post(
            "/api/html2pdf",
            data={
                "html_file": (io.BytesIO(b"<html></html>"), "resume.html"),
                "mode": "single_page",
                "media": "screen",
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/pdf")
    assert "attachment" in response.headers["Content-Disposition"]


def test_html2pdf_invalid_mode_fallback(client, tmp_path):
    output_file = tmp_path / "resume.pdf"
    output_file.write_bytes(b"%PDF-1.4")

    with patch("tools.html2pdf.check_playwright_chromium") as mocked_check, patch("tools.html2pdf.convert", return_value=str(output_file)) as mocked_convert:
        mocked_check.return_value.ok = True
        response = client.post(
            "/api/html2pdf",
            data={
                "html_file": (io.BytesIO(b"<html></html>"), "resume.html"),
                "mode": "weird",
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    assert mocked_convert.call_args.kwargs["mode"] == "single_page"
