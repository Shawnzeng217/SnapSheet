"""
Tests for OCR API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "healthy"


def test_list_templates():
    resp = client.get("/api/v1/templates/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert isinstance(data["data"], list)


def test_recognize_no_file():
    """Should return 422 when no file provided"""
    resp = client.post("/api/v1/ocr/recognize")
    assert resp.status_code == 422


def test_download_not_found():
    resp = client.get("/api/v1/ocr/download/nonexistent-task-id")
    assert resp.status_code == 404
