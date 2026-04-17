"""
Production VinBank AI Agent — kết hợp logic Day 11 và hạ tầng Day 12
"""
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost
from app.logic.pipeline import DefensePipeline

# ─────────────────────────────────────────────────────────
# Logging — Structured JSON
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_pipeline: DefensePipeline = None

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready, _pipeline
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
    }))
    
    # Initialize Defense Pipeline
    try:
        _pipeline = DefensePipeline()
        _is_ready = True
        logger.info(json.dumps({"event": "ready", "status": "pipeline_initialized"}))
    except Exception as e:
        logger.error(json.dumps({"event": "startup_failed", "error": str(e)}))
        _is_ready = False

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App & Middleware
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Mount static files (UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        logger.error(json.dumps({"event": "unhandled_error", "path": request.url.path, "error": str(e)}))
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    question: str = Field(..., min_length=1, max_length=2000)

class AskResponse(BaseModel):
    session_id: str
    question: str
    response: str  # Updated to match JS expectation
    metadata: dict
    timestamp: str

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Redirect to the UI by default."""
    return RedirectResponse(url="/static/index.html")

@app.get("/api/metrics")
def get_api_metrics(_key: str = Depends(verify_api_key)):
    """Metrics for the UI."""
    return _pipeline.get_metrics()

@app.get("/api/audit")
def get_api_audit(_key: str = Depends(verify_api_key)):
    """Audit logs for the UI."""
    return _pipeline.audit_log

@app.post("/api/chat", response_model=AskResponse)
async def chat_agent(
    body: dict, # UI sends {user_id, message}
    _key: str = Depends(verify_api_key),
):
    """
    UI-compatible chat endpoint.
    """
    if not _is_ready:
        raise HTTPException(503, "Service not ready")

    user_id = body.get("user_id", "unknown")
    question = body.get("message", "")

    # 1. Rate Limiting
    check_rate_limit(_key)

    # 2. Daily Budget Guard
    input_tokens = len(question.split()) * 2
    check_and_record_cost(input_tokens, 0)

    # 3. Process via Defense Pipeline
    answer, log_metadata = await _pipeline.process_query(user_id, question)

    # 4. Record output cost
    output_tokens = len(answer.split()) * 2
    check_and_record_cost(0, output_tokens)

    return AskResponse(
        session_id=user_id,
        question=question,
        response=answer,
        metadata=log_metadata,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.post("/ask", response_model=AskResponse)
async def ask_agent(
    body: AskRequest,
    _key: str = Depends(verify_api_key),
):
    # (Legacy/CLI compatible endpoint)
    res = await chat_agent({"user_id": body.user_id, "message": body.question}, _key)
    return res

@app.get("/health")
def health():
    return {
        "status": "ok" if _is_ready else "degraded",
        "uptime": round(time.time() - START_TIME, 1),
        "requests": _request_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"status": "ready"}

# ─────────────────────────────────────────────────────────
# Signal Handling
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal_received", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
