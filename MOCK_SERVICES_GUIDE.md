# Mock Services Guide — Local Testing

Trước Session 6, bạn có thể test Core Business **mà không cần** Access Gate hay AI Vision team chạy trên máy khác.

Hướng dẫn này giúp setup mock services trên cùng máy để test end-to-end.

---

## 1. Mock Access Gate Service

### Setup

Tạo file `mock_services/mock_access_gate.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Access Gate Service", version="1.0.0")

class AuthRequest(BaseModel):
    subject_id: str
    action: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-access-gate", "version": "1.0.0"}

@app.post("/authorize")
def authorize(request: AuthRequest):
    # Mock logic: always approve
    return {
        "authorized": True,
        "clearance": 3,
        "gate_id": "GATE-MOCK-01",
        "timestamp": "2026-06-18T08:30:01+07:00"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Run

```bash
python mock_services/mock_access_gate.py
# Listen on http://localhost:8001
```

### Test

```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/authorize \
  -H "Content-Type: application/json" \
  -d '{"subject_id":"user-001","action":"test"}'
```

---

## 2. Mock AI Vision Service

### Setup

Tạo file `mock_services/mock_ai_vision.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Mock AI Vision Service", version="1.0.0")

class PredictRequest(BaseModel):
    event_id: str
    event_type: str
    source: str
    payload: Dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-ai-vision", "version": "1.0.0"}

@app.post("/predict")
def predict(request: PredictRequest):
    # Mock logic: return detected objects
    return {
        "objects": ["person", "backpack"],
        "confidence": [0.98, 0.85],
        "analysis_id": f"ANA-{request.event_id}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

### Run

```bash
python mock_services/mock_ai_vision.py
# Listen on http://localhost:9000
```

### Test

```bash
curl http://localhost:9000/health
curl -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{"event_id":"EVT-001","event_type":"motion","source":"camera-01","payload":{"confidence":0.95}}'
```

---

## 3. Full Integration Test (Local)

### Step 1: Start all services

**Terminal 1 — Core Business:**
```bash
docker compose up -d --build
```

**Terminal 2 — Mock Access Gate:**
```bash
cd mock_services
python mock_access_gate.py
```

**Terminal 3 — Mock AI Vision:**
```bash
cd mock_services
python mock_ai_vision.py
```

### Step 2: Verify all health checks

```bash
curl http://localhost:8000/health  # Core Business
curl http://localhost:8001/health  # Mock Access Gate
curl http://localhost:9000/health  # Mock AI Vision
```

### Step 3: Test Policy Evaluation (calls Access Gate)

```bash
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "user-001",
    "action": "enter-restricted-area",
    "context": {"location": "building-a", "clearance_level": 3},
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'
```

**Expected Response:**
```json
{
  "policy_id": "POL-20260618-0001",
  "subject_id": "user-001",
  "decision": "approve",
  "reason": "Policy approved by default"
}
```

### Step 4: Test Event Processing (calls AI Vision)

```bash
curl -X POST http://localhost:8000/event/process \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT-20260618-0001",
    "event_type": "motion_detected",
    "source": "camera-01",
    "payload": {"confidence": 0.95, "region": "entrance"},
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'
```

**Expected Response:**
```json
{
  "event_id": "EVT-20260618-0001",
  "processed": true,
  "decision": "pending",
  "actions_taken": ["ai_vision_analysis_completed", "analytics_logged"],
  "processed_at": "2026-06-18T08:30:02+07:00"
}
```

### Step 5: Check database

```bash
docker exec -it lab05-db psql -U lab05_user -d lab05_db -c \
  "SELECT policy_id, decision FROM policies ORDER BY created_at DESC LIMIT 5;"

docker exec -it lab05-db psql -U lab05_user -d lab05_db -c \
  "SELECT event_id, event_type, decision FROM events ORDER BY created_at DESC LIMIT 5;"
```

### Step 6: Verify timeout handling

Kill mock Access Gate, rồi gọi lại `/policy/evaluate`:

```bash
# Terminal 2 (trong Python REPL): Ctrl+C

# Try policy evaluation again
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Expected:** Response timeout, nhưng Core Business log "access_gate timeout" → decision = "pending", không treo.

---

## 4. MQTT Local Testing

### Setup Mosquitto (if needed)

**Docker:**
```bash
docker run -d -p 1883:1883 -p 9001:9001 \
  --name mosquitto \
  eclipse-mosquitto
```

**or macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

### Test MQTT Subscribe (Core Business receives events)

**Terminal 1 — Subscribe to IoT events:**
```bash
mosquitto_sub -h localhost -p 1883 -t "smart-campus/events/iot" -v
```

**Terminal 2 — Publish from IoT mock:**
```bash
mosquitto_pub -h localhost -p 1883 -t "smart-campus/events/iot" -m '{
  "reading_id": "R-20260618-0001",
  "device_id": "ESP32-01",
  "metric": "temperature",
  "value": 31.5,
  "timestamp": "2026-06-18T08:30:00+07:00"
}'
```

**Output in Terminal 1:**
```
smart-campus/events/iot {"reading_id":"R-20260618-0001",...}
```

---

## 5. Postman Collection — Mock Integration

Trong Postman, gunakan collection `postman/collections/iot_collection.postman_collection.json`:

1. Set environment variables:
   - `baseUrl` = `http://localhost:8000`
   - `authToken` = `your_dummy_token_here`

2. Run requests in order:
   - Health check
   - Evaluate policy (calls mock Access Gate)
   - Process event (calls mock AI Vision)
   - Get policies
   - Get events

3. Verify responses match CONTRACT.md

---

## 6. Full Test Checklist

- [ ] Docker Compose up, 3 containers running
- [ ] Core Business `/health` → 200
- [ ] Mock Access Gate `/health` → 200
- [ ] Mock AI Vision `/health` → 200
- [ ] POST `/policy/evaluate` → decision approve/reject
- [ ] POST `/event/process` → processed true, actions_taken filled
- [ ] Database policies table có data
- [ ] Database events table có data
- [ ] Kill mock Access Gate, `/policy/evaluate` vẫn return 200 (graceful)
- [ ] MQTT publish/subscribe test thành công
- [ ] Postman collection all tests pass

---

## 7. Screenshot Evidence

Capture để lưu vào `reports/`:

- `01-docker-compose-ps.png` — `docker compose ps` output
- `02-health-checks.png` — Curl /health 3 services
- `03-policy-evaluate-success.png` — Policy evaluation response
- `04-event-process-success.png` — Event processing response
- `05-database-records.png` — Policies and events tables
- `06-timeout-handling.png` — Policy eval khi Access Gate down
- `07-mqtt-publish-subscribe.png` — MQTT test

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8001/9000 already in use | Change port in mock_services code |
| Mock services crash | Check Python syntax, install FastAPI/Uvicorn |
| Database empty | Check if process event succeeded |
| MQTT not connecting | Verify mosquitto running, broker IP correct |

---

Sau khi test local thành công, bạn sẽ tự tin integration với team khác ở Session 6!
