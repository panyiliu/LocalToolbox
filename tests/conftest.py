import io

import pytest

from app import app as flask_app


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_html_file():
    return (io.BytesIO(b"<html><body><h1>demo</h1></body></html>"), "demo.html")
