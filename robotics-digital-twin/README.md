```markdown
# UR5 Industrial Robotics Digital Twin

[![CI Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![MuJoCo](https://img.shields.io/badge/physics-MuJoCo%203.x-red.svg)]()
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)]()
[![Three.js](https://img.shields.io/badge/frontend-Three.js%20r128-black.svg)]()
[![Docker](https://img.shields.io/badge/deployment-Docker%20%7C%20OSMesa-2496ED.svg)]()
[![Tests](https://img.shields.io/badge/tests-16%20passed-success.svg)]()

A containerized, physics-based digital twin of a 6-DOF Universal Robots UR5 industrial arm. This platform integrates rigid-body dynamics, Image-Based Visual Servoing (IBVS), quintic minimum-jerk trajectory generation, potential field obstacle avoidance, and mechanical energy/jerk analytics into an interactive 3D WebGL dashboard.

Developed as a core module of the **Industrial AI Suite**.

---

## Author & Project Metadata

* **Author / Maintainer**: Bamstep ([@Bamstep](https://github.com/Bamstep))
* **Repository**: [industrial-ai-suite](https://github.com/Bamstep/industrial-ai-suite)
* **Module Path**: `robotics-digital-twin/`
* **License**: MIT
* **Status**: Production-Ready / Fully Tested (16/16 Unit & Integration Tests Passing)

---

## Table of Contents

1. [Industrial Value & Use Cases](#1-industrial-value--use-cases)
2. [Technical Architecture](#2-technical-architecture)
3. [Repository Layout](#3-repository-layout)
4. [Mathematical & Theoretical Foundations](#4-mathematical--theoretical-foundations)
5. [Getting Started & Installation](#5-getting-started--installation)
   - [Local Environment Setup](#local-environment-setup)
   - [Headless Docker Deployment](#headless-docker-deployment)
6. [Interactive Web Dashboard Guide](#6-interactive-web-dashboard-guide)
7. [REST & WebSocket API Reference](#7-rest--websocket-api-reference)
8. [Automated Testing Suite](#8-automated-testing-suite)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. Industrial Value & Use Cases

Physical robotics hardware carries high capital and downtime costs. This platform acts as a high-fidelity digital testbed before factory-floor deployment:

* **Virtual Workcell Commissioning**: Verify reachability, joint torque bounds, cycle times, and kinematic singularities before deploying hardware.
* **Closed-Loop Vision Validation**: Prototype eye-in-hand visual tracking routines and camera frame calibrations in software without risk of physical collisions.
* **Energy & Sustainability Optimization**: Benchmark joint power draw and cumulative energy across varied paths to select low-energy operating trajectories.
* **Predictive Asset Maintenance**: Track third-derivative joint jerk ($rad/s^3$) to identify profiles that cause excessive harmonic drive gearbox stress.
* **Obstacle Avoidance & Path Clearance**: Validate dynamic keep-out zones and replanning algorithms in a contact-accurate physics simulator.

---

## 2. Technical Architecture

The system connects numerical physics, perception, motion planning, and real-time streaming:


```

┌─────────────────────────────────────────────────────────────┐
│                 Interactive WebGL Dashboard                 │
│      Three.js 3D Viewport  •  Eye-in-Hand Feed  •  50 Hz WS │
└──────────────────────────────▲──────────────────────────────┘
│ HTTP / WebSocket (Port 8000)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Web Service                      │
│        Thread-Safe Re-Entrant Lock (GLFW / Rendering)       │
└───────▲──────────────────────▲──────────────────────▲───────┘
│                      │                      │
┌───────▼──────────────┐┌──────▼──────────────┐┌──────▼───────┐
│     Perception       ││   Motion Planning   ││   Analytics  │
│ • Synthetic RGB Cam  ││ • Quintic Min-Jerk  ││ • Power (W)  │
│ • HSV Centroid Track ││ • Potential Fields  ││ • Energy (J) │
│ • Interaction Matrix ││ • Pick-and-Place SM ││ • Jerk Check │
└───────▲──────────────┘└──────▲──────────────┘└──────▲───────┘
│                      │                      │
┌───────┴──────────────────────┴──────────────────────┴───────┐
│                   MuJoCo 3.x Physics Engine                 │
│    UR5 Kinematic Chain • Gravity Bias • Equality Weld Lock  │
└─────────────────────────────────────────────────────────────┘

```

* **Simulation Backend**: MuJoCo 3.x native C-API with numerical forward dynamics and equality weld constraints.
* **Offscreen Vision**: Dual-mode rendering (OpenGL hardware context or OSMesa software rendering for headless Linux containers) coupled with sub-pixel HSV segmentation.
* **Real-Time Synchronization**: 50 Hz WebSocket stream updating end-effector position, orientation quaternions, joint angles, velocities, and motor torques.

---

## 3. Repository Layout

```text
robotics-digital-twin/
├── Dockerfile                   # Multi-stage Debian image with OSMesa
├── docker-compose.yml           # Single-command container deployment
├── pyproject.toml               # Python package configuration & dependencies
├── README.md                    # Module documentation
├── src/robotics_twin/
│   ├── analytics/
│   │   ├── __init__.py
│   │   └── logger.py            # Power, energy, and jerk computation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI server, endpoints, WebGL UI
│   │   └── schemas.py           # Pydantic v2 telemetry & request schemas
│   ├── control/
│   │   ├── __init__.py
│   │   └── task_sequencer.py    # 4-stage autonomous pick-and-place coordinator
│   ├── kinematics/
│   │   ├── __init__.py
│   │   ├── dh_parameters.py     # Standard UR5 Denavit-Hartenberg table
│   │   ├── forward_kinematics.py# Forward kinematics & transform trees
│   │   ├── inverse_kinematics.py# Damped Least Squares (DLS) IK solver
│   │   └── jacobian.py          # Geometric Jacobian & manipulability index
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── simulator.py         # MuJoCo Python wrapper & telemetry builder
│   │   └── models/
│   │       └── robot_arm.xml    # Workcell XML (UR5, tables, obstacle, workpiece)
│   ├── trajectory/
│   │   ├── __init__.py
│   │   ├── potential_field.py   # Parabolic clearance & obstacle repulser
│   │   └── quintic_trajectory.py# 5th-order continuous polynomial planner
│   └── vision/
│       ├── __init__.py
│       ├── ibvs_controller.py   # Closed-loop visual servoing solver
│       └── visual_servoing.py   # Feature detection & interaction matrix
└── tests/                       # Complete automated pytest suite (16 tests)
    ├── test_analytics_and_avoidance.py
    ├── test_api.py
    ├── test_kinematics.py
    ├── test_simulation_trajectory.py
    ├── test_task_sequencer.py
    └── test_visual_servoing.py

```

---

## 4. Mathematical & Theoretical Foundations

### 1. Quintic Polynomial Trajectory Planning

To eliminate sudden torque jumps, each segment is planned as a 5th-degree polynomial:

$$s(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3 + a_4 t^4 + a_5 t^5$$

Enforcing continuous boundary conditions for position, velocity, and acceleration ($q(0), \dot{q}(0), \ddot{q}(0), q(T), \dot{q}(T), \ddot{q}(T)$) guarantees $C^2$ continuity and minimizes joint jerk.

### 2. Image-Based Visual Servoing (IBVS)

The relationship between end-effector camera velocity $v_c = [v_x, v_y, v_z, \omega_x, \omega_y, \omega_z]^T$ and image coordinate feature velocity $\dot{s} = [\dot{u}, \dot{v}]^T$ is governed by the interaction matrix $L_e$:

$$L_e = \begin{bmatrix} -\frac{\lambda}{Z} & 0 & \frac{u}{Z} & \frac{uv}{\lambda} & -\frac{\lambda^2 + u^2}{\lambda} & v \\ 0 & -\frac{\lambda}{Z} & \frac{v}{Z} & \frac{\lambda^2 + v^2}{\lambda} & -\frac{uv}{\lambda} & -u \end{bmatrix}$$

Camera velocity commands are derived using a proportional error-reduction law:

$$v_c = -\lambda_{gain} L_e^\dagger (s - s^*)$$

where $L_e^\dagger = L_e^T (L_e L_e^T)^{-1}$ is the Moore-Penrose pseudo-inverse.

### 3. Operational Power & Energy Analytics

Instantaneous mechanical power consumed by all 6 drive joints is calculated at each simulation step ($dt = 0.002\text{ s}$):

$$P(t) = \sum_{i=1}^6 \vert{}\tau_i(t) \cdot \dot{q}_i(t)\vert{}$$

Cumulative work done across the cycle is calculated via trapezoidal numerical integration:

$$E = \int_0^T P(t) \, dt \quad \text{[Joules]}$$

---

## 5. Getting Started & Installation

### Local Environment Setup

#### Prerequisites

* Python 3.11, 3.12, or 3.13
* Git

#### Step-by-step

```bash
# 1. Clone repository
git clone [https://github.com/Bamstep/industrial-ai-suite.git](https://github.com/Bamstep/industrial-ai-suite.git)
cd industrial-ai-suite/robotics-digital-twin

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 3. Install module dependencies in editable mode
pip install --upgrade pip
pip install -e .

# 4. Verify test suite
pytest -v

# 5. Start development server
uvicorn robotics_twin.api.app:app --host 127.0.0.1 --port 8000 --reload

```

Open `http://127.0.0.1:8000` in your web browser.

---

### Headless Docker Deployment

The application is containerized with software OpenGL fallback (`osmesa`), allowing it to run without a GPU or active window manager:

```bash
# Build and start container
docker compose up --build

```

To run in the background (detached mode):

```bash
docker compose up -d

```

The web dashboard and API endpoints are exposed on `http://localhost:8000`.

To stop the container:

```bash
docker compose down

```

---

## 6. Interactive Web Dashboard Guide

When loading `http://127.0.0.1:8000`, the single-page application provides:

1. **Top Status Bar**: Live 50 Hz WebSocket stream monitor, instantaneous power reading, and total energy consumption ($J$).
2. **Interactive 3D WebGL Viewport (Three.js)**:
* **Left Click + Drag**: Orbit view around the robotic cell.
* **Right Click + Drag**: Pan camera laterally.
* **Scroll**: Zoom in/out.
* **Visual Elements**: UR5 kinematic links, pickup table, droptable, yellow obstacle pillar, and dynamic red workpiece.


3. **Synthetic Eye-in-Hand Camera Stream**: Displays what the end-effector camera sees, updated with centroid detection overlays, crosshairs, and tracking offset vectors.
4. **Control Action Panel**:
* **Execute Full Pick-and-Place Cycle**: Initiates autonomous alignment, descent, magnetic weld coupling, obstacle clearance transfer, and drop table placement.
* **IBVS Align (25 Cycles)**: Runs standalone visual servoing steps to center the camera over the target workpiece.
* **Reset Scene & Workpiece**: Returns all joints to home pose and resets workpiece coordinates to the pickup station.
* **Download CSV Log**: Streams the recorded cycle telemetry log directly to a `.csv` file.



---

## 7. REST & WebSocket API Reference

### Endpoints Overview

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | System health check and MuJoCo backend verification |
| `GET` | `/telemetry/snapshot` | Current joint states, end-effector pose, workpiece coordinates, and collision flag |
| `GET` | `/camera/frame.jpg` | Live rendered eye-in-hand JPEG frame with tracking overlays |
| `GET` | `/analytics/summary` | Cycle duration, cumulative energy ($J$), average power ($W$), and peak jerk |
| `GET` | `/analytics/export-csv` | Download logged cycle metrics as a CSV file |
| `POST` | `/task/pick-and-place` | Trigger autonomous 4-stage transfer sequence |
| `POST` | `/task/reset-scene` | Reset robot arm and workpiece back to default home pose |
| `POST` | `/trajectory/plan-and-execute` | Plan and execute a $C^2$ quintic joint trajectory |
| `POST` | `/servoing/step` | Execute closed-loop IBVS visual tracking iterations |
| `WS` | `/ws/telemetry` | Full-duplex WebSocket streaming simulation state at 50 Hz |

### Example CLI Requests

#### 1. Inspect System Telemetry

```bash
curl -X GET "[http://127.0.0.1:8000/telemetry/snapshot](http://127.0.0.1:8000/telemetry/snapshot)"

```

#### 2. Execute Custom Minimum-Jerk Joint Trajectory

```bash
curl -X POST "[http://127.0.0.1:8000/trajectory/plan-and-execute](http://127.0.0.1:8000/trajectory/plan-and-execute)" \
     -H "Content-Type: application/json" \
     -d '{
       "goal_positions": [3.1415, -1.05, 0.55, -1.80, 0.0, 0.0],
       "duration": 1.5
     }'

```

#### 3. Run Visual Servoing Calibration Iterations

```bash
curl -X POST "[http://127.0.0.1:8000/servoing/step](http://127.0.0.1:8000/servoing/step)" \
     -H "Content-Type: application/json" \
     -d '{"cycles": 25}'

```

#### 4. Run Full Autonomous Transfer Cycle

```bash
curl -X POST "[http://127.0.0.1:8000/task/pick-and-place](http://127.0.0.1:8000/task/pick-and-place)"

```

---

## 8. Automated Testing Suite

The project includes 16 unit and integration tests covering kinematics, visual servoing, trajectory tracking, sequencer execution, and REST endpoints:

```bash
pytest -v

```

### Test Coverage Highlights

* `tests/test_kinematics.py`: Verifies DH link transformations, forward kinematic rotation matrix orthonormality ($R R^T = I, \det(R) = 1$), Jacobian rank, manipulability, and DLS inverse kinematics convergence.
* `tests/test_simulation_trajectory.py`: Validates that joint tracking under gravity bias compensation converges with small tracking error ($< 0.05\text{ rad}$).
* `tests/test_visual_servoing.py`: Tests interaction matrix conditioning, synthetic HSV workpiece detection accuracy, and monotonic pixel error decrease during IBVS loops.
* `tests/test_task_sequencer.py`: Runs the complete pick-and-place cycle and asserts that the workpiece is transferred across tables and placed above the secondary surface ($Z > 0.35\text{ m}$).
* `tests/test_analytics_and_avoidance.py`: Verifies potential field waypoint deflection and power calculation routines.
* `tests/test_api.py`: Tests FastAPI REST routes, telemetry snapshots, and WebSocket frame delivery.

---

## 9. Troubleshooting & FAQs

### Q: Why do I see a GLFW warning on Windows when running live?

```text
GLFWError: (65544) b'WGL: Failed to make context current: The requested resource is in use.'

```

* **Explanation**: This is a harmless concurrency warning from GLFW when multiple offscreen render requests hit the graphics driver simultaneously.
* **Fix**: The backend guards offscreen rendering with a re-entrant threading lock (`threading.RLock()`) and delegates blocking execution to an asynchronous worker pool via `starlette.concurrency.run_in_threadpool`.

### Q: How do I deploy to a server without a GPU?

* **Solution**: Use the included `Dockerfile`. It sets `ENV MUJOCO_GL=osmesa` and installs `libosmesa6-dev`, using software CPU rendering for all offscreen camera feeds.

---

## License

This project is open-source under the [MIT License](https://opensource.org/licenses/MIT).

```

```
