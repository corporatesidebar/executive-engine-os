from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import urllib.request
import urllib.error

VERSION = "36330-stable-merge-recovery"

app = FastAPI(title="Executive Engine OS", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest").strip() or "claude-3-5-sonnet-latest"

class RunRequest(BaseModel):
    input: str = ""
    mode: Optional[str] = "execution"

class RunResponse(BaseModel):
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str
    provider_used: str
    status: str


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _fallback_response(user_input: str, provider_used: str = "local:fallback") -> Dict[str, Any]:
    text = _safe_text(user_input)
    lower = text.lower()

    priority = "High" if any(w in lower for w in ["urgent", "proposal", "client", "meeting", "revenue", "today", "risk"]) else "Medium"

    if "proposal" in lower:
        decision = "Treat this as an active proposal opportunity and convert the request into a clear client-ready scope before moving forward."
        next_move = "Create the proposal outline, confirm scope/pricing/timeline, then prepare the client-facing version."
        actions = [
            "Summarize the client need in one sentence.",
            "Define the recommended scope and expected outcome.",
            "Identify missing pricing, timeline, and decision-maker details.",
            "Draft the proposal structure and follow-up message.",
        ]
        risk = "The opportunity may stall or be underpriced if scope, budget, and timeline remain vague."
    elif "meeting" in lower or "met with" in lower or "call" in lower:
        decision = "Treat this as a meeting-prep and follow-up workflow, not a loose note."
        next_move = "Prepare talking points and define the decision or next action that must be confirmed before the meeting ends."
        actions = [
            "Clarify who is attending and what outcome matters.",
            "Prepare three talking points tied to the business objective.",
            "List likely objections, risks, or missing context.",
            "Draft the post-meeting follow-up before the meeting happens.",
        ]
        risk = "The meeting may create conversation without operational progress if no owner, deadline, or follow-up is confirmed."
    elif "strategy" in lower or "sales" in lower or "marketing" in lower or "growth" in lower:
        decision = "Turn this strategy request into one executable direction with a clear first move."
        next_move = "Define the strategic objective, the constraint, and the first action that creates momentum."
        actions = [
            "State the business objective clearly.",
            "Identify the biggest constraint or bottleneck.",
            "Choose the first operational move.",
            "Assign a measurable outcome and review point.",
        ]
        risk = "The strategy will stay theoretical if it is not tied to ownership, timing, and measurable execution."
    else:
        decision = "Convert this input into an active executive action and move it toward a clear operational outcome."
        next_move = "Clarify the objective, identify the next decision, and create the first concrete action."
        actions = [
            "Define what outcome this action should produce.",
            "Identify the owner, deadline, and missing information.",
            "Create the next step or draft required to move it forward.",
            "Keep the item open until the follow-up or decision is complete.",
        ]
        risk = "The item may remain a loose thought unless it becomes a specific action with ownership and timing."

    return {
        "decision": decision,
        "next_move": next_move,
        "actions": actions,
        "risk": risk,
        "priority": priority,
        "provider_used": provider_used,
        "status": "success",
    }


def _normalize_response(data: Any, provider_used: str, user_input: str) -> Dict[str, Any]:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}

    fallback = _fallback_response(user_input, provider_used)
    actions = data.get("actions", fallback["actions"])
    if isinstance(actions, str):
        actions = [a.strip(" -") for a in actions.split("\n") if a.strip()]
    if not isinstance(actions, list) or not actions:
        actions = fallback["actions"]

    priority = data.get("priority", fallback["priority"])
    if priority not in ["High", "Medium", "Low"]:
        priority = fallback["priority"]

    return {
        "decision": _safe_text(data.get("decision")) or fallback["decision"],
        "next_move": _safe_text(data.get("next_move")) or fallback["next_move"],
        "actions": [str(a) for a in actions[:6]],
        "risk": _safe_text(data.get("risk")) or fallback["risk"],
        "priority": priority,
        "provider_used": provider_used,
        "status": "success",
    }


def _system_prompt() -> str:
    return (
        "You are Executive Engine OS, a senior executive operating assistant. "
        "Return ONLY valid JSON with exactly these keys: decision, next_move, actions, risk, priority. "
        "priority must be High, Medium, or Low. "
        "Be direct, practical, executive-level, and operational. No markdown."
    )


def _call_openai(user_input: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        body = json.loads(res.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    return _normalize_response(content, f"openai:{OPENAI_MODEL}", user_input)


def _call_claude(user_input: str) -> Dict[str, Any]:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 700,
        "temperature": 0.2,
        "system": _system_prompt(),
        "messages": [{"role": "user", "content": user_input}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        body = json.loads(res.read().decode("utf-8"))
    parts = body.get("content", [])
    content = ""
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            content += part.get("text", "")
    return _normalize_response(content, f"claude:{ANTHROPIC_MODEL}", user_input)


@app.get("/")
def root():
    return {
        "status": "live",
        "service": "Executive Engine OS",
        "version": VERSION,
        "message": "Stable Merge Recovery online.",
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/debug")
def debug():
    return {
        "status": "ok",
        "version": VERSION,
        "timestamp": now_iso(),
        "openai": {"has_api_key": bool(OPENAI_API_KEY), "model": OPENAI_MODEL},
        "claude": {"has_api_key": bool(ANTHROPIC_API_KEY), "model": ANTHROPIC_MODEL},
        "routing": "openai-first; claude fallback; local fallback",
        "required_response_shape": ["decision", "next_move", "actions", "risk", "priority", "provider_used", "status"],
    }


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    user_input = _safe_text(req.input)
    if not user_input:
        return _fallback_response("No input provided. Create a first executive action.", "local:empty-input")

    try:
        return _call_openai(user_input)
    except Exception:
        try:
            return _call_claude(user_input)
        except Exception:
            return _fallback_response(user_input, "local:fallback-after-provider-error")
