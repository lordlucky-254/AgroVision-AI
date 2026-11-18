# Training and evaluation

The training pipeline uses a MobileNetV3-Small image classifier and `ImageFolder` datasets. It does not download or bundle crop images. You supply data only after reviewing its license and attribution requirements.

## Dataset layout

Use the same class directory names in all three partitions:

```text
data/
  train/
    Tomato___healthy/
    Tomato___Early_blight/
  validation/
    Tomato___healthy/
    Tomato___Early_blight/
  test/
    Tomato___healthy/
    Tomato___Early_blight/
```

Keep related images from the same plant, farm, or capture session in one partition to limit leakage. A random image-level split can substantially overstate performance. The test set must remain untouched until the final evaluation.

The [PlantDoc dataset](https://github.com/pratikkayal/PlantDoc-Dataset) declares CC BY 4.0; retain the required attribution and inspect its contents and source-image rights before use. Its paper is Singh et al., *PlantDoc: A Dataset for Visual Plant Disease Detection* (CoDS-COMAD 2020, [DOI 10.1145/3371158.3371196](https://doi.org/10.1145/3371158.3371196)). PlantVillage has separate attribution/share-alike terms; review the dataset's current terms before training or sharing derived artifacts. Neither dataset substitutes for local field validation.

## Train

Use Python 3.12. The following command installs CPU-only PyTorch wheels. For GPU training, use the matching Torch and Torchvision wheels from the official [PyTorch installation selector](https://pytorch.org/get-started/locally/).

```bash
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
python ml/train.py \
  --train-dir data/train \
  --validation-dir data/validation \
  --test-dir data/test \
  --checkpoint models/agrovision.pth \
  --metrics models/test-metrics.json
```

The default run starts from torchvision's ImageNet MobileNetV3-Small weights. To train without downloading those weights, pass `--no-pretrained`. The script saves the checkpoint selected by validation accuracy and evaluates it once against the held-out test directory. The report includes overall accuracy, per-class precision/recall/F1, and a confusion matrix.

## Enable local inference

After training, install the model-serving dependencies and start the API:

```bash
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r backend/requirements-ml.txt
AGROVISION_MODEL_PATH=models/agrovision.pth \
  uvicorn app.main:app --app-dir backend --reload
```

`GET /api/v1/model` reports whether a checkpoint loaded. Uploads are processed in memory and are not saved. If the checkpoint is missing, malformed, or incompatible, the app does not return a disease prediction.

## Release gate

The supplied validation score is not a deployment claim. Before using this with farmers, evaluate on independently collected and expert-labelled field images from each intended crop/region, report class-level false positives and negatives, calibrate the abstention threshold, obtain agronomist review, and test under varying light, backgrounds, growth stages, and camera quality. The default score threshold (`AGROVISION_MIN_MODEL_SCORE=0.65`) is a prototype heuristic, not a validated clinical/agronomic boundary.
