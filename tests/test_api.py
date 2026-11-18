from backend.app.main import health
from backend.app.service import diagnose_crop


def test_health() -> None:
    assert health()["status"] == "ok"


def test_diagnosis_is_cautious() -> None:
    body = diagnose_crop("tomato", "leaf.jpg", b"image")
    assert body["needs_expert_confirmation"] is True
