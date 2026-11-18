# AgroVision AI

A crop-photo intake and disease-screening prototype for smallholder farmers. The repository currently validates image uploads and presents a safe, explicit **model not configured** result. It does not infer a disease yet; it must not be used to select a treatment.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The API and browser client are served from the same origin.

## API

- `GET /health` — service health
- `POST /api/v1/diagnoses` — multipart fields `image` (JPEG, PNG, or WebP; maximum 10 MB) and optional `crop`
- `GET /api/v1/diagnoses` — recent in-memory submissions (up to 100; cleared when the process restarts)

The current result intentionally has no confidence score and makes no disease claim. Uploads are not retained, but do not submit sensitive images.

## Development

```bash
python -m pytest -q
```

Before adding an image model, create a field-representative, permissioned dataset, keep an independent field-image test set, report per-class precision/recall and calibration, and include an abstain/unknown outcome. All crop-protection guidance must be reviewed by qualified local agricultural experts; do not generate pesticide products or dosages from model predictions.

## License

MIT. Dataset and pretrained-model licenses remain the responsibility of their users.
