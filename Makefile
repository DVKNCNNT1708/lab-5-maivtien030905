# Makefile hỗ trợ chạy Docker Compose nhanh chóng

.PHONY: compose-up compose-down logs test-compose

compose-up:
	@echo "Đang build và khởi động stack..."
	docker compose up -d --build

compose-down:
	@echo "Đang tắt và xóa stack..."
	docker compose down

logs:
	@echo "Đang theo dõi logs của hệ thống..."
	docker compose logs -f

test-compose:
	@echo "Đang chạy test Newman..."
	@mkdir -p reports
	npx newman run postman/collections/iot_collection.postman_collection.json -e postman/environments/FIT4110_lab05_local.postman_environment.json -r cli,htmlextra,junit --reporter-junit-export reports/newman-lab05-compose.xml --reporter-htmlextra-export reports/newman-lab05-compose.html