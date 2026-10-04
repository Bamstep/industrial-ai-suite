import io
import base64
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pipeline_vision.detector import PipelineCorrosionDetector
from pipeline_vision.api.schemas import InspectionResponse, DefectClusterResponse

app = FastAPI(
    title="Pipeline Vision Integrity Inspector",
    description="Automated AI-assisted corrosion and defect analysis for oil & gas infrastructure",
    version="0.1.0"
)

detector = PipelineCorrosionDetector()


@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "pipeline-vision-inspector"}


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

    # Encode annotated image to JPEG base64
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


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Oil & Gas Pipeline Integrity Inspector</title>
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
            .header h1 { font-size: 20px; font-weight: 600; letter-spacing: -0.5px; }
            .badge { background: #0284c7; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 340px 1fr; gap: 24px; }
            .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
            .card h2 { font-size: 14px; text-transform: uppercase; color: #94a3b8; margin-bottom: 16px; letter-spacing: 0.5px; }
            .btn { width: 100%; background: #2563eb; color: white; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 12px; }
            .btn:hover { background: #1d4ed8; }
            .btn-outline { background: transparent; border: 1px solid var(--border); color: #cbd5e1; margin-top: 8px; }
            .btn-outline:hover { background: #334155; }
            .metric-box { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155; }
            .metric-label { color: #94a3b8; font-size: 14px; }
            .metric-val { font-weight: bold; }
            .status-badge { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 13px; text-transform: uppercase; }
            .status-REPAIR_REQUIRED { background: rgba(239, 68, 68, 0.2); color: var(--danger); border: 1px solid var(--danger); }
            .status-MONITOR { background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); }
            .status-ACCEPTABLE { background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid var(--success); }
            .viewport { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 480px; background: #020617; border-radius: 6px; border: 1px dashed var(--border); overflow: hidden; }
            .viewport img { max-width: 100%; height: auto; border-radius: 4px; }
            table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }
            th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
            th { color: #94a3b8; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Oil & Gas Pipeline Defect & Corrosion Inspector</h1>
                <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Automated NDT Computer Vision Engine & ASME B31G Severity Triage</p>
            </div>
            <span class="badge">API 570 / ASME B31G Standard</span>
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <h2>Input Inspection Feed</h2>
                    <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="handleFileSelected(event)">
                    <button class="btn" onclick="document.getElementById('fileInput').click()">Upload Borescope / Crawler Frame</button>
                    <button class="btn btn-outline" onclick="loadSample('pipe_moderate_corrosion.jpg')">Load Sample: Rust Bloom</button>
                    <button class="btn btn-outline" onclick="loadSample('pipe_severe_pitting.jpg')">Load Sample: Severe Pitting</button>
                    <button class="btn btn-outline" onclick="loadSample('pipe_clean.jpg')">Load Sample: Baseline Clean Pipe</button>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <h2>Integrity Scorecard</h2>
                    <div class="metric-box">
                        <span class="metric-label">Status:</span>
                        <span id="statStatus" class="status-badge status-ACCEPTABLE">STANDBY</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Corrosion Coverage:</span>
                        <span id="statCoverage" class="metric-val">0.0%</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Defect Clusters:</span>
                        <span id="statClusters" class="metric-val">0</span>
                    </div>

                    <table id="clusterTable" style="display: none;">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Severity</th>
                                <th>Area (px)</th>
                                <th>Depth Score</th>
                            </tr>
                        </thead>
                        <tbody id="clusterTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>Borescope Computer Vision Overlay</h2>
                <div class="viewport" id="viewportContainer">
                    <p style="color: #64748b;" id="placeholderText">Upload an image or select a sample above to run automated defect segmentation</p>
                    <img id="resultImage" style="display: none;" alt="Pipeline Inspection Overlay">
                </div>
            </div>
        </div>

        <script>
            async function uploadAndAnalyze(blob) {
                const formData = new FormData();
                formData.append('file', blob, 'sample.jpg');

                document.getElementById('placeholderText').innerText = "Processing through OpenCV and CLAHE filters...";
                document.getElementById('placeholderText').style.display = "block";
                document.getElementById('resultImage').style.display = "none";

                const response = await fetch('/api/v1/inspect/visualize', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    alert("Analysis failed.");
                    return;
                }

                const data = await response.json();
                document.getElementById('placeholderText').style.display = "none";
                const img = document.getElementById('resultImage');
                img.src = data.image_base64;
                img.style.display = "block";

                const statusEl = document.getElementById('statStatus');
                statusEl.innerText = data.integrity_status.replace('_', ' ');
                statusEl.className = 'status-badge status-' + data.integrity_status;

                document.getElementById('statCoverage').innerText = data.corrosion_percentage + '%';
                document.getElementById('statClusters').innerText = data.clusters_detected;

                const tbody = document.getElementById('clusterTableBody');
                tbody.innerHTML = '';
                if (data.clusters.length > 0) {
                    document.getElementById('clusterTable').style.display = 'table';
                    data.clusters.forEach(c => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>#${c.id}</td>
                            <td style="color: ${c.severity === 'CRITICAL' ? '#ef4444' : c.severity === 'MODERATE' ? '#f59e0b' : '#38bdf8'}; font-weight: bold;">${c.severity}</td>
                            <td>${c.area_px}</td>
                            <td>${c.depth_score}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    document.getElementById('clusterTable').style.display = 'none';
                }
            }

            function handleFileSelected(event) {
                const file = event.target.files[0];
                if (file) uploadAndAnalyze(file);
            }

            async function loadSample(filename) {
                // Fetch the sample from static folder or generate on the fly
                const res = await fetch('/sample/' + filename);
                const blob = await res.blob();
                uploadAndAnalyze(blob);
            }
        </script>
    </body>
    </html>
    """
from fastapi.responses import FileResponse
from pathlib import Path

@app.get("/sample/{filename}")
def get_sample_image(filename: str):
    p = Path("sample_data") / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(p)
