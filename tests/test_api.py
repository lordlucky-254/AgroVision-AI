from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.service import diagnose_crop

client = TestClient(app)


def png_image() -> bytes:
    output = BytesIO()
    Image.new("RGB", (16, 16), color="green").save(output, format="PNG")
    return output.getvalue()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_ready"] is False


def test_root_serves_frontend() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AgroVision AI" in response.text


def test_diagnosis_does_not_claim_model_prediction() -> None:
    body = diagnose_crop("tomato", None)
    assert body["diagnosis"] == "Image classifier not configured"
    assert body["needs_expert_confirmation"] is True
    assert body["candidates"] == []


def test_diagnosis_marks_uncalibrated_scores_and_abstains_below_threshold() -> None:
    body = diagnose_crop(
        "tomato",
        [{"label": "Tomato___healthy", "score": 0.5}],
        model_version="test-model",
    )
    assert body["diagnosis"] == "Uncertain result"
    assert body["model_score"] == 0.5
    assert body["score_note"] == "Scores are uncalibrated model outputs, not probabilities."
    assert body["model"] == "test-model"


def test_diagnosis_does_not_show_a_different_crop_as_a_match() -> None:
    body = diagnose_crop(
        "tomato",
        [{"label": "Potato leaf early blight", "score": 0.99}],
        model_version="test-model",
    )
    assert body["diagnosis"] == "Unable to screen this crop"
    assert body["candidates"] == []
    assert body["model_score"] is None


def test_diagnosis_returns_matching_crop_suggestion_above_threshold() -> None:
    body = diagnose_crop(
        "tomato",
        [
            {"label": "Tomato___healthy", "score": 0.8},
            {"label": "Tomato___leaf_spot", "score": 0.2},
        ],
        model_version="test-model",
    )
    assert body["diagnosis"] == "Tomato___healthy"
    assert body["needs_expert_confirmation"] is True
    assert body["model_score"] == 0.8


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


def test_model_status_explains_missing_checkpoint() -> None:
    response = client.get("/api/v1/model")
    assert response.status_code == 200
    assert response.json()["ready"] is False


def test_valid_upload_returns_clear_unavailable_status_without_model() -> None:
    response = client.post(
        "/api/v1/diagnoses",
        data={"crop": "tomato"},
        files={"image": ("leaf.png", png_image(), "image/png")},
    )
    assert response.status_code == 503


def test_oversized_image_is_rejected() -> None:
    response = client.post(
        "/api/v1/diagnoses",
        files={"image": ("leaf.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
    )
    assert response.status_code == 413
