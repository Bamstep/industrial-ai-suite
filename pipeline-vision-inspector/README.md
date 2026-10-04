Yes, exactly! That was the **old** single-frame `pipeline-vision-inspector/README.md` before we built:

1. **Continuous Video Crawler Processing** (`video_processor.py`)
2. **Odometer Chainage (KP) Tracking**
3. **Automated ASME B31G Excel Compliance Report Generator** (`report_generator.py`)
4. **Synthetic Video Run Generator** (`generate_video.py`)

Here is the fully updated, complete `pipeline-vision-inspector/README.md` reflecting all the new enterprise features and endpoints:

---

```markdown
# Pipeline Vision Integrity Inspector (Oil & Gas NDT Engine)

An automated Non-Destructive Testing (NDT) computer vision engine, continuous crawler video processor, and compliance triage dashboard engineered for internal pipeline borescope feeds, robotic crawlers, and In-Line Inspection (ILI) optical data.

---

## 1. Industry Background & Problem Statement

Energy infrastructure across upstream production, midstream transmission pipelines, and downstream refining relies on continuous asset integrity management to prevent containment loss, catastrophic pipeline ruptures, and severe environmental spills.

* **The Inspection Bottleneck:** Robotic pipeline crawlers and borescopes produce continuous video feeds covering hundreds of meters. Reviewing continuous footage manually is labor-intensive and prone to engineer visual fatigue, leading to missed pitting or delayed maintenance triage.
* **The Solution:** This engine processes both standalone still frames and continuous `.mp4` crawler video feeds at runtime. It computes linear odometer chainage (Kilometer Post / KP), performs automated defect segmentation, calculates corrosion area coverage, proxies localized cavity depth, and exports formal **ASME B31G** (*Manual for Determining Remaining Strength of Corroded Pipelines*) and **API 570** audit workbooks.

---

## 2. Technical Architecture & Core Pipeline


```

Continuous Crawler Video (.mp4) / Raw Still Frame
│
▼
[ CLAHE Normalization ]          ──> Equalizes radial headlamp illumination
│
▼
[ HSV / LAB Color Isolation ]       ──> Segments iron-oxide oxidation signatures
│
▼
[ Morphological Filtering ]        ──> Eliminates camera sensor & speckle noise
│
▼
[ Contour & Depth Metric ]         ──> Extracts surface area, centroids & luminance drop
│
▼
[ Odometer Chainage (KP) Tracker ]   ──> Correlates timestamps to linear pipe position
│
▼
[ ASME B31G Severity Triage ]       ──> Classifies ACCEPTABLE / MONITOR / REPAIR REQUIRED
│
├──────────────────────────────────┐
▼                                  ▼
[ FastAPI & Web Dashboard ]         [ Automated Excel Audit Sign-off ]
(Real-time visual overlay & HUD)        (.xlsx sheet with embedded keyframes)

```

### Key Engineering Features

1. **Illumination Normalization (CLAHE):** Crawler headlamps generate intense center hotspots and dark peripheral edges. Contrast Limited Adaptive Histogram Equalization is applied to the CIE L\*a\*b\* luminance channel (`clipLimit=2.5`, `tileGridSize=(8, 8)`) to preserve local boundary contrast without amplifying camera noise.
2. **Multi-Space Color Segmentation:** Identifies active oxidation products (rust blooms) by combining calibrated HSV hue-saturation gates with morphological elliptical structuring kernels (`cv2.MORPH_ELLIPSE`) to discard camera sensor artifacts.
3. **Cavity Depth Proxy & Defect Clustering:** Extracts defect cluster contours, centroids, and bounding boxes. Evaluates local luminance drop within defect perimeters to distinguish superficial surface oxidation from deep localized pitting cavities.
4. **Continuous Video & Odometer Chainage Tracking (KP):** Ingests continuous `.mp4` inspection streams, computes linear pipe chainage (KP markers) from crawler travel velocity, logs anomaly intervals, and automatically extracts keyframe evidence snapshots.
5. **ASME B31G Automated Excel Reporting:** Automatically compiles the chainage anomaly register, executive statistics, severity breakdown, and high-resolution keyframe evidence thumbnails into an audit-ready `.xlsx` inspection sign-off sheet.
6. **Standard-Aligned Triage Engine:** Automatically categorizes pipeline segments into three operational tiers:
   * **ACCEPTABLE:** Clean baseline pipe with zero defect clusters and negligible surface discoloration.
   * **MONITOR:** Non-critical surface oxidation requiring scheduled tracking in line with maintenance intervals.
   * **REPAIR REQUIRED:** High defect area coverage (> 15%) or localized deep cavity scores exceeding safety margins.

---

## 3. Project Structure

```text
pipeline-vision-inspector/
├── Dockerfile                         # Container definition for pipeline inspector service
├── pyproject.toml                     # Module dependencies, build setup, and openpyxl
├── README.md                          # Engineering documentation
├── sample_data/
│   ├── crawler_run_sample.mp4         # Synthetic 5-second 25fps continuous crawler inspection run
│   ├── generate_samples.py            # Generates synthetic still images (clean, moderate, severe)
│   ├── generate_video.py              # Generates synthetic continuous crawler inspection video
│   ├── pipe_clean.jpg                 # Baseline clean steel pipe wall
│   ├── pipe_moderate_corrosion.jpg    # Surface oxidation / rust bloom sample
│   └── pipe_severe_pitting.jpg        # Deep localized cavity sample
├── src/
│   └── pipeline_vision/
│       ├── __init__.py
│       ├── detector.py                # OpenCV CLAHE, HSV segmentation & depth proxy logic
│       ├── report_generator.py        # ASME B31G automated Excel (.xlsx) sign-off report generator
│       ├── video_processor.py         # Continuous crawler video stream & odometer chainage tracker
│       └── api/
│           ├── app.py                 # FastAPI application, streaming endpoints & web dashboard
│           └── schemas.py             # Pydantic request & response models
└── tests/
    └── test_pipeline_vision.py        # Pytest suite (image triage, video crawler & Excel report)

```

---

## 4. Quickstart Guide

### Prerequisites

* Python 3.10+
* Virtual environment (`venv`) active

### Installation

From within the `pipeline-vision-inspector` directory (or from workspace root):

```bash
pip install -e pipeline-vision-inspector

```

### Generate Synthetic Test Assets

Generate both still test frames and the synthetic crawler video stream:

```bash
python pipeline-vision-inspector/sample_data/generate_samples.py
python pipeline-vision-inspector/sample_data/generate_video.py

```

### Run Automated Test Suite

Verify detection accuracy, continuous video parsing, and automated Excel report generation:

```bash
pytest pipeline-vision-inspector/tests/ -v

```

### Launch the Inspection Dashboard

Start the FastAPI application:

```bash
uvicorn pipeline_vision.api.app:app --app-dir pipeline-vision-inspector/src --host 127.0.0.1 --port 8001 --reload

```

Open your browser and navigate to: `http://127.0.0.1:8001`

---

## 5. API Reference

### Health Check

* **Endpoint:** `GET /health`
* **Response:**

```json
{
  "status": "healthy",
  "module": "pipeline-vision-inspector",
  "version": "0.2.0"
}

```

### Inspect Single Frame (Telemetry Only)

* **Endpoint:** `POST /api/v1/inspect`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns defect count, surface corrosion percentage, and cluster bounding boxes.

### Inspect & Visualize Single Frame

* **Endpoint:** `POST /api/v1/inspect/visualize`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns JSON metrics accompanied by a base64-encoded JPEG with defect contour overlays.

### Inspect Continuous Crawler Video

* **Endpoint:** `POST /api/v1/inspect/video`
* **Content-Type:** `multipart/form-data`
* **Response:**

```json
{
  "total_distance_m": 1.0,
  "duration_sec": 5.0,
  "total_frames": 125,
  "worst_severity": "REPAIR_REQUIRED",
  "anomalies_logged": 15,
  "keyframes": [
    {
      "event_id": 1,
      "chainage_meters": 0.32,
      "timestamp_sec": 1.6,
      "severity": "REPAIR_REQUIRED",
      "corrosion_percentage": 3.99,
      "image_base64": "data:image/jpeg;base64,..."
    }
  ],
  "anomaly_log": [
    {
      "id": 1,
      "kp_chainage_m": 0.32,
      "time_sec": 1.6,
      "severity": "REPAIR_REQUIRED",
      "coverage_pct": 3.99
    }
  ]
}

```

### Export ASME B31G Excel Audit Sign-off Sheet

* **Endpoint:** `POST /api/v1/inspect/video/report`
* **Content-Type:** `multipart/form-data`
* **Response:** Binary download of `ASME_B31G_Inspection_Audit.xlsx` containing the executive survey summary, full chainage log, and embedded defect keyframe thumbnails.

---

## 6. Verification & Test Metrics

The automated test suite (`tests/test_pipeline_vision.py`) validates:

1. `test_clean_pipe_detection`: Verifies 0% false alarms on clean steel surfaces.
2. `test_corrosion_patch_segmentation`: Validates contour segmentation and triage escalation on active rust patches.
3. `test_api_health_endpoint`: Ensures REST service health availability.
4. `test_api_inspect_endpoint`: Validates request handling and Pydantic serialization.
5. `test_video_inspector_and_report_generation`: Validates end-to-end 125-frame continuous crawler video ingestion, odometer chainage tracking, and binary generation of the ASME B31G `.xlsx` audit sheet.

```

---

### Command to Apply It Directly

You can update the file in one command from your PowerShell terminal:

```powershell
Set-Content -Path "pipeline-vision-inspector/README.md" -Encoding Ascii -Value @'
# Pipeline Vision Integrity Inspector (Oil & Gas NDT Engine)

An automated Non-Destructive Testing (NDT) computer vision engine, continuous crawler video processor, and compliance triage dashboard engineered for internal pipeline borescope feeds, robotic crawlers, and In-Line Inspection (ILI) optical data.

---

## 1. Industry Background & Problem Statement

Energy infrastructure across upstream production, midstream transmission pipelines, and downstream refining relies on continuous asset integrity management to prevent containment loss, catastrophic pipeline ruptures, and severe environmental spills.

* **The Inspection Bottleneck:** Robotic pipeline crawlers and borescopes produce continuous video feeds covering hundreds of meters. Reviewing continuous footage manually is labor-intensive and prone to engineer visual fatigue, leading to missed pitting or delayed maintenance triage.
* **The Solution:** This engine processes both standalone still frames and continuous `.mp4` crawler video feeds at runtime. It computes linear odometer chainage (Kilometer Post / KP), performs automated defect segmentation, calculates corrosion area coverage, proxies localized cavity depth, and exports formal **ASME B31G** (*Manual for Determining Remaining Strength of Corroded Pipelines*) and **API 570** audit workbooks.

---

## 2. Technical Architecture & Core Pipeline


```

Continuous Crawler Video (.mp4) / Raw Still Frame
│
▼
[ CLAHE Normalization ]          ──> Equalizes radial headlamp illumination
│
▼
[ HSV / LAB Color Isolation ]       ──> Segments iron-oxide oxidation signatures
│
▼
[ Morphological Filtering ]        ──> Eliminates camera sensor & speckle noise
│
▼
[ Contour & Depth Metric ]         ──> Extracts surface area, centroids & luminance drop
│
▼
[ Odometer Chainage (KP) Tracker ]   ──> Correlates timestamps to linear pipe position
│
▼
[ ASME B31G Severity Triage ]       ──> Classifies ACCEPTABLE / MONITOR / REPAIR REQUIRED
│
├──────────────────────────────────┐
▼                                  ▼
[ FastAPI & Web Dashboard ]         [ Automated Excel Audit Sign-off ]
(Real-time visual overlay & HUD)        (.xlsx sheet with embedded keyframes)

```

### Key Engineering Features

1. **Illumination Normalization (CLAHE):** Crawler headlamps generate intense center hotspots and dark peripheral edges. Contrast Limited Adaptive Histogram Equalization is applied to the CIE L*a*b* luminance channel (`clipLimit=2.5`, `tileGridSize=(8, 8)`) to preserve local boundary contrast without amplifying camera noise.
2. **Multi-Space Color Segmentation:** Identifies active oxidation products (rust blooms) by combining calibrated HSV hue-saturation gates with morphological elliptical structuring kernels (`cv2.MORPH_ELLIPSE`) to discard camera sensor artifacts.
3. **Cavity Depth Proxy & Defect Clustering:** Extracts defect cluster contours, centroids, and bounding boxes. Evaluates local luminance drop within defect perimeters to distinguish superficial surface oxidation from deep localized pitting cavities.
4. **Continuous Video & Odometer Chainage Tracking (KP):** Ingests continuous `.mp4` inspection streams, computes linear pipe chainage (KP markers) from crawler travel velocity, logs anomaly intervals, and automatically extracts keyframe evidence snapshots.
5. **ASME B31G Automated Excel Reporting:** Automatically compiles the chainage anomaly register, executive statistics, severity breakdown, and high-resolution keyframe evidence thumbnails into an audit-ready `.xlsx` inspection sign-off sheet.
6. **Standard-Aligned Triage Engine:** Automatically categorizes pipeline segments into three operational tiers:
   * **ACCEPTABLE:** Clean baseline pipe with zero defect clusters and negligible surface discoloration.
   * **MONITOR:** Non-critical surface oxidation requiring scheduled tracking in line with maintenance intervals.
   * **REPAIR REQUIRED:** High defect area coverage (> 15%) or localized deep cavity scores exceeding safety margins.

---

## 3. Project Structure

```text
pipeline-vision-inspector/
├── Dockerfile                         # Container definition for pipeline inspector service
├── pyproject.toml                     # Module dependencies, build setup, and openpyxl
├── README.md                          # Engineering documentation
├── sample_data/
│   ├── crawler_run_sample.mp4         # Synthetic 5-second 25fps continuous crawler inspection run
│   ├── generate_samples.py            # Generates synthetic still images (clean, moderate, severe)
│   ├── generate_video.py              # Generates synthetic continuous crawler inspection video
│   ├── pipe_clean.jpg                 # Baseline clean steel pipe wall
│   ├── pipe_moderate_corrosion.jpg    # Surface oxidation / rust bloom sample
│   └── pipe_severe_pitting.jpg        # Deep localized cavity sample
├── src/
│   └── pipeline_vision/
│       ├── __init__.py
│       ├── detector.py                # OpenCV CLAHE, HSV segmentation & depth proxy logic
│       ├── report_generator.py        # ASME B31G automated Excel (.xlsx) sign-off report generator
│       ├── video_processor.py         # Continuous crawler video stream & odometer chainage tracker
│       └── api/
│           ├── app.py                 # FastAPI application, streaming endpoints & web dashboard
│           └── schemas.py             # Pydantic request & response models
└── tests/
    └── test_pipeline_vision.py        # Pytest suite (image triage, video crawler & Excel report)

```

---

## 4. Quickstart Guide

### Prerequisites

* Python 3.10+
* Virtual environment (`venv`) active

### Installation

From within the `pipeline-vision-inspector` directory (or from workspace root):

```bash
pip install -e pipeline-vision-inspector

```

### Generate Synthetic Test Assets

Generate both still test frames and the synthetic crawler video stream:

```bash
python pipeline-vision-inspector/sample_data/generate_samples.py
python pipeline-vision-inspector/sample_data/generate_video.py

```

### Run Automated Test Suite

Verify detection accuracy, continuous video parsing, and automated Excel report generation:

```bash
pytest pipeline-vision-inspector/tests/ -v

```

### Launch the Inspection Dashboard

Start the FastAPI application:

```bash
uvicorn pipeline_vision.api.app:app --app-dir pipeline-vision-inspector/src --host 127.0.0.1 --port 8001 --reload

```

Open your browser and navigate to: `http://127.0.0.1:8001`

---

## 5. API Reference

### Health Check

* **Endpoint:** `GET /health`
* **Response:**

```json
{
  "status": "healthy",
  "module": "pipeline-vision-inspector",
  "version": "0.2.0"
}

```

### Inspect Single Frame (Telemetry Only)

* **Endpoint:** `POST /api/v1/inspect`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns defect count, surface corrosion percentage, and cluster bounding boxes.

### Inspect & Visualize Single Frame

* **Endpoint:** `POST /api/v1/inspect/visualize`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns JSON metrics accompanied by a base64-encoded JPEG with defect contour overlays.

### Inspect Continuous Crawler Video

* **Endpoint:** `POST /api/v1/inspect/video`
* **Content-Type:** `multipart/form-data`
* **Response:**

```json
{
  "total_distance_m": 1.0,
  "duration_sec": 5.0,
  "total_frames": 125,
  "worst_severity": "REPAIR_REQUIRED",
  "anomalies_logged": 15,
  "keyframes": [
    {
      "event_id": 1,
      "chainage_meters": 0.32,
      "timestamp_sec": 1.6,
      "severity": "REPAIR_REQUIRED",
      "corrosion_percentage": 3.99,
      "image_base64": "data:image/jpeg;base64,..."
    }
  ],
  "anomaly_log": [
    {
      "id": 1,
      "kp_chainage_m": 0.32,
      "time_sec": 1.6,
      "severity": "REPAIR_REQUIRED",
      "coverage_pct": 3.99
    }
  ]
}

```

### Export ASME B31G Excel Audit Sign-off Sheet

* **Endpoint:** `POST /api/v1/inspect/video/report`
* **Content-Type:** `multipart/form-data`
* **Response:** Binary download of `ASME_B31G_Inspection_Audit.xlsx` containing the executive survey summary, full chainage log, and embedded defect keyframe thumbnails.

---

## 6. Verification & Test Metrics

The automated test suite (`tests/test_pipeline_vision.py`) validates:

1. `test_clean_pipe_detection`: Verifies 0% false alarms on clean steel surfaces.
2. `test_corrosion_patch_segmentation`: Validates contour segmentation and triage escalation on active rust patches.
3. `test_api_health_endpoint`: Ensures REST service health availability.
4. `test_api_inspect_endpoint`: Validates request handling and Pydantic serialization.
5. `test_video_inspector_and_report_generation`: Validates end-to-end 125-frame continuous crawler video ingestion, odometer chainage tracking, and binary generation of the ASME B31G `.xlsx` audit sheet.
'@

```
