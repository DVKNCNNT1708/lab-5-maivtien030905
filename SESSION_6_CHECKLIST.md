# Session 6 Preparation Checklist – Core Business Team

Buổi 6 sẽ tích hợp service Core Business với các nhóm khác qua iPhone hotspot. Hãy đảm bảo các điểm sau:

## 1. Lab 05 Chuẩn bị ở nhà (Bắt buộc)

- [ ] Máy demo đã clone repo và chạy thử ở nhà:
  ```bash
  git clone <repo>
  cd <repo>
  cp .env.example .env
  docker compose up -d --build
  docker compose ps  # tất cả container phải running
  curl http://localhost:8000/health  # phải return 200
  ```

- [ ] Docker build không lỗi, image đã lưu trên máy.
- [ ] PostgreSQL database khởi tạo bảng `policies` và `events` thành công.
- [ ] Đã test các endpoint Core Business:
  - `GET /health` → 200
  - `POST /policy/evaluate` → 200 với policy decision
  - `POST /event/process` → 200 với actions_taken
  - `GET /policy` → 200 với danh sách
  - `GET /events` → 200 với danh sách

## 2. Máy Demo Spec

- [ ] RAM tối thiểu 8GB, sạc đầy.
- [ ] Ổ trống tối thiểu 30GB.
- [ ] Wi-Fi adapter bắt được 2.4GHz (sẽ kết nối iPhone hotspot).
- [ ] Đã cài Docker, chạy được `docker compose`.
- [ ] Có sạc đi kèm để dùng cả buổi.

## 3. Contract tích hợp với các nhóm khác

Core Business (theo Dependency Map):
- **Consumer của**: AI Vision, Access Gate, Notification, Analytics
- **Provider cho**: IoT Ingestion, Camera Stream, Access Gate

### Cần chốt trước Buổi 6:

**Nhóm IoT Ingestion gọi Core Business:**
- [ ] Endpoint: `POST /policy/evaluate` 
- [ ] Port: `8000`
- [ ] Payload mẫu (đã chốt): ___________________________

**Nhóm Camera Stream gọi Core Business:**
- [ ] Endpoint: ___________________________
- [ ] Port: ___________________________
- [ ] Payload mẫu: ___________________________

**Nhóm Access Gate gọi Core Business:**
- [ ] Endpoint: ___________________________
- [ ] Port: ___________________________
- [ ] Payload mẫu: ___________________________

### Core Business gọi các nhóm:

**Core Business → AI Vision** (cho `/event/process`):
- [ ] Endpoint: `/predict` (mặc định, có thể khác?)
- [ ] Port: `9000` (mặc định)
- [ ] Yêu cầu: AI service phải expose `/health` và `/predict`

**Core Business → Access Gate** (cho `/policy/evaluate`):
- [ ] Endpoint: `/authorize` (mặc định, có thể khác?)
- [ ] Port: `8001` (mặc định)
- [ ] Yêu cầu: Access Gate phải expose `/health` và `/authorize`

**Core Business → Notification** (cho `/event/process`):
- [ ] Endpoint: `/alert` (mặc định, có thể khác?)
- [ ] Port: `8002` (mặc định)
- [ ] Yêu cầu: Notification phải expose `/health` và `/alert`

**Core Business → Analytics** (cho `/event/process`):
- [ ] Endpoint: `/report` (mặc định, có thể khác?)
- [ ] Port: `8003` (mặc định)
- [ ] Yêu cầu: Analytics phải expose `/health` và `/report`

## 4. Chuẩn bị Environment Variables

- [ ] `.env` có đầy đủ service URLs:
  ```
  APP_PORT=8000
  SERVICE_NAME=core-business
  SERVICE_VERSION=v0.1.0-team-core
  AUTH_TOKEN=your_dummy_token_here
  POSTGRES_USER=lab05_user
  POSTGRES_PASSWORD=lab05_password
  POSTGRES_DB=lab05_db
  DB_HOST=db
  DB_PORT=5432
  AI_VISION_URL=http://ai-service:9000      (ở nhà)
  ACCESS_GATE_URL=http://localhost:8001     (ở nhà - mock)
  NOTIFICATION_URL=http://localhost:8002    (ở nhà - mock)
  ANALYTICS_URL=http://localhost:8003       (ở nhà - mock)
  ```

- [ ] Khi Buổi 6 kết nối hotspot, sẽ cập nhật URLs của external services từ IP hotspot.

## 5. Networking chuẩn bị

- [ ] Dockerfile đảm bảo bind `0.0.0.0`:
  ```
  CMD ["uvicorn", "src.core_business.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
  ✅ Đã có

- [ ] docker-compose.yml expose port 8000:
  ```yaml
  ports:
    - "8000:8000"
  ```
  ✅ Đã có

- [ ] Windows Firewall cho phép port 8000 (inbound):
  - [ ] Nếu lỗi connection refused từ nhóm khác, check Windows Firewall
  - [ ] Lệnh kiểm tra: `netstat -ano | findstr :8000` (xem có process listen không)

## 6. Test Timeout Handling

- [ ] Core Business phải **KHÔNG TREO** khi service phụ thuộc lỗi:
  - [ ] Mỗi gọi external service có timeout 5 giây
  - [ ] Nếu timeout/error, trả response 200 nhưng `actions_taken` không bao gồm action đó
  - [ ] Kiểm tra code:
    ```python
    except requests.RequestException:
        return None
    ```
    ✅ Đã có

- [ ] Test simulation: tắt AI service, gọi `/event/process` → phải trả 200 không treo

## 7. Minh chứng cần lưu

Tạo folder `reports/` và lưu:

- [ ] `docker-compose-ps.png` - chụp `docker compose ps` output, tất cả container running
- [ ] `health-localhost.png` - chụp `curl http://localhost:8000/health` kết quả 200
- [ ] `policy-evaluate-test.png` - chụp request/response của `/policy/evaluate` với sample payload
- [ ] `event-process-test.png` - chụp request/response của `/event/process` với sample payload
- [ ] `logs-final.txt` - `docker compose logs` khi chạy test
- [ ] `session6-checklist.md` - checklist này khi đã hoàn thành, export dạng markdown

## 8. Lịch trình Buổi 6 (60 phút đầu)

| Thời gian | Việc | Status |
|---|---|:---:|
| 0-10 min | Kết nối iPhone hotspot, lấy IP (dải 172.20.10.x) | |
| 10-20 min | Cập nhật `.env` với IP của external services từ nhóm khác | |
| 20-30 min | `docker compose up -d --build` | |
| 30-40 min | Kiểm tra `GET /health` của nhóm mình | |
| 40-50 min | Test `GET /health` của nhóm khác (nếu REST) | |
| 50-60 min | Test endpoint tích hợp theo contract → lưu minh chứng | |

## 9. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `connection refused` | Service chưa chạy hoặc sai port | `docker compose ps`, `docker compose logs` |
| `timeout` | Sai IP, khác hotspot, firewall | Check IP hotspot, firewall port |
| `404 Not Found` | Sai path endpoint | Verify contract, kiểm tra URL |
| `curl: (7) Failed to connect` | Service tắt hoặc bind sai | Ensure `0.0.0.0`, check bind đúng không |
| Service "treo" khi gọi nhóm khác | Timeout chưa set | Đã có `timeout=5`, kiểm tra code |

## 10. Bảng IP dùng chung (điền khi Buổi 6)

| Nhóm | IP Hotspot | Port | Notes |
|---|---|---|---|
| team-core (mình) | `172.20.10.__` | 8000 | |
| team-iot | `172.20.10.__` | 8000 | |
| team-camera | `172.20.10.__` | 8000 | |
| team-gate | `172.20.10.__` | 8000 | |
| team-vision | `172.20.10.__` | 9000 | |
| team-analytics | `172.20.10.__` | 8000 | |
| team-notify | `172.20.10.__` | 8000 | |

## 11. Phiếu hẹn tích hợp (Mẫu)

Nhóm nào gọi Core Business, yêu cầu điền:

```
NHÓM GỌILÀ: _______________
ENDPOINT: POST /policy/evaluate
REQUEST MẪU:
{
  "subject_id": "user-001",
  "action": "enter-restricted-area",
  "timestamp": "2026-06-18T08:30:00+07:00"
}

RESPONSE MONG ĐỢI:
{
  "policy_id": "POL-...",
  "decision": "approve" | "reject" | "pending",
  "reason": "..."
}
```

## 12. Kết luận

Trước khi đến lớp:
1. ✅ Chạy được Docker Compose ở nhà
2. ✅ `/health` thành công
3. ✅ Chốt contract với nhóm đối tác
4. ✅ Có sample payload để test nhanh
5. ✅ Biết xử lý khi nhóm khác lỗi

Khi đến lớp:
1. Kết nối hotspot
2. Lấy IP của nhóm khác
3. Cập nhật `.env`
4. Chạy `docker compose up -d --build`
5. Test tích hợp theo contract
6. Lưu minh chứng

---

**Ghi chú cuối:**
- Không chạy thử ở nhà = rất khó kịp sửa trong 60 phút đầu Buổi 6.
- Chuẩn bị tốt ở nhà = lên lớp chỉ cần bật hotspot và verify tích hợp.
