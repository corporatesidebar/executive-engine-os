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


APP_NAME = "Executive Engine OS V48"
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
        "time_horizon": "Immediate"
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
    }


SYSTEM_PROMPT = """
You are Executive Engine OS V48.

You respond like a CEO / President / COO-level operating partner.

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

You are not a generic assistant.
You are not a motivational coach.
You are not a junior consultant.

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
  "time_horizon": "Immediate|Short-term|Medium-term|Long-term"
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


@app.get("/memory")
async def memory():
    return {"memory": MEMORY[-20:]}
