from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os

from intelligence.structured_execution_engine import build_structured_execution_response
from intelligence.state_store import load_workspace, save_structured_execution_state

APP_VERSION = "V36800-Structured-Execution-Object-Engine"
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
    depth: Optional[str] = "auto"
    provider: Optional[str] = "openai"
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"
    context: Optional[Dict[str, Any]] = None

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "structured_execution_object_engine",
        "purpose": "return operational objects instead of generic text blocks"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.post("/run")
def run(req: RunRequest):
    workspace = load_workspace(req.workspace_id or "default", req.user_id or "will")

    response = build_structured_execution_response(
        user_input=req.input,
        workspace=workspace,
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        depth=req.depth or "auto",
        mode=req.mode or "execution",
        brain=req.brain or "operator",
        output_type=req.output_type or "standard",
    )

    save_structured_execution_state(
        workspace_id=req.workspace_id or "default",
        user_id=req.user_id or "will",
        user_input=req.input,
        response=response,
    )

    response["version"] = APP_VERSION
    return response

@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    return {
        "status": "success",
        "version": APP_VERSION,
        "workspace": load_workspace(workspace_id, user_id)
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36800",
            "POST /run returns executive_scan object",
            "POST /run returns execution_objects array",
            "POST /run returns frontend-compatible legacy keys",
            "POST /run returns object types: proposal, outreach, crm_pipeline, kpi_scorecard, deployment_checklist, operating_system",
            "Response renderer can render by object type",
            "Supabase SQL is additive only"
        ],
        "test_commands": [
            "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
            "How do I make Executive Engine profitable fastest?",
            "I need 10 clients for Executive Engine in 30 days.",
            "I have too many projects and feel overwhelmed."
        ]
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
