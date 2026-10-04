from dataclasses import dataclass
from typing import List
import numpy as np
from scipy.signal import find_peaks


@dataclass
class TimeDomainMetrics:
    rms_velocity_mms: float
    peak_to_peak_g: float
    crest_factor: float
    kurtosis: float


@dataclass
class SpectralPeak:
    frequency_hz: float
    amplitude_g: float
    order: float  # Multiples of running speed 1X


@dataclass
class DiagnosticResult:
    machine_id: str
    running_speed_rpm: float
    running_speed_hz: float
    iso_zone: str  # "ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"
    time_domain: TimeDomainMetrics
    dominant_peaks: List[SpectralPeak]
    suspected_faults: List[str]
    maintenance_recommendation: str


class TurbomachineryVibrationAnalyzer:
    """
    Industrial signal processing engine adhering to ISO 10816-3.
    """

    def __init__(self, machine_class: int = 2, rigid_foundation: bool = True):
        self.machine_class = machine_class
        self.rigid_foundation = rigid_foundation

    def compute_time_domain(self, signal: np.ndarray, sampling_rate_hz: float) -> TimeDomainMetrics:
        centered = signal - np.mean(signal)
        p2p = float(np.ptp(centered))
        rms_accel = float(np.sqrt(np.mean(centered**2)))

        # Frequency-domain integration (ISO 2954 standard 10 Hz - 1000 Hz passband)
        n = len(centered)
        freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate_hz)
        fft_accel = np.fft.rfft(centered) * (2.0 / n)

        # Restrict to ISO band: 10 Hz to 1000 Hz
        valid_mask = (freqs >= 10.0) & (freqs <= 1000.0)
        v_spectrum = np.zeros_like(fft_accel, dtype=np.complex128)
        
        # V(f) = A(f) / (j * 2 * pi * f) in mm/s (1 g = 9806.65 mm/s^2)
        omega = 2.0 * np.pi * freqs[valid_mask]
        v_spectrum[valid_mask] = (fft_accel[valid_mask] * 9806.65) / (1j * omega)

        # RMS velocity in mm/s
        rms_velocity = float(np.sqrt(np.sum(np.abs(v_spectrum[valid_mask]) ** 2) / 2.0))

        # Crest Factor
        peak_val = np.max(np.abs(centered))
        crest_factor = float(peak_val / (rms_accel + 1e-6))

        # Kurtosis
        variance = np.var(centered)
        kurtosis = float(np.mean(centered**4) / (variance**2 + 1e-6))

        return TimeDomainMetrics(
            rms_velocity_mms=round(rms_velocity, 2),
            peak_to_peak_g=round(p2p, 3),
            crest_factor=round(crest_factor, 2),
            kurtosis=round(kurtosis, 2),
        )

    def compute_fft_spectrum(
        self, signal: np.ndarray, sampling_rate_hz: float, running_speed_hz: float, top_n: int = 5
    ) -> List[SpectralPeak]:
        n = len(signal)
        windowed = signal * np.hanning(n)
        fft_vals = np.abs(np.fft.rfft(windowed)) * (2.0 / n)
        freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate_hz)

        min_distance = max(1, int(len(freqs) * 0.005))
        peaks_indices, _ = find_peaks(fft_vals, distance=min_distance, prominence=0.01)

        if len(peaks_indices) == 0:
            return []

        sorted_indices = peaks_indices[np.argsort(fft_vals[peaks_indices])[::-1]][:top_n]

        results = []
        for idx in sorted_indices:
            f = float(freqs[idx])
            amp = float(fft_vals[idx])
            order = round(f / (running_speed_hz + 1e-6), 2)
            results.append(SpectralPeak(frequency_hz=round(f, 1), amplitude_g=round(amp, 3), order=order))

        return sorted(results, key=lambda x: x.amplitude_g, reverse=True)

    def evaluate_iso_10816(self, rms_velocity_mms: float) -> str:
        """
        ISO 10816-3 thresholds:
        Zone A (Good): <= 1.4 mm/s
        Zone B (Acceptable): <= 2.8 mm/s
        Zone C (Warning): <= 4.5 mm/s
        Zone D (Danger/Trip): > 4.5 mm/s
        """
        if rms_velocity_mms <= 1.4:
            return "ZONE_A"
        elif rms_velocity_mms <= 2.8:
            return "ZONE_B"
        elif rms_velocity_mms <= 4.5:
            return "ZONE_C"
        else:
            return "ZONE_D"

    def diagnose(
        self,
        machine_id: str,
        vibration_signal_g: np.ndarray,
        sampling_rate_hz: float,
        running_speed_rpm: float,
    ) -> DiagnosticResult:
        running_hz = running_speed_rpm / 60.0
        time_metrics = self.compute_time_domain(vibration_signal_g, sampling_rate_hz)
        peaks = self.compute_fft_spectrum(vibration_signal_g, sampling_rate_hz, running_hz)
        iso_zone = self.evaluate_iso_10816(time_metrics.rms_velocity_mms)

        suspected_faults = []
        recommendations = []

        unbalance_candidates = [p for p in peaks if 0.95 <= p.order <= 1.05 and p.amplitude_g >= 0.3]
        if unbalance_candidates:
            suspected_faults.append("Rotor Dynamic Mass Unbalance (1X Peak)")
            recommendations.append("Perform field dynamic balancing.")

        misalignment_candidates = [p for p in peaks if 1.95 <= p.order <= 2.05 and p.amplitude_g >= 0.3]
        if misalignment_candidates:
            suspected_faults.append("Shaft Angular/Parallel Misalignment (2X Harmonic)")
            recommendations.append("Inspect flexible coupling and re-align using laser dial indicators.")

        if time_metrics.kurtosis > 4.5:
            suspected_faults.append("High Impulsive Impacting (Bearing Race Micro-Spalling)")
            recommendations.append("Schedule ultrasound lubrication check or bearing cage replacement.")

        if not suspected_faults:
            suspected_faults.append("Nominal Baseline Operation")
            recommendations.append("Maintain standard condition monitoring routine.")

        if iso_zone == "ZONE_D":
            rec_text = "CRITICAL: Immediate automated trip required. " + " ".join(recommendations)
        elif iso_zone == "ZONE_C":
            rec_text = "WARNING: Restrict load and inspect within 48h. " + " ".join(recommendations)
        else:
            rec_text = " ".join(recommendations)

        return DiagnosticResult(
            machine_id=machine_id,
            running_speed_rpm=running_speed_rpm,
            running_speed_hz=round(running_hz, 2),
            iso_zone=iso_zone,
            time_domain=time_metrics,
            dominant_peaks=peaks,
            suspected_faults=suspected_faults,
            maintenance_recommendation=rec_text,
        )
