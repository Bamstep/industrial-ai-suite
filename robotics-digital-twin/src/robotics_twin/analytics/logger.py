"""Analytics Engine for Joint Jerk, Energy Consumption, and Operational Metrics."""

from __future__ import annotations
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import numpy as np


@dataclass
class CycleTelemetryRecord:
    timestamp: float
    total_power_watts: float
    max_joint_jerk: float
    collision: bool


class AnalyticsLogger:
    """Computes real-time robotics power, jerk, and logs cycle metrics to CSV."""

    def __init__(self, output_dir: str = "logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.records: List[CycleTelemetryRecord] = []
        self.prev_dq: np.ndarray = np.zeros(6)
        self.prev_acc: np.ndarray = np.zeros(6)
        self.prev_time: float = 0.0
        self.cumulative_energy_joules: float = 0.0

    def record_step(self, timestamp: float, qvel: List[float], torques: List[float], collision: bool) -> float:
        dt = max(1e-4, timestamp - self.prev_time)
        dq = np.array(qvel, dtype=np.float64)
        tau = np.array(torques, dtype=np.float64)

        # Power = sum(|tau * omega|)
        power = float(np.sum(np.abs(tau * dq)))
        self.cumulative_energy_joules += power * dt

        # Jerk = d(acc)/dt
        acc = (dq - self.prev_dq) / dt
        jerk = (acc - self.prev_acc) / dt
        max_jerk = float(np.max(np.abs(jerk))) if dt > 0.001 else 0.0

        self.prev_dq = dq
        self.prev_acc = acc
        self.prev_time = timestamp

        self.records.append(CycleTelemetryRecord(
            timestamp=round(timestamp, 4),
            total_power_watts=round(power, 3),
            max_joint_jerk=round(max_jerk, 2),
            collision=collision
        ))
        return power

    def export_csv(self, filename: str = "cycle_analytics.csv") -> Path:
        out_path = self.output_dir / filename
        with open(out_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp_s", "Power_Watts", "Max_Jerk_rad_s3", "Collision"])
            for r in self.records:
                writer.writerow([r.timestamp, r.total_power_watts, r.max_joint_jerk, r.collision])
        return out_path

    def get_summary(self) -> dict:
        total_time = self.records[-1].timestamp - self.records[0].timestamp if len(self.records) > 1 else 0.0
        avg_power = float(np.mean([r.total_power_watts for r in self.records])) if self.records else 0.0
        peak_jerk = float(np.max([r.max_joint_jerk for r in self.records])) if self.records else 0.0
        any_collision = any(r.collision for r in self.records)

        return {
            "duration_seconds": round(total_time, 3),
            "cumulative_energy_joules": round(self.cumulative_energy_joules, 2),
            "average_power_watts": round(avg_power, 2),
            "peak_jerk_rad_s3": round(peak_jerk, 2),
            "collision_detected": any_collision,
            "sample_count": len(self.records),
        }
