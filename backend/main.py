from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from openai import OpenAI

from intelligence.dual_layer_engine import build_dual_layer_response
from intelligence.context_engine import load_workspace, save_run_context

APP_VERSION = "V36630-Dual-Layer-Executive-Intelligence-Engine"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

app = FastAPI(title="Executive Engine OS", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://executive-engine-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: Optional[str] = "execution"
    brain: Optional[str] = "operator"
    output_type: Optional[str] = "standard"
    depth: Optional[str] = "standard"
    provider: Optional[str] = "openai"
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"
    context: Optional[Dict[str, Any]] = None

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "dual_layer_executive_intelligence",
        "purpose": "executive scan layer + operational depth layer"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "openai_configured": bool(OPENAI_API_KEY),
    }

@app.post("/run")
def run(req: RunRequest):
    workspace = load_workspace(req.workspace_id or "default", req.user_id or "will")

    response = build_dual_layer_response(
        user_input=req.input,
        mode=req.mode or "execution",
        brain=req.brain or "operator",
        output_type=req.output_type or "standard",
        workspace=workspace,
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
    )

    save_run_context(
        workspace_id=req.workspace_id or "default",
        user_id=req.user_id or "will",
        user_input=req.input,
        response=response,
    )

    response["version"] = APP_VERSION
    return response

@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    return {
        "status": "success",
        "version": APP_VERSION,
        "workspace": workspace,
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36630",
            "POST /run returns executive_scan and operational_depth",
            "POST /run preserves existing required contract",
            "Overwhelm input returns actual actions/resources/assets",
            "Profitability input returns monetization sequence"
        ],
        "test_commands": [
            "I have too many projects and feel overwhelmed.",
            "How do I make Executive Engine profitable fastest?",
            "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
        ]
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
