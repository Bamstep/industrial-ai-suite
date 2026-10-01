"""FastAPI Digital Twin telemetry, Three.js 3D WebGL viewport, Analytics and Task Sequencer."""

from __future__ import annotations
import asyncio
import threading
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from robotics_twin.simulation.simulator import MuJoCoSimulator
from robotics_twin.trajectory.quintic_trajectory import QuinticTrajectoryGenerator
from robotics_twin.vision.ibvs_controller import ClosedLoopIBVS
from robotics_twin.control.task_sequencer import PickAndPlaceSequencer
from robotics_twin.analytics.logger import AnalyticsLogger
from robotics_twin.api.schemas import (
    TelemetryResponse,
    JointState,
    PoseCartesian,
    TrajectoryRequest,
    ServoRequest,
    ServoResponse,
)

app = FastAPI(title="Robotics Digital Twin API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

render_lock = threading.RLock()
sim = MuJoCoSimulator()
q_home = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
sim.reset(initial_q=q_home)
for _ in range(50):
    sim.step(target_q=q_home)

ibvs_controller = ClosedLoopIBVS(sim, kp_u=0.22, kp_v=0.45)
traj_gen = QuinticTrajectoryGenerator(dof=6)
sequencer = PickAndPlaceSequencer(sim, ibvs_controller, render_lock=render_lock)
analytics = AnalyticsLogger()


def _telemetry_to_schema() -> TelemetryResponse:
    t = sim.get_telemetry()
    return TelemetryResponse(
        timestamp=round(t.timestamp, 4),
        joints=JointState(
            positions=[round(float(v), 4) for v in t.joint_positions],
            velocities=[round(float(v), 4) for v in t.joint_velocities],
            torques=[round(float(v), 4) for v in t.joint_torques],
        ),
        end_effector=PoseCartesian(
            position=[round(float(v), 4) for v in t.ee_position],
            orientation_quat=[round(float(v), 4) for v in t.ee_orientation],
        ),
        workpiece_position=[round(float(v), 4) for v in t.workpiece_position],
        collision_detected=bool(t.collision_detected),
    )


@app.get("/camera/frame.jpg")
def get_camera_frame():
    with render_lock:
        frame_rgb = sim.render_eye_in_hand(width=320, height=240)
    feat = ibvs_controller.vision.detect_workpiece(frame_rgb)
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    cv2.drawMarker(frame_bgr, (160, 120), (0, 255, 0), cv2.MARKER_CROSS, 16, 2)
    if feat.detected:
        cv2.circle(frame_bgr, (int(feat.u), int(feat.v)), 8, (0, 0, 255), 2)
        cv2.line(frame_bgr, (160, 120), (int(feat.u), int(feat.v)), (255, 200, 0), 1)

    _, jpeg = cv2.imencode(".jpg", frame_bgr)
    return Response(content=jpeg.tobytes(), media_type="image/jpeg")


@app.get("/analytics/summary")
def get_analytics_summary():
    return analytics.get_summary()


@app.get("/analytics/export-csv")
def export_analytics_csv():
    csv_path = analytics.export_csv("cycle_analytics.csv")
    return FileResponse(path=csv_path, filename="cycle_analytics.csv", media_type="text/csv")


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>UR5 Digital Twin - 3D Simulation & Control</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b1120; color: #f1f5f9; margin: 0; padding: 18px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { font-size: 20px; color: #38bdf8; margin: 0 0 4px 0; }
            .subtitle { color: #94a3b8; font-size: 13px; margin-bottom: 14px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 14px; }
            .panel { background: #1e293b; border-radius: 8px; padding: 14px; border: 1px solid #334155; }
            .panel-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px; letter-spacing: 0.05em; }
            .metric { font-size: 15px; font-weight: 700; color: #f8fafc; font-family: monospace; }
            .table { width: 100%; border-collapse: collapse; font-family: monospace; font-size: 12px; }
            .table th, .table td { padding: 4px 6px; text-align: left; border-bottom: 1px solid #334155; }
            .table th { color: #94a3b8; }
            .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; }
            .badge-live { background: #065f46; color: #34d399; }
            .badge-err { background: #7f1d1d; color: #f87171; }
            .btn { background: #0284c7; color: white; border: none; border-radius: 6px; padding: 8px 14px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.2s; }
            .btn:hover { background: #0369a1; }
            .btn-green { background: #16a34a; }
            .btn-green:hover { background: #15803d; }
            .btn-purple { background: #7c3aed; }
            .btn-purple:hover { background: #6d28d9; }
            .btn-amber { background: #d97706; }
            .btn-amber:hover { background: #b45309; }
            #three-container { width: 100%; height: 280px; border-radius: 6px; overflow: hidden; background: #0f172a; border: 1px solid #475569; }
            img#cam-stream { width: 100%; height: 280px; object-fit: contain; background: #000; border-radius: 6px; border: 1px solid #475569; display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <h1>UR5 Digital Twin - Real-Time 3D & Telemetry</h1>
                    <div class="subtitle">MuJoCo Physics Engine | Offscreen IBVS Perception | WebSockets | Analytics</div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <a href="/analytics/export-csv" class="btn btn-amber" style="text-decoration: none;">Download CSV Log</a>
                    <div id="status-badge" class="badge badge-live">STREAM LIVE (50 Hz)</div>
                </div>
            </div>

            <div class="grid">
                <div class="panel">
                    <div class="panel-title">Sim Time</div>
                    <div id="sim-time" class="metric">0.000 s</div>
                </div>
                <div class="panel">
                    <div class="panel-title">End-Effector [X, Y, Z]</div>
                    <div id="ee-pos" class="metric">[0, 0, 0]</div>
                </div>
                <div class="panel">
                    <div class="panel-title">Workpiece [X, Y, Z]</div>
                    <div id="wp-pos" class="metric">[0, 0, 0]</div>
                </div>
                <div class="panel">
                    <div class="panel-title">Energy Consumption</div>
                    <div id="energy-metric" class="metric">0.00 J</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="panel">
                    <div class="panel-title">Interactive 3D WebGL Digital Twin Viewport (Orbit / Zoom)</div>
                    <div id="three-container"></div>
                </div>

                <div class="panel">
                    <div class="panel-title">Eye-in-Hand Camera Feed (HSV Centroid Tracking)</div>
                    <img id="cam-stream" src="/camera/frame.jpg" alt="Eye-in-Hand Feed" />
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px;">
                <div class="panel">
                    <div class="panel-title">Joint Telemetry (6-DOF)</div>
                    <table class="table">
                        <thead>
                            <tr><th>Joint</th><th>Position (rad)</th><th>Velocity (rad/s)</th><th>Torque (Nm)</th></tr>
                        </thead>
                        <tbody id="joints-table"></tbody>
                    </table>
                </div>

                <div class="panel">
                    <div class="panel-title">Control Actions</div>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button class="btn btn-purple" onclick="runPickAndPlace()">Execute Full Pick-and-Place Cycle</button>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-green" style="flex: 1;" onclick="runServoing(25)">IBVS Align (25 Cycles)</button>
                            <button class="btn btn-amber" style="flex: 1;" onclick="resetScene()">Reset Scene & Workpiece</button>
                        </div>
                        <div id="action-status" style="font-size: 12px; color: #38bdf8; font-family: monospace; margin-top: 4px;">Status: Ready</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const container = document.getElementById("three-container");
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0f172a);

            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 280, 0.1, 50);
            camera.position.set(1.4, -1.2, 1.3);
            camera.up.set(0, 0, 1);

            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, 280);
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(0.2, 0.0, 0.4);
            controls.update();

            const ambient = new THREE.AmbientLight(0xffffff, 0.7);
            scene.add(ambient);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(1, 1, 3);
            scene.add(dirLight);

            const grid = new THREE.GridHelper(3, 30, 0x38bdf8, 0x334155);
            grid.rotation.x = Math.PI / 2;
            scene.add(grid);

            // Worktables
            const workTable = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.7, 0.4), new THREE.MeshStandardMaterial({ color: 0x475569 }));
            workTable.position.set(0.5, 0, 0.2);
            scene.add(workTable);

            const dropTable = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.7, 0.4), new THREE.MeshStandardMaterial({ color: 0x334155 }));
            dropTable.position.set(0.0, 0.5, 0.2);
            scene.add(dropTable);

            // Obstacle Zone Pillar
            const obsMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.3, 16), new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.3 }));
            obsMesh.rotation.x = Math.PI / 2;
            obsMesh.position.set(0.22, 0.22, 0.35);
            scene.add(obsMesh);

            const wpMesh = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 0.05), new THREE.MeshStandardMaterial({ color: 0xef4444 }));
            scene.add(wpMesh);

            const armRoot = new THREE.Group();
            scene.add(armRoot);

            const baseMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.1, 16), new THREE.MeshStandardMaterial({ color: 0x64748b }));
            baseMesh.rotation.x = Math.PI / 2;
            baseMesh.position.z = 0.05;
            armRoot.add(baseMesh);

            const j1 = new THREE.Group(); j1.position.z = 0.12; armRoot.add(j1);
            const j2 = new THREE.Group(); j2.position.z = 0.06; j1.add(j2);
            const j3 = new THREE.Group(); j3.position.x = -0.425; j2.add(j3);
            const j4 = new THREE.Group(); j4.position.x = -0.392; j4.position.z = 0.109; j3.add(j4);
            const j5 = new THREE.Group(); j5.position.z = 0.094; j4.add(j5);
            const j6 = new THREE.Group(); j6.position.z = 0.082; j5.add(j6);

            function makeLink(len, radius, color) {
                const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, len, 12), new THREE.MeshStandardMaterial({ color }));
                mesh.position.x = -len / 2;
                mesh.rotation.z = Math.PI / 2;
                return mesh;
            }
            j2.add(makeLink(0.425, 0.045, 0x0284c7));
            j3.add(makeLink(0.392, 0.038, 0x38bdf8));

            const eeMesh = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 12), new THREE.MeshStandardMaterial({ color: 0x22c55e }));
            j6.add(eeMesh);

            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }
            animate();

            const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
            const ws = new WebSocket(`${proto}//${window.location.host}/ws/telemetry`);
            const statusBadge = document.getElementById("status-badge");
            const simTime = document.getElementById("sim-time");
            const eePos = document.getElementById("ee-pos");
            const wpPos = document.getElementById("wp-pos");
            const energyMetric = document.getElementById("energy-metric");
            const jointsTable = document.getElementById("joints-table");
            const camStream = document.getElementById("cam-stream");
            const actionStatus = document.getElementById("action-status");

            ws.onopen = () => {
                statusBadge.innerText = "STREAM LIVE (50 Hz)";
                statusBadge.className = "badge badge-live";
            };

            ws.onclose = () => {
                statusBadge.innerText = "DISCONNECTED";
                statusBadge.className = "badge badge-err";
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                simTime.innerText = data.timestamp.toFixed(3) + " s";
                eePos.innerText = `[${data.end_effector.position.map(v => v.toFixed(3)).join(', ')}]`;
                wpPos.innerText = `[${data.workpiece_position.map(v => v.toFixed(3)).join(', ')}]`;

                wpMesh.position.set(...data.workpiece_position);

                const q = data.joints.positions;
                j1.rotation.z = q[0];
                j2.rotation.y = q[1];
                j3.rotation.y = q[2];
                j4.rotation.y = q[3];
                j5.rotation.z = q[4];
                j6.rotation.x = q[5];

                let rows = "";
                for (let i = 0; i < 6; i++) {
                    rows += `<tr>
                        <td>Joint ${i + 1}</td>
                        <td>${data.joints.positions[i].toFixed(4)}</td>
                        <td>${data.joints.velocities[i].toFixed(4)}</td>
                        <td>${data.joints.torques[i].toFixed(2)}</td>
                    </tr>`;
                }
                jointsTable.innerHTML = rows;
            };

            setInterval(async () => {
                camStream.src = `/camera/frame.jpg?t=${Date.now()}`;
                try {
                    const res = await fetch("/analytics/summary");
                    const sm = await res.json();
                    energyMetric.innerText = `${sm.cumulative_energy_joules.toFixed(1)} J | ${sm.average_power_watts.toFixed(1)} W`;
                } catch(e) {}
            }, 500);

            async function runPickAndPlace() {
                actionStatus.innerText = "Executing Pick-and-Place State Machine...";
                try {
                    const res = await fetch("/task/pick-and-place", { method: "POST" });
                    const d = await res.json();
                    actionStatus.innerText = d.message;
                } catch(e) {
                    actionStatus.innerText = "Error executing cycle";
                }
            }

            async function runServoing(cycles) {
                actionStatus.innerText = "Executing IBVS loop...";
                try {
                    const res = await fetch("/servoing/step", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ cycles })
                    });
                    const d = await res.json();
                    actionStatus.innerText = `IBVS: ${d.cycles_executed} cycles | Error: ${d.final_error_px} px`;
                } catch(e) {
                    actionStatus.innerText = "Error running IBVS";
                }
            }

            async function resetScene() {
                actionStatus.innerText = "Resetting arm & workpiece to initial pose...";
                try {
                    await fetch("/task/reset-scene", { method: "POST" });
                    actionStatus.innerText = "Scene reset successfully";
                } catch(e) {
                    actionStatus.innerText = "Error resetting scene";
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
def health_check():
    return {"status": "online", "model": "6-DOF UR5 Digital Twin", "backend": "MuJoCo C-API"}


@app.get("/telemetry/snapshot", response_model=TelemetryResponse)
def get_snapshot():
    return _telemetry_to_schema()


@app.post("/task/reset-scene")
async def reset_scene():
    def _run():
        with render_lock:
            sim.reset(initial_q=q_home)
            for _ in range(50):
                sim.step(target_q=q_home)
        return {"status": "reset", "message": "Robot and workpiece returned to origin."}

    return await run_in_threadpool(_run)


@app.post("/trajectory/plan-and-execute", response_model=TelemetryResponse)
async def execute_trajectory(req: TrajectoryRequest):
    def _run():
        with render_lock:
            current_q = np.array(sim.get_telemetry().joint_positions, dtype=np.float64)
            target_q = np.array(req.goal_positions, dtype=np.float64)
            dt_sim = 0.002
            num_steps = max(10, int(req.duration / dt_sim))
            waypoints = traj_gen.plan_segment(current_q, target_q, duration=req.duration, num_points=num_steps)
            for pt in waypoints:
                t = sim.step(target_q=pt.positions, target_dq=pt.velocities)
                analytics.record_step(t.timestamp, t.joint_velocities, t.joint_torques, t.collision_detected)
            for _ in range(50):
                t = sim.step(target_q=target_q)
                analytics.record_step(t.timestamp, t.joint_velocities, t.joint_torques, t.collision_detected)
        return _telemetry_to_schema()

    return await run_in_threadpool(_run)


@app.post("/servoing/step", response_model=ServoResponse)
async def run_visual_servoing(req: ServoRequest):
    def _run():
        with render_lock:
            current_q = np.array(sim.get_telemetry().joint_positions, dtype=np.float64)
            frame = sim.render_eye_in_hand(width=320, height=240)
            feat_init = ibvs_controller.vision.detect_workpiece(frame)
            init_err = float(np.linalg.norm([feat_init.u - 160.0, feat_init.v - 120.0])) if feat_init.detected else 0.0

            last_res = None
            for _ in range(req.cycles):
                current_q, last_res = ibvs_controller.step_servo(current_q, dt=0.05)
                for _ in range(25):
                    t = sim.step(target_q=current_q)
                    analytics.record_step(t.timestamp, t.joint_velocities, t.joint_torques, t.collision_detected)

            final_err = last_res.error_norm if last_res else init_err
            detected = last_res.feature.detected if last_res else False
            centroid = [round(last_res.feature.u, 2), round(last_res.feature.v, 2)] if last_res else [0.0, 0.0]

        return ServoResponse(
            success=bool(final_err < init_err or final_err < 80.0),
            cycles_executed=req.cycles,
            initial_error_px=round(init_err, 2),
            final_error_px=round(final_err, 2),
            detected=detected,
            final_centroid=centroid,
        )

    return await run_in_threadpool(_run)


@app.post("/task/pick-and-place")
async def run_autonomous_cycle():
    def _run():
        return sequencer.run_full_cycle()

    success = await run_in_threadpool(_run)
    return {"success": success, "message": "Pick-and-place cycle completed successfully."}


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            t = sim.get_telemetry()
            analytics.record_step(t.timestamp, t.joint_velocities, t.joint_torques, t.collision_detected)
            payload = _telemetry_to_schema().model_dump()
            await websocket.send_json(payload)
            await asyncio.sleep(0.02)
    except WebSocketDisconnect:
        pass
