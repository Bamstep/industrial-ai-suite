# Industrial AI Suite

[![CI](https://github.com/Bamstep/industrial-ai-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Bamstep/industrial-ai-suite/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Modular industrial intelligence monorepo combining physical domain models, real-time kinematics simulation, non-destructive optical inspection, and condition-based predictive maintenance.

---

## Architecture Overview

Master Gateway (:8080) -> [Robotics Twin :8000 | Pipeline Vision :8001 | Turbomachinery PdM :8002]

---

## Quickstart

### 1. Run Unit Tests (25/25 Passing)
```bash
pytest robotics-digital-twin/tests/ -v
pytest pipeline-vision-inspector/tests/ -v
pytest turbomachinery-pdm/tests/ -v
```

### 2. Run Local Microservices
```bash
uvicorn robotics_twin.api.app:app --port 8000 --reload
uvicorn pipeline_vision.api.app:app --port 8001 --reload
uvicorn turbomachinery_pdm.api.app:app --port 8002 --reload
```

### 3. Run Unified Gateway
```bash
uvicorn src.gateway:app --port 8080 --reload
```

## API Testing
Import `postman_collection.json` into Postman, Bruno, or Insomnia for ready-to-run requests across all endpoints.
