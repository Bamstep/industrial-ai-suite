import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from pipeline_vision.detector import PipelineCorrosionDetector
from pipeline_vision.api.app import app

client = TestClient(app)


def test_clean_pipe_detection():
    detector = PipelineCorrosionDetector()
    clean_img = np.full((300, 300, 3), 140, dtype=np.uint8)
    result = detector.analyze(clean_img)

    assert result.corrosion_percentage == 0.0
    assert result.integrity_status == "ACCEPTABLE"
    assert len(result.defect_clusters) == 0


def test_corrosion_patch_segmentation():
    detector = PipelineCorrosionDetector()
    test_img = np.full((300, 300, 3), 140, dtype=np.uint8)
    
    # Draw simulated rust patch (BGR: brownish-orange)
    cv2.circle(test_img, (150, 150), 50, (30, 80, 170), -1)
    result = detector.analyze(test_img)

    assert result.corrosion_percentage > 0.0
    assert len(result.defect_clusters) >= 1
    assert result.integrity_status in ["MONITOR", "REPAIR_REQUIRED"]


def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_api_inspect_endpoint():
    test_img = np.full((100, 100, 3), 140, dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", test_img)
    
    response = client.post(
        "/api/v1/inspect",
        files={"file": ("test.jpg", encoded.tobytes(), "image/jpeg")}
    )
    assert response.status_code == 200
    payload = response.json()
    assert "integrity_status" in payload
    assert payload["integrity_status"] == "ACCEPTABLE"
