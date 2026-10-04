FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY sample_data/ ./sample_data/

RUN pip install --no-cache-dir -e . && \
    python sample_data/generate_telemetry.py

EXPOSE 8002

CMD ["uvicorn", "turbomachinery_pdm.api.app:app", "--host", "0.0.0.0", "--port", "8002"]
