"""
FastAPI server exposing the Guided Component Architect pipeline
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from architect import run_pipeline

app = FastAPI(title="Angular Component Architect", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store (keyed by session_id)
sessions: dict[str, list[dict]] = {}


class GenerateRequest(BaseModel):
    prompt: str
    session_id: str = "default"


class GenerateResponse(BaseModel):
    code: str
    errors: list[str]
    warnings: list[str]
    hard_errors: list[str]
    attempts: int
    success: bool
    session_id: str


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not configured on server")

    history = sessions.get(req.session_id, [])

    result = run_pipeline(req.prompt, api_key, conversation_history=history)

    # Update conversation history
    history.append({"role": "user", "content": req.prompt})
    history.append({"role": "assistant", "content": result["code"][:500]})
    sessions[req.session_id] = history[-20:]  # keep last 20 turns

    return GenerateResponse(
        code=result["code"],
        errors=result["errors"],
        warnings=result["warnings"],
        hard_errors=result["hard_errors"],
        attempts=result["attempts"],
        success=result["success"],
        session_id=req.session_id,
    )


@app.get("/tokens")
async def get_tokens():
    tokens_path = Path(__file__).parent.parent / "design-system" / "tokens.json"
    with open(tokens_path) as f:
        return json.load(f)


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


@app.get("/health")
async def health():
    return {"status": "ok", "groq_key_set": bool(os.environ.get("GROQ_API_KEY"))}