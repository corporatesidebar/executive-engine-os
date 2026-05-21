import os
import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

VERSION = "V36800-structured-execution-object-engine"
API_STATUS = "active"

FRONTEND_ORIGINS = [
    "https://executive-engine-frontend.onrender.com",
    "https://executive-engine-os-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
]

app = FastAPI(
    title="Executive Engine OS Backend",
    version=VERSION,
    description="Structured Execution Object Engine for Executive Engine OS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS + ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: Optional[str] = Field(default=None)
    command: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None)
    mode: Optional[str] = Field(default="execution")
    brain: Optional[str] = Field(default="operator")
    output_type: Optional[str] = Field(default="structured")
    depth: Optional[str] = Field(default="standard")
    provider: Optional[str] = Field(default=None)
    context: Optional[Union[str, Dict[str, Any], List[Any]]] = Field(default=None)
    thread: Optional[Union[str, List[Any], Dict[str, Any]]] = Field(default=None)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value).strip()


def get_command(payload: RunRequest) -> str:
    command = clean_text(payload.input or payload.command or payload.message)
    return command or "Clarify the operating objective and create the next execution move."


def detect_intent(command: str) -> str:
    c = command.lower()
    if any(x in c for x in ["proposal", "pitch", "quote", "scope", "client"]):
        return "proposal"
    if any(x in c for x in ["meeting", "board", "prep", "agenda", "talking points"]):
        return "meeting_prep"
    if any(x in c for x in ["risk", "blocker", "issue", "problem", "concern"]):
        return "risk_review"
    if any(x in c for x in ["strategy", "market", "expand", "expansion", "growth"]):
        return "strategy"
    if any(x in c for x in ["draft", "email", "document", "asset", "write"]):
        return "asset_creation"
    if any(x in c for x in ["plan", "task", "execute", "launch", "build"]):
        return "execution"
    return "operator_command"


def extract_subject(command: str) -> str:
    text = re.sub(r"\s+", " ", command).strip()
    if len(text) <= 86:
        return text
    return text[:83].rstrip() + "..."


def priority_for_intent(intent: str, command: str) -> str:
    c = command.lower()
    if any(x in c for x in ["urgent", "asap", "today", "board", "investor", "deadline", "proposal"]):
        return "High"
    if intent in {"proposal", "meeting_prep", "risk_review"}:
        return "High"
    if intent in {"strategy", "execution", "asset_creation"}:
        return "Medium"
    return "Medium"


def build_actions(intent: str, command: str) -> List[str]:
    if intent == "proposal":
        return [
            "Define the client outcome, commercial offer, timeline, and approval path.",
            "Turn the offer into a one-page proposal with scope, deliverables, pricing logic, and next step.",
            "Add proof points: relevant experience, expected business lift, risk controls, and success metric.",
            "Prepare the send-ready email that positions the proposal as the next logical move.",
            "Set the follow-up trigger and decision deadline before sending.",
        ]
    if intent == "meeting_prep":
        return [
            "Confirm the meeting objective and the decision that must be made.",
            "Prepare three executive talking points tied to revenue, risk, and timeline.",
            "List likely objections and prepare concise responses.",
            "Identify the ask, owner, and next commitment required before the meeting ends.",
        ]
    if intent == "strategy":
        return [
            "State the strategic objective in one measurable sentence.",
            "Separate the opportunity, constraint, and decision needed now.",
            "Identify the fastest validation path before committing resources.",
            "Create the first execution asset that moves the strategy from idea to action.",
        ]
    if intent == "risk_review":
        return [
            "Name the risk, owner, trigger, and business impact.",
            "Define the mitigation move that reduces exposure this week.",
            "Create an escalation path if the risk is not reduced within 48 hours.",
        ]
    if intent == "asset_creation":
        return [
            "Clarify the audience, desired action, and success condition for the asset.",
            "Draft the asset in a direct executive format.",
            "Add a review checkpoint for accuracy, tone, and business outcome.",
        ]
    return [
        "Clarify the business objective and the decision required.",
        "Convert the command into one owned next action.",
        "Create the asset or workflow item that moves execution forward.",
        "Set the follow-up command to continue momentum.",
    ]


def build_assets(intent: str, command: str) -> List[Dict[str, str]]:
    subject = extract_subject(command)
    if intent == "proposal":
        return [
            {"title": "Proposal Outline", "description": f"A structured offer for: {subject}"},
            {"title": "Client Follow-Up Email", "description": "A concise send-ready note that moves the buyer toward a decision."},
            {"title": "ROI / Success Metric", "description": "The measurable business result the proposal should be judged against."},
        ]
    if intent == "meeting_prep":
        return [
            {"title": "Meeting Brief", "description": "Objective, decision required, talking points, and likely objections."},
            {"title": "Objection Response Sheet", "description": "Short answers for the highest-friction moments in the conversation."},
        ]
    if intent == "strategy":
        return [
            {"title": "Strategy Execution Brief", "description": "Objective, market logic, constraint, decision, and first move."},
            {"title": "Validation Checklist", "description": "Fast checks before committing time, money, or team capacity."},
        ]
    if intent == "risk_review":
        return [
            {"title": "Risk Register Item", "description": "Risk, owner, impact, mitigation, and escalation trigger."},
        ]
    return [
        {"title": "Execution Note", "description": f"Operational summary and next step for: {subject}"},
    ]


def build_risk(intent: str, command: str) -> str:
    if intent == "proposal":
        return "The main risk is sending a generic proposal without a clear business outcome, decision path, or measurable ROI."
    if intent == "meeting_prep":
        return "The main risk is entering the meeting with talking points but no decision target or next commitment."
    if intent == "strategy":
        return "The main risk is overbuilding strategy before validating demand, timing, and execution capacity."
    if intent == "risk_review":
        return "The main risk is naming the issue without assigning ownership, mitigation, and escalation timing."
    return "The main risk is leaving the command as discussion instead of converting it into an owned execution step."


def build_mitigation(intent: str) -> str:
    if intent == "proposal":
        return "Anchor the proposal to one buyer outcome, one decision deadline, and one measurable success metric."
    if intent == "meeting_prep":
        return "Open with the desired decision and close with owner, deadline, and next action."
    if intent == "strategy":
        return "Run a narrow validation step before committing a broader build or campaign."
    if intent == "risk_review":
        return "Assign one owner, one mitigation action, and one escalation threshold."
    return "Turn the command into a named task with an owner, output, and follow-up command."


def build_recommended_command(intent: str, command: str) -> str:
    subject = extract_subject(command)
    if intent == "proposal":
        return f"Draft the full proposal and client follow-up email for: {subject}"
    if intent == "meeting_prep":
        return f"Create the meeting brief, talking points, objections, and close for: {subject}"
    if intent == "strategy":
        return f"Turn this strategy into a 7-day execution plan: {subject}"
    if intent == "risk_review":
        return f"Create a mitigation plan and escalation path for: {subject}"
    if intent == "asset_creation":
        return f"Draft the asset with executive tone and action-oriented structure for: {subject}"
    return f"Turn this into a clear action plan with owner, asset, and next step: {subject}"


def build_execution_objects(intent: str, command: str, actions: List[str], assets: List[Dict[str, str]], risk: str) -> List[Dict[str, Any]]:
    objects: List[Dict[str, Any]] = []
    objects.append({
        "id": "obj-decision-1",
        "type": "decision",
        "title": "Operating Decision",
        "status": "ready",
        "priority": priority_for_intent(intent, command),
        "description": decision_for_intent(intent, command),
        "source": "run",
    })
    for i, action in enumerate(actions, start=1):
        objects.append({
            "id": f"obj-action-{i}",
            "type": "action",
            "title": f"Action {i}",
            "status": "open" if i == 1 else "queued",
            "priority": "High" if i == 1 else "Medium",
            "description": action,
            "owner": "Executive",
            "source": "run",
        })
    for i, asset in enumerate(assets, start=1):
        objects.append({
            "id": f"obj-asset-{i}",
            "type": "asset",
            "title": asset.get("title", f"Asset {i}"),
            "status": "draft-ready",
            "priority": "High" if i == 1 else "Medium",
            "description": asset.get("description", "Ready asset generated from command."),
            "source": "run",
        })
    objects.append({
        "id": "obj-risk-1",
        "type": "risk",
        "title": "Active Risk",
        "status": "monitor",
        "priority": "High" if priority_for_intent(intent, command) == "High" else "Medium",
        "description": risk,
        "mitigation": build_mitigation(intent),
        "source": "run",
    })
    return objects


def next_move_for_intent(intent: str, command: str) -> str:
    subject = extract_subject(command)
    if intent == "proposal":
        return f"Convert the request into a decision-ready proposal package for {subject}."
    if intent == "meeting_prep":
        return f"Prepare the meeting to drive one clear decision and one committed next action for {subject}."
    if intent == "strategy":
        return f"Narrow the strategy into one validated execution move for {subject}."
    if intent == "risk_review":
        return f"Move from risk identification to mitigation ownership for {subject}."
    if intent == "asset_creation":
        return f"Create the first usable asset that advances {subject}."
    return f"Turn the command into a clear execution object for {subject}."


def decision_for_intent(intent: str, command: str) -> str:
    if intent == "proposal":
        return "Proceed with a structured proposal, but only after defining the buyer outcome, success metric, timeline, and decision path."
    if intent == "meeting_prep":
        return "Prepare for the meeting around the decision required, not around general discussion."
    if intent == "strategy":
        return "Advance the strategy through a narrow validation step before scaling effort."
    if intent == "risk_review":
        return "Treat the issue as an owned risk with mitigation timing, not as a general concern."
    if intent == "asset_creation":
        return "Create the asset now in executive format, then use it to drive the next action."
    return "Do not leave this as a loose command. Convert it into an execution plan with a next move, owner, and follow-up."


def executive_summary_for(intent: str, command: str, next_move: str, decision: str) -> str:
    subject = extract_subject(command)
    return f"Current focus: {subject}. {next_move} Decision: {decision}"


def deployment_sequence_for(actions: List[str], assets: List[Dict[str, str]], recommended: str) -> List[Dict[str, Any]]:
    sequence = []
    sequence.append({"step": 1, "name": "Clarify outcome", "status": "ready", "action": actions[0] if actions else "Define the desired business outcome."})
    if len(actions) > 1:
        sequence.append({"step": 2, "name": "Build execution path", "status": "queued", "action": actions[1]})
    if assets:
        sequence.append({"step": 3, "name": "Create asset", "status": "queued", "action": f"Prepare {assets[0].get('title', 'the primary asset')}."})
    sequence.append({"step": len(sequence) + 1, "name": "Continue workflow", "status": "next", "action": recommended})
    return sequence


def executive_scan_for(intent: str, command: str, priority: str, risk: str, recommended: str) -> Dict[str, Any]:
    return {
        "intent": intent,
        "current_focus": extract_subject(command),
        "priority": priority,
        "active_risk": risk,
        "recommended_follow_up": recommended,
        "what_changed": "The command has been converted into structured execution objects the frontend can render as workspace state.",
        "operator_note": "Use the recommended command to continue the same workflow instead of starting over.",
    }


def build_response(command: str, payload: Optional[RunRequest] = None) -> Dict[str, Any]:
    intent = detect_intent(command)
    priority = priority_for_intent(intent, command)
    next_move = next_move_for_intent(intent, command)
    decision = decision_for_intent(intent, command)
    actions = build_actions(intent, command)
    assets = build_assets(intent, command)
    risk = build_risk(intent, command)
    recommended = build_recommended_command(intent, command)
    execution_objects = build_execution_objects(intent, command, actions, assets, risk)
    primary_object = execution_objects[0] if execution_objects else None
    deployment_sequence = deployment_sequence_for(actions, assets, recommended)
    executive_scan = executive_scan_for(intent, command, priority, risk, recommended)
    summary = executive_summary_for(intent, command, next_move, decision)
    return {
        "status": "success",
        "version": VERSION,
        "provider_used": "structured-engine:v36800",
        "timestamp": now_iso(),
        "executive_summary": summary,
        "next_move": next_move,
        "decision": decision,
        "action_steps": actions,
        "ready_assets": assets,
        "risk": risk,
        "priority": priority,
        "recommended_command": recommended,
        "execution_objects": execution_objects,
        "primary_object": primary_object,
        "deployment_sequence": deployment_sequence,
        "executive_scan": executive_scan,
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Executive Engine OS Backend",
        "version": VERSION,
        "status": API_STATUS,
        "contract": "V36800 structured execution object engine",
        "routes": ["/health", "/run", "/test-report", "/test-report-json", "/debug", "/providers"],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "backend": "structured-execution-object-engine",
        "timestamp": now_iso(),
    }


@app.get("/debug")
def debug() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "cors_origins": FRONTEND_ORIGINS,
        "required_fields": [
            "executive_summary",
            "next_move",
            "decision",
            "action_steps",
            "ready_assets",
            "risk",
            "priority",
            "recommended_command",
            "execution_objects",
            "primary_object",
            "deployment_sequence",
            "executive_scan",
        ],
    }


@app.get("/providers")
def providers() -> Dict[str, Any]:
    return {
        "status": "success",
        "default": "structured-engine:v36800",
        "available": ["structured-engine:v36800"],
        "external_ai_required": False,
    }


@app.post("/run")
async def run(payload: RunRequest, request: Request) -> JSONResponse:
    command = get_command(payload)
    response = build_response(command, payload)
    return JSONResponse(response)


@app.get("/test-report-json")
def test_report_json() -> Dict[str, Any]:
    sample = build_response("Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.")
    required = [
        "executive_summary",
        "next_move",
        "decision",
        "action_steps",
        "ready_assets",
        "risk",
        "priority",
        "recommended_command",
        "execution_objects",
        "primary_object",
        "deployment_sequence",
        "executive_scan",
    ]
    checks = {field: field in sample and sample[field] not in [None, "", []] for field in required}
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "version": VERSION,
        "checks": checks,
        "sample": sample,
    }


@app.get("/test-report", response_class=HTMLResponse)
def test_report() -> str:
    data = test_report_json()
    rows = "".join(
        f"<tr><td>{field}</td><td>{'PASS' if ok else 'FAIL'}</td></tr>"
        for field, ok in data["checks"].items()
    )
    return f"""
    <!doctype html>
    <html>
    <head>
      <title>Executive Engine OS Test Report</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 32px; color: #0f172a; }}
        h1 {{ margin-bottom: 4px; }}
        table {{ border-collapse: collapse; width: 720px; max-width: 100%; }}
        td, th {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
        th {{ background: #f8fafc; }}
        .pass {{ color: #15803d; font-weight: 700; }}
        pre {{ background: #f8fafc; padding: 16px; overflow: auto; }}
      </style>
    </head>
    <body>
      <h1>Executive Engine OS Backend Test Report</h1>
      <p><strong>Version:</strong> {VERSION}</p>
      <p><strong>Status:</strong> <span class="pass">{data['status'].upper()}</span></p>
      <table><thead><tr><th>Required Field</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>
      <h2>Sample /run Output</h2>
      <pre>{json.dumps(data['sample'], indent=2)}</pre>
    </body>
    </html>
    """


# Compatibility aliases sometimes used by previous frontend/backend tests.
@app.get("/workspace-state")
def workspace_state() -> Dict[str, Any]:
    return build_response("Show current workspace state.")


@app.get("/workspace-summary")
def workspace_summary() -> Dict[str, Any]:
    sample = build_response("Summarize current executive workspace.")
    return {"status": "success", "version": VERSION, "executive_summary": sample["executive_summary"], "executive_scan": sample["executive_scan"]}
