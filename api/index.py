import json
import os
import statistics
import math
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# ---------- Load telemetry safely ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "telemetry.json")

with open(DATA_FILE, "r") as f:
    raw = json.load(f)

# Ensure DATA is always a list
if isinstance(raw, list):
    DATA = raw
elif isinstance(raw, dict):
    for key in ["data", "telemetry", "records", "items"]:
        if key in raw and isinstance(raw[key], list):
            DATA = raw[key]
            break
    else:
        # fallback to first list value found
        DATA = next((v for v in raw.values() if isinstance(v, list)), [])
else:
    DATA = []

# ---------- CORS ----------
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS,PATCH,DELETE,POST,PUT",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

# ---------- Endpoint ----------
@app.post("/")
async def handler(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    response_data = []

    for region in regions:
        region_data = [
            r for r in DATA
            if isinstance(r, dict) and r.get("region") == region
        ]

        if not region_data:
            continue

        # Safely extract numeric values
        latencies = []
        uptimes = []

        for r in region_data:
            try:
                latencies.append(float(r.get("latency_ms", 0)))
            except (TypeError, ValueError):
                pass

            try:
                uptimes.append(float(r.get("uptime", 0)))
            except (TypeError, ValueError):
                pass

        if not latencies or not uptimes:
            continue

        # Mean
        avg_latency = statistics.mean(latencies)
        avg_uptime = statistics.mean(uptimes)

        # Proper 95th percentile
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        index_95 = max(math.ceil(0.95 * n) - 1, 0)
        p95_latency = latencies_sorted[index_95]

        breaches = sum(1 for l in latencies if l > threshold)

        response_data.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })

    response = JSONResponse(response_data)

    for key, value in CORS_HEADERS.items():
        response.headers[key] = value

    return response