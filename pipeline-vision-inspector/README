# Pipeline Vision Integrity Inspector (Oil & Gas NDT Engine)

An automated Non-Destructive Testing (NDT) computer vision engine and triage dashboard engineered for internal pipeline borescope inspection feeds, robotic crawlers, and In-Line Inspection (ILI) optical data.

---

## 1. Industry Background & Problem Statement

Energy infrastructure across upstream production, midstream pipelines, and downstream refining relies on continuous asset integrity management to prevent containment loss, catastrophic blowouts, and severe environmental spills.

* **The Inspection Bottleneck:** Robotic pipeline crawlers and borescopes generate hundreds of gigabytes of raw optical inspection footage. Human integrity engineers face severe visual fatigue when reviewing continuous video logs to detect localized pitting, rust blooms, and surface wall loss.
* **The Solution:** This engine processes internal pipeline imagery at runtime to automate defect segmentation, surface area calculation, and defect cavity depth proxy scoring. Triage states are evaluated against principles derived from **ASME B31G** (*Manual for Determining the Remaining Strength of Corroded Pipelines*) and **API 570** (*Piping Inspection Code*).

---

## 2. Technical Architecture & Core Algorithms

```
Raw Crawler / Borescope Frame
             │
             ▼
   [ CLAHE Normalization ]  ──> Equalizes radial headlamp illumination
             │
             ▼
[ HSV / LAB Color Isolation ] ──> Segments iron-oxide oxidation signatures
             │
             ▼
 [ Morphological Filtering ]  ──> Eliminates camera sensor & speckle noise
             │
             ▼
  [ Contour & Depth Metric ]  ──> Extracts surface area, centroids & luminance drop
             │
             ▼
[ ASME B31G Severity Triage ] ──> Classifies ACCEPTABLE / MONITOR / REPAIR REQUIRED
             │
             ▼
 [ FastAPI & Web Dashboard ]  ──> Visual overlay rendering & REST telemetry

```

### Key Engineering Features

1. **Luminance Normalization (CLAHE):** Crawler lighting systems introduce strong center hotspots and dark peripheral edges. Contrast Limited Adaptive Histogram Equalization is applied to the LAB color space L-channel (`clipLimit=2.5`, `tileGridSize=(8, 8)`) to maintain feature contrast without over-amplifying noise.
2. **Multi-Space Color Segmentation:** Isolates active oxidation zones by combining HSV hue gating (`[5, 28]`) with morphological open/close operations (`cv2.MORPH_ELLIPSE`) to separate bare steel backgrounds from corroded surfaces.
3. **Cavity Depth Proxy & Defect Clustering:** Computes geometric contours, defect cluster centroids, and bounding boxes. Evaluates local luminance attenuation within defect boundaries to differentiate shallow surface oxidation from deep localized pitting.
4. **Standard-Aligned Triage Engine:** Automatically categorizes pipeline segments into three operational tiers:
* **ACCEPTABLE:** Clean baseline pipe with zero defect clusters and negligible surface discoloration.
* **MONITOR:** Non-critical surface oxidation requiring scheduled tracking in line with maintenance intervals.
* **REPAIR REQUIRED:** High defect area coverage (> 15%) or localized deep cavity scores exceeding safety margins.



---

## 3. Project Structure

```text
pipeline-vision-inspector/
├── pyproject.toml                     # Module dependencies and metadata
├── README.md                          # Engineering documentation
├── sample_data/
│   ├── generate_samples.py            # Synthetic pipeline condition generator
│   ├── pipe_clean.jpg                 # Baseline clean steel pipe wall
│   ├── pipe_moderate_corrosion.jpg    # Surface oxidation / rust bloom sample
│   └── pipe_severe_pitting.jpg        # Deep localized cavity sample
├── src/
│   └── pipeline_vision/
│       ├── __init__.py
│       ├── detector.py                # Core CV engine & severity scoring logic
│       └── api/
│           ├── app.py                 # FastAPI application & web dashboard
│           └── schemas.py             # Pydantic response/request models
└── tests/
    └── test_pipeline_vision.py        # Automated test suite (Pytest & TestClient)

```

---

## 4. Quickstart Guide

### Prerequisites

* Python 3.10+
* Virtual environment (`venv`) active

### Installation

From within the `pipeline-vision-inspector` directory:

```bash
pip install -e ".[dev]"

```

### Generate Synthetic Test Data

Create realistic pipe inspection images simulating headlamp vignette, clean steel, oxidation patches, and localized pitting:

```bash
python sample_data/generate_samples.py

```

### Run Automated Unit Tests

Verify the detection engine, severity thresholds, and API endpoints:

```bash
pytest -v

```

### Launch the Inspection Dashboard

Start the FastAPI server:

```bash
uvicorn pipeline_vision.api.app:app --host 127.0.0.1 --port 8001 --reload

```

Open your browser and navigate to: `[http://127.0.0.1:8001](http://127.0.0.1:8001)`

---

## 5. API Reference

### Health Check

* **Endpoint:** `GET /health`
* **Response:**
```json
{
  "status": "healthy",
  "module": "pipeline-vision-inspector"
}

```



### Inspect Frame (Telemetry Only)

* **Endpoint:** `POST /api/v1/inspect`
* **Content-Type:** `multipart/form-data` (File payload)
* **Response:**
```json
{
  "total_surface_pixels": 307200,
  "corrosion_percentage": 13.45,
  "integrity_status": "REPAIR_REQUIRED",
  "clusters_detected": 2,
  "defect_clusters": [
    {
      "defect_id": 1,
      "centroid": [471, 318],
      "bounding_box": [376, 237, 191, 163],
      "area_pixels": 24770,
      "severity": "CRITICAL",
      "estimated_depth_score": 0.44
    }
  ]
}

```



### Inspect & Visualize (Dashboard Feed)

* **Endpoint:** `POST /api/v1/inspect/visualize`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns JSON containing defect metrics alongside a base64-encoded annotated JPEG displaying bounding boxes and cluster labels.

---

## 6. Verification & Test Metrics

The test suite validates the detection and scoring pipeline:

* `test_clean_pipe_detection`: Confirms zero false positives on clean pipe walls with status `ACCEPTABLE`.
* `test_corrosion_patch_segmentation`: Validates contour segmentation and triage escalation on corroded surfaces.
* `test_api_health_endpoint`: Ensures service availability.
* `test_api_inspect_endpoint`: Validates image serialization and JSON schema compliance.# Pipeline Vision Integrity Inspector (Oil & Gas NDT Engine)

An automated Non-Destructive Testing (NDT) computer vision engine and triage dashboard engineered for internal pipeline borescope inspection feeds, robotic crawlers, and In-Line Inspection (ILI) optical data.

---

## 1. Industry Background & Problem Statement

Energy infrastructure across upstream production, midstream pipelines, and downstream refining relies on continuous asset integrity management to prevent containment loss, catastrophic blowouts, and severe environmental spills.

* **The Inspection Bottleneck:** Robotic pipeline crawlers and borescopes generate hundreds of gigabytes of raw optical inspection footage. Human integrity engineers face severe visual fatigue when reviewing continuous video logs to detect localized pitting, rust blooms, and surface wall loss.
* **The Solution:** This engine processes internal pipeline imagery at runtime to automate defect segmentation, surface area calculation, and defect cavity depth proxy scoring. Triage states are evaluated against principles derived from **ASME B31G** (*Manual for Determining the Remaining Strength of Corroded Pipelines*) and **API 570** (*Piping Inspection Code*).

---

## 2. Technical Architecture & Core Algorithms

```
Raw Crawler / Borescope Frame
             │
             ▼
   [ CLAHE Normalization ]  ──> Equalizes radial headlamp illumination
             │
             ▼
[ HSV / LAB Color Isolation ] ──> Segments iron-oxide oxidation signatures
             │
             ▼
 [ Morphological Filtering ]  ──> Eliminates camera sensor & speckle noise
             │
             ▼
  [ Contour & Depth Metric ]  ──> Extracts surface area, centroids & luminance drop
             │
             ▼
[ ASME B31G Severity Triage ] ──> Classifies ACCEPTABLE / MONITOR / REPAIR REQUIRED
             │
             ▼
 [ FastAPI & Web Dashboard ]  ──> Visual overlay rendering & REST telemetry

```

### Key Engineering Features

1. **Luminance Normalization (CLAHE):** Crawler lighting systems introduce strong center hotspots and dark peripheral edges. Contrast Limited Adaptive Histogram Equalization is applied to the LAB color space L-channel (`clipLimit=2.5`, `tileGridSize=(8, 8)`) to maintain feature contrast without over-amplifying noise.
2. **Multi-Space Color Segmentation:** Isolates active oxidation zones by combining HSV hue gating (`[5, 28]`) with morphological open/close operations (`cv2.MORPH_ELLIPSE`) to separate bare steel backgrounds from corroded surfaces.
3. **Cavity Depth Proxy & Defect Clustering:** Computes geometric contours, defect cluster centroids, and bounding boxes. Evaluates local luminance attenuation within defect boundaries to differentiate shallow surface oxidation from deep localized pitting.
4. **Standard-Aligned Triage Engine:** Automatically categorizes pipeline segments into three operational tiers:
* **ACCEPTABLE:** Clean baseline pipe with zero defect clusters and negligible surface discoloration.
* **MONITOR:** Non-critical surface oxidation requiring scheduled tracking in line with maintenance intervals.
* **REPAIR REQUIRED:** High defect area coverage (> 15%) or localized deep cavity scores exceeding safety margins.



---

## 3. Project Structure

```text
pipeline-vision-inspector/
├── pyproject.toml                     # Module dependencies and metadata
├── README.md                          # Engineering documentation
├── sample_data/
│   ├── generate_samples.py            # Synthetic pipeline condition generator
│   ├── pipe_clean.jpg                 # Baseline clean steel pipe wall
│   ├── pipe_moderate_corrosion.jpg    # Surface oxidation / rust bloom sample
│   └── pipe_severe_pitting.jpg        # Deep localized cavity sample
├── src/
│   └── pipeline_vision/
│       ├── __init__.py
│       ├── detector.py                # Core CV engine & severity scoring logic
│       └── api/
│           ├── app.py                 # FastAPI application & web dashboard
│           └── schemas.py             # Pydantic response/request models
└── tests/
    └── test_pipeline_vision.py        # Automated test suite (Pytest & TestClient)

```

---

## 4. Quickstart Guide

### Prerequisites

* Python 3.10+
* Virtual environment (`venv`) active

### Installation

From within the `pipeline-vision-inspector` directory:

```bash
pip install -e ".[dev]"

```

### Generate Synthetic Test Data

Create realistic pipe inspection images simulating headlamp vignette, clean steel, oxidation patches, and localized pitting:

```bash
python sample_data/generate_samples.py

```

### Run Automated Unit Tests

Verify the detection engine, severity thresholds, and API endpoints:

```bash
pytest -v

```

### Launch the Inspection Dashboard

Start the FastAPI server:

```bash
uvicorn pipeline_vision.api.app:app --host 127.0.0.1 --port 8001 --reload

```

Open your browser and navigate to: `[http://127.0.0.1:8001](http://127.0.0.1:8001)`

---

## 5. API Reference

### Health Check

* **Endpoint:** `GET /health`
* **Response:**
```json
{
  "status": "healthy",
  "module": "pipeline-vision-inspector"
}

```



### Inspect Frame (Telemetry Only)

* **Endpoint:** `POST /api/v1/inspect`
* **Content-Type:** `multipart/form-data` (File payload)
* **Response:**
```json
{
  "total_surface_pixels": 307200,
  "corrosion_percentage": 13.45,
  "integrity_status": "REPAIR_REQUIRED",
  "clusters_detected": 2,
  "defect_clusters": [
    {
      "defect_id": 1,
      "centroid": [471, 318],
      "bounding_box": [376, 237, 191, 163],
      "area_pixels": 24770,
      "severity": "CRITICAL",
      "estimated_depth_score": 0.44
    }
  ]
}

```



### Inspect & Visualize (Dashboard Feed)

* **Endpoint:** `POST /api/v1/inspect/visualize`
* **Content-Type:** `multipart/form-data`
* **Response:** Returns JSON containing defect metrics alongside a base64-encoded annotated JPEG displaying bounding boxes and cluster labels.

---

## 6. Verification & Test Metrics

The test suite validates the detection and scoring pipeline:

* `test_clean_pipe_detection`: Confirms zero false positives on clean pipe walls with status `ACCEPTABLE`.
* `test_corrosion_patch_segmentation`: Validates contour segmentation and triage escalation on corroded surfaces.
* `test_api_health_endpoint`: Ensures service availability.
* `test_api_inspect_endpoint`: Validates image serialization and JSON schema compliance.
