# hãy di chuyển tới branch MASTER
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
# Use paths relative to project root
COPY 06-lab-complete/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code from Lab 6 folder
COPY 06-lab-complete/app/ /app/app/
COPY 06-lab-complete/static/ /app/static/

# Copy shared utils from root
COPY utils/ /app/utils/

RUN chown -R appuser:appuser /app

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
