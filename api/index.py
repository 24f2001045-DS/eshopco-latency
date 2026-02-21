import json
import os
import statistics
import math
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "telemetry.json")

with open(DATA_FILE, "r") as f:
    raw = json.load(f)

# If JSON is wrapped inside a key like "data" or "telemetry"
if isinstance(raw, dict):
    DATA = raw.get("data") or raw.get("telemetry") or list(raw.values())[0]
else:
    DATA = raw

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}


@app.post("/")
async def handler(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    response_data = []

    for region in regions:
        region_data = [r for r in DATA if r.get("region") == region]

        if not region_data:
            continue

        latencies = [r.get("latency_ms", 0) for r in region_data]
        uptimes = [r.get("uptime", 0) for r in region_data]

        avg_latency = statistics.mean(latencies)

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        index_95 = max(math.ceil(0.95 * n) - 1, 0)
        p95_latency = latencies_sorted[index_95]

        avg_uptime = statistics.mean(uptimes)
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


@app.options("/")
async def options():
    response = JSONResponse({})
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response