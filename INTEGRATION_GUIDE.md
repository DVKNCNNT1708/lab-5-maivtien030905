# Core Business — Integration Guide for Session 6

---

## Part 1: Setup trước Session 6

### 1.1 Clone repo và chuẩn bị

```bash
git clone <repo-core-business>
cd lab-5-maivtien030905
cp .env.example .env
```

### 1.2 Chạy Docker Compose

```bash
docker compose up -d --build
docker compose ps  # kiểm tra container đang chạy

# Output mong đợi:
# NAME                    STATUS
# lab05-db               Up 2 minutes (healthy)
# lab05-ai-service       Up 2 minutes (healthy)
# lab05-core-business    Up 2 minutes (healthy)
```

### 1.3 Kiểm tra /health

```bash
curl http://localhost:8000/health
```

**Output:**
```json
{
  "status": "ok",
  "service": "core-business",
  "version": "v0.1.0-team-core"
}
```

---

## Part 2: REST Integration Examples

### 2.1 Test Policy Evaluation (tính năng chính)

**Giả lập:** Access Gate gọi Core Business để check policy.

```bash
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "user-001",
    "action": "enter-restricted-area",
    "context": {
      "location": "building-a",
      "clearance_level": 3
    },
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'
```

**Expected Response:**
```json
{
  "policy_id": "POL-20260618-0001",
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "decision": "approve",
  "reason": "Policy approved by default",
  "evaluated_at": "2026-06-18T08:30:01+07:00"
}
```

---

### 2.2 Test Event Processing

**Giả lập:** Motion detection event từ camera.

```bash
curl -X POST http://localhost:8000/event/process \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT-20260618-0001",
    "event_type": "motion_detected",
    "source": "camera-01",
    "payload": {
      "confidence": 0.95,
      "region": "entrance"
    },
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'
```

**Expected Response:**
```json
{
  "event_id": "EVT-20260618-0001",
  "processed": true,
  "decision": "pending",
  "actions_taken": [
    "ai_vision_analysis_completed",
    "analytics_logged"
  ],
  "processed_at": "2026-06-18T08:30:02+07:00"
}
```

---

### 2.3 Get all policies

```bash
curl -X GET http://localhost:8000/policy \
  -H "Authorization: Bearer your_dummy_token_here"
```

**Output:**
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

### 2.4 Get all events

```bash
curl -X GET http://localhost:8000/events \
  -H "Authorization: Bearer your_dummy_token_here"
```

**Output:**
```json
{
  "events": [
    {
      "event_id": "EVT-20260618-0001",
      "event_type": "motion_detected",
      "source": "camera-01",
      "decision": "pending",
      "actions_taken": ["ai_vision_analysis_completed"],
      "created_at": "2026-06-18T08:30:02+07:00"
    }
  ]
}
```

---

## Part 3: MQTT Integration (Async)

MQTT dùng cho tích hợp **bất đồng bộ** với IoT Ingestion, Camera Stream, Notification, Analytics.

### 3.1 Setup MQTT Broker (Development)

Nếu máy không có MQTT broker, cài Mosquitto:

**Windows (via WSL/Docker):**
```bash
docker run -d -p 1883:1883 -p 9001:9001 eclipse-mosquitto
```

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

**Linux:**
```bash
sudo apt-get install mosquitto
sudo service mosquitto start
```

### 3.2 Subscribe to IoT Events (Core Business nhận từ IoT Ingestion)

```bash
mosquitto_sub -h localhost -p 1883 \
  -t "smart-campus/events/iot" -v
```

**Output (khi IoT Ingestion publish):**
```
smart-campus/events/iot {"reading_id":"R-20260618-0001","device_id":"ESP32-LAB-A01","metric":"temperature","value":31.5,"unit":"celsius","timestamp":"2026-06-18T08:30:00+07:00"}
```

### 3.3 Subscribe to Camera Events (Core Business nhận từ Camera Stream)

```bash
mosquitto_sub -h localhost -p 1883 \
  -t "smart-campus/events/camera" -v
```

**Output (khi Camera Stream publish):**
```
smart-campus/events/camera {"event_id":"CAM-20260618-0001","source":"camera-entrance","event_type":"motion_detected","confidence":0.95,"region":"entrance","timestamp":"2026-06-18T08:30:00+07:00"}
```

### 3.4 Publish Notification Alert (Core Business gửi đến Notification)

Simulate:
```bash
mosquitto_pub -h localhost -p 1883 \
  -t "smart-campus/actions/notifications" \
  -m '{
    "alert_id": "ALR-20260618-0001",
    "alert_type": "anomaly_detected",
    "priority": "high",
    "message": "Anomaly detected in entrance camera",
    "channels": ["email", "sms"],
    "recipients": ["admin@campus.local"],
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'
```

### 3.5 Publish Analytics Data (Core Business gửi đến Analytics)

Simulate:
```bash
mosquitto_pub -h localhost -p 1883 \
  -t "smart-campus/actions/analytics" \
  -m '{
    "timestamp": "2026-06-18T08:30:00+07:00",
    "event_id": "EVT-20260618-0001",
    "event_type": "anomaly_detected",
    "decision": "approve",
    "actions": ["ai_vision_analysis_completed", "notification_sent"]
  }'
```

---

## Part 4: Integration Testing (Session 6)

### 4.1 Pre-demo Checklist (ở nhà)

```bash
# 1. Docker stack running
docker compose ps

# 2. Health check nội bộ
curl http://localhost:8000/health

# 3. Test Policy evaluation
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{"subject_id":"user-001","action":"test",...}'

# 4. Check database
docker exec -it lab05-db psql -U lab05_user -d lab05_db -c "SELECT * FROM policies LIMIT 1;"
docker exec -it lab05-db psql -U lab05_user -d lab05_db -c "SELECT * FROM events LIMIT 1;"

# 5. View logs
docker compose logs core-business
```

### 4.2 Session 6 Integration Steps

**Lúc 0-10 phút:**
1. Bật iPhone hotspot (Product)
2. Kết nối máy demo vào hotspot
3. Lấy IP máy demo (ví dụ: `172.20.10.5`)

**Lúc 10-20 phút:**
1. Lấy IP của nhóm khác (ví dụ Access Gate ở `172.20.10.7`)
2. Ghi vào bảng IP chung

**Lúc 20-30 phút:**
1. Cập nhật `.env` trên máy demo:
   ```
   AI_VISION_URL=http://172.20.10.4:9000
   ACCESS_GATE_URL=http://172.20.10.7:8001
   MQTT_BROKER=172.20.10.1  (iPhone hotspot = gateway)
   ```
2. Restart Docker Compose:
   ```bash
   docker compose up -d
   ```

**Lúc 30-40 phút:**
1. Test `/health` của nhóm mình:
   ```bash
   curl http://localhost:8000/health
   ```
2. Test `/health` của nhóm khác qua hotspot:
   ```bash
   curl http://172.20.10.7:8000/health  # Access Gate
   ```

**Lúc 40-50 phút:**
1. Test Policy Evaluation (gọi Access Gate):
   ```bash
   curl -X POST http://localhost:8000/policy/evaluate \
     -H "Authorization: Bearer your_dummy_token_here" \
     -d '{...}'
   ```
   Kiểm tra nếu Access Gate khả dụng, decision = "approve"

2. Test Event Processing (nếu AI Vision khả dụng):
   ```bash
   curl -X POST http://localhost:8000/event/process \
     -d '{...}'
   ```

3. Test MQTT (nếu có Notification/Analytics):
   ```bash
   mosquitto_sub -h 172.20.10.1 -t "smart-campus/actions/notifications" -v
   ```

**Lúc 50-60 phút:**
1. Lưu screenshot tất cả test vào `reports/`
2. Chốt checklist

---

## Part 5: Common Issues & Solutions

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-----------|----------|
| `curl: (7) Failed to connect` | Service chưa chạy | `docker compose ps`, `docker compose logs` |
| `{"detail":"Unauthorized"}` | Thiếu `Authorization` header | Thêm `-H "Authorization: Bearer token"` |
| `504 Gateway Timeout` | Service phụ thuộc lỗi | Kiểm tra access gate, đảm bảo có timeout handling |
| MQTT publish không nhận | Broker down hoặc topic sai | `docker logs`, verify topic name |
| Firewall blocked | Windows firewall chặn | Mở inbound rule cho port 8000 |

---

## Part 6: Postman Collection

Sử dụng file `postman/collections/iot_collection.postman_collection.json` để test nhanh:

1. Mở Postman
2. Import collection
3. Set Environment: `baseUrl = http://localhost:8000` (ở nhà) hoặc `http://172.20.10.5:8000` (Session 6)
4. Set auth token trong Environment
5. Run requests

---

## Part 7: Demo Narrative

**Khi présent với giáo viên:**

> "Core Business service nhận event từ IoT và Camera qua MQTT, 
> kiểm tra policy với Access Gate qua REST, 
> trigger alert đến Notification team, 
> và publish KPI data đến Analytics team. 
> 
> Dữ liệu lưu vào PostgreSQL để audit trail. 
> Nếu service phụ thuộc lỗi (timeout), Core Business vẫn xử lý 
> gracefully và không treo."

Minh chứng:
1. Screenshot `docker compose ps` (containers running)
2. Screenshot `/health` return 200
3. Screenshot `/policy/evaluate` call với policy decision
4. Screenshot `/event/process` call khi AI Vision timeout → vẫn return 200 (xử lý gracefully)
5. Screenshot MQTT publish/subscribe (nếu có broker)
6. Screenshot logs (action_taken, timeout handling, DB insert)

---

## Part 8: Troubleshooting Template

Nếu integration fail, ghi lại:

```markdown
## Integration Issue: [nhóm_khác] → Core Business

**Timestamp:** 2026-06-18 10:30 AM

**What happened:**
- Gọi POST /policy/evaluate đến Core Business
- Response: [timeout / 500 / 503 / sai format]

**Expected:**
- HTTP 200 với policy decision

**Actual:**
[paste actual response]

**Debug info:**
- Core Business logs: [paste từ docker logs]
- Network: [có thể ping/curl được nhóm khác không?]
- Firewall: [port 8000 mở chưa?]
- Auth header: [Authorization header format đúng chưa?]

**Action taken:**
- ...

**Resolved:** Yes / No / Partial
```

---

Chúc bạn thành công với Session 6!
