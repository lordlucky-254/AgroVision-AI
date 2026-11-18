from io import BytesIO

from fastapi.testclient import TestClient
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from PIL import Image
from torch import nn
from torchvision.models import mobilenet_v3_small

from backend.app import main


def test_checkpoint_loads_and_serves_an_image_prediction(tmp_path, monkeypatch) -> None:
    model = mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)
    checkpoint_path = tmp_path / "model.pth"
    torch.save(
        {
            "architecture": "mobilenet_v3_small",
            "model_version": "test-version",
            "classes": ["Tomato___healthy", "Tomato___leaf_spot"],
            "state_dict": model.state_dict(),
        },
        checkpoint_path,
    )
    monkeypatch.setattr(main, "MODEL_PATH", checkpoint_path)

    output = BytesIO()
    Image.new("RGB", (224, 224), color="green").save(output, format="PNG")
    with TestClient(main.app) as client:
        assert client.get("/api/v1/model").json()["ready"] is True
        response = client.post(
            "/api/v1/diagnoses",
            data={"crop": "tomato"},
            files={"image": ("leaf.png", output.getvalue(), "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "test-version"
    assert len(body["candidates"]) == 2
    assert all(0 <= item["score"] <= 1 for item in body["candidates"])
    assert "confidence" not in body
