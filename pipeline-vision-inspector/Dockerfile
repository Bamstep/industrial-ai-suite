FROM python:3.11-slim

# Install system-level OpenCV dependencies (GL/graphics libraries for headless processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package setup files first for efficient Docker layer caching
COPY pyproject.toml ./
COPY src/ ./src/
COPY sample_data/ ./sample_data/

# Install the application and generate baseline sample images inside container
RUN pip install --no-cache-dir -e . && \
    python sample_data/generate_samples.py

EXPOSE 8001

CMD ["uvicorn", "pipeline_vision.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
