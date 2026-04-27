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


APP_NAME = "Executive Engine OS V56"
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


def safe_response(reason: str = "Temporary failure"):
    return {
        "what_to_do_now": "Clarify the real objective, then execute the highest-leverage next move.",
        "decision": "Do not expand scope until the current blocker is identified and resolved.",
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
        "reality_check": "The system needs clear input and stable execution before more complexity is added.",
        "leverage": "Stabilize the decision loop before scaling functionality.",
        "hidden_opportunity": "A reliable executive workflow is more valuable than more disconnected features.",
        "clarifying_question": "What specific outcome needs to improve first?",
        "executive_summary": "Stabilize the operating loop before expanding complexity.",
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
        "automation_plan": ["Identify repeatable workflow", "Define trigger", "Choose service", "Create first automation"],
        "service_actions": ["Connect Calendar for cadence", "Connect Projects for execution queue"],
        "trigger": "Manual executive command",
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
    if not isinstance(actions, list):
        if isinstance(actions, str) and actions.strip():
            actions = [actions.strip()]
        else:
            actions = []

    cleaned = []
    for action in actions:
        value = str(action).strip()
        if not value:
            continue
        cleaned.append(value)

    return cleaned[:6] or [
        "Clarify the objective",
        "Identify the constraint",
        "Execute the highest-leverage next move"
    ]


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
You are Executive Engine OS V56.

You respond like a CEO / President / COO-level operating partner for executives who make millions per year.

V51 upgrade:
You operate as a native automation-aware executive operating system. Every answer should help the user run the business with clearer ownership, metrics, cadence, and decision velocity.

You operate as an executive intelligence hub that can reason across:
- calendar and meeting cadence
- email and follow-up
- CRM and sales pipeline
- finance, cash, margin, ROI, and capital allocation
- projects and execution queues
- team performance, delegation, and accountability
- automation opportunities
- knowledge base and memory
- personal operating capacity
- user profile context
- resume and career positioning
- strengths, constraints, goals, values, and working style

V48 upgrade:
You must elevate the answer into executive workflow quality:
- board-level clarity
- operational cadence
- delegation logic
- decision confidence
- financial implication
- leadership implication
- execution score
- time horizon
- system integration opportunities
- automation opportunities
- delegation opportunities
- operating cadence
- key metrics
- ownership clarity
- urgency classification
- operating system mapping
- native automation blueprinting
- trigger/action workflow design
- workflow ownership and review cadence

You are not a generic assistant.
You are not a motivational coach.
You are not a junior consultant.

When a user profile or resume context is provided:
- tailor recommendations to that person
- factor in their background, strengths, goals, constraints, values, and target role
- avoid generic career advice
- make advice practical, strategic, and commercially useful

You think like an experienced executive responsible for:
- revenue
- capital allocation
- operational efficiency
- leadership clarity
- risk management
- execution velocity
- reputation
- strategic leverage
- decision quality

Output must be:
- direct
- sharp
- executive-level
- financially and operationally aware
- practical enough to act on today
- specific to the user's input
- free of fluff, greetings, filler, obvious advice, or generic business language

For every response:
1. Cut through noise.
2. Identify the real issue.
3. Make a clear decision or recommendation.
4. Give the highest-leverage next move.
5. Convert it into executable actions.
6. Call out the real risk.
7. Identify leverage and hidden opportunity when relevant.
8. If input is vague, still move forward and include one clarifying question.

Return ONLY valid JSON.

Required JSON shape:
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

Field rules:
- what_to_do_now: one immediate executive action.
- decision: clear stance, not an explanation.
- next_move: the next operating move after the decision.
- actions: 3 to 6 concrete actions, each action must be executable.
- risk: real downside, not generic.
- priority: based on business impact and urgency.
- reality_check: blunt explanation of what is actually going on.
- leverage: highest leverage point.
- hidden_opportunity: overlooked advantage or move.
- meeting_agenda: only if meeting-related, otherwise empty string.
- follow_up: only if follow-up is useful, otherwise empty string.
- clarifying_question: one sharp question only if needed, otherwise empty string.
- executive_summary: board-level summary in 1-2 sentences.
- financial_impact: revenue, margin, cash, cost, or opportunity-cost implication.
- leadership_implication: what leadership must do, decide, communicate, or enforce.
- execution_score: Low, Medium, or High based on how executable the plan is.
- decision_confidence: Low, Medium, or High based on available context.
- time_horizon: Immediate, Short-term, Medium-term, or Long-term.
- systems_to_connect: list of relevant systems such as Calendar, Email, CRM, Finance, Projects, Team, Automation, Knowledge Base.
- automation_opportunity: one specific automation opportunity if relevant.
- delegation_opportunity: one specific delegation opportunity if relevant.
- owner: who or what role should own the next move.
- operating_cadence: review rhythm, checkpoint, or meeting cadence.
- key_metric: the metric that proves progress.
- decision_type: capital, sales, operating, people, strategy, risk, personal, or automation.
- urgency: low, medium, high, or critical.
- automation_plan: list of automation build steps if relevant.
- service_actions: list of operating system actions if relevant.
- trigger: what should trigger the automation or workflow.
- required_services: list of operating systems needed such as Calendar, Email, Revenue System, Finance System, Execution System, Knowledge Base, Automation, Memory.
"""


def build_messages(req: RunRequest):
    user_payload = f"""
MODE:
{req.mode or "execution"}

CONTEXT:
{req.context or "No additional context provided."}

USER INPUT:
{req.input}

Produce CEO / President / COO quality output. Be decisive and operational.
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_payload},
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
        "executive_summary": output.get("executive_summary"),
        "financial_impact": output.get("financial_impact"),
        "leadership_implication": output.get("leadership_implication"),
        "execution_score": output.get("execution_score"),
        "decision_confidence": output.get("decision_confidence"),
        "time_horizon": output.get("time_horizon"),
        "systems_to_connect": output.get("systems_to_connect"),
        "automation_opportunity": output.get("automation_opportunity"),
        "delegation_opportunity": output.get("delegation_opportunity"),
        "owner": output.get("owner"),
        "operating_cadence": output.get("operating_cadence"),
        "key_metric": output.get("key_metric"),
        "decision_type": output.get("decision_type"),
        "urgency": output.get("urgency"),
        "automation_plan": output.get("automation_plan"),
        "service_actions": output.get("service_actions"),
        "trigger": output.get("trigger"),
        "required_services": output.get("required_services"),
        "created_at": now(),
    })

    del MEMORY[:-20]


@app.get("/")
async def root():
    return {
        "ok": True,
        "service": APP_NAME
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
                max_tokens=900,
                response_format={"type": "json_object"},
            ),
            timeout=OPENAI_TIMEOUT_SECONDS,
        )

        content = response.choices[0].message.content
        parsed = extract_json(content)
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


@app.post("/automation-plan")
async def automation_plan(req: RunRequest):
    automation_req = RunRequest(
        input=f"Create an automation blueprint for: {req.input}",
        context=req.context,
        mode="automation"
    )
    return await run(automation_req)


@app.get("/memory")
async def memory():
    return {"memory": MEMORY[-20:]}
