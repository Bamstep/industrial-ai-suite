"""
anomaly_engine.py
-----------------
Hybrid Anomaly Detection:
- Rule-based ISO 10816 Vibration Severity evaluation.
- Isolation Forest unsupervised outlier scoring on multidimensional features.
"""

from enum import Enum
from typing import Dict, Any, List
import numpy as np
import yaml
from sklearn.ensemble import IsolationForest


class SeverityZone(str, Enum):
    GOOD = "GOOD"                    # Zone A: Newly commissioned
    ACCEPTABLE = "ACCEPTABLE"        # Zone B: Unrestricted operation
    ALERT = "ALERT"                  # Zone C: Remedial maintenance required
    DANGER = "DANGER"                # Zone D: Trip / immediate shutdown


class AnomalyEngine:
    def __init__(self, thresholds_path: str = "config/alarm_thresholds.yaml"):
        with open(thresholds_path, "r") as f:
            cfg = yaml.safe_load(f)
            
        self.iso_limits = cfg["vibration_severity_iso_10816"]
        self.stat_limits = cfg["statistical_thresholds"]

        # Isolation Forest baseline model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        self.is_fitted = False

    def train_baseline(self, baseline_feature_matrix: np.ndarray):
        """
        Fits Isolation Forest on known healthy run-in cycles.
        Features expected: [rms, crest_factor, kurtosis, temperature_c]
        """
        if len(baseline_feature_matrix) < 20:
            raise ValueError("Baseline training requires at least 20 run-in cycles.")
            
        self.model.fit(baseline_feature_matrix)
        self.is_fitted = True

    def classify_iso_severity(self, rms_g: float) -> SeverityZone:
        """Determines ISO 10816 machine operational zone."""
        if rms_g <= self.iso_limits["good_rms_limit"]:
            return SeverityZone.GOOD
        elif rms_g <= self.iso_limits["acceptable_rms_limit"]:
            return SeverityZone.ACCEPTABLE
        elif rms_g <= self.iso_limits["alert_rms_limit"]:
            return SeverityZone.ALERT
        else:
            return SeverityZone.DANGER

    def score_telemetry(
        self,
        rms: float,
        crest_factor: float,
        kurtosis: float,
        temperature_c: float
    ) -> Dict[str, Any]:
        """
        Evaluates a single telemetry frame against ISO thresholds and ML baseline.
        """
        iso_state = self.classify_iso_severity(rms)
        
        # Check statistical shock limits
        kurtosis_alarm = kurtosis >= self.stat_limits["kurtosis_alarm"]
        crest_factor_alarm = crest_factor >= self.stat_limits["crest_factor_alarm"]

        # ML anomaly probability (if trained)
        ml_anomaly_score = 0.0
        is_ml_outlier = False
        
        if self.is_fitted:
            features = np.array([[rms, crest_factor, kurtosis, temperature_c]])
            # decision_function: lower score = more anomalous
            raw_score = self.model.decision_function(features)[0]
            # Normalize roughly to [0, 1] range where 1.0 is severe anomaly
            ml_anomaly_score = float(np.clip(0.5 - (raw_score * 2.0), 0.0, 1.0))
            is_ml_outlier = bool(self.model.predict(features)[0] == -1)

        # Health Index calculation (100% down to 0%)
        # Degrades when RMS climbs or ML anomaly score is high
        rms_penalty = min(50.0, (rms / self.iso_limits["danger_rms_limit"]) * 50.0)
        ml_penalty = ml_anomaly_score * 50.0
        health_index = max(0.0, 100.0 - (rms_penalty + ml_penalty))

        return {
            "iso_zone": iso_state.value,
            "health_index": round(health_index, 1),
            "ml_anomaly_score": round(ml_anomaly_score, 3),
            "is_outlier": is_ml_outlier,
            "kurtosis_alarm": kurtosis_alarm,
            "crest_factor_alarm": crest_factor_alarm
        }
