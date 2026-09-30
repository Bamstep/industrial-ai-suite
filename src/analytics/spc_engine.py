"""
src/analytics/spc_engine.py
Statistical Process Control (SPC) and Process Capability (Cp / Cpk) Engine.
Evaluates inspection lot runs and alerts on Nelson / Western Electric out-of-control rules.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class CapabilityMetrics:
    sample_size: int
    mean: float
    std_dev: float
    lsl: float
    usl: float
    cp: float
    cpk: float
    is_capable: bool          # Standard threshold: Cpk >= 1.33
    nelson_violations: List[str]


class MetrologySPCEngine:
    def __init__(self, cpk_threshold: float = 1.33):
        self.cpk_threshold = cpk_threshold

    def calculate_capability(
        self, samples: List[float], lsl: float, usl: float
    ) -> CapabilityMetrics:
        arr = np.array(samples, dtype=np.float64)
        n = len(arr)
        if n < 3:
            raise ValueError("SPC capability calculation requires at least 3 sample data points")

        mean = float(np.mean(arr))
        # Use Bessel's correction for sample standard deviation
        std_dev = float(np.std(arr, ddof=1))

        if std_dev == 0.0:
            std_dev = 1e-6

        # Standard Process Capability Indices
        cp = (usl - lsl) / (6.0 * std_dev)
        cpu = (usl - mean) / (3.0 * std_dev)
        cpl = (mean - lsl) / (3.0 * std_dev)
        cpk = min(cpu, cpl)

        # Nelson Rules Trend Detection
        violations = []
        # Rule 1: One point beyond 3 sigma
        outliers = [i for i, x in enumerate(arr) if abs(x - mean) > 3.0 * std_dev]
        if outliers:
            violations.append(f"Nelson Rule 1: {len(outliers)} sample(s) beyond 3-sigma control limits")

        # Rule 2: 9 points in a row on the same side of the mean
        if n >= 9:
            for i in range(n - 8):
                window = arr[i : i + 9]
                if all(w > mean for w in window) or all(w < mean for w in window):
                    violations.append(f"Nelson Rule 2: 9 consecutive samples shifted to one side of mean at idx {i}")
                    break

        # Rule 3: 6 points in a row steadily increasing or decreasing
        if n >= 6:
            for i in range(n - 5):
                diffs = np.diff(arr[i : i + 6])
                if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
                    violations.append(f"Nelson Rule 3: 6 consecutive points trending in one direction at idx {i}")
                    break

        return CapabilityMetrics(
            sample_size=n,
            mean=round(mean, 4),
            std_dev=round(std_dev, 4),
            lsl=lsl,
            usl=usl,
            cp=round(cp, 3),
            cpk=round(cpk, 3),
            is_capable=bool(cpk >= self.cpk_threshold),
            nelson_violations=violations,
        )
