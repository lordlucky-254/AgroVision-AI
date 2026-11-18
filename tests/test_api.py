from fastapi.testclient import TestClient

from backend.app.main import app, health
from backend.app.service import diagnose_crop

client = TestClient(app)
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def test_health() -> None:
    assert health()["status"] == "ok"


def test_root_serves_frontend() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AgroVision AI" in response.text


def test_diagnosis_does_not_claim_model_prediction() -> None:
    body = diagnose_crop("tomato", PNG_HEADER)
    assert body["diagnosis"] == "Image classifier not configured"
    assert body["confidence"] is None
    assert body["needs_expert_confirmation"] is True


def test_upload_requires_supported_image_type() -> None:
    response = client.post(
        "/api/v1/diagnoses",
        files={"image": ("leaf.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_upload_rejects_non_image_content() -> None:
    response = client.post(
        "/api/v1/diagnoses",
        files={"image": ("leaf.png", b"not an image", "image/png")},
    )
    assert response.status_code == 415


def test_upload_accepts_png_and_records_cautious_result() -> None:
    response = client.post(
        "/api/v1/diagnoses",
        data={"crop": "tomato"},
        files={"image": ("leaf.png", PNG_HEADER, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["confidence"] is None
    assert response.json()["needs_expert_confirmation"] is True
