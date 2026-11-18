from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any


class PlantDiseaseClassifier:
    def __init__(self, checkpoint_path: Path) -> None:
        import torch
        from torch import nn
        from torchvision.models import mobilenet_v3_small
        from torchvision import transforms

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if not isinstance(checkpoint, dict):
            raise ValueError("Model checkpoint must contain a dictionary.")
        if checkpoint.get("architecture") != "mobilenet_v3_small":
            raise ValueError("Unsupported model architecture in checkpoint.")

        classes = checkpoint.get("classes")
        state_dict = checkpoint.get("state_dict")
        if (
            not isinstance(classes, list)
            or not classes
            or not all(isinstance(label, str) and label for label in classes)
            or not isinstance(state_dict, dict)
        ):
            raise ValueError("Model checkpoint is missing valid classes or weights.")

        model = mobilenet_v3_small(weights=None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
        model.load_state_dict(state_dict, strict=True)
        model.eval()

        self._torch = torch
        self._model = model
        self.classes = classes
        self.version = str(checkpoint.get("model_version", "unversioned"))
        self._transform = transforms.Compose(
            [
                transforms.Resize(232),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225),
                ),
            ]
        )

    def predict(self, image_bytes: bytes) -> list[dict[str, Any]]:
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGB")

        inputs = self._transform(image).unsqueeze(0)
        with self._torch.inference_mode():
            scores = self._torch.softmax(self._model(inputs)[0], dim=0)

        count = len(self.classes)
        values, indices = self._torch.topk(scores, count)
        return [
            {"label": self.classes[index.item()], "score": value.item()}
            for value, index in zip(values, indices)
        ]
