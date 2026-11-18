FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGROVISION_MODEL_PATH=/app/models/agrovision.pth

WORKDIR /app
COPY backend/requirements.txt backend/requirements-ml.txt ./backend/
RUN python -m pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r backend/requirements-ml.txt

COPY backend/app /app/backend/app
COPY frontend /app/frontend
RUN mkdir -p /app/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
