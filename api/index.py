import json
import os
import math
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# ---------- Load telemetry safely ----------
DATA = []

try:
    CURRENT_DIR = os.path.dirname(__file__)
    DATA_FILE = os.path.join(CURRENT_DIR, "..", "telemetry.json")

    with open(DATA_FILE, "r") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        DATA = raw
    elif isinstance(raw, dict):
        for key in ["data", "telemetry", "records", "items"]:
            if key in raw and isinstance(raw[key], list):
                DATA = raw[key]
                break
        else:
            DATA = next((v for v in raw.values() if isinstance(v, list)), [])
except Exception as e:
    print("Telemetry load error:", str(e))
    DATA = []


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS,PATCH,DELETE,POST,PUT",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


@app.post("/latency")
async def handler(request: Request):
    body = await request.json()

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

        latencies = []
        uptimes = []

        for r in region_data:
            if "latency_ms" in r:
                latencies.append(float(r["latency_ms"]))
            if "uptime" in r:
                uptimes.append(float(r["uptime"]))

        if not latencies or not uptimes:
            continue

        avg_latency = sum(latencies) / len(latencies)
        avg_uptime = sum(uptimes) / len(uptimes)

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

    return JSONResponse(response_data)

    for key, value in CORS_HEADERS.items():
        response.headers[key] = value

    return response