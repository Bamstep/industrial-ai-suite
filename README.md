```markdown
# Industrial AI Suite — ASME Y14.5 CAD & GD&T Inspection Platform

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Testing](https://img.shields.io/badge/pytest-15%20passed%20(100%25)-brightgreen.svg)](https://docs.pytest.org/)
[![Compliance](https://img.shields.io/badge/standards-ASME%20Y14.5%20%7C%20AS9102%20Rev%20C-orange.svg)](#standards-compliance)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An enterprise-grade, end-to-end industrial computer vision and metrology microservice designed for aerospace and precision manufacturing quality assurance. 

The suite automates the traditional quality engineering workflow: ingesting engineering blueprints (multi-page PDF, multi-frame TIFF, raster images, and native DXF vector CAD), extracting Feature Control Frames (FCFs) and dimensions, applying ASME Y14.5 bonus tolerancing logic, computing real-time Statistical Process Control (SPC), generating AS9102 Rev C First Article Inspection (FAI) workbooks, exporting executable DMIS 5.2 CMM probe routines, and securely dispatching inspection telemetry to upstream MES/QMS systems via authenticated webhooks.

---

## Architecture Overview


```

```
                      Engineering Drawing Ingestion
           [Multi-Page PDF / TIFF / PNG / DXF Vector CAD]
                                 │
                                 ▼
            ┌─────────────────────────────────────────┐
            │        Vision & OCR Parsing Engine      │
            │  - Otsu Adaptive Image Binarization     │
            │  - Contour Feature Control Frame (FCF)  │
            │  - Nearest-Neighbor Balloon Linker      │
            │  - Bilateral & Limit Dimension Parser   │
            └────────────────────┬────────────────────┘
                                 │
                                 ▼
            ┌─────────────────────────────────────────┐
            │       ASME Y14.5 DRF & SPC Engine       │
            │  - Datum Reference Frame (DRF) Solver   │
            │  - Dynamic Bonus Tolerancing (MMC/LMC)  │
            │  - Cp, Cpk & Nelson Rules (1-3) Anomaly │
            └────────────────────┬────────────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼

```

┌──────────────────┐       ┌──────────────────┐        ┌──────────────────┐
│  AS9102 Rev C    │       │     CMM / DMIS   │        │  Enterprise MES  │
│  Aerospace FAI   │       │  Routine Code    │        │  & QMS Webhooks  │
│  (Forms 1, 2, 3) │       │  (DMIS 5.2 .dmi) │        │  (OAuth2 / JWT)  │
└──────────────────┘       └──────────────────┘        └──────────────────┘

```

---

## Key Capabilities

### 1. Computer Vision & Automated Ballooning
* **Intelligent Characteristic Detection**: Identifies circular inspection balloons and associates them with nearby dimensions and Feature Control Frames using Euclidean nearest-neighbor indexing.
* **Geometric FCF Localization**: Evaluates rectangular aspect ratios and semantic symbol structures to isolate GD&T callouts directly from 2D drawings.
* **Multi-Format Ingestion**: Supports raster blueprints (`.png`, `.jpg`), vector/raster multi-page technical drawings (`.pdf`), multi-frame scans (`.tiff`), and vector CAD (`.dxf`).

### 2. ASME Y14.5 GD&T Resolver & Dynamic Bonus Tolerancing
* Resolves Datum Reference Frames (Primary, Secondary, Tertiary) with material condition modifiers ($MMC / \text{Ⓜ}$, $LMC / \text{Ⓛ}$, $RFS$).
* Automatically calculates bonus tolerances based on actual feature-of-size measurements:
  $$\text{Bonus Tolerance} = \vert{}\text{Actual Size} - \text{MMC Boundary}\vert{}$$
  $$\text{Total Allowable Tolerance} = \text{Specified Tolerance} + \text{Bonus Tolerance}$$

### 3. AS9102 Rev C First Article Inspection Packaging
* Generates standard multi-tier OpenXML workbooks (`.xlsx`):
  * **Form 1: Part Number Accountability**: Serial tracking, drawing revisions, organization metadata, and baseline FAI status.
  * **Form 2: Product Process Accountability**: Material specifications, special surface treatments, and functional testing records.
  * **Form 3: Characteristic Accountability & Verification**: Bill of Characteristics linking balloon numbers, design requirements, nominals, tolerance bands, measured results, pass/fail status, and automated metrology tool assignments (e.g., Bore Gauge, Vernier Caliper, CMM).

### 4. Statistical Process Control (SPC) Metrology Health
* Real-time calculation of lot capability:
  $$C_p = \frac{\text{USL} - \text{LSL}}{6\sigma}, \quad C_{pk} = \min\left(\frac{\text{USL} - \mu}{3\sigma}, \frac{\mu - \text{LSL}}{3\sigma}\right)$$
* Statistical process anomaly detection matching Nelson Control Rules 1, 2, and 3.

### 5. Automated Coordinate Measuring Machine (CMM) Routine Export
* Direct export of standardized **DMIS 5.2** routine scripts (`.dmi`) parameterized with part nominals, vector approach coordinates, feature types (planes, cylinders, circles), and alignment datums.

### 6. Security, RBAC & Enterprise Persistence
* **OAuth2 / JWT Authentication**: Scoped role-based access control protecting quality sign-offs and production routes.
  * `inspector`: Ingestion, dimension verification, webhook dispatch.
  * `quality_engineer`: Tolerance modification, multi-page batch analysis, SPC monitoring.
  * `lead_auditor`: Complete AS9102 package verification and compliance approvals.
* **Persistence Layer**: Native SQLAlchemy engine storing inspection runs, serial logs, and audit trails in SQLite or PostgreSQL.

---

## Directory Structure


```

industrial-ai-suite/
├── data/
│   ├── drawings/              # Engineering blueprints & synthetic reference drawings
│   └── output/                # Segmented FCFs, exported workbooks, and CMM routines
├── src/
│   ├── analytics/
│   │   └── spc_engine.py      # Statistical Process Control (Cp/Cpk, Nelson rules)
│   ├── api/
│   │   └── app.py             # FastAPI service, reactive dashboard UI, endpoints
│   ├── core/
│   │   ├── as9102_exporter.py # Form 3 characteristic spreadsheet generator
│   │   ├── as9102_package_exporter.py # Forms 1-3 AS9102 Rev C complete workbook generator
│   │   ├── balloon_extractor.py       # Circle detection & feature association
│   │   ├── cmm_exporter.py    # DMIS 5.2 automated CMM routine generator
│   │   ├── database.py        # SQLAlchemy persistence layer
│   │   ├── dimension_parser.py# Bilateral and limit dimension parser
│   │   ├── drawing_ocr.py     # OCR engine with adaptive thresholding
│   │   ├── fcf_detector.py    # Geometric Feature Control Frame detector
│   │   ├── qms_dispatcher.py  # Enterprise MES/QMS webhook dispatcher
│   │   └── security.py        # PBKDF2-HMAC-SHA256 hashing, JWT & RBAC
│   ├── parsers/
│   │   ├── document_ingestor.py # Multi-page PDF (PyMuPDF) & TIFF frame extractor
│   │   ├── drf_resolver.py    # Datum Reference Frame & MMC bonus solver
│   │   ├── dxf_parser.py      # Native DXF vector CAD extractor (ezdxf)
│   │   └── gdt_parser.py      # ASME Y14.5 symbol catalog & callout parser
│   └── synthetic/
│       └── drawing_generator.py # Procedural mechanical blueprint generator
├── tests/
│   ├── test_database.py       # Persistence & transaction tests
│   ├── test_full_suite.py     # End-to-end integration tests
│   ├── test_inspection_suite.py # Computer vision & parsing unit tests
│   ├── test_pdm.py            # Predictive maintenance & DSP feature tests
│   └── test_security_and_batch.py # JWT, RBAC & multi-page ingestion tests
├── docker-compose.yml         # Containerized production stack (FastAPI + PostgreSQL)
├── Dockerfile                 # Multi-stage production container build
└── requirements.txt           # Pinned environment dependencies

```

---

## Quickstart

### Prerequisites
* Python 3.10+ (Tested up to Python 3.13)
* Git

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/Bamstep/industrial-ai-suite.git](https://github.com/Bamstep/industrial-ai-suite.git)
   cd industrial-ai-suite

```

2. **Create and activate a virtual environment**:
```bash
# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

```


3. **Install dependencies**:
```bash
pip install -r requirements.txt

```


4. **Run the test suite**:
```bash
pytest tests/ -v

```


*All 15 regression and integration tests should pass.*
5. **Start the application server**:
```bash
uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000

```



---

## Usage & Access Points

* **Interactive Metrology Dashboard**: Navigate to `http://127.0.0.1:8000` to inspect blueprints, view real-time capability statistics, upload drawings, export AS9102 packages, and trigger QMS dispatching.
* **Interactive API Documentation (Swagger)**: Navigate to `http://127.0.0.1:8000/docs` to test endpoints and manage authentication.

### Default Authentication Credentials

| Username | Password | Role(s) | Scope |
| --- | --- | --- | --- |
| `inspector01` | `inspect123` | `inspector` | Document upload, telemetry dispatch |
| `engineer01` | `eng123` | `inspector`, `quality_engineer` | SPC calculation, drawing analysis |
| `auditor01` | `audit123` | `inspector`, `quality_engineer`, `lead_auditor` | Full system administration, AS9102 sign-off |

---

## Core API Endpoints

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token` | OAuth2 password token route; returns scoped JWT | No |
| `POST` | `/api/analyze` | Ingests PDF, TIFF, or PNG drawing and executes CV extraction | No |
| `POST` | `/api/v1/dispatch-qms` | Dispatches telemetry event to upstream MES/QMS webhook | **Yes** (`Bearer JWT`) |
| `GET` | `/api/v1/export/as9102-package` | Generates complete 3-sheet AS9102 Rev C Excel workbook | **Yes** (`Bearer JWT`) |
| `GET` | `/api/v1/export/cmm-dmis` | Generates executable DMIS 5.2 Coordinate Measuring routine | No |
| `GET` | `/api/v1/export/as9102` | Generates Form 3 Characteristic report (`.xlsx` or `.csv`) | No |

---

## Production Deployment (Docker Compose)

To spin up the service in a containerized environment backed by PostgreSQL:

```bash
docker compose up -d --build

```

The database container includes integrated health checks and automatically provisions persistent storage volumes for inspection records.

---

## Standards Compliance

* **ASME Y14.5-2018 / ASME Y14.5M-1994**: Dimensioning and Tolerancing (GD&T symbol definitions, Feature Control Frames, Datum Reference Frames, Material Condition Modifiers).
* **SAE AS9102 Rev C**: Aerospace First Article Inspection Requirement (Forms 1, 2, and 3 tabular standards).
* **ISO 1101 / ISO 286**: Geometrical Product Specifications (GPS).
* **ANSI/CAM-I 101-1990**: Dimensional Measuring Interface Standard (DMIS 5.2 CMM routines).

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

```

```
