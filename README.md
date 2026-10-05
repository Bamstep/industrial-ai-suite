

```markdown
# Industrial AI Suite

[![CI](https://github.com/Bamstep/industrial-ai-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Bamstep/industrial-ai-suite/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modular industrial intelligence monorepo combining physical domain models, real-time kinematics simulation, non-destructive optical inspection, and condition-based predictive maintenance.

---

## System Architecture

```text
                      +-------------------------------+
                      |     Master Gateway (:8080)    |
                      +---------------+---------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+------------------+        +-------------------+        +--------------------+
|  Robotics Twin   |        |  Pipeline Vision  |        | Turbomachinery PdM |
|     (:8000)      |        |      (:8001)      |        |      (:8002)       |
+------------------+        +-------------------+        +--------------------+
| - 6-DOF UR5 Kin. |        | - CLAHE Normalize |        | - ISO 10816-3 RMS  |
| - Quintic Traj.  |        | - Optical Crawler |        | - Spectral FFT     |
| - IBVS Servoing  |        | - ASME B31G Audit |        | - Kurtosis Triage  |
| - WebGL Telemetry|        | - Chainage Log    |        | - Bandpass Filter  |
+------------------+        +-------------------+        +--------------------+

```

---

## Domain Capabilities

* **Robotics Digital Twin (`robotics-digital-twin`):** 6-DOF kinematics using standard Denavit-Hartenberg parameters, artificial repulsive potential fields for continuous obstacle avoidance, quintic polynomial trajectory interpolation, and closed-loop Image-Based Visual Servoing (IBVS).
* **Pipeline Vision Inspector (`pipeline-vision-inspector`):** In-pipe crawler video feed processing with Contrast-Limited Adaptive Histogram Equalization (CLAHE), automated optical chainage tracking, defect segmentation, and automated ASME B31G compliance report generation.
* **Turbomachinery PdM Engine (`turbomachinery-pdm`):** High-frequency accelerometer signal processing featuring Butterworth bandpass filtering, frequency-domain velocity integration, order-tracking FFT harmonic decomposition (1X/2X unbalance and misalignment), and ISO 10816-3 severity classification.

---

## Getting Started

### 1. Prerequisites

* **Python:** 3.11 or higher
* **Git:** Installed and configured
* **System Packages (Linux only):**
```bash
sudo apt-get update && sudo apt-get install -y libgl1 libglx-mesa0 libosmesa6 libosmesa6-dev libglew-dev libglfw3-dev tesseract-ocr xvfb

```



### 2. Clone the Repository

```bash
git clone [https://github.com/Bamstep/industrial-ai-suite.git](https://github.com/Bamstep/industrial-ai-suite.git)
cd industrial-ai-suite

```

### 3. Set Up Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 4. Install Dependencies

Install core packages and register all three submodules in editable (`-e`) mode:

```bash
python -m pip install --upgrade pip
pip install pytest httpx starlette fastapi uvicorn numpy opencv-python pydantic scipy openpyxl Pillow websockets
pip install -e robotics-digital-twin
pip install -e pipeline-vision-inspector
pip install -e turbomachinery-pdm

```

---

## Running the Test Suites

Execute all 25 unit tests across every module:

```bash
# 1. Robotics Digital Twin (16 unit tests)
pytest robotics-digital-twin/tests/ -v

# 2. Pipeline Vision Inspector (5 unit tests)
pytest pipeline-vision-inspector/tests/ -v

# 3. Turbomachinery PdM (4 unit tests)
pytest turbomachinery-pdm/tests/ -v

```

---

## Running the Services

### Option A: Unified Operations Gateway (Recommended)

Launches the master portal routing traffic across all microservices:

```bash
uvicorn src.gateway:app --port 8080 --reload

```

Open **`http://localhost:8080`** in your browser to view the system HUD and cross-service telemetry links.

### Option B: Running Individual Services

You can run any module independently in a dedicated terminal window:

1. **Robotics Digital Twin**
```bash
uvicorn robotics_twin.api.app:app --port 8000 --reload

```


* Web Interface: `http://localhost:8000`
* API Documentation: `http://localhost:8000/docs`


2. **Pipeline Vision Inspector**
```bash
uvicorn pipeline_vision.api.app:app --port 8001 --reload

```


* Web Interface: `http://localhost:8001`
* API Documentation: `http://localhost:8001/docs`


3. **Turbomachinery PdM Engine**
```bash
uvicorn turbomachinery_pdm.api.app:app --port 8002 --reload

```


* Web Interface: `http://localhost:8002`
* API Documentation: `http://localhost:8002/docs`



---

## API Testing with Postman / Bruno

A pre-configured API collection is included in the project root:

1. Open **Postman**, **Bruno**, or **Insomnia**.
2. Click **Import** and select `postman_collection.json`.
3. Execute pre-configured requests against `/trajectory/plan-and-execute`, `/inspect`, and `/diagnose`.

```

```
