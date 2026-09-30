import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

from src.ingestion.sensor_stream import IndustrialTelemetrySimulator
from src.core.signal_processor import SignalProcessor
from src.core.anomaly_engine import AnomalyEngine
from src.core.rul_estimator import RULEstimator

simulator = IndustrialTelemetrySimulator()
dsp = SignalProcessor(sampling_rate_hz=10000)
anomaly_engine = AnomalyEngine()
rul_estimator = RULEstimator(failure_threshold_rms=4.50)

history_hours: List[float] = []
history_rms: List[float] = []
operating_hour_counter: float = 0.0

def fit_baseline_sync():
    baseline_samples = []
    for _ in range(25):
        pkt = simulator.generate_vibration_packet()
        m = dsp.process(pkt["waveform_z"])
        baseline_samples.append([
            float(m.rms),
            float(m.crest_factor),
            float(m.kurtosis),
            float(pkt["temperature_c"])
        ])
    anomaly_engine.train_baseline(np.array(baseline_samples))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Calibrating baseline in background...")
    await asyncio.to_thread(fit_baseline_sync)
    print("[INFO] Predictive Maintenance baseline ready.")
    yield

app = FastAPI(title="Industrial Predictive Maintenance API", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("src/api/index.html", "r", encoding="utf-8") as f:
        return f.read()

async def event_generator():
    global operating_hour_counter
    while True:
        packet = simulator.generate_vibration_packet()
        metrics = dsp.process(packet["waveform_z"])
        
        scoring = anomaly_engine.score_telemetry(
            rms=float(metrics.rms),
            crest_factor=float(metrics.crest_factor),
            kurtosis=float(metrics.kurtosis),
            temperature_c=float(packet["temperature_c"])
        )
        
        operating_hour_counter += 0.5
        history_hours.append(float(operating_hour_counter))
        history_rms.append(float(metrics.rms))
        if len(history_hours) > 50:
            history_hours.pop(0)
            history_rms.pop(0)
            
        rul_hours = rul_estimator.estimate_hours_remaining(history_hours, history_rms)
        
        freqs, amps = dsp.compute_fft(packet["waveform_z"])
        spectrum_mask = freqs <= 500.0
        sample_step = max(1, int(np.sum(spectrum_mask) / 80))
        
        chart_freqs = [float(round(f, 1)) for f in freqs[spectrum_mask][::sample_step]]
        chart_amps = [float(round(a, 4)) for a in amps[spectrum_mask][::sample_step]]
        peaks = [[float(round(p[0], 1)), float(round(p[1], 4))] for p in metrics.dominant_frequencies[:3]]

        payload = {
            "timestamp": float(packet["timestamp"]),
            "cycle": int(packet["cycle"]),
            "degradation_factor": float(packet["degradation_factor"]),
            "temperature_c": float(packet["temperature_c"]),
            "rms": float(metrics.rms),
            "crest_factor": float(metrics.crest_factor),
            "kurtosis": float(metrics.kurtosis),
            "iso_zone": str(scoring["iso_zone"]),
            "health_index": float(scoring["health_index"]),
            "ml_anomaly_score": float(scoring["ml_anomaly_score"]),
            "is_outlier": bool(scoring["is_outlier"]),
            "rul_hours": float(rul_hours) if rul_hours is not None else -1.0,
            "dominant_peaks": peaks,
            "fft_frequencies": chart_freqs,
            "fft_amplitudes": chart_amps
        }
        
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(0.5)

@app.get("/stream")
async def stream_telemetry():
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/degrade")
async def trigger_wear(rate: float = 0.05):
    simulator.step_degradation(rate=rate)
    return {"status": "degradation_stepped", "current_degradation": simulator.degradation_factor}

@app.post("/api/reset")
async def reset_machine():
    global history_hours, history_rms, operating_hour_counter
    simulator.degradation_factor = 0.0
    simulator.age_cycles = 0
    history_hours.clear()
    history_rms.clear()
    operating_hour_counter = 0.0
    return {"status": "machine_reset"}
