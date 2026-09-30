"""
rul_estimator.py
----------------
Remaining Useful Life (RUL) estimation using historical degradation trajectory.
Fits an exponential wear curve: y(t) = a * exp(b * t) to project when
RMS vibration will breach ISO 10816 Zone D (trip threshold).
"""

from typing import List, Optional
import numpy as np


class RULEstimator:
    def __init__(self, failure_threshold_rms: float = 7.10):
        self.threshold = failure_threshold_rms

    def estimate_hours_remaining(
        self,
        cycle_timestamps_hours: List[float],
        rms_history: List[float]
    ) -> Optional[float]:
        """
        Calculates estimated operating hours remaining until failure threshold breach.
        Requires at least 5 observation points.
        """
        if len(rms_history) < 5:
            return None

        x = np.array(cycle_timestamps_hours)
        y = np.array(rms_history)

        # Protect against non-positive values for log transform
        y = np.maximum(y, 1e-4)

        try:
            # Linear regression on log-transformed data: ln(y) = ln(a) + b * t
            coeffs = np.polyfit(x, np.log(y), 1)
            b = coeffs[0]
            ln_a = coeffs[1]
            a = np.exp(ln_a)

            # If degradation trend is flat or downward, RUL is safe / infinite
            if b <= 1e-5:
                return 999.0

            # Solve: threshold = a * exp(b * t_fail) -> t_fail = (ln(threshold) - ln(a)) / b
            t_fail = (np.log(self.threshold) - ln_a) / b
            current_t = x[-1]

            rul = max(0.0, float(t_fail - current_t))
            return round(rul, 1)
        except Exception:
            return None
