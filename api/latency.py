import json
import os
import statistics
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "telemetry.json")

with open(DATA_FILE, "r") as f:
    DATA = json.load(f)

# ✅ Corrected CORS headers
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

    result = {}

    for region in regions:
        region_data = [r for r in DATA if r["region"] == region]

        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime"] for r in region_data]

        avg_latency = statistics.mean(latencies)

        # safer p95 calculation
        latencies_sorted = sorted(latencies)
        index_95 = int(0.95 * len(latencies_sorted)) - 1
        p95_latency = latencies_sorted[max(index_95, 0)]

        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for l in latencies if l > threshold)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    response = JSONResponse(result)

    # ✅ Attach CORS headers
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value

    return response


@app.options("/")
async def options():
    response = JSONResponse({})
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response