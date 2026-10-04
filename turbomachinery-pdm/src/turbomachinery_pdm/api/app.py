import json
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from turbomachinery_pdm.analyzer import TurbomachineryVibrationAnalyzer
from turbomachinery_pdm.api.schemas import VibrationTelemetryInput, DiagnosticResponse

app = FastAPI(
    title="Turbomachinery Vibration & Predictive Maintenance Engine",
    description="ISO 10816-3 Condition Monitoring, FFT Spectral Peak Demodulation, and Fault Triage",
    version="0.1.0"
)

analyzer = TurbomachineryVibrationAnalyzer()


@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "turbomachinery-pdm", "version": "0.1.0"}


@app.get("/sample/{sample_name}")
def get_sample_telemetry(sample_name: str):
    p = Path("sample_data") / f"{sample_name}.json"
    if not p.exists():
        p = Path("turbomachinery-pdm/sample_data") / f"{sample_name}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Sample dataset not found")
    with open(p, "r") as f:
        return json.load(f)


@app.post("/api/v1/diagnose", response_model=DiagnosticResponse)
def diagnose_telemetry(payload: VibrationTelemetryInput):
    signal_arr = np.array(payload.signal_g, dtype=np.float64)
    if len(signal_arr) < 64:
        raise HTTPException(status_code=400, detail="Insufficient signal duration for FFT decomposition.")

    res = analyzer.diagnose(
        machine_id=payload.machine_id,
        vibration_signal_g=signal_arr,
        sampling_rate_hz=payload.sampling_rate_hz,
        running_speed_rpm=payload.running_speed_rpm
    )

    return DiagnosticResponse(
        machine_id=res.machine_id,
        running_speed_rpm=res.running_speed_rpm,
        running_speed_hz=res.running_speed_hz,
        iso_zone=res.iso_zone,
        time_domain=res.time_domain.__dict__,
        dominant_peaks=[p.__dict__ for p in res.dominant_peaks],
        suspected_faults=res.suspected_faults,
        maintenance_recommendation=res.maintenance_recommendation
    )


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Turbomachinery Predictive Maintenance & Vibration Triage</title>
        <style>
            :root {
                --bg: #0b1120;
                --card: #1e293b;
                --text: #f8fafc;
                --accent: #38bdf8;
                --zone-a: #10b981;
                --zone-b: #3b82f6;
                --zone-c: #f59e0b;
                --zone-d: #ef4444;
                --border: #334155;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: var(--bg); color: var(--text); padding: 24px; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
            .header h1 { font-size: 20px; font-weight: 600; }
            .badge { background: #0284c7; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 360px 1fr; gap: 24px; }
            .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .card h2 { font-size: 13px; text-transform: uppercase; color: #94a3b8; margin-bottom: 16px; }
            .btn { width: 100%; background: #2563eb; color: white; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 8px; }
            .btn:hover { background: #1d4ed8; }
            .btn-accent { background: #0891b2; }
            .btn-accent:hover { background: #0e7490; }
            .metric-box { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; font-size: 13px; }
            .metric-label { color: #94a3b8; }
            .metric-val { font-weight: bold; }
            .zone-badge { display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            .ZONE_A { background: rgba(16, 185, 129, 0.2); color: var(--zone-a); border: 1px solid var(--zone-a); }
            .ZONE_B { background: rgba(59, 130, 246, 0.2); color: var(--zone-b); border: 1px solid var(--zone-b); }
            .ZONE_C { background: rgba(245, 158, 11, 0.2); color: var(--zone-c); border: 1px solid var(--zone-c); }
            .ZONE_D { background: rgba(239, 68, 68, 0.2); color: var(--zone-d); border: 1px solid var(--zone-d); }
            table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }
            th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
            th { color: #94a3b8; }
            .fault-tag { display: inline-block; background: #334155; padding: 3px 8px; border-radius: 4px; margin: 2px; font-size: 12px; }
            .rec-box { background: #0f172a; border-left: 4px solid var(--accent); padding: 14px; border-radius: 4px; margin-top: 14px; font-size: 13px; line-height: 1.5; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Turbomachinery Vibration & Predictive Maintenance Engine</h1>
                <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Continuous ISO 10816-3 Severity Triage & FFT Harmonics Demodulator</p>
            </div>
            <span class="badge">ISO 10816-3 Class II/III Standard</span>
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <h2>Live Sensor Ingestion</h2>
                    <button class="btn btn-accent" onclick="loadAndDiagnose('healthy_baseline')">Centrifugal Compressor (Healthy)</button>
                    <button class="btn btn-accent" onclick="loadAndDiagnose('rotor_unbalance')">Turbine Rotor (Dynamic Unbalance)</button>
                    <button class="btn btn-accent" onclick="loadAndDiagnose('bearing_defect_trip')">Crude Export Pump (Critical Trip)</button>
                </div>

                <div class="card">
                    <h2>ISO 10816-3 Severity Triage</h2>
                    <div class="metric-box">
                        <span class="metric-label">Machine Tag:</span>
                        <span id="statMachineId" class="metric-val">--</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Operating Speed:</span>
                        <span id="statRpm" class="metric-val">-- RPM</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">ISO Severity Zone:</span>
                        <span id="statZone" class="zone-badge ZONE_A">STANDBY</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">RMS Velocity:</span>
                        <span id="statRms" class="metric-val">-- mm/s</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Crest Factor / Kurtosis:</span>
                        <span id="statKurt" class="metric-val">-- / --</span>
                    </div>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2>Spectral Harmonics & Diagnosed Fault Signatures</h2>
                    <div id="faultsContainer" style="margin-bottom: 16px;">
                        <span style="color: #64748b; font-size: 13px;">Select an operating asset to run frequency decomposition...</span>
                    </div>

                    <h2 style="margin-top: 16px;">Dominant FFT Spectral Peaks</h2>
                    <table id="peaksTable">
                        <thead>
                            <tr>
                                <th>Order</th>
                                <th>Frequency (Hz)</th>
                                <th>Peak Amplitude (g)</th>
                                <th>Physical Correlation</th>
                            </tr>
                        </thead>
                        <tbody id="peaksBody"></tbody>
                    </table>

                    <h2 style="margin-top: 24px;">Condition-Based Maintenance Action</h2>
                    <div id="recContainer" class="rec-box">
                        Engine awaiting telemetry input.
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function loadAndDiagnose(sampleName) {
                const res = await fetch(`/sample/${sampleName}`);
                const telemetry = await res.json();

                const diagRes = await fetch('/api/v1/diagnose', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        machine_id: telemetry.machine_id,
                        running_speed_rpm: telemetry.rpm,
                        sampling_rate_hz: telemetry.sampling_rate_hz,
                        signal_g: telemetry.signal_g
                    })
                });
                const data = await diagRes.json();

                document.getElementById('statMachineId').innerText = data.machine_id;
                document.getElementById('statRpm').innerText = `${data.running_speed_rpm} RPM (${data.running_speed_hz} Hz)`;
                
                const zEl = document.getElementById('statZone');
                zEl.innerText = data.iso_zone.replace('_', ' ');
                zEl.className = 'zone-badge ' + data.iso_zone;

                document.getElementById('statRms').innerText = `${data.time_domain.rms_velocity_mms} mm/s`;
                document.getElementById('statKurt').innerText = `${data.time_domain.crest_factor} / ${data.time_domain.kurtosis}`;

                const fContainer = document.getElementById('faultsContainer');
                fContainer.innerHTML = '';
                data.suspected_faults.forEach(f => {
                    const tag = document.createElement('span');
                    tag.className = 'fault-tag';
                    tag.innerText = f;
                    fContainer.appendChild(tag);
                });

                const tbody = document.getElementById('peaksBody');
                tbody.innerHTML = '';
                data.dominant_peaks.forEach(p => {
                    const tr = document.createElement('tr');
                    let corr = "Harmonic / Broadband";
                    if (Math.abs(p.order - 1.0) <= 0.05) corr = "1X RPM Fundamental (Unbalance)";
                    else if (Math.abs(p.order - 2.0) <= 0.05) corr = "2X RPM Harmonic (Misalignment)";
                    else if (p.frequency_hz > 500) corr = "High-Frequency Resonance / Impacting";
                    
                    tr.innerHTML = `
                        <td><strong>${p.order}X</strong></td>
                        <td>${p.frequency_hz} Hz</td>
                        <td>${p.amplitude_g} g</td>
                        <td style="color: #38bdf8;">${corr}</td>
                    `;
                    tbody.appendChild(tr);
                });

                document.getElementById('recContainer').innerText = data.maintenance_recommendation;
            }
        </script>
    </body>
    </html>
    """
