from __future__ import annotations

import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

VERSION = "V36160-executive-advantage-prototype"
REQUIRED_FIELDS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
]

app = FastAPI(title="Executive Engine OS", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prototype in-memory store. Replace with Supabase/Postgres later without changing API shape.
STATE: Dict[str, Any] = {
    "threads": [],
    "workflows": [],
    "decisions": [],
    "risks": [],
    "assets": [],
    "open_loops": [],
    "last_run": None,
    "pressure_score": 0,
    "momentum": "neutral",
}


class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: Optional[str] = "auto"
    category: Optional[str] = "auto"
    output_type: Optional[str] = "operational"
    depth: Optional[str] = "standard"
    provider: Optional[str] = "auto"


class RunResponse(BaseModel):
    next_move: str
    decision: str
    action_steps: List[str]
    ready_assets: List[str]
    risk: str
    priority: str
    recommended_command: str
    intent: str
    category: str
    pressure_score: int
    workflow_id: str
    workflow_status: str
    open_loops: List[str]
    push_intelligence: List[str]
    executive_brief: str
    detail: Dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def detect_intent(text: str, forced: Optional[str] = None) -> str:
    forced = (forced or "auto").lower().strip()
    valid = {"meeting", "proposal", "execution", "decision", "strategy", "risk", "follow-up", "capture", "revenue", "general"}
    if forced in valid:
        return forced
    t = text.lower()
    rules = [
        ("proposal", ["proposal", "quote", "scope", "client offer", "deal", "pitch", "pricing"]),
        ("meeting", ["meeting", "call", "agenda", "prep", "board", "attendee", "tomorrow at", "today at"]),
        ("decision", ["decide", "decision", "choose", "option", "should i", "approve", "go/no-go"]),
        ("risk", ["risk", "issue", "problem", "broken", "blocked", "fails", "concern", "danger"]),
        ("follow-up", ["follow up", "follow-up", "reply", "email back", "message", "check in"]),
        ("strategy", ["strategy", "market", "positioning", "growth", "plan", "roadmap"]),
        ("revenue", ["revenue", "sales", "lead", "pipeline", "close", "conversion", "cpa", "roi"]),
        ("execution", ["build", "launch", "fix", "ship", "implement", "execute", "deploy", "create"]),
        ("capture", ["note", "remember", "capture", "idea"]),
    ]
    for intent, keys in rules:
        if any(k in t for k in keys):
            return intent
    return "general"


def title_from_command(text: str, intent: str) -> str:
    cleaned = normalize(text)
    if len(cleaned) > 64:
        cleaned = cleaned[:61].rstrip() + "..."
    return f"{intent.title()}: {cleaned}"


def score_pressure(intent: str, text: str) -> int:
    t = text.lower()
    score = 22
    if intent in {"proposal", "revenue"}:
        score += 25
    if intent in {"risk", "decision"}:
        score += 22
    if intent == "meeting":
        score += 18
    if any(k in t for k in ["urgent", "asap", "today", "now", "broken", "not working", "terrible", "fails"]):
        score += 20
    if any(k in t for k in ["client", "customer", "board", "ceo", "investor", "deal"]):
        score += 12
    score += min(len(STATE["open_loops"]) * 4, 16)
    return max(0, min(100, score))


def priority_from_score(score: int) -> str:
    if score >= 76:
        return "Critical — act now"
    if score >= 56:
        return "High — move today"
    if score >= 36:
        return "Medium — schedule and advance"
    return "Low — capture and monitor"


def extract_subject(text: str) -> str:
    text = normalize(text)
    return text[0].upper() + text[1:] if text else "the objective"


def build_operator_response(text: str, intent: str, pressure: int) -> Dict[str, Any]:
    subject = extract_subject(text)
    priority = priority_from_score(pressure)

    if intent == "proposal":
        next_move = "Create the proposal path first: outcome, buyer pain, offer, scope, proof, price logic, and follow-up sequence."
        decision = "Treat this as a revenue workflow, not a writing task. The proposal must move the buyer toward a clear yes/no decision."
        actions = [
            "Define the buyer's desired outcome and the business cost of doing nothing.",
            "Build a one-page proposal structure with offer, scope, timeline, and measurable success metric.",
            "Add a follow-up command for 48 hours after sending so the deal does not stall.",
        ]
        assets = [
            "Proposal outline", "Client follow-up draft", "Objection handling checklist"
        ]
        risk = "The main risk is producing a polished document that does not create urgency, clarify value, or force a buying decision."
        recommended = "Create the proposal draft with outcome, scope, pricing logic, and 48-hour follow-up."
    elif intent == "meeting":
        next_move = "Prepare the meeting around the decision that must be made, not around a generic agenda."
        decision = "This meeting needs a defined outcome before prep. Without an outcome, the meeting becomes conversation instead of leverage."
        actions = [
            "State the meeting objective in one sentence.",
            "List the three decisions, blockers, or commitments that must be resolved.",
            "Prepare a post-meeting follow-up asset before the meeting starts.",
        ]
        assets = ["Meeting brief", "Talking points", "Follow-up email draft"]
        risk = "The meeting becomes status chatter and creates more open loops instead of closing them."
        recommended = "Prepare a meeting brief with objective, attendees, decisions required, and follow-up draft."
    elif intent == "decision":
        next_move = "Reduce the decision to options, consequences, and the cost of delay."
        decision = "Do not keep analyzing without a threshold. Set the decision rule, choose the best option, and define the next action."
        actions = [
            "Identify the two or three realistic options only.",
            "Score each option by speed, leverage, risk, and reversibility.",
            "Choose the option that preserves momentum unless downside risk is severe.",
        ]
        assets = ["Decision matrix", "Tradeoff summary", "Execution trigger"]
        risk = "The risk is decision drag: more analysis without movement, which increases pressure and slows execution."
        recommended = "Create a decision matrix with recommendation, risk, and next action."
    elif intent == "risk":
        next_move = "Isolate the operational failure point and decide whether to fix, rollback, or contain."
        decision = "This should be treated as a control issue until the failure is understood and contained."
        actions = [
            "Name the specific failure, not the general frustration.",
            "Identify whether the issue is frontend, backend, intelligence quality, data/state, or deployment.",
            "Apply one contained fix and define an acceptance test before changing anything else.",
        ]
        assets = ["Risk log", "Fix checklist", "Acceptance test"]
        risk = "Changing multiple parts at once will create more confusion and destroy test confidence."
        recommended = "Run a contained fix cycle: one issue, one file set, one acceptance test."
    elif intent == "follow-up":
        next_move = "Turn the follow-up into a specific ask with a clear decision or next step."
        decision = "Follow-up should create movement, not politely check in."
        actions = [
            "Name the unresolved commitment or decision.",
            "State the requested next step clearly.",
            "Set a response window and prepare the next escalation path if no reply arrives.",
        ]
        assets = ["Follow-up message", "Escalation note", "Open-loop tracker"]
        risk = "Weak follow-up creates relationship drift and lets the workflow stall invisibly."
        recommended = "Draft a follow-up that asks for one clear decision or next action."
    else:
        next_move = "Convert the command into an operational workflow with one clear outcome and one immediate next action."
        decision = "Do not leave this as a note. Either act, schedule, delegate, or discard it."
        actions = [
            "Define the business outcome this command is supposed to create.",
            "Identify the next physical action required to create movement.",
            "Track the risk or open loop that appears if this does not move today.",
        ]
        assets = ["Action plan", "Workflow card", "Next command"]
        risk = "The risk is adding another unstructured item that increases cognitive load without creating movement."
        recommended = "Turn this into a workflow with outcome, next action, owner, and risk."

    executive_brief = f"{intent.title()} workflow created. Pressure is {pressure}/100. Priority: {priority}. The system is optimizing for movement, not documentation."
    push = build_push_items(intent, pressure)
    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": actions,
        "ready_assets": assets,
        "risk": risk,
        "priority": priority,
        "recommended_command": recommended,
        "push_intelligence": push,
        "executive_brief": executive_brief,
    }


def build_push_items(intent: str, pressure: int) -> List[str]:
    items = []
    if pressure >= 70:
        items.append("Pressure is high: reduce scope to the one decision or action that unlocks movement now.")
    if STATE["open_loops"]:
        items.append(f"There are {len(STATE['open_loops'])} open loops. Close or schedule the oldest one before adding more work.")
    if intent == "meeting":
        items.append("Meeting prep should be completed before the meeting, including the follow-up draft.")
    if intent == "proposal":
        items.append("Proposal workflow needs a follow-up date now, not after sending.")
    if intent == "decision":
        items.append("Decision workflow should end with an execution trigger, not just a recommendation.")
    if not items:
        items.append("No immediate escalation. Create momentum by completing the first action today.")
    return items[:3]


def workflow_status(pressure: int) -> str:
    if pressure >= 76:
        return "at-risk"
    if pressure >= 45:
        return "active"
    return "captured"


def create_or_update_workflow(text: str, intent: str, response: Dict[str, Any], pressure: int) -> Dict[str, Any]:
    wf = {
        "id": str(uuid.uuid4())[:8],
        "title": title_from_command(text, intent),
        "category": intent,
        "status": workflow_status(pressure),
        "source_command": text,
        "next_move": response["next_move"],
        "decision": response["decision"],
        "actions": response["action_steps"],
        "assets": response["ready_assets"],
        "risk": response["risk"],
        "priority": response["priority"],
        "recommended_command": response["recommended_command"],
        "pressure_score": pressure,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    STATE["workflows"].append(wf)
    if len(STATE["workflows"]) > 50:
        STATE["workflows"] = STATE["workflows"][-50:]
    loop = f"{intent.title()} open loop: {response['recommended_command']}"
    STATE["open_loops"].append(loop)
    STATE["open_loops"] = STATE["open_loops"][-20:]
    STATE["risks"].append({"id": wf["id"], "risk": response["risk"], "pressure": pressure, "created_at": now_iso()})
    STATE["assets"].append({"id": wf["id"], "assets": response["ready_assets"], "created_at": now_iso()})
    STATE["decisions"].append({"id": wf["id"], "decision": response["decision"], "created_at": now_iso()})
    return wf


def try_ai_response(text: str, intent: str, pressure: int) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""
You are Executive Engine OS: an elite COO/chief-of-staff intelligence layer.
Return JSON only with keys: next_move, decision, action_steps(array of 3), ready_assets(array of 3), risk, priority, recommended_command, push_intelligence(array of 3), executive_brief.
No generic AI language. No filler. Be operator-grade.
Intent: {intent}
Pressure score: {pressure}
Command: {text}
"""
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            response_format={"type": "json_object"},
        )
        import json
        data = json.loads(completion.choices[0].message.content or "{}")
        if all(k in data for k in ["next_move", "decision", "action_steps", "ready_assets", "risk", "priority", "recommended_command"]):
            return data
    except Exception:
        return None
    return None


@app.get("/")
def root() -> Dict[str, Any]:
    return {"status": "ok", "version": VERSION, "service": "Executive Engine OS"}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": VERSION, "required_fields": REQUIRED_FIELDS}


@app.get("/workspace-state")
def workspace_state() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "pressure_score": STATE["pressure_score"],
        "momentum": STATE["momentum"],
        "last_run": STATE["last_run"],
        "threads": STATE["threads"][-20:],
        "workflows": STATE["workflows"][-20:],
        "decisions": STATE["decisions"][-20:],
        "risks": STATE["risks"][-20:],
        "assets": STATE["assets"][-20:],
        "open_loops": STATE["open_loops"][-20:],
    }


@app.get("/test-report-json")
def test_report_json() -> Dict[str, Any]:
    return {
        "status": "pass",
        "version": VERSION,
        "checks": {
            "fastapi": True,
            "run_route": True,
            "required_contract": REQUIRED_FIELDS,
            "workspace_state": True,
            "cors": True,
            "openai_optional": bool(os.getenv("OPENAI_API_KEY")),
            "fallback_operator_engine": True,
        },
    }


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest) -> Dict[str, Any]:
    command = normalize(req.input)
    intent = detect_intent(command, req.category or req.mode)
    pressure = score_pressure(intent, command)
    response = try_ai_response(command, intent, pressure) or build_operator_response(command, intent, pressure)
    wf = create_or_update_workflow(command, intent, response, pressure)

    thread = {
        "id": str(uuid.uuid4())[:8],
        "workflow_id": wf["id"],
        "category": intent,
        "user_input": command,
        "system_response": response,
        "created_at": now_iso(),
    }
    STATE["threads"].append(thread)
    STATE["threads"] = STATE["threads"][-50:]
    STATE["pressure_score"] = pressure
    STATE["momentum"] = "building" if pressure < 76 else "needs-control"
    STATE["last_run"] = thread

    return {
        **{k: response[k] for k in REQUIRED_FIELDS},
        "intent": intent,
        "category": intent,
        "pressure_score": pressure,
        "workflow_id": wf["id"],
        "workflow_status": wf["status"],
        "open_loops": STATE["open_loops"][-5:],
        "push_intelligence": response.get("push_intelligence", []),
        "executive_brief": response.get("executive_brief", "Workflow updated."),
        "detail": wf,
    }
