import io
from unittest.mock import patch

from PIL import Image


def _create_image_bytes():
    image = Image.new("RGB", (32, 32), color="white")
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    stream.seek(0)
    return stream


def test_photo_timestamp_requires_files(client):
    response = client.post("/api/photo_timestamp", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json()["message"] == "请至少上传一个图片文件"


def test_photo_timestamp_single_file_download(client):
    response = client.post(
        "/api/photo_timestamp",
        data={"photos": (_create_image_bytes(), "one.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.headers["Content-Type"].startswith("image/jpeg")


def test_photo_timestamp_multi_file_zip_download(client):
    response = client.post(
        "/api/photo_timestamp",
        data={"photos": [(_create_image_bytes(), "one.jpg"), (_create_image_bytes(), "two.jpg")]},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/zip")


def test_photo_timestamp_all_unsupported_returns_400(client):
    response = client.post(
        "/api/photo_timestamp",
        data={"photos": (io.BytesIO(b"hello"), "note.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "没有成功处理的图片"
