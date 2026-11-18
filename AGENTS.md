# Instructions for coding agents

- Keep the API honest: no disease prediction or confidence score until a validated image model is actually loaded.
- Treat crop-health output as decision support, not a diagnosis. Never recommend pesticide products or dosages without verified local expert guidance.
- Validate uploads and avoid retaining image data or secrets by default.
- Run `python -m pytest -q` from the repository root after backend changes.
- Keep model datasets and weights out of Git unless their licenses and size have been verified.
