import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from src.openai_pipeline import DefensePipeline
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VinBank AI Defense Pipeline")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pipeline
pipeline = DefensePipeline()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        response, log = await pipeline.process_query(req.user_id, req.message)
        return {
            "response": response,
            "metadata": log
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    return pipeline.get_metrics()

@app.get("/api/audit")
async def get_audit():
    return pipeline.audit_log[-20:] # Return last 20 entries

# Serve Static Files
# Ensure the 'static' directory exists before mounting
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
