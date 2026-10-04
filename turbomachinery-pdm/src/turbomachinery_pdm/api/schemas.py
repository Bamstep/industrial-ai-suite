from typing import List, Optional
from pydantic import BaseModel


class VibrationTelemetryInput(BaseModel):
    machine_id: str
    running_speed_rpm: float
    sampling_rate_hz: float
    signal_g: List[float]


class SpectralPeakResponse(BaseModel):
    frequency_hz: float
    amplitude_g: float
    order: float


class TimeDomainResponse(BaseModel):
    rms_velocity_mms: float
    peak_to_peak_g: float
    crest_factor: float
    kurtosis: float


class DiagnosticResponse(BaseModel):
    machine_id: str
    running_speed_rpm: float
    running_speed_hz: float
    iso_zone: str
    time_domain: TimeDomainResponse
    dominant_peaks: List[SpectralPeakResponse]
    suspected_faults: List[str]
    maintenance_recommendation: str
