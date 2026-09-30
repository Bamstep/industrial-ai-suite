import numpy as np
from src.ingestion.sensor_stream import IndustrialTelemetrySimulator
from src.core.signal_processor import SignalProcessor
from src.core.anomaly_engine import AnomalyEngine
from src.core.rul_estimator import RULEstimator

def run_e2e_pipeline():
    sim = IndustrialTelemetrySimulator()
    dsp = SignalProcessor(sampling_rate_hz=10000)
    engine = AnomalyEngine()
    rul_calc = RULEstimator(failure_threshold_rms=4.5)  # Zone C alert limit

    print("[1/3] Generating 50 healthy cycles to train Isolation Forest baseline...")
    baseline_records = []
    for _ in range(50):
        pkt = sim.generate_vibration_packet()
        m = dsp.process(pkt["waveform_z"])
        baseline_records.append([m.rms, m.crest_factor, m.kurtosis, pkt["temperature_c"]])

    engine.train_baseline(np.array(baseline_records))
    print("Baseline trained successfully.")

    print("\n[2/3] Simulating progressive machine wear over 10 cycles...")
    history_hours = []
    history_rms = []

    for step in range(1, 11):
        sim.step_degradation(rate=0.08)  # Rapid wear injection
        pkt = sim.generate_vibration_packet()
        m = dsp.process(pkt["waveform_z"])
        
        telemetry_eval = engine.score_telemetry(
            rms=m.rms,
            crest_factor=m.crest_factor,
            kurtosis=m.kurtosis,
            temperature_c=pkt["temperature_c"]
        )

        operating_hours = step * 10.0
        history_hours.append(operating_hours)
        history_rms.append(m.rms)

        rul_hours = rul_calc.estimate_hours_remaining(history_hours, history_rms)

        print(
            f"Cycle {step:02d} | RMS: {m.rms:.2f}g | Temp: {pkt['temperature_c']}C | "
            f"ISO: {telemetry_eval['iso_zone']:<10} | Health: {telemetry_eval['health_index']:5.1f}% | "
            f"RUL: {str(rul_hours) + ' hrs' if rul_hours is not None else 'Calibrating...'}"
        )

    print("\n[3/3] End-to-end telemetry evaluation completed.")

if __name__ == "__main__":
    run_e2e_pipeline()
