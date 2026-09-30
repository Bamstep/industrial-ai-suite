import time
import numpy as np
from typing import Generator, Dict, Any

class IndustrialTelemetrySimulator:
    def __init__(self, sampling_rate_hz: int = 10000, duration_sec: float = 1.0):
        self.fs = sampling_rate_hz
        self.duration = duration_sec
        self.n_samples = int(self.fs * self.duration)
        
        # Equipment parameters
        self.running_speed_hz = 29.5  # ~1770 RPM
        self.bpfo_hz = self.running_speed_hz * 3.584  # ~105.7 Hz
        
        # State tracking
        self.age_cycles = 0
        self.degradation_factor = 0.0  # 0.0 = brand new, 1.0 = failed

    def step_degradation(self, rate: float = 0.01):
        """Simulates wear over runtime."""
        self.age_cycles += 1
        self.degradation_factor = min(1.0, self.degradation_factor + rate)

    def generate_vibration_packet(self) -> Dict[str, Any]:
        """
        Synthesizes a 1-second multi-channel vibration packet.
        Includes shaft rotation, harmonics, bearing impacts, and thermal drift.
        """
        t = np.linspace(0, self.duration, self.n_samples, endpoint=False)
        
        # 1. Base 1X running shaft frequency (unbalance grows with degradation)
        unbalance_amp = 0.8 + (1.5 * self.degradation_factor)
        shaft_1x = unbalance_amp * np.sin(2 * np.pi * self.running_speed_hz * t)
        
        # 2. 2X harmonic (misalignment)
        misalignment_amp = 0.2 + (0.6 * self.degradation_factor)
        shaft_2x = misalignment_amp * np.sin(2 * np.pi * (self.running_speed_hz * 2) * t)

        # 3. Bearing impact shocks (BPFO impulses appear as degradation increases)
        bearing_signal = np.zeros(self.n_samples)
        if self.degradation_factor > 0.2:
            impact_period_samples = int(self.fs / self.bpfo_hz)
            decay_time = 0.005  # 5 ms ring-down
            decay_samples = int(self.fs * decay_time)
            decay_envelope = np.exp(-np.linspace(0, 5, decay_samples))
            
            # Place impacts at periodic BPFO intervals
            impact_amp = 3.5 * (self.degradation_factor ** 1.5)
            for idx in range(0, self.n_samples - decay_samples, impact_period_samples):
                bearing_signal[idx:idx + decay_samples] += impact_amp * decay_envelope

        # 4. Background high-frequency industrial noise
        noise = np.random.normal(0, 0.15, self.n_samples)

        # Composite acceleration signal (Z-axis / Radial)
        accel_z = shaft_1x + shaft_2x + bearing_signal + noise

        # Simulated bearing temperature (drifts upward with friction)
        baseline_temp_c = 42.0
        temp_c = baseline_temp_c + (28.0 * self.degradation_factor) + float(np.random.normal(0, 0.2))

        return {
            "timestamp": time.time(),
            "cycle": self.age_cycles,
            "degradation_factor": round(self.degradation_factor, 3),
            "sampling_rate_hz": self.fs,
            "waveform_z": accel_z,
            "temperature_c": round(temp_c, 2)
        }

    def stream(self, interval_sec: float = 0.5) -> Generator[Dict[str, Any], None, None]:
        """Continuous generator for real-time streaming."""
        while True:
            yield self.generate_vibration_packet()
            time.sleep(interval_sec)

if __name__ == "__main__":
    sim = IndustrialTelemetrySimulator()
    print("Testing sensor packet generation...")
    packet = sim.generate_vibration_packet()
    print(f"Generated {len(packet['waveform_z'])} samples at {packet['sampling_rate_hz']} Hz")
    print(f"Bearing Temp: {packet['temperature_c']} deg C | Degradation: {packet['degradation_factor']}")
