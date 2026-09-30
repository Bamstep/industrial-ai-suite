"""
signal_processor.py
-------------------
DSP engine for industrial condition monitoring:
Extracts statistical time-domain features and FFT spectral peaks.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import numpy as np
from scipy import signal, stats


@dataclass(frozen=True)
class VibrationMetrics:
    rms: float
    peak: float
    peak_to_peak: float
    crest_factor: float
    kurtosis: float
    skewness: float
    dominant_frequencies: List[Tuple[float, float]]  # (frequency_hz, amplitude_g)


class SignalProcessor:
    def __init__(self, sampling_rate_hz: int = 10000):
        if sampling_rate_hz <= 0:
            raise ValueError("Sampling rate must be positive.")
        self.sampling_rate_hz = sampling_rate_hz

    def compute_time_domain_features(self, raw_signal: np.ndarray) -> Dict[str, float]:
        """Calculates foundational statistical condition indicators."""
        if raw_signal.size == 0:
            raise ValueError("Input signal buffer cannot be empty.")

        detrended = raw_signal - np.mean(raw_signal)

        rms = float(np.sqrt(np.mean(detrended**2)))
        peak = float(np.max(np.abs(detrended)))
        peak_to_peak = float(np.ptp(detrended))
        crest_factor = float(peak / (rms + 1e-9))
        kurt = float(stats.kurtosis(detrended, fisher=False))
        skew = float(stats.skew(detrended))

        return {
            "rms": round(rms, 4),
            "peak": round(peak, 4),
            "peak_to_peak": round(peak_to_peak, 4),
            "crest_factor": round(crest_factor, 2),
            "kurtosis": round(kurt, 2),
            "skewness": round(skew, 2),
        }

    def compute_fft(self, raw_signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates single-sided amplitude spectrum with Hann windowing."""
        n_samples = len(raw_signal)
        detrended = raw_signal - np.mean(raw_signal)

        window = np.hanning(n_samples)
        windowed = detrended * window

        fft_values = np.fft.rfft(windowed)
        frequencies_hz = np.fft.rfftfreq(n_samples, d=1.0 / self.sampling_rate_hz)
        amplitudes = (2.0 * np.abs(fft_values)) / (np.sum(window) + 1e-9)

        return frequencies_hz, amplitudes

    def extract_dominant_peaks(
        self,
        frequencies_hz: np.ndarray,
        amplitudes: np.ndarray,
        top_k: int = 5,
        min_distance_hz: float = 5.0,
    ) -> List[Tuple[float, float]]:
        """Finds highest amplitude harmonics, suppressing spectral noise."""
        freq_resolution = frequencies_hz[1] - frequencies_hz[0]
        distance_indices = max(1, int(min_distance_hz / freq_resolution))

        peak_indices, _ = signal.find_peaks(
            amplitudes,
            distance=distance_indices,
            prominence=np.max(amplitudes) * 0.05,
        )

        if len(peak_indices) == 0:
            return []

        sorted_indices = peak_indices[np.argsort(amplitudes[peak_indices])[::-1]]
        top_indices = sorted_indices[:top_k]

        return [
            (float(round(frequencies_hz[idx], 2)), float(round(amplitudes[idx], 4)))
            for idx in top_indices
        ]

    def process(self, raw_signal: np.ndarray, top_k_peaks: int = 5) -> VibrationMetrics:
        """Unified analysis pipeline returning structured metrics."""
        time_feats = self.compute_time_domain_features(raw_signal)
        freqs, amps = self.compute_fft(raw_signal)
        peaks = self.extract_dominant_peaks(freqs, amps, top_k=top_k_peaks)

        return VibrationMetrics(
            rms=time_feats["rms"],
            peak=time_feats["peak"],
            peak_to_peak=time_feats["peak_to_peak"],
            crest_factor=time_feats["crest_factor"],
            kurtosis=time_feats["kurtosis"],
            skewness=time_feats["skewness"],
            dominant_frequencies=peaks,
        )
