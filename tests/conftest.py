import io

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
