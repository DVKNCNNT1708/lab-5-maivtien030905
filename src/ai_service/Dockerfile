FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# Tạo file requirements.txt tạm thời nếu chưa có để tránh lỗi build
RUN echo "fastapi\nuvicorn" > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m aiuser && chown -R aiuser:aiuser /app
USER aiuser
COPY . .
EXPOSE 9000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]