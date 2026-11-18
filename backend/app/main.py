from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from .service import diagnose_crop, is_supported_image

app = FastAPI(title="AgroVision AI", version="0.1.0")

history: list[dict] = []
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "agrovision-api"}


@app.post("/api/v1/diagnoses")
async def create_diagnosis(image: UploadFile = File(...), crop: str = Form("unknown")) -> dict:
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")

    payload = await image.read(MAX_IMAGE_BYTES + 1)
    if len(payload) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    if not is_supported_image(payload):
        raise HTTPException(status_code=415, detail="The uploaded file is not a supported image.")

    result = diagnose_crop(crop=crop, content=payload)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "crop": crop,
        **result,
    }
    history.insert(0, record)
    del history[100:]
    return record


@app.get("/api/v1/diagnoses")
def list_diagnoses() -> list[dict]:
    return history


frontend = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
