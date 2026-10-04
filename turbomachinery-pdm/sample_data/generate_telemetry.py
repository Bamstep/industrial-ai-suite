from pathlib import Path
import json
import numpy as np


def generate_turbomachinery_dataset():
    out_dir = Path("turbomachinery-pdm/sample_data")
    out_dir.mkdir(parents=True, exist_ok=True)

    sampling_rate = 5000  # 5 kHz sampling
    duration = 1.0  # 1 second sample
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    rpm = 3000.0  # 50 Hz fundamental
    f1 = 50.0

    # 1. Healthy Baseline: Residual 1X = 0.04g (~0.88 mm/s RMS -> Zone A < 1.4 mm/s)
    healthy_signal = (
        0.04 * np.sin(2 * np.pi * f1 * t)
        + 0.015 * np.sin(2 * np.pi * 2 * f1 * t)
        + np.random.normal(0, 0.01, len(t))
    )

    # 2. Rotor Unbalance: Pronounced 1X = 0.8g (~17.6 mm/s -> Zone D unbalance trip)
    unbalance_signal = (
        0.80 * np.sin(2 * np.pi * f1 * t)
        + 0.05 * np.sin(2 * np.pi * 2 * f1 * t)
        + np.random.normal(0, 0.02, len(t))
    )

    # 3. Severe Misalignment & Bearing Impacting (1X + 2X + Periodic high kurtosis shocks)
    spall_shocks = np.zeros_like(t)
    shock_indices = np.arange(0, len(t), int(sampling_rate / 120))
    spall_shocks[shock_indices] = 2.5

    bearing_fault_signal = (
        0.30 * np.sin(2 * np.pi * f1 * t)
        + 0.60 * np.sin(2 * np.pi * 2 * f1 * t)
        + spall_shocks
        + np.random.normal(0, 0.05, len(t))
    )

    datasets = {
        "healthy_baseline.json": {
            "machine_id": "COMP-CENT-01A",
            "rpm": rpm,
            "sampling_rate_hz": sampling_rate,
            "signal_g": healthy_signal.tolist()
        },
        "rotor_unbalance.json": {
            "machine_id": "COMP-CENT-01B",
            "rpm": rpm,
            "sampling_rate_hz": sampling_rate,
            "signal_g": unbalance_signal.tolist()
        },
        "bearing_defect_trip.json": {
            "machine_id": "PUMP-CRUDE-02",
            "rpm": rpm,
            "sampling_rate_hz": sampling_rate,
            "signal_g": bearing_fault_signal.tolist()
        }
    }

    for fname, payload in datasets.items():
        target = out_dir / fname
        with open(target, "w") as f:
            json.dump(payload, f)
        print(f"Generated telemetry sample: {target}")


if __name__ == "__main__":
    generate_turbomachinery_dataset()
