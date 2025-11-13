import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import main


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    monkeypatch.setattr(main, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(main, "files_stored_counter", 0)
    return storage_dir


@pytest.fixture
def client(temp_storage):
    return TestClient(main.app)


def test_root_endpoint_lists_available_routes(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "File Storage API"
    assert "GET /files" in body["endpoints"]


def test_store_file_persists_content(client, temp_storage):
    payload = {"file": ("hello.txt", b"hello world", "text/plain")}
    response = client.post("/files", files=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "hello.txt"
    assert data["size"] == len(b"hello world")
    assert (temp_storage / "hello.txt").read_bytes() == b"hello world"
    assert main.files_stored_counter == 1


def test_get_file_returns_404_for_missing_file(client):
    response = client.get("/files/missing.txt")
    assert response.status_code == 404
    assert response.json()["detail"] == "File 'missing.txt' not found"


def test_get_file_returns_stored_binary(client, temp_storage):
    file_path = temp_storage / "stored.bin"
    payload = b"\x00\x01\x02"
    file_path.write_bytes(payload)

    response = client.get("/files/stored.bin")
    assert response.status_code == 200
    assert response.content == payload
    assert 'filename="stored.bin"' in response.headers.get("content-disposition", "")


def test_list_files_reports_current_files(client, temp_storage):
    (temp_storage / "a.txt").write_text("a")
    (temp_storage / "b.txt").write_text("bb")

    response = client.get("/files")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert set(data["files"]) == {"a.txt", "b.txt"}


def test_metrics_reflect_storage_usage(client):
    payload = {"file": ("metrics.txt", b"abcd", "text/plain")}
    store_response = client.post("/files", files=payload)
    assert store_response.status_code == 200

    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["files_stored_total"] == 1
    assert metrics["files_current"] == 1
    assert metrics["total_storage_bytes"] == 4
    assert metrics["total_storage_mb"] == 0.0