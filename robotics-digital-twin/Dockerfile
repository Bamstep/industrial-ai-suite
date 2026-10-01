FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MUJOCO_GL=osmesa

# Install system dependencies for headless MuJoCo and OpenCV rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libosmesa6-dev \
    libglib2.0-0 \
    libglfw3 \
    libglew-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python package and dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source and tests
COPY src/ ./src/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["uvicorn", "robotics_twin.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
