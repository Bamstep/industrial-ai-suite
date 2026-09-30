"""
tests/test_full_suite.py
Automated test suite verifying the complete Industrial CAD/GD&T Metrology Suite.
"""
import pytest
import numpy as np
from src.core.balloon_extractor import BalloonExtractor
from src.core.dimension_parser import DimensionParser
from src.core.as9102_exporter import AS9102RevCExporter, InspectionCharacteristic
from src.core.as9102_package_exporter import AS9102PackageExporter
from src.parsers.drf_resolver import DatumReferenceFrameResolver
from src.analytics.spc_engine import MetrologySPCEngine
from src.core.cmm_exporter import DMISRoutineExporter, CMMMeasurementFeature
from src.parsers.dxf_parser import DXFBlueprintParser


def test_drf_bonus_calculation():
    resolver = DatumReferenceFrameResolver()
    res = resolver.resolve(
        ["POS", "%%C 0.05 (M)", "A", "B (M)"],
        feature_actual_size=320.018,
        feature_mmc_size=320.00,
        is_internal_feature=True,
    )
    assert res.tolerance_zone_shape == "DIAMETRAL"
    assert res.bonus_tolerance == 0.018
    assert res.total_allowable_tolerance == 0.068


def test_spc_engine_capability():
    spc = MetrologySPCEngine()
    samples = [620.015, 620.010, 620.022, 620.018, 620.008, 620.012, 620.020, 620.014]
    metrics = spc.calculate_capability(samples, lsl=619.85, usl=620.15)
    assert metrics.cp > 1.33
    assert metrics.cpk > 1.33
    assert metrics.is_capable is True


def test_as9102_three_tier_package():
    exporter = AS9102PackageExporter()
    chars = [
        InspectionCharacteristic(
            char_no=1,
            reference_location="SH1-B2",
            characteristic_type="Linear Dimension",
            requirement="620.00 +/- 0.15",
            nominal=620.0,
            lower_limit=619.85,
            upper_limit=620.15,
            inspection_tool="Height Gauge",
            results=620.015,
            pass_fail="PASS",
        )
    ]
    pkg_bytes = exporter.generate_full_package(chars)
    assert len(pkg_bytes) > 4000
    assert pkg_bytes[:2] == b"PK"


def test_cmm_dmis_routine_generation():
    exporter = DMISRoutineExporter()
    feats = [
        CMMMeasurementFeature("FCF-01", "PLANE", (250.0, 360.0, 0.0), (0, 0, 1), 0.02, "FLAT", ["A"]),
        CMMMeasurementFeature("FCF-02", "CIRCLE", (550.0, 480.0, 0.0), (0, 0, 1), 0.068, "POS", ["A", "B"]),
    ]
    dmis_code = exporter.export_dmis(feats)
    assert "DMISMN/'STEPPED_FLANGE'" in dmis_code
    assert "TOL/FLAT,0.0200" in dmis_code
    assert "TOL/POS,DIAM,0.0680,MMC,DAT(A),DAT(B)" in dmis_code
    assert "ENDFIL" in dmis_code


def test_dxf_vector_parser(tmp_path):
    dxf_file = str(tmp_path / "test.dxf")
    parser = DXFBlueprintParser()
    parser.create_synthetic_dxf(dxf_file)
    dims = parser.parse_dxf(dxf_file)
    assert len(dims) == 1
    assert "620.00 +/- 0.15" in dims[0].override_text
