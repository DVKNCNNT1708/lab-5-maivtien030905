# Core Business Service — Integration Contracts

**Service:** Core Business (B6)  
**Version:** v0.1.0-team-core  
**Date:** 2026-06-18

---

## 1. Overview

Core Business xử lý nghiệp vụ trung tâm, tích hợp với 6 service khác qua 2 loại protocol:
- **REST sync**: AI Vision, Access Gate (gọi đồng bộ)
- **MQTT async**: IoT Ingestion, Camera Stream, Notification, Analytics (bất đồng bộ qua queue)

---

## 2. Outbound Contracts (Core Business gọi service khác)

### 2.1 AI Vision — REST Sync

**Mục đích:** Lấy kết quả phân tích ảnh / detect từ AI Vision khi có event.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | REST HTTP |
| **Method** | POST |
| **Endpoint** | `/predict` |
| **Port** | 9000 |
| **URL** | `http://<AI_VISION_HOST>:9000/predict` |
| **Timeout** | 5 giây |

**Request Body:**
```json
{
  "event_id": "EVT-20260618-0001",
  "event_type": "motion_detected",
  "source": "camera-01",
  "payload": {
    "confidence": 0.95,
    "region": "entrance",
    "timestamp": "2026-06-18T08:30:00+07:00"
  }
}
```

**Response (Success 200):**
```json
{
  "objects": ["person", "backpack"],
  "confidence": [0.98, 0.85],
  "analysis_id": "ANA-001"
}
```

**Response (Timeout/Error):**
- Core Business xử lý gracefully, không treo
- Log warning, tiếp tục xử lý event mà không action AI result

---

### 2.2 Access Gate — REST Sync

**Mục đích:** Kiểm tra quyền / log quetch khi có policy request.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | REST HTTP |
| **Method** | POST |
| **Endpoint** | `/authorize` |
| **Port** | 8001 |
| **URL** | `http://<ACCESS_GATE_HOST>:8001/authorize` |
| **Timeout** | 5 giây |

**Request Body:**
```json
{
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "context": {
    "location": "building-a",
    "clearance_level": 3,
    "timestamp": "2026-06-18T08:30:00+07:00"
  }
}
```

**Response (Success 200):**
```json
{
  "authorized": true,
  "clearance": 3,
  "gate_id": "GATE-A01",
  "timestamp": "2026-06-18T08:30:01+07:00"
}
```

**Response (Timeout/Error):**
- Policy decision = "pending" nếu Access Gate timeout
- Log error, thông báo admin

---

### 2.3 Notification — MQTT Async

**Mục đích:** Trigger gửi alert đa kênh (email, SMS, push) khi có alert event.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | MQTT |
| **Topic** | `smart-campus/actions/notifications` |
| **QoS** | 1 (at-least-once) |
| **Broker** | Configured in `.env` (`MQTT_BROKER`, `MQTT_PORT`) |

**Publish Payload:**
```json
{
  "alert_id": "ALR-20260618-0001",
  "alert_type": "anomaly_detected",
  "priority": "high",
  "message": "Anomaly detected in entrance camera",
  "channels": ["email", "sms", "push"],
  "recipients": ["admin@campus.local"],
  "timestamp": "2026-06-18T08:30:00+07:00"
}
```

**Notes:**
- Fire-and-forget: Core Business publish rồi không chờ response
- Nếu MQTT broker down, log warning, tiếp tục
- Notification team subscribe topic này để nhận alert

---

### 2.4 Analytics — MQTT Async

**Mục đích:** Feed event alert / policy decision cho KPI aggregate.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | MQTT |
| **Topic** | `smart-campus/actions/analytics` |
| **QoS** | 1 (at-least-once) |
| **Broker** | Configured in `.env` |

**Publish Payload:**
```json
{
  "timestamp": "2026-06-18T08:30:00+07:00",
  "event_id": "EVT-20260618-0001",
  "event_type": "anomaly_detected",
  "policy_id": "POL-20260618-0001",
  "decision": "approve",
  "actions": ["ai_vision_analysis_completed", "notification_sent"],
  "metadata": {
    "source": "camera-01",
    "alert_priority": "high"
  }
}
```

**Notes:**
- Analytics team subscribe để lưu vào data warehouse
- Dùng cho KPI, reporting, trend analysis

---

## 3. Inbound Contracts (Service khác gọi Core Business)

### 3.1 IoT Ingestion → Core Business — MQTT Async

**Mục đích:** IoT Ingestion publish sensor data mới, Core Business subscribe để process.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | MQTT |
| **Topic** | `smart-campus/events/iot` |
| **QoS** | 1 (at-least-once) |
| **Frequency** | Real-time (event-driven) |

**Subscribe Payload (IoT publishes):**
```json
{
  "reading_id": "R-20260618-0001",
  "device_id": "ESP32-LAB-A01",
  "metric": "temperature",
  "value": 31.5,
  "unit": "celsius",
  "timestamp": "2026-06-18T08:30:00+07:00",
  "analysis": ["person", "backpack"]
}
```

**Core Business Processing:**
- Subscribe topic `smart-campus/events/iot`
- Parse payload
- Nếu temperature >= 70 → trigger Notification alert
- Log vào Analytics

---

### 3.2 Camera Stream → Core Business — MQTT Async

**Mục đích:** Camera Stream publish camera events, Core Business subscribe để process.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | MQTT |
| **Topic** | `smart-campus/events/camera` |
| **QoS** | 1 (at-least-once) |
| **Frequency** | Real-time (event-driven) |

**Subscribe Payload (Camera publishes):**
```json
{
  "event_id": "CAM-20260618-0001",
  "source": "camera-entrance",
  "event_type": "motion_detected",
  "confidence": 0.95,
  "region": "entrance",
  "timestamp": "2026-06-18T08:30:00+07:00",
  "frame_url": "s3://campus-footage/2026-06-18/entrance/..."
}
```

**Core Business Processing:**
- Subscribe topic `smart-campus/events/camera`
- Call AI Vision để analyze
- Nếu anomaly detect → trigger alert
- Publish result đến Analytics

---

### 3.3 Access Gate → Core Business — REST Sync

**Mục đích:** Access Gate check policy realtime trước khi cấp quyền.

| Trường | Giá trị |
|--------|--------|
| **Protocol** | REST HTTP |
| **Method** | POST |
| **Endpoint** | `/policy/check` (hoặc `/policy/evaluate`) |
| **Port** | 8000 |
| **Timeout** | 3 giây (critical, realtime) |

**Request Body (Access Gate gửi):**
```json
{
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "context": {
    "location": "building-a",
    "time": "2026-06-18T08:30:00+07:00",
    "previous_access": true
  }
}
```

**Response (Core Business trả):**
```json
{
  "policy_id": "POL-20260618-0001",
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "decision": "approve",
  "reason": "User clearance level sufficient",
  "evaluated_at": "2026-06-18T08:30:01+07:00"
}
```

**Response (Timeout/Error):**
- Status 503 Service Unavailable
- Access Gate có fallback policy (e.g., deny or allow based on local cache)

---

## 4. API Endpoints cho Inbound REST

### 4.1 GET /health

**Mục đích:** Health check từ monitoring/orchestration.

**Response:**
```json
{
  "status": "ok",
  "service": "core-business",
  "version": "v0.1.0-team-core"
}
```

---

### 4.2 POST /policy/evaluate (hay /policy/check)

**Mục đích:** Evaluate policy decision (dùng bởi Access Gate).

**Request:**
```json
{
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "context": {
    "location": "building-a",
    "clearance_level": 3
  },
  "timestamp": "2026-06-18T08:30:00+07:00"
}
```

**Response:**
```json
{
  "policy_id": "POL-20260618-0001",
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "decision": "approve",
  "reason": "Policy approved",
  "evaluated_at": "2026-06-18T08:30:01+07:00"
}
```

---

### 4.3 POST /event/process

**Mục đích:** Process event (nội bộ hoặc từ webhook).

**Request:**
```json
{
  "event_id": "EVT-20260618-0001",
  "event_type": "motion_detected",
  "source": "camera-01",
  "payload": {
    "confidence": 0.95,
    "region": "entrance"
  },
  "timestamp": "2026-06-18T08:30:00+07:00"
}
```

**Response:**
```json
{
  "event_id": "EVT-20260618-0001",
  "processed": true,
  "decision": "approve",
  "actions_taken": [
    "ai_vision_analysis_completed",
    "notification_sent",
    "analytics_logged"
  ],
  "processed_at": "2026-06-18T08:30:02+07:00"
}
```

---

### 4.4 GET /policy

**Mục đích:** Lấy danh sách tất cả policies (admin view).

**Query Params:**
- `subject_id` (optional): filter theo subject
- `limit` (optional, default=10): max records

**Response:**
```json
{
  "policies": [
    {
      "policy_id": "POL-20260618-0001",
      "subject_id": "user-001",
      "action": "enter-restricted-area",
      "decision": "approve",
      "created_at": "2026-06-18T08:30:01+07:00"
    }
  ]
}
```

---

### 4.5 GET /events

**Mục đích:** Lấy danh sách tất cả events đã process.

**Query Params:**
- `event_type` (optional): filter theo type
- `limit` (optional, default=10): max records

**Response:**
```json
{
  "events": [
    {
      "event_id": "EVT-20260618-0001",
      "event_type": "motion_detected",
      "source": "camera-01",
      "decision": "approve",
      "actions_taken": ["ai_vision_analysis_completed"],
      "created_at": "2026-06-18T08:30:02+07:00"
    }
  ]
}
```

---

## 5. Authentication

Tất cả REST endpoints sử dụng Bearer token:

```
Authorization: Bearer <AUTH_TOKEN>
```

Giá trị `AUTH_TOKEN` lấy từ `.env` (default: `local-dev-token`).

MQTT: dùng username/password từ `.env` (`MQTT_USERNAME`, `MQTT_PASSWORD`).

---

## 6. Error Handling

### 6.1 REST Errors

| Status | Scenario | Handling |
|--------|----------|----------|
| 200 | Success | Normal response |
| 400 | Invalid request | Validate payload |
| 401 | Unauthorized | Check Auth header |
| 422 | Validation error | Check schema |
| 503 | Service dependency fail | Return 503, log error |
| 504 | Timeout | Fallback decision, log error |

### 6.2 MQTT Errors

- **Broker down**: Log warning, retry publish every 30s
- **Publish timeout**: Log error, continue processing
- **Subscribe fail**: Auto-reconnect with exponential backoff

---

## 7. Testing Checklist

Trước Session 6, kiểm tra:

- [ ] `/health` trả 200
- [ ] POST `/policy/evaluate` trả decision đúng
- [ ] POST `/event/process` gọi AI Vision thành công
- [ ] POST `/event/process` timeout không treo
- [ ] MQTT subscribe sensor events từ IoT
- [ ] MQTT publish alerts đến Notification
- [ ] Database `policies` và `events` có dữ liệu
- [ ] Logs chi tiết mỗi integration point

---

## 8. Sample Integration Flow

```
1. Access Gate gọi Core Business:
   POST /policy/evaluate (REST sync, 3s timeout)
   ↓
2. Core Business gọi AI Vision:
   POST /predict (REST sync, 5s timeout)
   ↓
3. Nếu anomaly, publish Notification:
   MQTT publish smart-campus/actions/notifications
   ↓
4. Publish Analytics:
   MQTT publish smart-campus/actions/analytics
   ↓
5. Lưu result vào DB:
   INSERT INTO policies / events
```

---

## 9. Contract Versioning

- **Current:** v0.1.0-team-core (2026-06-18)
- **Next:** v0.2.0-team-core (post-Session 6 feedback)

Khi update contract, cập nhật header và notify các team đối tác.
