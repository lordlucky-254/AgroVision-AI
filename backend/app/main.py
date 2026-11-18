from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .service import diagnose_crop

app = FastAPI(title="AgroVision AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

history: list[dict] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "agrovision-api"}


@app.post("/api/v1/diagnoses")
async def create_diagnosis(image: UploadFile = File(...), crop: str = Form("unknown")) -> dict:
    payload = await image.read()
    result = diagnose_crop(crop=crop, filename=image.filename or "upload", content=payload)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filename": image.filename,
        "crop": crop,
        **result,
    }
    history.insert(0, record)
    return record


@app.get("/api/v1/diagnoses")
def list_diagnoses() -> list[dict]:
    return history
