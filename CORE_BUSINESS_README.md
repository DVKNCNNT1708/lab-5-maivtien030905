# Core Business Service — Lab 05 Summary

**Nhóm:** Core Business (B6)  
**Vai trò:** Xây dựng dịch vụ xử lý nghiệp vụ trung tâm  
**Status:** Ready for Session 6 Integration

---

## 📋 Tài liệu Lab 05

| File | Nội dung |
|------|---------|
| **CONTRACT.md** | Định nghĩa REST/MQTT contracts với tất cả service khác |
| **INTEGRATION_GUIDE.md** | Hướng dẫn test từng integration point |
| **SESSION_6_CHECKLIST.md** | Checklist chuẩn bị cho Buổi 6 |
| **docker-compose.yml** | 3 services: db (PostgreSQL), ai-service (mock), core-business (main) |
| **Dockerfile** | Build image cho Core Business |
| **.env.example** | Cấu hình mẫu (lưu secret vào .env thật) |
| **src/core_business/main.py** | API chính với timeout handling |
| **postman/collections/** | Collection test tất cả endpoints |
| **reports/** | Folder lưu screenshot/log cho Session 6 |

---

## 🎯 Key Features Implemented

### ✅ Core Business API Endpoints

1. **GET /health** — Health check (public)
   - Response: `{"status":"ok", "service":"core-business", "version":"..."}`

2. **POST /policy/evaluate** — Đánh giá chính sách (gọi Access Gate)
   - Input: `subject_id`, `action`, `context`, `timestamp`
   - Output: `policy_id`, `decision` (approve/reject/pending), `reason`
   - Timeout: 5 giây
   - DB: Lưu vào `policies` table

3. **POST /event/process** — Xử lý sự kiện (gọi AI Vision, Notification, Analytics)
   - Input: `event_id`, `event_type`, `source`, `payload`
   - Output: `event_id`, `processed`, `decision`, `actions_taken`
   - Timeout: 5 giây mỗi external call
   - DB: Lưu vào `events` table

4. **GET /policy** — Lấy danh sách chính sách (admin view)
   - Query param: `subject_id` (optional), `limit` (optional, default=10)

5. **GET /events** — Lấy danh sách sự kiện (admin view)
   - Query param: `event_type` (optional), `limit` (optional, default=10)

### ✅ External Service Integration

**REST Sync (Sync calls):**
- **AI Vision** (`/predict`, port 9000): Phân tích ảnh/motion detection
- **Access Gate** (`/authorize`, port 8001): Kiểm tra quyền truy cập

**MQTT Async (Fire-and-forget):**
- **Notification**: Subscribe `smart-campus/actions/notifications` để gửi alert
- **Analytics**: Subscribe `smart-campus/actions/analytics` để log KPI data
- **IoT Ingestion**: Subscribe `smart-campus/events/iot` để nhận sensor events
- **Camera Stream**: Subscribe `smart-campus/events/camera` để nhận camera events

### ✅ Database Schema

```sql
-- Policies: lưu quyết định chính sách
CREATE TABLE policies (
  policy_id TEXT PRIMARY KEY,
  subject_id TEXT,
  action TEXT,
  decision TEXT,
  reason TEXT,
  created_at TEXT,
  metadata JSONB
);

-- Events: lưu sự kiện đã xử lý
CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT,
  source TEXT,
  payload JSONB,
  decision TEXT,
  actions JSONB,
  created_at TEXT
);
```

### ✅ Error Handling

- **Timeout (5s)**: Service phụ thuộc chậm/lỗi → Core Business không treo, trả response 503/pending
- **Graceful degradation**: Nếu AI Vision lỗi, vẫn process event, chỉ bỏ action AI
- **Logging**: Tất cả error được log chi tiết vào Docker logs

### ✅ Security

- **Authentication**: Bearer token (từ `.env` AUTH_TOKEN)
- **Authorization**: All endpoints require token header
- **No secrets committed**: `.env` có trong `.gitignore`, chỉ commit `.env.example`

---

## 🚀 Chạy Lab 05 (Local)

### Step 1: Setup

```bash
git clone <repo>
cd lab-5-maivtien030905
cp .env.example .env  # chỉnh sửa AUTH_TOKEN nếu cần
```

### Step 2: Build & Run

```bash
docker compose up -d --build

# Verify
docker compose ps
```

### Step 3: Test Health

```bash
curl http://localhost:8000/health
```

### Step 4: Test Core Endpoints

```bash
# Policy Evaluation
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Authorization: Bearer your_dummy_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "user-001",
    "action": "enter-restricted-area",
    "context": {"location": "building-a", "clearance_level": 3},
    "timestamp": "2026-06-18T08:30:00+07:00"
  }'

# Event Processing
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

# Get policies
curl -X GET http://localhost:8000/policy \
  -H "Authorization: Bearer your_dummy_token_here"

# Get events
curl -X GET http://localhost:8000/events \
  -H "Authorization: Bearer your_dummy_token_here"
```

### Step 5: Cleanup

```bash
docker compose down
```

---

## 📊 Buổi 6 Integration Mục tiêu

| Tích hợp | Type | Status | Test |
|---------|------|--------|------|
| Core Business `/health` | REST | ✅ | `curl http://localhost:8000/health` |
| Policy Evaluate | REST | ✅ | Postman collection |
| Event Process | REST | ✅ | Postman collection |
| Timeout Handling | REST | ✅ | Giảm external service URL |
| IoT Events (inbound) | MQTT | ⏳ | Đợi IoT Ingestion team |
| Camera Events (inbound) | MQTT | ⏳ | Đợi Camera Stream team |
| Notifications (outbound) | MQTT | ⏳ | Đợi Notification team |
| Analytics (outbound) | MQTT | ⏳ | Đợi Analytics team |
| Access Gate integration | REST | ⏳ | Đợi Access Gate team |
| AI Vision integration | REST | ✅ | Mock endpoint ready |

---

## 🔗 Contract Quick Reference

### Outbound REST (Core Business calls)

```
POST http://<ACCESS_GATE_HOST>:8001/authorize
  → decision approve/reject/pending

POST http://<AI_VISION_HOST>:9000/predict
  → analysis objects, confidence
```

### Inbound REST (nhóm khác calls)

```
POST http://<CORE_BUSINESS_HOST>:8000/policy/evaluate
  → policy_id, decision, reason

POST http://<CORE_BUSINESS_HOST>:8000/event/process
  → event_id, processed, decision, actions_taken
```

### MQTT Topics

```
Inbound:
  smart-campus/events/iot → Core Business (from IoT Ingestion)
  smart-campus/events/camera → Core Business (from Camera Stream)

Outbound:
  smart-campus/actions/notifications ← Core Business (to Notification)
  smart-campus/actions/analytics ← Core Business (to Analytics)
```

---

## 📝 Session 6 Timeline

| Thời gian | Task | Owner |
|-----------|------|-------|
| 0-10 min | Kết nối iPhone hotspot, lấy IP | Product admin |
| 10-20 min | Công bố IP tất cả nhóm | Tất cả nhóm |
| 20-30 min | Cập nhật `.env` với IP nhóm đối tác | Từng nhóm |
| 30-40 min | `docker compose up`, check health | Từng nhóm |
| 40-50 min | Test `/health` cross-team | Từng cặp nhóm |
| 50-60 min | Test endpoint tích hợp, lưu screenshot | Từng cặp nhóm |

---

## 🎓 Chứng chỉ Thành công (Session 6)

Nhóm được credit nếu:

✅ Core Business `/health` trả 200  
✅ Core Business có thể được gọi bởi nhóm khác qua hotspot IP  
✅ Core Business call được Access Gate → nhận response đúng  
✅ Core Business call được AI Vision → nhận response đúng  
✅ Nếu nhóm khác timeout → Core Business vẫn trả response (không treo)  
✅ Có minh chứng: log, screenshot, payload mẫu  
✅ Database có dữ liệu từ test  

---

## 📚 Tài liệu tham khảo

- [CONTRACT.md](CONTRACT.md) — Contract chi tiết
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) — Hướng dẫn test
- [SESSION_6_CHECKLIST.md](SESSION_6_CHECKLIST.md) — Checklist Buổi 6
- [RUN_COMPOSE.md](RUN_COMPOSE.md) — Chạy Docker Compose
- [checklists/readiness-checklist.md](checklists/readiness-checklist.md) — Readiness checklist

---

## 🆘 Support

Nếu gặp issue:

1. Đọc [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) mục "Common Issues"
2. Check `docker compose logs core-business`
3. Verify `.env` có đúng AUTH_TOKEN
4. Kiểm tra Firewall port 8000

---

## ✨ Điểm nhấn

> Core Business không phải chỉ một REST API. Nó là trung tâm điều phối:
> - Nhận policy request từ Access Gate (sync)
> - Nhận sensor data từ IoT (async via MQTT)
> - Nhận camera event từ Camera Stream (async via MQTT)
> - Đánh giá decision → gửi alert, analytics
> - Xử lý timeout gracefully (không treo)
> - Lưu audit trail vào DB

Khi intergration thành công, bạn sẽ thấy dòng dữ liệu chảy từ sensor → Core Business → Notification/Analytics — đó chính là Smart Campus Operations Platform!

---

**Chúc bạn thành công!** 🎉

Nếu có câu hỏi, xem [SESSION_6_CHECKLIST.md](SESSION_6_CHECKLIST.md) hoặc liên hệ giáo viên.
