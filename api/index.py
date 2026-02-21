import json
import os
import math
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ✅ Proper CORS (this fixes OPTIONS automatically)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Load telemetry ----------
DATA = []

try:
    DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "telemetry.json")
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        DATA = raw
    elif isinstance(raw, dict):
        DATA = next((v for v in raw.values() if isinstance(v, list)), [])
except Exception as e:
    print("Telemetry load error:", str(e))
    DATA = []

# ---------- Endpoint ----------
@app.post("/latency")
async def latency(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    result = []

    for region in regions:
        region_data = [r for r in DATA if r.get("region") == region]

        if not region_data:
            continue

        latencies = [float(r["latency_ms"]) for r in region_data if "latency_ms" in r]
        uptimes = [float(r["uptime"]) for r in region_data if "uptime" in r]

        if not latencies or not uptimes:
            continue

        avg_latency = sum(latencies) / len(latencies)
        avg_uptime = sum(uptimes) / len(uptimes)

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        p95 = latencies_sorted[max(math.ceil(0.95 * n) - 1, 0)]

        breaches = sum(1 for l in latencies if l > threshold)

        result.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })

    return JSONResponse(result)