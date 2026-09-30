import pytest
import numpy as np
from src.core.signal_processor import SignalProcessor
from src.core.anomaly_engine import AnomalyEngine, SeverityZone
from src.core.rul_estimator import RULEstimator

def test_dsp_feature_extraction():
    dsp = SignalProcessor(sampling_rate_hz=10000)
    # Generate clean 30 Hz sine wave
    t = np.linspace(0, 1.0, 10000, endpoint=False)
    signal = 1.0 * np.sin(2 * np.pi * 30.0 * t)
    
    metrics = dsp.process(signal)
    
    # RMS of unit sine wave is 1/sqrt(2) ≈ 0.7071
    assert pytest.approx(metrics.rms, 0.05) == 0.7071
    assert pytest.approx(metrics.crest_factor, 0.1) == 1.41
    # Dominant peak should be detected near 30 Hz
    assert abs(metrics.dominant_frequencies[0][0] - 30.0) < 1.0

def test_iso_severity_classification():
    engine = AnomalyEngine()
    assert engine.classify_iso_severity(0.8) == SeverityZone.GOOD
    assert engine.classify_iso_severity(2.0) == SeverityZone.ACCEPTABLE
    assert engine.classify_iso_severity(3.5) == SeverityZone.ALERT
    assert engine.classify_iso_severity(8.0) == SeverityZone.DANGER

def test_rul_estimation_trend():
    estimator = RULEstimator(failure_threshold_rms=4.5)
    # 5 observation points with exponential climb
    hours = [10.0, 20.0, 30.0, 40.0, 50.0]
    rms_vals = [0.8, 1.1, 1.5, 2.1, 2.9]
    
    rul = estimator.estimate_hours_remaining(hours, rms_vals)
    assert rul is not None
    assert 0.0 < rul < 50.0  # Should project imminent breach within ~20-30 hours
