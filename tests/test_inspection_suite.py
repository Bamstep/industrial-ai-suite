"""
tests/test_inspection_suite.py
Automated test suite verifying the Balloon Extractor, Dimension Parser,
and AS9102 Revision C Exporter.
"""
import pytest
import numpy as np
import cv2
from src.core.balloon_extractor import BalloonExtractor
from src.core.dimension_parser import DimensionParser
from src.core.as9102_exporter import AS9102RevCExporter, InspectionCharacteristic


def test_dimension_parser_bilateral():
    parser = DimensionParser()
    parsed = parser.parse("620.00 +/- 0.15", dim_id="DIM-01")
    assert parsed is not None
    assert parsed.nominal == 620.00
    assert parsed.upper_limit == 620.15
    assert parsed.lower_limit == 619.85
    assert not parsed.is_diameter


def test_dimension_parser_diametral_limits():
    parser = DimensionParser()
    parsed = parser.parse("Ø320.00 +0.05/-0.00", dim_id="DIM-02")
    assert parsed is not None
    assert parsed.nominal == 320.00
    assert parsed.upper_limit == 320.05
    assert parsed.lower_limit == 320.00
    assert parsed.is_diameter


def test_balloon_extractor_circle_detection():
    extractor = BalloonExtractor()
    # Create white canvas with a single red circle
    canvas = np.ones((200, 200, 3), dtype=np.uint8) * 255
    cv2.circle(canvas, (100, 100), 20, (0, 0, 220), 2)

    balloons = extractor.detect_balloons(canvas)
    assert len(balloons) == 1
    assert abs(balloons[0].center_xy[0] - 100) <= 2
    assert abs(balloons[0].center_xy[1] - 100) <= 2


def test_as9102_excel_export():
    exporter = AS9102RevCExporter(part_number="FLANGE-TEST-01")
    records = [
        InspectionCharacteristic(
            char_no=1,
            reference_location="SH1-A1",
            characteristic_type="Linear Dimension",
            requirement="100.00 +/- 0.10",
            nominal=100.0,
            lower_limit=99.9,
            upper_limit=100.1,
            inspection_tool="Vernier Caliper",
            results=100.02,
            pass_fail="PASS",
        )
    ]
    xlsx_bytes = exporter.export_excel(records)
    assert len(xlsx_bytes) > 2000
    assert xlsx_bytes[:2] == b"PK"  # Valid ZIP/XLSX header
