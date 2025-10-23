FROM python:3.10-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY app/ /app/app/
COPY model/ /app/model/

RUN mkdir -p /app/models

ENV MODEL_PATH=/app/models/model.pkl
ENV DRIFT_DETECTOR_PATH=/app/models/drift_detector.pkl
ENV REFERENCE_DATA_PATH=/app/models/reference_data.npy
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
