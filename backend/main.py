import os
import json
import re
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI


APP_NAME = "Executive Engine OS V63"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "40"))

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMORY: List[Dict[str, Any]] = []

SERVICES = [
    {"name": "Calendar", "status": "ready", "purpose": "Meeting prep, daily brief, reminders, review cadence"},
    {"name": "Email", "status": "ready", "purpose": "Follow-ups, draft replies, summaries, outbound next steps"},
    {"name": "Revenue System", "status": "ready", "purpose": "Pipeline, deals, client follow-up, revenue actions"},
    {"name": "Finance System", "status": "ready", "purpose": "Capital allocation, margin, cash risk, ROI"},
    {"name": "Execution System", "status": "ready", "purpose": "Execution queue, owners, deadlines, operating cadence"},
    {"name": "Knowledge Base", "status": "ready", "purpose": "Docs, decisions, strategy, context library"},
    {"name": "Automation", "status": "ready", "purpose": "Triggers, repeatable workflows, systemized execution"},
]


class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None
    mode: Optional[str] = "execution"


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_response(reason: str = "Temporary fallback"):
    return {
        "what_to_do_now": "Clarify the real objective, then execute the highest-leverage next move.",
        "decision": "Do not add complexity until the current blocker is resolved.",
        "next_move": "Identify the single constraint stopping progress and remove it first.",
        "actions": [
            "Define the intended outcome in one sentence",
            "Identify the current blocker",
            "Choose the highest-leverage action",
            "Execute that action before adding more features",
            "Review the result and adjust"
        ],
        "risk": reason,
        "priority": "high",
        "reality_check": "The system needs stable execution before more complexity is useful.",
        "leverage": "Stabilize the operating loop before scaling functionality.",
        "hidden_opportunity": "A reliable executive workflow is more valuable than disconnected features.",
        "clarifying_question": "What specific outcome needs to improve first?",
        "executive_summary": "Stabilize the operating loop and force the next action.",
        "financial_impact": "Poor execution wastes time, delays revenue, and increases operating drag.",
        "leadership_implication": "Leadership must force clarity and sequencing.",
        "execution_score": "Medium",
        "decision_confidence": "Medium",
        "time_horizon": "Immediate",
        "systems_to_connect": ["Calendar", "Execution System", "Memory"],
        "automation_opportunity": "Capture repeated decisions and turn them into workflows.",
        "delegation_opportunity": "Assign ownership once the next move is clear.",
        "owner": "Executive owner",
        "operating_cadence": "Review progress daily until resolved.",
        "key_metric": "Execution progress",
        "decision_type": "Operating decision",
        "urgency": "High",
        "automation_plan": ["Identify repeatable workflow", "Define trigger", "Choose system", "Create first automation"],
        "service_actions": ["Use Calendar for cadence", "Use Execution System for action tracking"],
        "trigger": "Executive command or repeated workflow",
        "required_services": ["Calendar", "Execution System", "Memory"]
    }


def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text or "")
        if match:
            return json.loads(match.group(0))
    raise ValueError("Invalid JSON")


def clean_actions(actions):
    if isinstance(actions, str) and actions.strip():
        actions = [actions.strip()]
    if not isinstance(actions, list):
        actions = []
    cleaned = [str(a).strip() for a in actions if str(a).strip()]
    return cleaned[:7] or ["Clarify the objective", "Identify the constraint", "Execute the highest-leverage next move"]


def normalize(data: Dict[str, Any]):
    if not isinstance(data, dict):
        return safe_response("Invalid response shape")

    priority = str(data.get("priority", "high")).lower().strip()
    if priority not in ["low", "medium", "high", "critical"]:
        priority = "high"

    return {
        "what_to_do_now": str(data.get("what_to_do_now") or "Execute the highest-leverage next move.").strip(),
        "decision": str(data.get("decision") or "Commit to the clearest execution path.").strip(),
        "next_move": str(data.get("next_move") or "Move from discussion to execution.").strip(),
        "actions": clean_actions(data.get("actions")),
        "risk": str(data.get("risk") or "Unclear execution creates wasted time and weak decisions.").strip(),
        "priority": priority,
        "reality_check": str(data.get("reality_check") or "").strip(),
        "leverage": str(data.get("leverage") or "").strip(),
        "hidden_opportunity": str(data.get("hidden_opportunity") or "").strip(),
        "meeting_agenda": str(data.get("meeting_agenda") or "").strip(),
        "follow_up": str(data.get("follow_up") or "").strip(),
        "clarifying_question": str(data.get("clarifying_question") or "").strip(),
        "executive_summary": str(data.get("executive_summary") or "").strip(),
        "financial_impact": str(data.get("financial_impact") or "").strip(),
        "leadership_implication": str(data.get("leadership_implication") or "").strip(),
        "execution_score": str(data.get("execution_score") or "").strip(),
        "decision_confidence": str(data.get("decision_confidence") or "").strip(),
        "time_horizon": str(data.get("time_horizon") or "").strip(),
        "systems_to_connect": data.get("systems_to_connect") if isinstance(data.get("systems_to_connect"), list) else [],
        "automation_opportunity": str(data.get("automation_opportunity") or "").strip(),
        "delegation_opportunity": str(data.get("delegation_opportunity") or "").strip(),
        "owner": str(data.get("owner") or "").strip(),
        "operating_cadence": str(data.get("operating_cadence") or "").strip(),
        "key_metric": str(data.get("key_metric") or "").strip(),
        "decision_type": str(data.get("decision_type") or "").strip(),
        "urgency": str(data.get("urgency") or priority).strip(),
        "automation_plan": data.get("automation_plan") if isinstance(data.get("automation_plan"), list) else [],
        "service_actions": data.get("service_actions") if isinstance(data.get("service_actions"), list) else [],
        "trigger": str(data.get("trigger") or "").strip(),
        "required_services": data.get("required_services") if isinstance(data.get("required_services"), list) else [],
    }


SYSTEM_PROMPT = """
You are Executive Engine OS V63.

You respond like a CEO / President / COO-level operating partner for executives who make millions per year.

You are not a generic assistant, motivational coach, or junior consultant.

You think across:
- revenue
- capital allocation
- operational efficiency
- leadership clarity
- risk management
- execution velocity
- reputation
- strategic leverage
- decision quality
- personal operating capacity
- user profile/resume context
- automation and systems
- internal automation workflows
- daily briefs
- follow-up planning
- open-loop detection
- action queue building
- weekly operator reviews

Output must be direct, sharp, executive-level, practical, specific to the user's input, and useful to a CEO/COO/President making high-stakes decisions. Avoid generic advice. Every action must be executable today.

For internal automation requests, behave like an operating system:
- identify trigger
- define workflow
- extract actions
- identify open loops
- assign owner/role
- create cadence
- define output
- state what to ignore
- do not mention external integrations unless explicitly requested.

Return ONLY valid JSON with this shape:
{
  "what_to_do_now": "",
  "decision": "",
  "next_move": "",
  "actions": [],
  "risk": "",
  "priority": "low|medium|high|critical",
  "reality_check": "",
  "leverage": "",
  "hidden_opportunity": "",
  "meeting_agenda": "",
  "follow_up": "",
  "clarifying_question": "",
  "executive_summary": "",
  "financial_impact": "",
  "leadership_implication": "",
  "execution_score": "Low|Medium|High",
  "decision_confidence": "Low|Medium|High",
  "time_horizon": "Immediate|Short-term|Medium-term|Long-term",
  "systems_to_connect": [],
  "automation_opportunity": "",
  "delegation_opportunity": "",
  "owner": "",
  "operating_cadence": "",
  "key_metric": "",
  "decision_type": "",
  "urgency": "low|medium|high|critical",
  "automation_plan": [],
  "service_actions": [],
  "trigger": "",
  "required_services": []
}
"""


def build_messages(req: RunRequest):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"MODE:\n{req.mode}\n\nCONTEXT:\n{req.context or 'No context'}\n\nUSER INPUT:\n{req.input}"}
    ]


def save_memory(req: RunRequest, output: Dict[str, Any]):
    MEMORY.append({
        "input": req.input,
        "mode": req.mode,
        "decision": output.get("decision"),
        "next_move": output.get("next_move"),
        "actions": output.get("actions"),
        "risk": output.get("risk"),
        "priority": output.get("priority"),
        "created_at": now(),
    })
    del MEMORY[:-20]


@app.get("/")
async def root():
    return {"ok": True, "service": APP_NAME}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": APP_NAME,
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "memory_items": len(MEMORY),
    }


@app.get("/run")
async def run_info():
    return {
        "ok": True,
        "message": "Use POST /run with JSON body",
        "example": {"input": "What should I focus on today?", "mode": "execution"}
    }


@app.post("/run")
async def run(req: RunRequest):
    if not req.input or not req.input.strip():
        return safe_response("Missing input")

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                messages=build_messages(req),
                temperature=0.25,
                max_tokens=1100,
                response_format={"type": "json_object"},
            ),
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        parsed = extract_json(response.choices[0].message.content)
        clean = normalize(parsed)
        save_memory(req, clean)
        return clean
    except Exception as e:
        return safe_response(f"Backend fallback: {str(e)[:160]}")


@app.get("/integrations")
async def integrations():
    return {
        "services": SERVICES,
        "note": "Operating systems are mapped for native executive workflows."
    }


@app.post("/daily-brief")
async def daily_brief(req: RunRequest):
    auto_req = RunRequest(
        input=f"Run internal Daily Brief: {req.input}",
        context=req.context,
        mode="daily_brief"
    )
    return await run(auto_req)


@app.post("/open-loops")
async def open_loops(req: RunRequest):
    auto_req = RunRequest(
        input=f"Detect open loops and unresolved execution risks: {req.input}",
        context=req.context,
        mode="automation"
    )
    return await run(auto_req)


@app.post("/follow-up")
async def follow_up(req: RunRequest):
    auto_req = RunRequest(
        input=f"Create follow-up plan, message drafts, action owners, timing, and next move: {req.input}",
        context=req.context,
        mode="automation"
    )
    return await run(auto_req)


@app.post("/action-queue")
async def action_queue(req: RunRequest):
    auto_req = RunRequest(
        input=f"Build execution action queue from context: {req.input}",
        context=req.context,
        mode="automation"
    )
    return await run(auto_req)


@app.post("/automation-plan")
async def automation_plan(req: RunRequest):
    automation_req = RunRequest(
        input=f"Create an automation blueprint for: {req.input}",
        context=req.context,
        mode="automation"
    )
    return await run(automation_req)


@app.get("/debug")
async def debug():
    return {
        "ok": True,
        "service": APP_NAME,
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "allowed_origins": ALLOWED_ORIGINS,
        "memory_items": len(MEMORY),
        "routes": ["/", "/health", "/run", "/memory", "/integrations", "/automation-plan", "/daily-brief", "/open-loops", "/follow-up", "/action-queue", "/debug"]
    }


@app.get("/memory")
async def memory():
    return {"memory": MEMORY[-20:]}
