from fastapi.testclient import TestClient
from pathlib import Path
import os
import sys
import io
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app, STORAGE_DIR

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_storage():
    for f in STORAGE_DIR.iterdir():
        if f.is_file():
            f.unlink()
    yield
    for f in STORAGE_DIR.iterdir():
        if f.is_file():
            f.unlink()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    assert any("/files" in e for e in data["endpoints"])


def test_upload_file():
    file_content = b"Hello FastAPI!"
    response = client.post(
        "/files",
        files={"file": ("test.txt", file_content, "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "File stored successfully"
    assert (STORAGE_DIR / "test.txt").exists()


def test_get_uploaded_file():
    client.post(
        "/files",
        files={"file": ("data.txt", b"content", "text/plain")},
    )

    response = client.get("/files/data.txt")
    assert response.status_code == 200
    assert response.content == b"content"
    assert response.headers["content-type"] == "application/octet-stream"


def test_list_files():
    client.post("/files", files={"file": ("a.txt", b"a", "text/plain")})
    client.post("/files", files={"file": ("b.txt", b"b", "text/plain")})

    response = client.get("/files")
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert set(data["files"]) == {"a.txt", "b.txt"}
    assert data["count"] == 2


def test_health_and_metrics():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    client.post("/files", files={"file": ("x.txt", b"1234", "text/plain")})

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    data = metrics.json()
    assert "files_stored_total" in data
    assert "total_storage_bytes" in data
    assert data["files_current"] >= 1