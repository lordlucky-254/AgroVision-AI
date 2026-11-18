# Instructions for coding agents

- Treat crop-health output as a screening aid, not a diagnosis. Never recommend pesticide products or dosages from model predictions.
- Explain that training-set performance does not imply field performance; do not make accuracy or safety claims without reproducible independent field evaluation.
- Do not call an uncalibrated softmax score "confidence" or a probability.
- Validate image content and size; never persist uploaded image bytes.
- Run `python -m pytest -q` from the repository root after backend changes.
- Keep datasets and model weights out of Git unless licenses, attribution, and size have been reviewed.
- Preserve the separation between training data, validation data, and an independent field test set.
