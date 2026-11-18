from io import BytesIO
import os

from PIL import Image, UnidentifiedImageError


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 20_000_000
MIN_MODEL_SCORE = float(os.getenv("AGROVISION_MIN_MODEL_SCORE", "0.65"))
if not 0.0 <= MIN_MODEL_SCORE <= 1.0:
    raise ValueError("AGROVISION_MIN_MODEL_SCORE must be between 0 and 1.")
GENERIC_NEXT_STEPS = (
    "This is an unverified screening suggestion, not a diagnosis. "
    "Photograph the affected plant in daylight and contact a local agricultural extension officer. "
    "Do not apply a pesticide based only on this result."
)


class InvalidImageError(ValueError):
    pass


class ImageTooLargeError(ValueError):
    pass


def validate_image(content: bytes) -> None:
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in SUPPORTED_FORMATS:
                raise InvalidImageError("Upload a JPEG, PNG, or WebP image.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageTooLargeError("Image dimensions exceed the 20-megapixel limit.")
            image.verify()
    except Image.DecompressionBombError as error:
        raise ImageTooLargeError("Image dimensions exceed the 20-megapixel limit.") from error
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise InvalidImageError("The uploaded file is not a valid image.") from error


def diagnose_crop(
    crop: str,
    predictions: list[dict] | None,
    model_version: str = "unconfigured-v0",
) -> dict:
    """Format model output without presenting uncalibrated scores as probabilities."""
    if not predictions:
        return {
            "diagnosis": "Image classifier not configured",
            "model_score": None,
            "candidates": [],
            "needs_expert_confirmation": True,
            "next_steps": "No image analysis was performed. Configure a trained model before using the scanner.",
            "model": "unconfigured-v0",
        }

    crop_aliases = {
        "tomato": ("tomato",),
        "maize": ("maize", "corn"),
        "potato": ("potato",),
        "pepper": ("pepper", "capsicum", "bell_pepper", "bell pepper"),
    }
    aliases = crop_aliases.get(crop.strip().lower())
    matching = [
        item
        for item in predictions
        if aliases is None or item["label"].strip().lower().startswith(aliases)
    ]
    if not matching:
        return {
            "diagnosis": "Unable to screen this crop",
            "model_score": None,
            "candidates": [],
            "crop_selected": crop,
            "needs_expert_confirmation": True,
            "next_steps": (
                "The model has no matching classes for this crop or the image did not match them. "
                "Ask a local agricultural extension officer to inspect the plant."
            ),
            "model": model_version,
        }

    candidates = matching[:3]
    best = candidates[0]
    score = float(best["score"])
    accepted = score >= MIN_MODEL_SCORE
    return {
        "diagnosis": best["label"] if accepted else "Uncertain result",
        "model_score": score,
        "candidates": candidates,
        "crop_selected": crop,
        "needs_expert_confirmation": True,
        "next_steps": GENERIC_NEXT_STEPS,
        "score_note": "Scores are uncalibrated model outputs, not probabilities.",
        "model": model_version,
    }
