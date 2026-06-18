"""
Mock AI Vision Service — for local testing before Session 6

Run: python mock_services/mock_ai_vision.py
Listen: http://localhost:9000
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timezone

app = FastAPI(
    title="Mock AI Vision Service",
    version="1.0.0",
    description="Mock service for testing Core Business event processing"
)

class PredictRequest(BaseModel):
    event_id: str
    event_type: str
    source: str
    payload: Dict[str, Any]
    timestamp: str = None

class DetectedObject(BaseModel):
    object_type: str
    confidence: float

class PredictResponse(BaseModel):
    analysis_id: str
    objects: List[DetectedObject]
    timestamp: str

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "mock-ai-vision",
        "version": "1.0.0"
    }

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Mock prediction endpoint
    
    Returns detected objects from a camera frame.
    In production, would run ML models.
    """
    
    # Mock logic: detect person + motion
    objects = [
        DetectedObject(object_type="person", confidence=0.98),
        DetectedObject(object_type="motion", confidence=0.95)
    ]
    
    return PredictResponse(
        analysis_id=f"ANA-{request.event_id}",
        objects=objects,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
