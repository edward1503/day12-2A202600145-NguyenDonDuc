# hãy di chuyển tới branch MASTER
# 05-scaling-reliability/production/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Cài đặt dependencies
COPY 05-scaling-reliability/production/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code và utils
COPY 05-scaling-reliability/production/app.py .
COPY utils/ /app/utils/

# Môi trường
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Chạy app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
