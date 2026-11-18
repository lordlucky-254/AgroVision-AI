def is_supported_image(content: bytes) -> bool:
    return (
        content.startswith(b"\xff\xd8\xff")
        or content.startswith(b"\x89PNG\r\n\x1a\n")
        or (len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP")
    )


def diagnose_crop(crop: str, content: bytes) -> dict:
    """Return a safe unavailable result until a validated image model is configured."""
    del crop, content
    return {
        "diagnosis": "Image classifier not configured",
        "confidence": None,
        "symptoms": "This prototype has not analyzed the image.",
        "next_steps": "Do not treat crops based on this result. Ask a local agricultural extension officer to inspect the plant.",
        "needs_expert_confirmation": True,
        "model": "unconfigured-v0",
    }
