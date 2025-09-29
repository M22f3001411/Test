from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from typing import List
import os

app = FastAPI()

# Enable CORS for all origins (POST only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data once at startup with absolute path fix
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_FILE, "r") as f:
    data = json.load(f)

class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/analytics")
async def get_latency_metrics(payload: MetricsRequest):
    try:
        print("Incoming payload:", payload.dict())

        results = {}

        for region in payload.regions:
            region_data = [entry for entry in data if entry.get("region") == region]

            if not region_data:
                results[region] = {
                    "avg_latency": None,
                    "p95_latency": None,
                    "avg_uptime": None,
                    "breaches": None
                }
                continue

            latencies = [entry.get("latency_ms") for entry in region_data if "latency_ms" in entry]
            latencies = [l for l in latencies if l is not None]

            uptimes = [entry.get("uptime", 1.0) for entry in region_data]

            breaches = sum(1 for l in latencies if l > payload.threshold_ms)

            results[region] = {
                "avg_latency": round(np.mean(latencies), 2) if latencies else None,
                "p95_latency": round(np.percentile(latencies, 95), 2) if latencies else None,
                "avg_uptime": round(np.mean(uptimes), 4) if uptimes else None,
                "breaches": breaches
            }

        return results

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

