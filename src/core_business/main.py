import http
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import Json
import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Đọc biến môi trường với giá trị mặc định
SERVICE_NAME = os.getenv("SERVICE_NAME", "core-business")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.5.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "lab05_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "lab05_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "lab05_db")
AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-service:9000")
ACCESS_GATE_URL = os.getenv("ACCESS_GATE_URL", "http://localhost:8001")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://localhost:8002")
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://localhost:8003")
DB_DSN = (
    f"dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD} "
    f"host={DB_HOST} port={DB_PORT}"
)


app = FastAPI(
    title="FIT4110 Lab 05 - Core Business Service",
    version=SERVICE_VERSION,
    description=(
        "Core Business Service xử lý nghiệp vụ trung tâm cho Smart Campus Operations Platform. "
        "Dịch vụ này tích hợp với AI Vision, Access Gate, Notification và Analytics."
    ),
)


class PolicyDecision(str, Enum):
    approve = "approve"
    reject = "reject"
    pending = "pending"


class EventType(str, Enum):
    motion_detected = "motion_detected"
    anomaly_detected = "anomaly_detected"
    access_request = "access_request"
    alert_triggered = "alert_triggered"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class PolicyEvaluationRequest(BaseModel):
    subject_id: str = Field(..., min_length=3, examples=["user-001"])
    action: str = Field(..., examples=["enter-restricted-area"])
    context: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: str = Field(..., examples=["2026-06-18T08:30:00+07:00"])


class PolicyEvaluationResponse(BaseModel):
    policy_id: str
    subject_id: str
    action: str
    decision: PolicyDecision
    reason: Optional[str] = None
    evaluated_at: str


class EventProcessRequest(BaseModel):
    event_id: str = Field(..., min_length=3, examples=["EVT-001"])
    event_type: EventType = Field(..., examples=["motion_detected"])
    source: str = Field(..., examples=["camera-01"])
    payload: Dict[str, Any]
    timestamp: str = Field(..., examples=["2026-06-18T08:30:00+07:00"])


class EventProcessResponse(BaseModel):
    event_id: str
    processed: bool
    decision: Optional[PolicyDecision] = None
    actions_taken: List[str]
    processed_at: str


POLICIES: List[Dict] = []
EVENTS: List[Dict] = []


def get_db_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(DB_DSN)


def init_database() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS policies (
                    policy_id TEXT PRIMARY KEY,
                    subject_id TEXT,
                    action TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    metadata JSONB
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload JSONB,
                    decision TEXT,
                    actions JSONB,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_database()


def save_policy_to_db(policy: Dict[str, Any]) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO policies (
                    policy_id,
                    subject_id,
                    action,
                    decision,
                    reason,
                    created_at,
                    metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    policy.get("policy_id"),
                    policy.get("subject_id"),
                    policy.get("action"),
                    policy.get("decision"),
                    policy.get("reason"),
                    policy.get("created_at"),
                    Json(policy.get("metadata")) if policy.get("metadata") else None,
                ),
            )
            conn.commit()


def save_event_to_db(event: Dict[str, Any]) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO events (
                    event_id,
                    event_type,
                    source,
                    payload,
                    decision,
                    actions,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.get("event_id"),
                    event.get("event_type"),
                    event.get("source"),
                    Json(event.get("payload")) if event.get("payload") else None,
                    event.get("decision"),
                    Json(event.get("actions")) if event.get("actions") else None,
                    event.get("created_at"),
                ),
            )
            conn.commit()


def call_ai_vision(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = requests.post(f"{AI_VISION_URL}/predict", json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def call_access_gate(subject_id: str, action: str) -> Optional[Dict[str, Any]]:
    try:
        payload = {"subject_id": subject_id, "action": action}
        response = requests.post(f"{ACCESS_GATE_URL}/authorize", json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def call_notification(alert_type: str, message: str) -> Optional[Dict[str, Any]]:
    try:
        payload = {"alert_type": alert_type, "message": message}
        response = requests.post(f"{NOTIFICATION_URL}/alert", json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def call_analytics(query: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    try:
        payload = {"query": query, "params": params or {}}
        response = requests.post(f"{ANALYTICS_URL}/report", json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


def get_http_status_text(status_code: int) -> str:
    try:
        return http.HTTPStatus(status_code).phrase
    except ValueError:
        return "HTTP Error"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        problem = build_problem(
            status_code=exc.status_code,
            title=get_http_status_text(exc.status_code),
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", get_http_status_text(exc.status_code))
    problem.setdefault("type", "about:blank")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title=get_http_status_text(status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Missing Authorization header",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )

    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_policy_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"POL-{today}-{len(POLICIES) + 1:04d}"


def next_event_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"EVT-{today}-{len(EVENTS) + 1:04d}"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )


@app.post(
    "/policy/evaluate",
    response_model=PolicyEvaluationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def evaluate_policy(payload: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
    """Evaluate business policy based on subject, action and context."""
    policy_id = next_policy_id()
    evaluated_at = now_iso()

    # Simple policy evaluation logic
    decision = PolicyDecision.approve
    reason = "Policy approved by default"

    # Call Access Gate to verify authorization
    gate_response = call_access_gate(payload.subject_id, payload.action)
    if gate_response and not gate_response.get("authorized", False):
        decision = PolicyDecision.reject
        reason = "Access Gate denied authorization"

    # Save to database
    policy_record = {
        "policy_id": policy_id,
        "subject_id": payload.subject_id,
        "action": payload.action,
        "decision": decision.value,
        "reason": reason,
        "created_at": evaluated_at,
        "metadata": {"gate_response": gate_response},
    }
    save_policy_to_db(policy_record)
    POLICIES.append(policy_record)

    return PolicyEvaluationResponse(
        policy_id=policy_id,
        subject_id=payload.subject_id,
        action=payload.action,
        decision=decision,
        reason=reason,
        evaluated_at=evaluated_at,
    )


@app.post(
    "/events",
    response_model=EventProcessResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def process_event(payload: EventProcessRequest) -> EventProcessResponse:
    """Process events from various sources and trigger appropriate actions."""
    event_id = payload.event_id if payload.event_id else next_event_id()
    processed_at = now_iso()
    actions_taken = []
    decision = PolicyDecision.pending

    # Process based on event type
    if payload.event_type == EventType.motion_detected:
        # Call AI Vision for analysis
        ai_response = call_ai_vision(payload.payload)
        if ai_response:
            actions_taken.append("ai_vision_analysis_completed")

    elif payload.event_type == EventType.anomaly_detected:
        # Trigger notification
        notification_response = call_notification(
            "anomaly_alert", f"Anomaly detected from {payload.source}"
        )
        if notification_response:
            actions_taken.append("notification_sent")
            decision = PolicyDecision.approve

    elif payload.event_type == EventType.access_request:
        # Evaluate access policy
        gate_response = call_access_gate(
            payload.payload.get("subject_id", ""), payload.payload.get("action", "")
        )
        if gate_response:
            actions_taken.append("access_gate_evaluated")
            decision = PolicyDecision.approve if gate_response.get("authorized") else PolicyDecision.reject

    # Call Analytics to feed data
    analytics_response = call_analytics("log_event", {"event_id": event_id, "type": payload.event_type.value})
    if analytics_response:
        actions_taken.append("analytics_logged")

    # Save to database
    event_record = {
        "event_id": event_id,
        "event_type": payload.event_type.value,
        "source": payload.source,
        "payload": payload.payload,
        "decision": decision.value,
        "actions": actions_taken,
        "created_at": processed_at,
    }
    save_event_to_db(event_record)
    EVENTS.append(event_record)

    return EventProcessResponse(
        event_id=event_id,
        processed=True,
        decision=decision,
        actions_taken=actions_taken,
        processed_at=processed_at,
    )


@app.get("/policy", dependencies=[Depends(verify_bearer_token)])
def get_policies() -> Dict[str, List[Dict]]:
    """Get all policies."""
    return {"policies": POLICIES}


@app.get("/events", dependencies=[Depends(verify_bearer_token)])
def get_events() -> Dict[str, List[Dict]]:
    """Get all events."""
    return {"events": EVENTS}
