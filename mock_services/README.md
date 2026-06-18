# Mock Services — Local Development

This folder contains mock implementations of external services for local testing.

## Quick Start

### 1. Install dependencies (if not already done)

```bash
pip install fastapi uvicorn pydantic
```

### 2. Run mock services in separate terminals

**Terminal 1 — Mock Access Gate (port 8001):**
```bash
python mock_access_gate.py
```

**Terminal 2 — Mock AI Vision (port 9000):**
```bash
python mock_ai_vision.py
```

### 3. Test with Core Business (run in separate terminal)

```bash
cd ..
docker compose up -d --build
```

### 4. Test integration

```bash
# Policy Evaluation (calls mock Access Gate)
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{"subject_id":"user-001","action":"enter","context":{},"timestamp":"2026-06-18T08:30:00+07:00"}'

# Event Processing (calls mock AI Vision)
curl -X POST http://localhost:8000/event/process \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"EVT-001","event_type":"motion_detected","source":"camera-01","payload":{"confidence":0.95},"timestamp":"2026-06-18T08:30:00+07:00"}'
```

## Services

### mock_access_gate.py (port 8001)

Simulates Access Gate service authorization endpoint.

- `GET /health` — Service health
- `POST /authorize` — Always returns `authorized: true`

### mock_ai_vision.py (port 9000)

Simulates AI Vision service prediction endpoint.

- `GET /health` — Service health
- `POST /predict` — Always returns detected objects (person, motion)

## Configuration

To change port or host, modify the `if __name__ == "__main__"` section:

```python
uvicorn.run(
    app,
    host="0.0.0.0",  # 0.0.0.0 = accessible from other machines
    port=8001,        # change this
    log_level="info"
)
```

## Notes

- Mock services always succeed (no error simulation)
- Useful for development/testing before real services available
- For production, replace with actual service implementations
- See [MOCK_SERVICES_GUIDE.md](../MOCK_SERVICES_GUIDE.md) for detailed examples
