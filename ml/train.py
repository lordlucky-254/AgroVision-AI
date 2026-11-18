from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch import nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, models, transforms
from torchvision.models import MobileNet_V3_Small_Weights

IMAGE_SIZE = 224
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate the AgroVision image classifier.")
    parser.add_argument("--train-dir", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--test-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=Path("models/agrovision.pth"))
    parser.add_argument("--metrics", type=Path, default=Path("models/test-metrics.json"))
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--no-pretrained", action="store_true")
    return parser.parse_args()


def make_model(class_count: int, pretrained: bool) -> nn.Module:
    weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    model = models.mobilenet_v3_small(weights=weights)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, class_count)
    return model


def make_datasets(args: argparse.Namespace) -> tuple[datasets.ImageFolder, ...]:
    train_transform = transforms.Compose(
        [
            transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )
    evaluation_transform = transforms.Compose(
        [
            transforms.Resize(232),
            transforms.CenterCrop(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )
    train = datasets.ImageFolder(args.train_dir, transform=train_transform)
    validation = datasets.ImageFolder(args.validation_dir, transform=evaluation_transform)
    test = datasets.ImageFolder(args.test_dir, transform=evaluation_transform)
    if train.classes != validation.classes or train.classes != test.classes:
        raise ValueError("Train, validation, and test directories must have identical class folders.")
    if not train.samples or not validation.samples or not test.samples:
        raise ValueError("Train, validation, and test directories must all contain images.")
    return train, validation, test


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None = None,
) -> tuple[float, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    labels: list[int] = []
    predictions: list[int] = []

    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, targets)
            if training:
                loss.backward()
                optimizer.step()

        total_loss += loss.item() * targets.size(0)
        labels.extend(targets.cpu().tolist())
        predictions.extend(logits.argmax(dim=1).cpu().tolist())

    return total_loss / len(loader.dataset), accuracy_score(labels, predictions)


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    classes: list[str],
) -> dict:
    model.eval()
    labels: list[int] = []
    predictions: list[int] = []
    with torch.inference_mode():
        for images, targets in loader:
            logits = model(images.to(device))
            labels.extend(targets.tolist())
            predictions.extend(logits.argmax(dim=1).cpu().tolist())

    return {
        "accuracy": accuracy_score(labels, predictions),
        "classification_report": classification_report(
            labels,
            predictions,
            labels=list(range(len(classes))),
            target_names=classes,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            labels, predictions, labels=list(range(len(classes)))
        ).tolist(),
    }


def main() -> None:
    args = parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.workers < 0:
        raise ValueError("Epochs and batch size must be positive; workers cannot be negative.")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    train_data, validation_data, test_data = make_datasets(args)
    loader_options = {"batch_size": args.batch_size, "num_workers": args.workers}
    class_counts = np.bincount(train_data.targets, minlength=len(train_data.classes))
    sample_weights = [1.0 / class_counts[label] for _, label in train_data.samples]
    sampler = WeightedRandomSampler(
        sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )
    train_loader = DataLoader(train_data, sampler=sampler, **loader_options)
    validation_loader = DataLoader(validation_data, shuffle=False, **loader_options)
    test_loader = DataLoader(test_data, shuffle=False, **loader_options)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = make_model(len(train_data.classes), pretrained=not args.no_pretrained).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    best_accuracy = -1.0
    best_state: dict[str, torch.Tensor] | None = None

    for epoch in range(args.epochs):
        train_loss, train_accuracy = run_epoch(model, train_loader, criterion, device, optimizer)
        validation_loss, validation_accuracy = run_epoch(
            model, validation_loader, criterion, device
        )
        print(
            f"epoch={epoch + 1}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_accuracy={train_accuracy:.4f} "
            f"validation_loss={validation_loss:.4f} validation_accuracy={validation_accuracy:.4f}"
        )
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_state = {
                name: tensor.detach().cpu().clone()
                for name, tensor in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError("Training completed without a checkpoint.")
    model.load_state_dict(best_state)
    metrics = evaluate(model, test_loader, device, train_data.classes)
    metrics["test_samples"] = len(test_data)
    metrics["classes"] = train_data.classes
    metrics["warning"] = (
        "Held-out dataset results do not establish field performance. "
        "Use an independently collected field test set before deployment."
    )

    checkpoint = {
        "architecture": "mobilenet_v3_small",
        "model_version": "agrovision-mobilenet-v3-small-v1",
        "classes": train_data.classes,
        "input_size": IMAGE_SIZE,
        "normalization_mean": MEAN,
        "normalization_std": STD,
        "state_dict": best_state,
    }
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    temporary_checkpoint = args.checkpoint.with_suffix(args.checkpoint.suffix + ".tmp")
    torch.save(checkpoint, temporary_checkpoint)
    temporary_checkpoint.replace(args.checkpoint)
    args.metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"test_accuracy={metrics['accuracy']:.4f}")
    print(f"checkpoint={args.checkpoint}")
    print(f"metrics={args.metrics}")


if __name__ == "__main__":
    main()
