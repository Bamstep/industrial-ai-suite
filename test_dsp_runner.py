from src.ingestion.sensor_stream import IndustrialTelemetrySimulator
from src.core.signal_processor import SignalProcessor

def run_diagnostic_check():
    sim = IndustrialTelemetrySimulator()
    dsp = SignalProcessor(sampling_rate_hz=10000)

    print("=" * 60)
    print("PHASE 1: HEALTHY MOTOR BASELINE (Degradation = 0.0)")
    print("=" * 60)
    healthy_packet = sim.generate_vibration_packet()
    m_healthy = dsp.process(healthy_packet["waveform_z"])
    print(f"RMS Energy   : {m_healthy.rms:.4f} g")
    print(f"Crest Factor : {m_healthy.crest_factor:.2f}")
    print(f"Kurtosis     : {m_healthy.kurtosis:.2f} (Gaussian baseline ~ 3.0)")
    print("Top Frequencies (Hz, Amplitude):")
    for f, a in m_healthy.dominant_frequencies[:3]:
        print(f"  -> {f:6.1f} Hz | {a:.4f} g")

    # Degrade machine to 80% wear
    sim.degradation_factor = 0.8
    sim.age_cycles = 800

    print("\n" + "=" * 60)
    print("PHASE 2: SEVERE BEARING FAULT (Degradation = 0.8)")
    print("=" * 60)
    fault_packet = sim.generate_vibration_packet()
    m_fault = dsp.process(fault_packet["waveform_z"])
    print(f"RMS Energy   : {m_fault.rms:.4f} g (Elevated)")
    print(f"Crest Factor : {m_fault.crest_factor:.2f} (Spike shocks)")
    print(f"Kurtosis     : {m_fault.kurtosis:.2f} (Fault threshold > 4.5)")
    print("Top Frequencies (Hz, Amplitude):")
    for f, a in m_fault.dominant_frequencies[:3]:
        print(f"  -> {f:6.1f} Hz | {a:.4f} g")

if __name__ == "__main__":
    run_diagnostic_check()
