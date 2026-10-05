# Turbomachinery Predictive Maintenance (PdM) Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Standards: ISO 10816-3](https://img.shields.io/badge/Standards-ISO%2010816--3-informational.svg)](https://www.iso.org/)

A high-fidelity digital signal processing (DSP) and condition-monitoring engine designed for high-criticality rotating machinery (gas/steam turbines, centrifugal compressors, boiler feed pumps, and industrial fans).

The service ingests high-frequency raw accelerometer telemetry, conducts automated time-frequency domain decomposition, tracks rotational order harmonics, and classifies mechanical fault severity according to international standards.

---

## Core Engineering Capabilities

### 1. ISO 10816-3 Vibration Severity Classification
- **Frequency-Domain Velocity Integration:** Converts raw acceleration ($\text{m/s}^2$ or $g$) into broadband RMS vibration velocity ($\text{mm/s}$) via spectral integration ($v(\omega) = \frac{a(\omega)}{j\omega}$) to suppress low-frequency DC drift.
- **Machine Class Assessment:** Automates machine evaluation across Class I (small machines $\le 15\text{ kW}$), Class II (medium $15\text{--}300\text{ kW}$), Class III (large rigid foundation), and Class IV (large flexible foundation).
- **Automated Alerting Tiers:** Classifies health states into Zone A (Newly commissioned), Zone B (Unrestricted continuous operation), Zone C (Restricted operation / alert), and Zone D (Unacceptable vibration / trip hazard).

### 2. Spectral Harmonic Order Tracking
- Identifies synchronous ($1\text{X}$) and harmonic multiples ($2\text{X}$, $3\text{X}$, $4\text{X}$) relative to the machine fundamental operating speed ($\text{RPM}$).
- Distinguishes between mass unbalance (dominant $1\text{X}$ peak), mechanical shaft misalignment (elevated $2\text{X}$ peak), and structural mechanical looseness (harmonics and sub-harmonics).

### 3. Impulsive Fault & Bearing Defect Triage
- **Statistical Kurtosis:** Detects early rolling-element bearing spalls and micro-pitting by tracking transient impulse events where kurtosis exceeds Gaussian baseline levels ($K > 3.0$).
- **Peak-to-Peak & Crest Factor:** Quantifies high-frequency energy content to guard against premature sensor saturation and catastrophic mechanical seizure.

---

## Architecture & Signal Flow

```
Raw Accelerometer Data
         |
         v
 [ Butterworth Bandpass Filter (10 Hz - 1000 Hz) ]
         |
         +------------------------+------------------------+
         |                                                 |
         v                                                 v
 [ Time-Domain Metrics ]                        [ Fast Fourier Transform (FFT) ]
 - RMS Acceleration                             - Spectral Peak Extraction
 - Kurtosis & Crest Factor                      - Rotational Order Tracking (1X, 2X)
         |                                                 |
         +------------------------+------------------------+
                                  |
                                  v
              [ ISO 10816-3 Velocity RMS Integration ]
                                  |
                                  v
                  [ Health Status & Diagnostic JSON ]
```

---

## API Reference

### Start the Standalone Service
```bash
uvicorn turbomachinery_pdm.api.app:app --port 8002 --reload
```

Interactive documentation is served at `http://localhost:8002/docs`.

### Diagnostic Endpoint
`POST /diagnose`

**Request Payload:**
```json
{
  "sampling_rate": 2048,
  "operating_rpm": 3000,
  "machine_class": "Class II",
  "acceleration_data": [0.012, 0.045, -0.021, 0.089, -0.034, 0.011]
}
```

**Response Body:**
```json
{
  "status": "HEALTHY",
  "iso_zone": "Zone A",
  "velocity_rms_mms": 1.15,
  "kurtosis": 2.94,
  "dominant_frequencies_hz": [50.0, 100.0],
  "order_harmonics": {
    "1X": 0.82,
    "2X": 0.14
  },
  "recommendation": "Machine operating within unrestricted continuous run parameters."
}
```

---

## Unit Testing

Execute the vibration and diagnostics test suite directly:
```bash
pytest turbomachinery-pdm/tests/ -v
```
