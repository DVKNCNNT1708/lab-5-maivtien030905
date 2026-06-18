"""
Mock Access Gate Service — for local testing before Session 6

Run: python mock_services/mock_access_gate.py
Listen: http://localhost:8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(
    title="Mock Access Gate Service",
    version="1.0.0",
    description="Mock service for testing Core Business policy evaluation"
)

class AuthorizeRequest(BaseModel):
    subject_id: str
    action: str
    context: dict = {}

class AuthorizeResponse(BaseModel):
    authorized: bool
    clearance: int
    gate_id: str
    timestamp: str

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "mock-access-gate",
        "version": "1.0.0"
    }

@app.post("/authorize", response_model=AuthorizeResponse)
def authorize(request: AuthorizeRequest):
    """
    Mock authorization endpoint
    
    Always returns authorized=True for testing.
    In production, would check policies, audit logs, etc.
    """
    
    # Mock logic: everyone is authorized
    return AuthorizeResponse(
        authorized=True,
        clearance=3,
        gate_id="GATE-MOCK-01",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
