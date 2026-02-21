import json
import os
import math
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

@app.middleware("http")
async def add_cors(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.options("/{path:path}")
async def options_handler():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "q-vercel-latency.json")

with open(DATA_PATH) as f:
    telemetry = json.load(f)

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