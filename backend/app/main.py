from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .model import PlantDiseaseClassifier
from .service import (
    MIN_MODEL_SCORE,
    ImageTooLargeError,
    InvalidImageError,
    diagnose_crop,
    validate_image,
)


MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MODEL_PATH = Path(os.getenv("AGROVISION_MODEL_PATH", "models/agrovision.pth"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = MODEL_PATH.resolve()
    app.state.classifier = (
        PlantDiseaseClassifier(model_path) if model_path.is_file() else None
    )
    yield


app = FastAPI(title="AgroVision AI", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "service": "agrovision-api",
        "model_ready": getattr(request.app.state, "classifier", None) is not None,
    }


@app.get("/api/v1/model")
def model_status(request: Request) -> dict:
    classifier = getattr(request.app.state, "classifier", None)
    if classifier is None:
        return {
            "ready": False,
            "message": "Train and configure a model checkpoint to enable screening.",
        }
    return {
        "ready": True,
        "model": classifier.version,
        "supported_classes": classifier.classes,
        "score_note": "Scores are uncalibrated and must not be interpreted as probabilities.",
        "prototype_score_threshold": MIN_MODEL_SCORE,
    }


@app.post("/api/v1/diagnoses")
async def create_diagnosis(
    request: Request,
    image: UploadFile = File(...),
    crop: str = Form(default="unknown", max_length=40),
) -> dict:
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")

    payload = await image.read(MAX_IMAGE_BYTES + 1)
    if len(payload) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        validate_image(payload)
    except ImageTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except InvalidImageError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error

    classifier = getattr(request.app.state, "classifier", None)
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="No trained model is configured. Follow the model training steps in README.md.",
        )

    predictions = await run_in_threadpool(classifier.predict, payload)
    result = diagnose_crop(
        crop=crop,
        predictions=predictions,
        model_version=classifier.version,
    )
    return {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "crop": crop.strip(),
        **result,
    }


frontend = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
