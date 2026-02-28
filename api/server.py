from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import SecureInferPipeline

app = FastAPI(
    title="SecureInfer API",
    description="On-device AI threat detection — zero data egress",
    version="1.0.0"
)
_pipeline = None

@app.on_event("startup")
async def startup():
    global _pipeline
    _pipeline = SecureInferPipeline()

class LogEntry(BaseModel):
    destination_port:       Optional[float] = 0
    flow_duration:          Optional[float] = 0
    total_fwd_packets:      Optional[float] = 0
    total_backward_packets: Optional[float] = 0
    packet_length_mean:     Optional[float] = 0
    flow_bytes_per_s:       Optional[float] = 0
    fwd_packet_length_mean: Optional[float] = 0
    bwd_packet_length_mean: Optional[float] = 0

@app.post("/analyze")
def analyze(log: LogEntry):
    return _pipeline.analyze({
        "Destination Port":       log.destination_port,
        "Flow Duration":          log.flow_duration,
        "Total Fwd Packets":      log.total_fwd_packets,
        "Total Backward Packets": log.total_backward_packets,
        "Packet Length Mean":     log.packet_length_mean,
        "Flow Bytes/s":           log.flow_bytes_per_s,
        "Fwd Packet Length Mean": log.fwd_packet_length_mean,
        "Bwd Packet Length Mean": log.bwd_packet_length_mean,
    })

@app.get("/health")
def health():
    return {"status":"ok","egress":"zero","version":"1.0.0"}
