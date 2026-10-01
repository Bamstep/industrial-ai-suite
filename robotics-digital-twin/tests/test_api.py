"""Integration tests for the Digital Twin FastAPI endpoints and WebSocket stream."""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from robotics_twin.api.app import app, sim

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "MuJoCo" in data["backend"]


def test_telemetry_snapshot():
    res = client.get("/telemetry/snapshot")
    assert res.status_code == 200
    data = res.json()
    assert len(data["joints"]["positions"]) == 6
    assert len(data["end_effector"]["position"]) == 3
    assert len(data["workpiece_position"]) == 3


def test_trajectory_execution_endpoint():
    q_home = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    sim.reset(initial_q=q_home)
    for _ in range(30):
        sim.step(target_q=q_home)

    target_q = q_home.copy()
    target_q[0] += 0.1

    payload = {"goal_positions": target_q.tolist(), "duration": 0.8}
    res = client.post("/trajectory/plan-and-execute", json=payload)
    assert res.status_code == 200
    updated_q = res.json()["joints"]["positions"]
    assert pytest.approx(target_q[0], abs=0.03) == updated_q[0]


def test_servoing_step_endpoint():
    q_home = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    sim.reset(initial_q=q_home)
    for _ in range(30):
        sim.step(target_q=q_home)

    res = client.post("/servoing/step", json={"cycles": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["cycles_executed"] == 10
    assert data["detected"] is True


def test_websocket_telemetry_stream():
    with client.websocket_connect("/ws/telemetry") as ws:
        frame = ws.receive_json()
        assert "joints" in frame
        assert "end_effector" in frame
        assert "workpiece_position" in frame
        assert len(frame["joints"]["positions"]) == 6
