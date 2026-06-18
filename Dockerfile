FROM python:3.10-slim

# Tạo thư mục làm việc
WORKDIR /app

# Cài đặt curl để phục vụ HEALTHCHECK
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tạo non-root user và thay đổi quyền sở hữu
RUN useradd -m appuser && chown -R appuser:appuser /app

# Đổi sang user non-root
USER appuser

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose port
EXPOSE 8000

# Lệnh khởi chạy ứng dụng
CMD ["uvicorn", "src.core_business.main:app", "--host", "0.0.0.0", "--port", "8000"]