from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Industrial AI Suite - Master Gateway",
    description="Unified API gateway and operator portal for all 4 industrial modules.",
    version="1.0.0"
)

HTML_PORTAL = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Industrial AI Suite - Operations Control</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-8 font-sans">
  <header class="max-w-6xl mx-auto border-b border-slate-800 pb-6 mb-8 flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
        <span class="inline-block w-4 h-4 bg-emerald-500 rounded-full animate-pulse"></span>
        Industrial AI Suite
      </h1>
      <p class="text-slate-400 text-sm mt-1">Autonomous Kinematics, Vision Metrology & Turbomachinery PdM</p>
    </div>
    <span class="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs font-mono text-emerald-400">
      v1.0.0 Monorepo Operational
    </span>
  </header>

  <main class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- Robotics Twin -->
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition">
      <div>
        <div class="flex justify-between items-start mb-4">
          <span class="text-xs uppercase font-bold tracking-wider px-2 py-1 rounded bg-blue-950 text-blue-400 border border-blue-800">Port 8000</span>
          <span class="text-xs text-slate-500 font-mono">FastAPI + MuJoCo</span>
        </div>
        <h2 class="text-xl font-bold mb-2">Robotics Digital Twin</h2>
        <p class="text-slate-400 text-sm mb-4">6-DOF UR5 kinematics, quintic polynomial path planning, obstacle repulsion, and visual servoing HUD.</p>
      </div>
      <div class="flex gap-2">
        <a href="http://localhost:8000" target="_blank" class="flex-1 bg-blue-600 hover:bg-blue-500 text-center py-2 rounded text-sm font-semibold text-white">Dashboard</a>
        <a href="http://localhost:8000/docs" target="_blank" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300">Swagger</a>
      </div>
    </div>

    <!-- Pipeline Vision Inspector -->
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition">
      <div>
        <div class="flex justify-between items-start mb-4">
          <span class="text-xs uppercase font-bold tracking-wider px-2 py-1 rounded bg-amber-950 text-amber-400 border border-amber-800">Port 8001</span>
          <span class="text-xs text-slate-500 font-mono">FastAPI + OpenCV</span>
        </div>
        <h2 class="text-xl font-bold mb-2">NDT Pipeline Inspector</h2>
        <p class="text-slate-400 text-sm mb-4">Autonomous crawler video telemetry, CLAHE corrosion segmentation, chainage (KP) tracking, and ASME B31G reports.</p>
      </div>
      <div class="flex gap-2">
        <a href="http://localhost:8001" target="_blank" class="flex-1 bg-amber-600 hover:bg-amber-500 text-center py-2 rounded text-sm font-semibold text-white">Dashboard</a>
        <a href="http://localhost:8001/docs" target="_blank" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300">Swagger</a>
      </div>
    </div>

    <!-- Turbomachinery PdM -->
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition">
      <div>
        <div class="flex justify-between items-start mb-4">
          <span class="text-xs uppercase font-bold tracking-wider px-2 py-1 rounded bg-purple-950 text-purple-400 border border-purple-800">Port 8002</span>
          <span class="text-xs text-slate-500 font-mono">FastAPI + SciPy</span>
        </div>
        <h2 class="text-xl font-bold mb-2">Turbomachinery PdM</h2>
        <p class="text-slate-400 text-sm mb-4">ISO 10816-3 condition monitoring, frequency-domain integration, spectral order harmonics, and kurtosis defect triage.</p>
      </div>
      <div class="flex gap-2">
        <a href="http://localhost:8002" target="_blank" class="flex-1 bg-purple-600 hover:bg-purple-500 text-center py-2 rounded text-sm font-semibold text-white">Dashboard</a>
        <a href="http://localhost:8002/docs" target="_blank" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300">Swagger</a>
      </div>
    </div>
  </main>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PORTAL

@app.get("/health")
def health():
    return {"status": "online", "service": "gateway"}
