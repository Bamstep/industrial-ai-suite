import io
import base64
import tempfile
from pathlib import Path
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pipeline_vision.detector import PipelineCorrosionDetector
from pipeline_vision.video_processor import PipelineVideoInspector
from pipeline_vision.api.schemas import InspectionResponse, DefectClusterResponse

app = FastAPI(
    title="Pipeline Vision Integrity Inspector",
    description="Automated NDT computer vision and continuous crawler chainage inspection engine",
    version="0.2.0"
)

detector = PipelineCorrosionDetector()
video_inspector = PipelineVideoInspector()


@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "pipeline-vision-inspector", "version": "0.2.0"}


@app.get("/sample/{filename}")
def get_sample_file(filename: str):
    p = Path("sample_data") / filename
    if not p.exists():
        # Fallback check relative to package dir
        p = Path("pipeline-vision-inspector/sample_data") / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Sample asset not found")
    return FileResponse(p)


@app.post("/api/v1/inspect", response_model=InspectionResponse)
async def inspect_pipe_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file format.")

    result = detector.analyze(image)
    clusters_payload = [
        DefectClusterResponse(
            defect_id=c.defect_id,
            centroid=c.centroid,
            bounding_box=c.bounding_box,
            area_pixels=c.area_pixels,
            severity=c.severity,
            estimated_depth_score=c.estimated_depth_score,
        )
        for c in result.defect_clusters
    ]

    return InspectionResponse(
        total_surface_pixels=result.total_surface_pixels,
        corrosion_percentage=result.corrosion_percentage,
        integrity_status=result.integrity_status,
        clusters_detected=len(clusters_payload),
        defect_clusters=clusters_payload,
    )


@app.post("/api/v1/inspect/visualize")
async def inspect_and_visualize(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image format.")

    result = detector.analyze(image)
    _, buffer = cv2.imencode(".jpg", result.annotated_image)
    jpg_as_text = base64.b64encode(buffer).decode("utf-8")

    return {
        "integrity_status": result.integrity_status,
        "corrosion_percentage": result.corrosion_percentage,
        "clusters_detected": len(result.defect_clusters),
        "clusters": [
            {
                "id": c.defect_id,
                "severity": c.severity,
                "area_px": c.area_pixels,
                "depth_score": c.estimated_depth_score,
            }
            for c in result.defect_clusters
        ],
        "image_base64": f"data:image/jpeg;base64,{jpg_as_text}",
    }


@app.post("/api/v1/inspect/video")
async def inspect_crawler_video(file: UploadFile = File(...)):
    # Write uploaded stream to temporary mp4 file
    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        summary = video_inspector.inspect_video(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    # Encode top 4 representative anomaly keyframes to base64
    keyframes_payload = []
    # Pick evenly spaced keyframes from detected anomalies
    sample_indices = np.linspace(0, max(0, len(summary.anomalies) - 1), min(4, len(summary.anomalies)), dtype=int)
    for idx in sample_indices:
        if not summary.anomalies:
            break
        a = summary.anomalies[idx]
        _, buffer = cv2.imencode(".jpg", a.keyframe_bgr)
        keyframes_payload.append({
            "event_id": a.event_id,
            "chainage_meters": a.chainage_meters,
            "timestamp_sec": a.timestamp_sec,
            "severity": a.severity,
            "corrosion_percentage": a.corrosion_percentage,
            "image_base64": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}",
        })

    return {
        "total_distance_m": summary.total_distance_inspected_m,
        "duration_sec": summary.duration_sec,
        "total_frames": summary.total_frames,
        "worst_severity": summary.worst_severity,
        "anomalies_logged": len(summary.anomalies),
        "keyframes": keyframes_payload,
        "anomaly_log": [
            {
                "id": a.event_id,
                "kp_chainage_m": a.chainage_meters,
                "time_sec": a.timestamp_sec,
                "severity": a.severity,
                "coverage_pct": a.corrosion_percentage,
            }
            for a in summary.anomalies
        ],
    }


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Oil & Gas Pipeline Integrity & Continuous Crawler Inspector</title>
        <style>
            :root {
                --bg: #0f172a;
                --card: #1e293b;
                --text: #f8fafc;
                --accent: #38bdf8;
                --danger: #ef4444;
                --warning: #f59e0b;
                --success: #10b981;
                --border: #334155;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background-color: var(--bg); color: var(--text); padding: 24px; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
            .header h1 { font-size: 20px; font-weight: 600; }
            .badge { background: #0284c7; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 360px 1fr; gap: 24px; }
            .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .card h2 { font-size: 14px; text-transform: uppercase; color: #94a3b8; margin-bottom: 16px; }
            .btn { width: 100%; background: #2563eb; color: white; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 10px; }
            .btn:hover { background: #1d4ed8; }
            .btn-accent { background: #0891b2; }
            .btn-accent:hover { background: #0e7490; }
            .btn-outline { background: transparent; border: 1px solid var(--border); color: #cbd5e1; }
            .btn-outline:hover { background: #334155; }
            .metric-box { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; }
            .metric-label { color: #94a3b8; font-size: 13px; }
            .metric-val { font-weight: bold; }
            .status-badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
            .status-REPAIR_REQUIRED { background: rgba(239, 68, 68, 0.2); color: var(--danger); border: 1px solid var(--danger); }
            .status-MONITOR { background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); }
            .status-ACCEPTABLE { background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid var(--success); }
            .viewport { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 420px; background: #020617; border-radius: 6px; border: 1px dashed var(--border); overflow: hidden; }
            .viewport img { max-width: 100%; height: auto; }
            .keyframe-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
            .keyframe-card { background: #020617; border: 1px solid var(--border); border-radius: 6px; padding: 8px; }
            .keyframe-card img { width: 100%; border-radius: 4px; }
            .keyframe-tag { font-size: 11px; color: #94a3b8; margin-top: 4px; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 12px; }
            th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
            th { color: #94a3b8; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Oil & Gas Pipeline Integrity & Continuous Crawler Inspector</h1>
                <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Automated NDT Video Feed Ingestion, Odometer Chainage (KP) & ASME B31G Severity Triage</p>
            </div>
            <span class="badge">API 570 / ASME B31G Standard</span>
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <h2>Input Source Selection</h2>
                    <input type="file" id="videoInput" accept="video/mp4" style="display: none;" onchange="handleVideoUpload(event)">
                    <button class="btn btn-accent" onclick="document.getElementById('videoInput').click()">Upload Crawler Video (.mp4)</button>
                    <button class="btn btn-accent" onclick="loadSampleVideo()">Run Sample Crawler Run (5s Stream)</button>

                    <div style="margin-top: 16px; border-top: 1px solid var(--border); padding-top: 12px;">
                        <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
                        <button class="btn btn-outline" onclick="document.getElementById('imageInput').click()">Upload Still Frame</button>
                        <button class="btn btn-outline" onclick="loadSampleImage('pipe_moderate_corrosion.jpg')">Sample: Rust Bloom</button>
                        <button class="btn btn-outline" onclick="loadSampleImage('pipe_severe_pitting.jpg')">Sample: Severe Pitting</button>
                    </div>
                </div>

                <div class="card">
                    <h2>Inspection Telemetry</h2>
                    <div class="metric-box">
                        <span class="metric-label">Integrity Status:</span>
                        <span id="statStatus" class="status-badge status-ACCEPTABLE">STANDBY</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Distance Inspected:</span>
                        <span id="statDistance" class="metric-val">0.000 m</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Anomalies Logged:</span>
                        <span id="statAnomalies" class="metric-val">0</span>
                    </div>

                    <table id="anomalyTable" style="display: none;">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Chainage (KP)</th>
                                <th>Severity</th>
                                <th>Coverage</th>
                            </tr>
                        </thead>
                        <tbody id="anomalyTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2 id="mainViewportTitle">Live Inspection Stream / Defect Overlay</h2>
                    <div class="viewport" id="viewportContainer">
                        <p style="color: #64748b;" id="placeholderText">Upload video or select a sample to begin crawler log processing...</p>
                        <img id="resultImage" style="display: none;" alt="Pipeline Inspection Overlay">
                    </div>

                    <div id="keyframeSection" style="display: none;">
                        <h2 style="margin-top: 20px; font-size: 13px; text-transform: uppercase; color: #94a3b8;">Critical Anomaly Keyframes (Recorded Along Chainage)</h2>
                        <div class="keyframe-grid" id="keyframeGrid"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function loadSampleImage(filename) {
                const res = await fetch('/sample/' + filename);
                const blob = await res.blob();
                analyzeSingleImage(blob);
            }

            function handleImageUpload(e) {
                if (e.target.files[0]) analyzeSingleImage(e.target.files[0]);
            }

            async function analyzeSingleImage(blob) {
                const formData = new FormData();
                formData.append('file', blob, 'frame.jpg');

                document.getElementById('placeholderText').innerText = "Analyzing frame via OpenCV CLAHE & color segmentation...";
                document.getElementById('placeholderText').style.display = "block";
                document.getElementById('resultImage').style.display = "none";
                document.getElementById('keyframeSection').style.display = "none";

                const res = await fetch('/api/v1/inspect/visualize', { method: 'POST', body: formData });
                const data = await res.json();

                document.getElementById('placeholderText').style.display = "none";
                const img = document.getElementById('resultImage');
                img.src = data.image_base64;
                img.style.display = "block";

                updateStatus(data.integrity_status, "Single Frame", data.clusters_detected);
            }

            async function loadSampleVideo() {
                const res = await fetch('/sample/crawler_run_sample.mp4');
                const blob = await res.blob();
                analyzeVideoFile(blob);
            }

            function handleVideoUpload(e) {
                if (e.target.files[0]) analyzeVideoFile(e.target.files[0]);
            }

            async function analyzeVideoFile(blob) {
                const formData = new FormData();
                formData.append('file', blob, 'crawler_run.mp4');

                document.getElementById('placeholderText').innerText = "Processing crawler video stream & tracking chainage (KP)...";
                document.getElementById('placeholderText').style.display = "block";
                document.getElementById('resultImage').style.display = "none";

                const res = await fetch('/api/v1/inspect/video', { method: 'POST', body: formData });
                const data = await res.json();

                document.getElementById('placeholderText').style.display = "none";
                updateStatus(data.worst_severity, `${data.total_distance_m.toFixed(3)} m`, data.anomalies_logged);

                // Populate Anomaly Log Table
                const tbody = document.getElementById('anomalyTableBody');
                tbody.innerHTML = '';
                if (data.anomaly_log.length > 0) {
                    document.getElementById('anomalyTable').style.display = 'table';
                    data.anomaly_log.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>#${item.id}</td>
                            <td>KP ${item.kp_chainage_m.toFixed(3)} m</td>
                            <td style="color: ${item.severity === 'REPAIR_REQUIRED' ? '#ef4444' : '#f59e0b'}; font-weight: bold;">${item.severity}</td>
                            <td>${item.coverage_pct}%</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }

                // Render Keyframe Snapshots
                const kfGrid = document.getElementById('keyframeGrid');
                kfGrid.innerHTML = '';
                if (data.keyframes && data.keyframes.length > 0) {
                    document.getElementById('keyframeSection').style.display = 'block';
                    data.keyframes.forEach(kf => {
                        const card = document.createElement('div');
                        card.className = 'keyframe-card';
                        card.innerHTML = `
                            <img src="${kf.image_base64}" alt="Anomaly Keyframe">
                            <div class="keyframe-tag">
                                <span>KP ${kf.chainage_meters.toFixed(3)} m (${kf.timestamp_sec}s)</span>
                                <span style="color: ${kf.severity === 'REPAIR_REQUIRED' ? '#ef4444' : '#f59e0b'}; font-weight: bold;">${kf.severity}</span>
                            </div>
                        `;
                        kfGrid.appendChild(card);
                    });
                }
            }

            function updateStatus(status, distanceStr, anomaliesCount) {
                const sEl = document.getElementById('statStatus');
                sEl.innerText = status.replace('_', ' ');
                sEl.className = 'status-badge status-' + status;
                document.getElementById('statDistance').innerText = distanceStr;
                document.getElementById('statAnomalies').innerText = anomaliesCount;
            }
        </script>
    </body>
    </html>
    """
