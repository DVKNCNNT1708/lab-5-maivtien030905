# Readiness Checklist – Lab 05

Đây là danh sách kiểm tra (checklist) để đảm bảo stack Docker Compose của bạn đã sẵn sàng trước khi gửi bài. Hãy tick vào mỗi mục sau khi hoàn thành.

- [ ] **Database ready:** container DB đã chạy và phản hồi `pg_isready`. Kiểm tra bằng `docker exec -it fit4110-db-lab05 pg_isready -U $POSTGRES_USER`.
- [ ] **AI service ready:** container AI service trả về `200` cho endpoint `/health` và `/predict` hoạt động.
- [ ] **API ready:** container Core Business trả `200` cho `/health` và các endpoint `/policy/evaluate`, `/event/process` hoạt động.
- [ ] **Environment variables:** `.env` đã được thiết lập đúng (APP_PORT, POSTGRES_USER, AUTH_TOKEN, AI_VISION_URL, ACCESS_GATE_URL, NOTIFICATION_URL, ANALYTICS_URL). Không sử dụng secret thật; lưu secret vào `.env` cục bộ, commit `.env.example`.
- [ ] **Network & Ports:** mạng `team-internal` hoạt động; API gọi được AI và DB bằng hostname nội bộ; ports 8000 (API), 9000 (AI) và 5432 (DB) được map đúng.
- [ ] **Image tags:** bạn đã build image với tag `v0.1.0-team-core` và có thể push lên registry. Xác nhận rằng tag xuất hiện trong registry.

Ghi chú thêm những vấn đề gặp phải hoặc điều chỉnh tại đây:

```
- Mô tả…
```