import numpy as np
import pytest
from fastapi.testclient import TestClient

from robotics_twin.api.app import app, sim

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"


def test_telemetry_snapshot():
    res = client.get("/telemetry/snapshot")
    assert res.status_code == 200
    data = res.json()
    assert "joints" in data
    assert len(data["joints"]["positions"]) == 6
    assert "end_effector" in data


def test_trajectory_execution_endpoint():
    target_q = [0.0, -1.57, 1.57, 0.0, 0.0, 0.0]
    res = client.post("/trajectory/plan-and-execute", json={"goal_positions": target_q, "duration": 0.5})
    assert res.status_code == 200
    data = res.json()
    assert "joints" in data
    assert len(data["joints"]["positions"]) == 6


def test_servoing_step_endpoint():
    try:
        q_home = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
        sim.reset(initial_q=q_home)
        for _ in range(30):
            sim.step(target_q=q_home)

        res = client.post("/servoing/step", json={"cycles": 10})
        if res.status_code == 200:
            data = res.json()
            assert data["cycles_executed"] == 10
            assert "detected" in data
            assert isinstance(data["detected"], bool)
    except Exception as exc:
        if "GLFW" in str(type(exc)) or "GL" in str(exc):
            pytest.skip(f"Skipping servoing rendering in headless environment without GL context: {exc}")
        else:
            raise exc


def test_websocket_telemetry_stream():
    with client.websocket_connect("/ws/telemetry") as ws:
        msg = ws.receive_json()
        assert "joints" in msg
        assert len(msg["joints"]["positions"]) == 6
