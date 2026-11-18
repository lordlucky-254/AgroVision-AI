from pathlib import Path

DISEASES = {
    "tomato": ("Possible early blight", "brown leaf spots with concentric rings", "Remove affected leaves, improve airflow, and seek local extension guidance."),
    "maize": ("Possible maize leaf blight", "elongated brown lesions on leaves", "Remove heavily affected debris and avoid overhead irrigation; confirm with an agronomist."),
    "potato": ("Possible late blight", "dark water-soaked lesions", "Isolate affected plants and request urgent local crop protection advice."),
}


def diagnose_crop(crop: str, filename: str, content: bytes) -> dict:
    """Transparent demo baseline; replace with a trained model behind this interface."""
    normalized = crop.strip().lower()
    disease, symptoms, action = DISEASES.get(
        normalized,
        ("Insufficient evidence", "the crop or image is outside the baseline model", "Retake a clear image in daylight and consult an agricultural officer."),
    )
    confidence = 0.61 if normalized in DISEASES and content else 0.18
    return {
        "diagnosis": disease,
        "confidence": confidence,
        "symptoms": symptoms,
        "next_steps": action,
        "needs_expert_confirmation": confidence < 0.75,
        "model": "transparent-baseline-v0",
    }
