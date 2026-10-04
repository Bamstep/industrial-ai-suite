import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from turbomachinery_pdm.analyzer import TurbomachineryVibrationAnalyzer
from turbomachinery_pdm.api.app import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_analyzer_on_healthy_baseline():
    analyzer = TurbomachineryVibrationAnalyzer()
    sample_file = Path("turbomachinery-pdm/sample_data/healthy_baseline.json")
    if not sample_file.exists():
        sample_file = Path("sample_data/healthy_baseline.json")
    with open(sample_file, "r") as f:
        data = json.load(f)

    res = analyzer.diagnose(
        machine_id=data["machine_id"],
        vibration_signal_g=np.array(data["signal_g"]),
        sampling_rate_hz=data["sampling_rate_hz"],
        running_speed_rpm=data["rpm"]
    )

    assert res.iso_zone in ["ZONE_A", "ZONE_B"]
    assert "Nominal Baseline Operation" in res.suspected_faults


def test_analyzer_on_critical_trip():
    analyzer = TurbomachineryVibrationAnalyzer()
    sample_file = Path("turbomachinery-pdm/sample_data/bearing_defect_trip.json")
    if not sample_file.exists():
        sample_file = Path("sample_data/bearing_defect_trip.json")
    with open(sample_file, "r") as f:
        data = json.load(f)

    res = analyzer.diagnose(
        machine_id=data["machine_id"],
        vibration_signal_g=np.array(data["signal_g"]),
        sampling_rate_hz=data["sampling_rate_hz"],
        running_speed_rpm=data["rpm"]
    )

    assert res.iso_zone == "ZONE_D"
    assert "CRITICAL" in res.maintenance_recommendation


def test_api_diagnose_endpoint():
    sample_file = Path("turbomachinery-pdm/sample_data/rotor_unbalance.json")
    if not sample_file.exists():
        sample_file = Path("sample_data/rotor_unbalance.json")
    with open(sample_file, "r") as f:
        data = json.load(f)

    response = client.post(
        "/api/v1/diagnose",
        json={
            "machine_id": data["machine_id"],
            "running_speed_rpm": data["rpm"],
            "sampling_rate_hz": data["sampling_rate_hz"],
            "signal_g": data["signal_g"]
        }
    )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["machine_id"] == "COMP-CENT-01B"
    assert len(res_json["dominant_peaks"]) > 0
