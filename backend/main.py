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


APP_NAME = "Executive Engine OS V79"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))

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
    {"name": "Calendar", "status": "ready", "purpose": "Cadence, meeting prep, daily brief, review rhythm"},
    {"name": "Email", "status": "ready", "purpose": "Follow-up, outbound response, stakeholder management"},
    {"name": "Revenue System", "status": "ready", "purpose": "Pipeline, sales motion, offer, close, retention"},
    {"name": "Finance System", "status": "ready", "purpose": "Cash, margin, ROI, burn, capital allocation"},
    {"name": "Execution System", "status": "ready", "purpose": "Owners, actions, operating cadence, deadlines"},
    {"name": "Knowledge Base", "status": "ready", "purpose": "Context, decisions, strategy, profile, memory"},
    {"name": "Automation", "status": "ready", "purpose": "Repeatable workflows, triggers, open-loop detection"},
]


class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None
    mode: Optional[str] = "execution"
    depth: Optional[str] = "standard"


def now():
    return datetime.now(timezone.utc).isoformat()


REQUIRED_KEYS = [
    "what_to_do_now",
    "decision",
    "next_move",
    "actions",
    "risk",
    "priority",
    "reality_check",
    "leverage",
    "hidden_opportunity",
    "meeting_agenda",
    "follow_up",
    "clarifying_question",
    "executive_summary",
    "financial_impact",
    "leadership_implication",
    "execution_score",
    "decision_confidence",
    "time_horizon",
    "systems_to_connect",
    "automation_opportunity",
    "delegation_opportunity",
    "owner",
    "operating_cadence",
    "key_metric",
    "decision_type",
    "urgency",
    "automation_plan",
    "service_actions",
    "trigger",
    "required_services",
    "executive_diagnosis",
    "strategic_read",
    "constraint",
    "unfair_advantage",
    "second_order_effect",
    "what_to_ignore",
    "ninety_day_play",
    "operating_rhythm",
    "success_metric",
    "decision_filter",
    "escalation_point",
]


def safe_response(reason: str = "Temporary fallback"):
    return {
        "what_to_do_now": "Stabilize the operating loop: define the outcome, isolate the constraint, and execute one high-leverage move.",
        "decision": "Do not add complexity until the current blocker is removed.",
        "next_move": "Write the desired outcome in one sentence, then choose the one action that moves it forward today.",
        "actions": [
            "Define the exact outcome in one sentence",
            "Identify the single constraint blocking progress",
            "Choose the highest-leverage action that can be completed today",
            "Execute that action before adding more features or options",
            "Review the result and decide whether to scale, fix, or stop"
        ],
        "risk": reason,
        "priority": "high",
        "reality_check": "More features will not fix an unclear operating loop.",
        "leverage": "The fastest improvement comes from removing the constraint, not expanding the system.",
        "hidden_opportunity": "A reliable decision-to-action loop becomes the core advantage.",
        "meeting_agenda": "",
        "follow_up": "",
        "clarifying_question": "What exact outcome do you want by the end of today?",
        "executive_summary": "Stabilize, simplify, execute, review.",
        "financial_impact": "Execution drag wastes time, delays revenue, and increases operating cost.",
        "leadership_implication": "Leadership must force clarity, sequencing, and ownership.",
        "execution_score": "Medium",
        "decision_confidence": "Medium",
        "time_horizon": "Immediate",
        "systems_to_connect": ["Execution System", "Memory", "Calendar"],
        "automation_opportunity": "Turn repeated decisions into an action workflow.",
        "delegation_opportunity": "Assign one owner to the current constraint.",
        "owner": "Executive owner",
        "operating_cadence": "Daily review until the blocker is cleared.",
        "key_metric": "One completed high-leverage action today.",
        "decision_type": "Operating decision",
        "urgency": "high",
        "automation_plan": ["Capture repeated workflow", "Define trigger", "Assign owner", "Review cadence"],
        "service_actions": ["Use Execution System for action tracking", "Use Memory for repeated patterns"],
        "trigger": "Executive command or repeated blocker",
        "required_services": ["Execution System", "Memory"],
        "executive_diagnosis": "The likely issue is not lack of options; it is lack of constraint clarity.",
        "strategic_read": "Simplify the decision surface and force one measurable move.",
        "constraint": "Unclear next action.",
        "unfair_advantage": "Speed of execution once clarity is restored.",
        "second_order_effect": "Cleaner execution compounds into better trust, faster cycles, and less decision fatigue.",
        "what_to_ignore": "Ignore cosmetic improvements until the operating loop works.",
        "ninety_day_play": "Build a repeatable decision-to-action system and remove one major blocker per week.",
        "operating_rhythm": "Daily priority check, weekly review, monthly strategy reset.",
        "success_metric": "Completed priority actions and fewer unresolved open loops.",
        "decision_filter": "Only do work that improves revenue, risk, speed, leverage, or personal operating capacity.",
        "escalation_point": "Escalate if the same blocker appears three times."
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
    return cleaned[:7] or [
        "Clarify the outcome",
        "Identify the constraint",
        "Execute the highest-leverage next move"
    ]


def clean_list(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()][:8]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize(data: Dict[str, Any]):
    if not isinstance(data, dict):
        return safe_response("Invalid response shape")

    priority = str(data.get("priority", "high")).lower().strip()
    if priority not in ["low", "medium", "high", "critical"]:
        priority = "high"

    normalized = {
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
        "systems_to_connect": clean_list(data.get("systems_to_connect")),
        "automation_opportunity": str(data.get("automation_opportunity") or "").strip(),
        "delegation_opportunity": str(data.get("delegation_opportunity") or "").strip(),
        "owner": str(data.get("owner") or "").strip(),
        "operating_cadence": str(data.get("operating_cadence") or "").strip(),
        "key_metric": str(data.get("key_metric") or "").strip(),
        "decision_type": str(data.get("decision_type") or "").strip(),
        "urgency": str(data.get("urgency") or priority).strip(),
        "automation_plan": clean_list(data.get("automation_plan")),
        "service_actions": clean_list(data.get("service_actions")),
        "trigger": str(data.get("trigger") or "").strip(),
        "required_services": clean_list(data.get("required_services")),
        "executive_diagnosis": str(data.get("executive_diagnosis") or "").strip(),
        "strategic_read": str(data.get("strategic_read") or "").strip(),
        "constraint": str(data.get("constraint") or "").strip(),
        "unfair_advantage": str(data.get("unfair_advantage") or "").strip(),
        "second_order_effect": str(data.get("second_order_effect") or "").strip(),
        "what_to_ignore": str(data.get("what_to_ignore") or "").strip(),
        "ninety_day_play": str(data.get("ninety_day_play") or "").strip(),
        "operating_rhythm": str(data.get("operating_rhythm") or "").strip(),
        "success_metric": str(data.get("success_metric") or "").strip(),
        "decision_filter": str(data.get("decision_filter") or "").strip(),
        "escalation_point": str(data.get("escalation_point") or "").strip(),
    }

    return normalized


SYSTEM_PROMPT = """
You are Executive Engine OS V79.

IDENTITY
You are an elite CEO / President / COO operating partner.
You think like a board-level operator, not a generic assistant.
You are direct, specific, commercially aware, and execution-focused.

OPERATING STANDARD
Every answer must improve one or more of:
- revenue
- speed
- risk reduction
- capital efficiency
- leadership clarity
- execution quality
- positioning
- delegation
- operating cadence
- personal operating capacity

RESPONSE QUALITY RULES
- No generic advice.
- No fluffy coaching.
- No vague actions.
- No "research opportunities" unless you specify exactly what to research, where, and why.
- No "conduct a self-assessment" unless it includes a specific framework and next action.
- Every action must be executable today.
- The first action must be immediate and concrete.
- Use the user profile/resume/context aggressively when available.
- Separate signal from noise.
- Identify the real constraint.
- Tell the user what to ignore.
- Give one decisive next move.
- Prioritize signal over completeness.
- Do not overfill optional fields unless they add real executive value.
- Keep the core response readable and high-signal.
- Make "what_to_do_now" the single most useful sentence in the response.
- Make "actions" sequential and time-aware when possible.
- Make "what_to_ignore" concrete, not philosophical.
- Default to practical brevity unless depth is deep.
- Avoid filling every optional field with weak content; only use optional fields when they add value.
- If inputs are messy, clarify the real issue and move them forward.
- If the user needs a business decision, give a real decision, not options paralysis.

OUTPUT DEPTH
sharp: prioritize the first 6 fields and keep optional fields short.
standard: balanced executive output with high-signal optional fields.
deep: include richer diagnosis, second-order effect, 90-day play, operating rhythm, and decision filter.

MODE BEHAVIOR
execution: convert input into action, owner, cadence, metric.
decision: force a call; state tradeoff, risk, and next move.
strategy: find leverage, constraint, sequencing, 90-day play.
meeting: agenda, power dynamics, questions, decision required, follow-up.
risk_review: downside, weak assumptions, mitigation, kill criteria.
proposal: offer, scope, outcome, proof, pricing logic, next step.
personal: practical life execution without sounding corporate.
misc: handle anything; remove noise; identify issue; give next move.
automation: trigger, workflow, owner, output, cadence, open loops.

OUTPUT FORMAT
Return ONLY valid JSON with this exact shape:
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
  "required_services": [],
  "executive_diagnosis": "",
  "strategic_read": "",
  "constraint": "",
  "unfair_advantage": "",
  "second_order_effect": "",
  "what_to_ignore": "",
  "ninety_day_play": "",
  "operating_rhythm": "",
  "success_metric": "",
  "decision_filter": "",
  "escalation_point": ""
}
"""


def build_messages(req: RunRequest):
    context = req.context or "No context"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
MODE:
{req.mode}

OUTPUT DEPTH:
{req.depth or "standard"}

CONTEXT:
{context}

USER INPUT:
{req.input}

DELIVERABLE:
Return elite operator intelligence. Diagnose the real issue, identify constraint, define leverage, state what to ignore, decide next move, and provide actions executable today.
"""
        }
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
        "constraint": output.get("constraint"),
        "leverage": output.get("leverage"),
        "created_at": now(),
    })
    del MEMORY[:-30]


@app.get("/robots.txt")
async def robots_txt():
    return "User-agent: *\nDisallow: /\n"


@app.get("/")
async def root():
    return {"ok": True, "service": APP_NAME}


@app.get("/status")
async def status():
    return {
        "ok": True,
        "service": APP_NAME,
        "backend": "live",
        "elite_output": "ready",
        "profile_intelligence": "ready",
        "internal_automation": "ready",
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }


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
                temperature=0.22,
                max_tokens=1400,
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


@app.get("/go-live-check")
async def go_live_check():
    return {
        "ok": True,
        "service": APP_NAME,
        "backend": "live",
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "model": MODEL,
        "features": {
            "run_endpoint": True,
            "health_endpoint": True,
            "debug_endpoint": True,
            "status_endpoint": True,
            "system_check_endpoint": True,
            "internal_automation_endpoints": True,
            "elite_output_schema": True
        },
        "ready": bool(os.getenv("OPENAI_API_KEY")),
        "message": "Backend is go-live ready when OPENAI_API_KEY is set."
    }


@app.get("/system-check")
async def system_check():
    return {
        "ok": True,
        "service": APP_NAME,
        "backend": "live",
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "model": MODEL,
        "memory_items": len(MEMORY),
        "features": {
            "profile_context": True,
            "internal_automation": True,
            "elite_output": True,
            "command_palette": True,
            "search": True
        }
    }


@app.get("/debug")
async def debug():
    return {
        "ok": True,
        "service": APP_NAME,
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "allowed_origins": ALLOWED_ORIGINS,
        "memory_items": len(MEMORY),
        "version": "V79",
        "routes": [
            "/", "/status", "/health", "/run", "/memory", "/integrations",
            "/automation-plan", "/daily-brief", "/open-loops", "/follow-up",
            "/action-queue", "/go-live-check", "/system-check", "/debug"
        ]
    }


@app.get("/memory")
async def memory():
    return {"memory": MEMORY[-30:]}
