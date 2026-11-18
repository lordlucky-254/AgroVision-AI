# AgroVision AI

An image-based crop disease **screening prototype** with a trainable MobileNetV3-Small pipeline, FastAPI inference service, and responsive browser client. It is not a validated diagnostic product: there is no model checkpoint or locally validated crop-treatment knowledge bundled in this repository.

## Run the application

Python 3.12 is recommended. Install the API dependencies and start the app:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp .env.example .env
uvicorn app.main:app --app-dir backend --env-file .env --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The API and frontend are served from the same origin. Without a trained checkpoint, the scanner reports that inference is unavailable rather than fabricating a disease result.

## Train a model

Prepare licensed, labelled images in `data/train`, `data/validation`, and `data/test`; each split must use identical class-named subdirectories. See [`ml/README.md`](ml/README.md) for dataset provenance, training, and evaluation instructions.

```bash
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
python ml/train.py \
  --train-dir data/train \
  --validation-dir data/validation \
  --test-dir data/test \
  --checkpoint models/agrovision.pth \
  --metrics models/test-metrics.json
```

Train and test data must be separated by plant/farm/session where possible. Training-set metrics are not evidence of field performance. The app expects the checkpoint at `models/agrovision.pth`, or at the path set with `AGROVISION_MODEL_PATH`. The abstention threshold can be set with `AGROVISION_MIN_MODEL_SCORE`; its default is a prototype heuristic and must be calibrated on local field data.

Use [`.env.example`](.env.example) as a local configuration template. The training dataset manifest and model card templates are in `ml/`.

## API

- `GET /health` — liveness and model readiness
- `GET /api/v1/model` — loaded model version and supported labels
- `POST /api/v1/diagnoses` — multipart fields `image` (JPEG/PNG/WebP, at most 10 MB) and optional `crop`

The application does not persist images, filenames, or diagnosis history on the server. Multipart uploads may be temporarily spooled by the web framework to the host's temporary directory and are removed after request handling. Recent scan summaries are stored only in the current browser's local storage and can be cleared there. The API does not provide pesticide products or dosages. Model scores are uncalibrated and are not probabilities; every result asks the user to confirm with local agricultural expertise.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Container

Train a model first, then run `docker compose up --build`. The container exposes port 8000 and mounts `models/` read-only. This starter is intended for local/private evaluation; public deployment needs authentication, rate limiting, monitored resource limits, and a reviewed privacy policy.

## Data, safety, and limitations

The PlantDoc dataset declares CC BY 4.0; PlantVillage has separate share-alike terms. Neither dataset is included here. Review current licenses, attribution, and source-image rights before using or redistributing data or model artifacts. A model trained on public datasets is not automatically suitable for Kenya or any other local context. Local agronomist review and independent field evaluation are release requirements.

This project gives screening suggestions only. It must not be used to select crop-protection chemicals or replace an agricultural extension officer.

Weather-risk alerts, authenticated multi-farm accounts, offline mobile inference, and treatment recommendations are not implemented. They require separate data-provider integrations, privacy controls, and local expert review.

## License

Application code: MIT. Dataset and pretrained-weight licenses remain separate and must be reviewed by the user.
