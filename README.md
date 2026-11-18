# AgroVision AI

Crop disease detection and treatment guidance for smallholder farmers.

## What is included

- FastAPI endpoint for crop image scans and diagnosis history
- Safe, explainable baseline classifier (file-name and symptom hints)
- Responsive browser client that works without a database
- Evaluation/training notes for replacing the baseline with EfficientNet or MobileNet
- Safety boundary: the app provides likely causes and next steps, not a definitive diagnosis or chemical prescription

## Run locally

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `frontend/index.html` in a browser. The API is available at `http://127.0.0.1:8000`.

## API

- `GET /health`
- `POST /api/v1/diagnoses` with multipart field `image` and optional `crop`
- `GET /api/v1/diagnoses`

The current model is intentionally a transparent baseline. Add field photographs, a held-out test set, calibration, and agronomist-reviewed guidance before production use.

## Roadmap

1. Add PlantVillage for initial transfer learning and PlantDoc/locally collected field images for validation.
2. Train a crop-specific MobileNet/EfficientNet model with confidence calibration and an `unknown` class.
3. Store scans in PostgreSQL and add user/farm history.
4. Localize explanations into Kiswahili and add an offline mobile model.

## License

MIT. Dataset licenses remain the responsibility of the dataset user.
