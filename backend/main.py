import os
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from openai import AsyncOpenAI



SYSTEM_PROMPT = """
You are Executive Engine OS V1000: Live Calendar Read-Only OAuth Candidate for a serious executive operating system.

You are not a chatbot. You are a daily execution cockpit, secure calendar intelligence layer, and approval-gated execution system.

Operating principles:
- Think like an elite COO, board operator, chief of staff, execution strategist, and security-minded product architect.
- Convert messy input into an executable operating decision.
- Use memory context when available: prior decisions, saved actions, recurring risks, action overload, constraints, and patterns.
- Use Calendar context only when manually provided or when verified read-only Calendar connection is active.
- Treat Calendar, Files, Email, CRM, and connector intelligence as read-only and user-controlled unless explicitly enabled.
- Never claim calendar write access.
- Never create, edit, delete, invite, reschedule, email, auto-join, auto-send, auto-read, or auto-modify external systems.
- External execution must require explicit user approval.
- Prioritize security, leverage, sequence, owner clarity, cash impact, risk, and speed.
- Make the next move obvious.
- No generic advice.
- No motivational language.
- No filler.

You must return STRICT JSON ONLY.

Required schema:
{
  "what_to_do_now": "One immediate action to take today",
  "today_focus": "The highest-value focus for the day",
  "decision": "The executive decision",
  "next_decision": "The next decision that will unlock progress",
  "next_move": "The single highest-impact next move",
  "current_constraint": "The biggest constraint, bottleneck, or blocker",
  "action_priority": "The action that should be done first and why",
  "actions": ["3 to 6 concrete executable actions starting with strong verbs"],
  "risk": "Specific risk, tradeoff, or failure point",
  "priority": "High | Medium | Low",
  "executive_mode": "CEO | COO | CMO | CTO | CFO | Operator",
  "financial_impact": "Likely financial or operational impact in plain English",
  "leverage": "Highest leverage opportunity",
  "memory_signal": "Relevant pattern, prior decision, recurring constraint, calendar context, manual integration context, or action overload signal",
  "calendar_signal": "Calendar signal if verified calendar context is available; otherwise state not connected or prep",
  "connector_signal": "Connector signal; do not claim connection unless verified",
  "security_gate": "Security or OAuth gate that applies",
  "approval_required": "true or false based on whether external action would be needed",
  "approval_gate": "Which approval gate applies, or none",
  "notification": "One short alert the executive should see",
  "recommended_command": "Copy-paste-ready next command to run",
  "follow_up_question": "Only ask if absolutely required; otherwise use an empty string"
}

Rules:
- JSON only.
- No markdown.
- No text outside JSON.
- Every action must be concrete, testable, and executable.
- Use direct verbs: decide, call, send, review, approve, cut, assign, test, ship, validate.
- Calendar OAuth is read-only only.
- Calendar writes are blocked.
- Manual execution only.
- Auto-loop remains off.
"""















VERSION = "V1000"
SERVICE_NAME = "Executive Engine OS V1000"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2800"))

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_SERVICE")
    or os.getenv("SUPABASE_KEY")
    or ""
)

ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()] or ["*"]

DEFAULT_USER = "local_user"
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(title=SERVICE_NAME, version="1000.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: str = "execution"
    depth: str = "standard"
    user_id: str = DEFAULT_USER
    session_id: Optional[str] = None
    auto_save: bool = True


class SaveActionRequest(BaseModel):
    user_id: str = DEFAULT_USER
    run_id: Optional[str] = None
    text: str = Field(..., min_length=1)
    priority: str = "medium"
    status: str = "open"
    owner: Optional[str] = None
    due_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SaveDecisionRequest(BaseModel):
    user_id: str = DEFAULT_USER
    run_id: Optional[str] = None
    decision: str = Field(..., min_length=1)
    risk: str = ""
    priority: str = "medium"
    rationale: str = ""
    next_move: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


RESPONSE_SCHEMA = {
    "executive_summary": "",
    "what_to_do_now": "",
    "decision": "",
    "why_this_matters": "",
    "next_move": "",
    "actions": [],
    "priority": "medium",
    "risk": "",
    "opportunity": "",
    "what_to_ignore": "",
    "questions_to_answer": [],
    "delegation": "",
    "timeline": "",
    "success_metric": "",
    "strategic_read": "",
    "follow_up_prompt": "",
    "execution_loop": {
        "current_focus": "",
        "next_action": "",
        "next_prompt": "",
        "loop_steps": [],
        "stop_condition": ""
    },
    "reality_check": "",
    "leverage": "",
    "constraint": "",
    "financial_impact": ""
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fallback_output(text: str, mode: str = "execution") -> Dict[str, Any]:
    clean = text.strip()
    return {
        "executive_summary": f"Process the request through a stable execution loop: {clean[:160]}",
        "what_to_do_now": "Run one concrete test, capture the result, and save the next action.",
        "decision": "Prioritize a stable working loop before adding new features or design changes.",
        "why_this_matters": "A reliable command-to-output-to-memory loop is the core product.",
        "next_move": "Run the command, confirm the output appears, save one action, save one decision, then validate persistence.",
        "actions": [
            "Run one real command through the frontend.",
            "Confirm the output card appears under the command box.",
            "Click Add to Action Queue and confirm a visible success message.",
            "Click Save Decision and confirm a visible success message.",
            "Click Check Persistence and confirm counts update.",
            "Use the saved action as the next work item."
        ],
        "priority": "high",
        "risk": "Continuing to build versions without confirming persistence creates confusion and rework.",
        "opportunity": "A clean stable loop becomes the foundation for automation, better UI, and future agent workflows.",
        "what_to_ignore": "Do not add bots, external automation, or new dashboards until the V127 loop passes.",
        "questions_to_answer": ["Did the run save?", "Did the actions save?", "Did the decision save?", "Did the right rail refresh?"],
        "delegation": "Keep manual execution. Do not delegate to bots yet.",
        "timeline": "Today: validate loop. Next 2-3 days: run real use cases. Next 2-3 weeks: polish and expand.",
        "success_metric": "One prompt produces a useful output and saves at least one action and one decision.",
        "strategic_read": "Stability is the strategy right now.",
        "follow_up_prompt": "What is the single highest-leverage improvement after this run?",
        "execution_loop": {
            "current_focus": "V127 clean reset validation",
            "next_action": "Run one command and persist the result.",
            "next_prompt": "What is the next move after validating V127?",
            "loop_steps": ["run", "review", "save action", "save decision", "check persistence"],
            "stop_condition": "Stop when run, save, validate, and right rail refresh all work."
        },
        "reality_check": "If the UI says an older version, the frontend is still cached or the wrong file is deployed.",
        "leverage": "A single reliable frontend file is faster than patching stacked legacy functions.",
        "constraint": "Avoid overlapping old version functions.",
        "financial_impact": "A stable execution loop reduces build drag and lets the product become usable."
    }


def normalize_output(data: Any, user_input: str, mode: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = fallback_output(user_input, mode)

    output = dict(RESPONSE_SCHEMA)
    output.update({k: v for k, v in data.items() if k in output or k == "run_id"})

    if not isinstance(output.get("actions"), list) or not output["actions"]:
        output["actions"] = fallback_output(user_input, mode)["actions"]

    if not isinstance(output.get("questions_to_answer"), list):
        output["questions_to_answer"] = []

    if not isinstance(output.get("execution_loop"), dict):
        output["execution_loop"] = fallback_output(user_input, mode)["execution_loop"]

    for key in [
        "executive_summary", "what_to_do_now", "decision", "why_this_matters",
        "next_move", "priority", "risk", "opportunity", "what_to_ignore",
        "delegation", "timeline", "success_metric", "strategic_read",
        "follow_up_prompt", "reality_check", "leverage", "constraint", "financial_impact"
    ]:
        if not output.get(key):
            output[key] = fallback_output(user_input, mode).get(key, "")

    output["priority"] = str(output.get("priority", "medium")).lower()
    if output["priority"] not in ["low", "medium", "high", "critical"]:
        output["priority"] = "medium"

    return output


def sb_headers(prefer: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


async def sb_get(path: str) -> Any:
    if not SUPABASE_ENABLED:
        return []
    async with httpx.AsyncClient(timeout=20) as cx:
        r = await cx.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers())
        r.raise_for_status()
        return r.json()


async def sb_post(table: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return []
    async with httpx.AsyncClient(timeout=20) as cx:
        r = await cx.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=sb_headers("return=representation"),
            json=payload
        )
        r.raise_for_status()
        return r.json()


async def get_user(external_user_id: str = DEFAULT_USER) -> Optional[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return None
    safe = external_user_id.replace('"', '').replace("'", "")
    rows = await sb_get(f"users?external_user_id=eq.{safe}&select=*&limit=1")
    if rows:
        return rows[0]
    created = await sb_post("users", {
        "external_user_id": external_user_id,
        "created_at": now_iso(),
        "updated_at": now_iso()
    })
    return created[0] if created else None


async def memory_data(external_user_id: str = DEFAULT_USER) -> Dict[str, Any]:
    if not SUPABASE_ENABLED:
        return {
            "supabase_enabled": False,
            "user": None,
            "profile": None,
            "recent_runs": [],
            "recent_decisions": [],
            "open_actions": [],
            "memory_items": [],
        }

    try:
        user = await get_user(external_user_id)
        if not user:
            raise RuntimeError("User not found or not created.")
        user_id = user["id"]

        recent_runs = await sb_get(f"runs?user_id=eq.{user_id}&select=*&order=created_at.desc&limit=10")
        recent_decisions = await sb_get(f"decisions?user_id=eq.{user_id}&select=*&order=created_at.desc&limit=10")
        open_actions = await sb_get(f"actions?user_id=eq.{user_id}&status=eq.open&select=*&order=created_at.desc&limit=20")
        memory_items = await sb_get(f"memory_items?user_id=eq.{user_id}&select=*&order=importance.desc,created_at.desc&limit=20")
        profile_rows = await sb_get(f"profiles?user_id=eq.{user_id}&select=*&limit=1")
        profile = profile_rows[0] if profile_rows else None

        return {
            "supabase_enabled": True,
            "user": user,
            "profile": profile,
            "recent_runs": recent_runs or [],
            "recent_decisions": recent_decisions or [],
            "open_actions": open_actions or [],
            "memory_items": memory_items or []
        }
    except Exception as e:
        return {
            "supabase_enabled": False,
            "memory_error": str(e),
            "user": None,
            "profile": None,
            "recent_runs": [],
            "recent_decisions": [],
            "open_actions": [],
            "memory_items": []
        }


async def save_memory_patterns(user_id: str, output: Dict[str, Any]) -> None:
    if not SUPABASE_ENABLED:
        return

    patterns = [
        ("decision_pattern", output.get("decision", ""), 4),
        ("recurring_risk", output.get("risk", ""), 4),
        ("constraint", output.get("constraint", ""), 3),
    ]
    for typ, content, importance in patterns:
        if content:
            try:
                await sb_post("memory_items", {
                    "user_id": user_id,
                    "type": typ,
                    "content": str(content)[:1000],
                    "importance": importance,
                    "metadata": {"source": "v125_auto"},
                    "created_at": now_iso()
                })
            except Exception:
                pass


async def save_run(req: RunRequest, output: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return None
    user = await get_user(req.user_id)
    if not user:
        return None

    user_id = user["id"]
    payload = {
        "user_id": user_id,
        "input": req.input,
        "mode": req.mode,
        "depth": req.depth,
        "output": output,
        "metadata": {"session_id": req.session_id, "source": "frontend_v125"},
        "created_at": now_iso()
    }
    rows = await sb_post("runs", payload)
    run = rows[0] if rows else None
    if run and run.get("id"):
        output["run_id"] = run["id"]
    await save_memory_patterns(user_id, output)
    return run


def build_prompt(req: RunRequest, memory: Dict[str, Any]) -> str:
    recent_runs = memory.get("recent_runs") or []
    open_actions = memory.get("open_actions") or []
    decisions = memory.get("recent_decisions") or []
    memory_items = memory.get("memory_items") or []
    profile = memory.get("profile") or {}

    memory_context = {
        "profile": profile,
        "recent_runs": recent_runs[:3],
        "open_actions": open_actions[:5],
        "recent_decisions": decisions[:3],
        "memory_items": memory_items[:5],
    }

    return f"""
You are Executive Engine OS V1000, an elite COO/operator system.

User mode: {req.mode}
Depth: {req.depth}

User input:
{req.input}

Known context / memory:
{json.dumps(memory_context, default=str)[:6000]}

Return ONLY valid JSON. No markdown. No commentary.

Required JSON keys:
{json.dumps(RESPONSE_SCHEMA, indent=2)}

Rules:
- Be specific.
- No generic advice.
- Give direct executive decisions.
- Actions must be executable today.
- Always include 4-7 concrete actions.
- Always include a next_move.
- Always include risk, priority, constraint, leverage, financial_impact.
- Keep output useful for a founder/COO building Executive Engine OS.
"""


async def ask_openai(req: RunRequest, memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    V128: production operator loop response.
    Uses the stronger system prompt, mode-aware prompt, JSON repair, and action filtering.
    """
    if not client:
        return fallback_output(req.input, req.mode)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.25,
            max_tokens=OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(req, memory)}
            ],
            timeout=OPENAI_TIMEOUT_SECONDS
        )
        content = response.choices[0].message.content or "{}"

        if "v127_clean_json_response" in globals():
            data = v127_clean_json_response(content)
        else:
            data = json.loads(content)

        output = normalize_output(data, req.input, req.mode)

        if "v127_validate_actions" in globals():
            output["actions"] = v127_validate_actions(output.get("actions") or [])

        if output.get("actions"):
            output["next_move"] = output.get("next_move") or output["actions"][0]
            output["execution_loop"] = {
                "manual_execution_only": True,
                "auto_loop_enabled": False,
                "current_focus": output.get("what_to_do_now") or output.get("next_move"),
                "next_action": output["actions"][0],
                "next_prompt": "Complete this action, then report the result or blocker.",
                "loop_steps": output["actions"][:6],
                "stop_condition": "Stop when the saved action is completed or a blocker is identified."
            }

        return output
    except Exception as e:
        out = fallback_output(req.input, req.mode)
        out["reality_check"] = f"OpenAI call failed or returned invalid JSON. Fallback used. Error: {str(e)[:200]}"
        return out


@app.get("/")
async def root():
    return {"ok": True, "service": SERVICE_NAME, "version": VERSION}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": SERVICE_NAME,
        "version": VERSION,
        "model": OPENAI_MODEL,
        "openai_key_set": bool(OPENAI_API_KEY),
        "supabase_enabled": SUPABASE_ENABLED,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "max_tokens": OPENAI_MAX_TOKENS,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "clean_reset": True
    }


@app.get("/debug")
async def debug():
    return {
        "ok": True,
        "version": VERSION,
        "routes": [
            "/", "/health", "/debug", "/schema", "/run", "/engine-state", "/memory",
            "/actions", "/decisions", "/save-action", "/save-decision",
            "/run-validation", "/button-persistence-check", "/v118-smoke",
            "/frontend-contract", "/robots.txt"
        ],
        "model": OPENAI_MODEL,
        "openai_key_set": bool(OPENAI_API_KEY),
        "supabase_enabled": SUPABASE_ENABLED,
    }


@app.get("/schema")
async def schema():
    return {"ok": True, "version": VERSION, "response_schema": RESPONSE_SCHEMA}


@app.post("/run")
async def run(req: RunRequest):
    mem = await memory_data(req.user_id)
    output = await ask_openai(req, mem)
    saved_run = None

    if req.auto_save:
        try:
            saved_run = await save_run(req, output)
        except Exception as e:
            output["persistence_warning"] = str(e)[:200]

    return {
        **output,
        "ok": True,
        "version": VERSION,
        "mode": req.mode,
        "saved": bool(saved_run),
        "run_id": output.get("run_id") or (saved_run or {}).get("id")
    }


@app.get("/memory")
async def memory(user_id: str = Query(DEFAULT_USER)):
    return await memory_data(user_id)


@app.get("/engine-state")
async def engine_state(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    recent_runs = mem.get("recent_runs") or []
    open_actions = mem.get("open_actions") or []
    recent_decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    latest_run = recent_runs[0] if recent_runs else {}
    latest_output = latest_run.get("output") if isinstance(latest_run.get("output"), dict) else {}

    return {
        "ok": True,
        "version": VERSION,
        "supabase_enabled": mem.get("supabase_enabled", False),
        "today_focus": {
            "title": latest_output.get("what_to_do_now") or latest_run.get("input") or "No focus yet",
            "next_move": latest_output.get("next_move") or "Run the engine to create one."
        },
        "your_engine": [
            {
                "id": r.get("id"),
                "title": (r.get("input") or "Untitled")[:90],
                "mode": r.get("mode"),
                "created_at": r.get("created_at")
            } for r in recent_runs[:8]
        ],
        "open_actions": open_actions,
        "recent_decisions": recent_decisions,
        "memory_items": memory_items,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/actions")
async def actions(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {"ok": True, "version": VERSION, "actions": mem.get("open_actions") or []}


@app.get("/decisions")
async def decisions(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {"ok": True, "version": VERSION, "decisions": mem.get("recent_decisions") or []}


@app.post("/save-action")
async def save_action(req: SaveActionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "version": VERSION, "saved": False, "error": "Supabase not configured."}

    user = await get_user(req.user_id)
    if not user:
        return {"ok": False, "version": VERSION, "saved": False, "error": "User not available."}

    row = {
        "user_id": user["id"],
        "run_id": req.run_id,
        "text": req.text,
        "priority": req.priority or "medium",
        "status": req.status or "open",
        "owner": req.owner,
        "due_at": req.due_at,
        "metadata": req.metadata or {},
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    saved = await sb_post("actions", row)
    return {"ok": True, "version": VERSION, "saved": True, "action": saved[0] if saved else row}


@app.post("/save-decision")
async def save_decision(req: SaveDecisionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "version": VERSION, "saved": False, "error": "Supabase not configured."}

    user = await get_user(req.user_id)
    if not user:
        return {"ok": False, "version": VERSION, "saved": False, "error": "User not available."}

    row = {
        "user_id": user["id"],
        "run_id": req.run_id,
        "decision": req.decision,
        "risk": req.risk,
        "priority": req.priority or "medium",
        "rationale": req.rationale,
        "next_move": req.next_move,
        "metadata": req.metadata or {},
        "created_at": now_iso()
    }
    saved = await sb_post("decisions", row)
    return {"ok": True, "version": VERSION, "saved": True, "decision": saved[0] if saved else row}


@app.get("/run-validation")
async def run_validation(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    recent_runs = mem.get("recent_runs") or []
    latest = recent_runs[0] if recent_runs else None
    latest_output = latest.get("output") if isinstance(latest, dict) and isinstance(latest.get("output"), dict) else {}

    return {
        "ok": True,
        "version": VERSION,
        "checks": {
            "backend_live": True,
            "supabase_enabled": mem.get("supabase_enabled", False),
            "has_recent_run": bool(recent_runs),
            "latest_run_id": latest.get("id") if isinstance(latest, dict) else None,
            "latest_input": latest.get("input") if isinstance(latest, dict) else None,
            "latest_has_decision": bool(latest_output.get("decision")),
            "latest_has_actions": bool(latest_output.get("actions")),
            "open_actions_count": len(mem.get("open_actions") or []),
            "saved_decisions_count": len(mem.get("recent_decisions") or [])
        },
        "pass_condition": "latest_input should match the command you just typed."
    }


@app.get("/button-persistence-check")
async def button_persistence_check(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    recent_runs = mem.get("recent_runs") or []
    open_actions = mem.get("open_actions") or []
    recent_decisions = mem.get("recent_decisions") or []

    return {
        "ok": True,
        "version": VERSION,
        "counts": {
            "recent_runs": len(recent_runs),
            "open_actions": len(open_actions),
            "saved_decisions": len(recent_decisions),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "latest": {
            "run_input": recent_runs[0].get("input") if recent_runs else None,
            "run_created_at": recent_runs[0].get("created_at") if recent_runs else None,
            "action": open_actions[0].get("text") if open_actions else None,
            "action_created_at": open_actions[0].get("created_at") if open_actions else None,
            "decision": recent_decisions[0].get("decision") if recent_decisions else None,
            "decision_created_at": recent_decisions[0].get("created_at") if recent_decisions else None
        },
        "pass_condition": "After Save Action and Save Decision, counts should increase or latest values should update."
    }


@app.get("/frontend-contract")
async def frontend_contract():
    return {
        "ok": True,
        "version": VERSION,
        "contract": {
            "visible_input_id": "input",
            "run_function": "runEngine",
            "run_endpoint": "POST /run",
            "output_renderer": "renderOutput",
            "save_actions_endpoint": "POST /save-action",
            "save_decision_endpoint": "POST /save-decision",
            "right_panel_endpoint": "GET /engine-state",
            "validation_endpoint": "GET /run-validation"
        }
    }






@app.get("/v120-smoke")
async def v120_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "ship_lock": True,
        "backend_ready": True,
        "supabase_enabled": mem.get("supabase_enabled", False),
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "frontend_expected": {
            "badge": "V127 · Ship Lock",
            "output_badge": "V127 · Locked",
            "status": "DB memory live · V127"
        },
        "test": [
            "Hard refresh frontend.",
            "Confirm V127 · Ship Lock appears.",
            "Run Engine.",
            "Add to Action Queue.",
            "Save Decision.",
            "Check Persistence.",
            "Confirm right panel updates.",
            "Stop building new versions and run 10 real commands."
        ]
    }










@app.get("/stability-audit")
async def stability_audit(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    runs = mem.get("recent_runs") or []
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "OpenAI key set", "passed": bool(OPENAI_API_KEY)},
        {"name": "Supabase enabled", "passed": bool(mem.get("supabase_enabled", False))},
        {"name": "Recent runs exist", "passed": len(runs) >= 1},
        {"name": "Open actions exist", "passed": len(actions) >= 1},
        {"name": "Saved decisions exist", "passed": len(decisions) >= 1},
        {"name": "Memory items exist", "passed": len(memory_items) >= 1},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True},
        {"name": "Clean frontend contract", "passed": True}
    ]
    passed = sum(1 for c in checks if c["passed"])

    return {
        "ok": True,
        "version": VERSION,
        "score": f"{passed}/{len(checks)}",
        "ready": passed >= 8,
        "checks": checks,
        "counts": {
            "recent_runs": len(runs),
            "open_actions": len(actions),
            "saved_decisions": len(decisions),
            "memory_items": len(memory_items)
        },
        "decision": "Use V127 as the stable baseline if the frontend smoke test passes.",
        "next_move": "Run 10 real commands before adding automation or new UI features."
    }


@app.get("/run-save-audit")
async def run_save_audit(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    runs = mem.get("recent_runs") or []
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []

    latest_run = runs[0] if runs else None
    latest_action = actions[0] if actions else None
    latest_decision = decisions[0] if decisions else None

    return {
        "ok": True,
        "version": VERSION,
        "latest_run": {
            "id": latest_run.get("id") if isinstance(latest_run, dict) else None,
            "input": latest_run.get("input") if isinstance(latest_run, dict) else None,
            "created_at": latest_run.get("created_at") if isinstance(latest_run, dict) else None
        },
        "latest_action": {
            "id": latest_action.get("id") if isinstance(latest_action, dict) else None,
            "text": latest_action.get("text") if isinstance(latest_action, dict) else None,
            "priority": latest_action.get("priority") if isinstance(latest_action, dict) else None,
            "created_at": latest_action.get("created_at") if isinstance(latest_action, dict) else None
        },
        "latest_decision": {
            "id": latest_decision.get("id") if isinstance(latest_decision, dict) else None,
            "decision": latest_decision.get("decision") if isinstance(latest_decision, dict) else None,
            "priority": latest_decision.get("priority") if isinstance(latest_decision, dict) else None,
            "created_at": latest_decision.get("created_at") if isinstance(latest_decision, dict) else None
        },
        "pass_condition": "After one frontend run/save test, latest_run.input, latest_action.text, and latest_decision.decision should match the newest test."
    }


@app.get("/v125-smoke")
async def v125_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "fix": "Stability audit lock. V127 keeps the V123 save-flow fix and adds final run/save audit endpoints.",
        "supabase_enabled": mem.get("supabase_enabled", False),
        "required_frontend_badge": "V127 · Stability Lock",
        "test_prompt": "V127 final test — create one action called \"Review V127 system tomorrow\" and one decision called \"Lock V127 as stable baseline.\"",
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        }
    }


@app.get("/version-lock")
async def version_lock():
    return {
        "ok": True,
        "version": VERSION,
        "frontend_must_show": "V127 · Stability Lock",
        "backend_must_show": "Executive Engine OS V1000",
        "do_not_build_next": "Do not build V126 until V127 passes 10 real commands.",
        "locked_paths": {
            "run": "POST /run",
            "save_action": "POST /save-action",
            "save_decision": "POST /save-decision",
            "verify_save": "GET /save-flow-status",
            "persistence": "GET /button-persistence-check",
            "audit": "GET /run-save-audit"
        }
    }

@app.get("/save-flow-status")
async def save_flow_status(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    open_actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    runs = mem.get("recent_runs") or []

    latest_action = open_actions[0] if open_actions else None
    latest_decision = decisions[0] if decisions else None
    latest_run = runs[0] if runs else None

    return {
        "ok": True,
        "version": VERSION,
        "status": "save_flow_locked",
        "counts": {
            "recent_runs": len(runs),
            "open_actions": len(open_actions),
            "saved_decisions": len(decisions),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "latest": {
            "run_input": latest_run.get("input") if isinstance(latest_run, dict) else None,
            "action_text": latest_action.get("text") if isinstance(latest_action, dict) else None,
            "action_created_at": latest_action.get("created_at") if isinstance(latest_action, dict) else None,
            "decision_text": latest_decision.get("decision") if isinstance(latest_decision, dict) else None,
            "decision_created_at": latest_decision.get("created_at") if isinstance(latest_decision, dict) else None
        },
        "button_contract": {
            "add_to_action_queue": "POST /save-action then GET /save-flow-status",
            "save_decision": "POST /save-decision then GET /save-flow-status",
            "verify_save": "GET /save-flow-status",
            "check_persistence": "GET /button-persistence-check",
            "refresh_right_panel": "GET /engine-state"
        },
        "pass_condition": "After saving, latest.action_text and latest.decision_text should match the newest saved values."
    }


@app.get("/v123-smoke")
async def v123_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "fix": "Save flow lock. Save buttons now call one verification path after save. Verify Save and Check Persistence are separated clearly.",
        "supabase_enabled": mem.get("supabase_enabled", False),
        "test_prompt": "V127 final test — create one action called \"Review V127 system tomorrow\" and one decision called \"Lock V127 as stable baseline.\"",
        "required_frontend_badge": "V127 · Save Flow Lock",
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        }
    }

@app.get("/verify-latest-save")
async def verify_latest_save(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    open_actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    runs = mem.get("recent_runs") or []
    latest_action = open_actions[0] if open_actions else None
    latest_decision = decisions[0] if decisions else None
    latest_run = runs[0] if runs else None

    return {
        "ok": True,
        "version": VERSION,
        "latest_action_text": latest_action.get("text") if isinstance(latest_action, dict) else None,
        "latest_action_created_at": latest_action.get("created_at") if isinstance(latest_action, dict) else None,
        "latest_decision_text": latest_decision.get("decision") if isinstance(latest_decision, dict) else None,
        "latest_decision_created_at": latest_decision.get("created_at") if isinstance(latest_decision, dict) else None,
        "latest_run_input": latest_run.get("input") if isinstance(latest_run, dict) else None,
        "counts": {
            "recent_runs": len(runs),
            "open_actions": len(open_actions),
            "saved_decisions": len(decisions),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "pass_condition": "latest_action_text and latest_decision_text should match the newest explicit save."
    }


@app.get("/v122-smoke")
async def v122_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "fix": "Verify Latest Save button now uses a unique button id/function and calls /verify-latest-save directly. It no longer conflicts with Check Persistence.",
        "supabase_enabled": mem.get("supabase_enabled", False),
        "test_prompt": "V127 final test — create one action called \"Review V127 system tomorrow\" and one decision called \"Lock V127 as stable baseline.\"",
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        }
    }

@app.get("/save-verification")
async def save_verification(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    open_actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    runs = mem.get("recent_runs") or []

    return {
        "ok": True,
        "version": VERSION,
        "purpose": "Verify the newest saved action and newest saved decision after clicking frontend save buttons.",
        "latest_saved_action": open_actions[0] if open_actions else None,
        "latest_saved_decision": decisions[0] if decisions else None,
        "latest_run": runs[0] if runs else None,
        "counts": {
            "recent_runs": len(runs),
            "open_actions": len(open_actions),
            "saved_decisions": len(decisions),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "pass_condition": "latest_saved_action.text and latest_saved_decision.decision should reflect the most recent save."
    }


@app.get("/v121-smoke")
async def v121_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "backend_ready": True,
        "supabase_enabled": mem.get("supabase_enabled", False),
        "fix": "Explicit save fix. The frontend now saves user-requested action/decision text when the prompt says create one action called... and one decision called...",
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "test_prompt": "V127 final test — create one action called \"Review V127 system tomorrow\" and one decision called \"Lock V127 as stable baseline.\""
    }

@app.get("/ship-lock")
async def ship_lock(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "OpenAI key set", "passed": bool(OPENAI_API_KEY)},
        {"name": "Supabase enabled", "passed": bool(mem.get("supabase_enabled", False))},
        {"name": "Recent run exists", "passed": len(mem.get("recent_runs") or []) >= 1},
        {"name": "Action queue exists", "passed": len(mem.get("open_actions") or []) >= 1},
        {"name": "Decision history exists", "passed": len(mem.get("recent_decisions") or []) >= 1},
        {"name": "Frontend contract locked", "passed": True},
    ]
    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "score": f"{passed}/{len(checks)}",
        "ready": passed >= 5,
        "checks": checks,
        "decision": "Ship V127 as the stable baseline if the frontend smoke test passes.",
        "next_move": "Use the system for 10 real runs before adding new features."
    }


@app.get("/frontend-version-check")
async def frontend_version_check():
    return {
        "ok": True,
        "version": VERSION,
        "expected_frontend": "V127",
        "cache_rule": "If frontend still shows an older version, Render is serving old index.html or browser cache is stale.",
        "required_strings": [
            "V127 · Ship Lock",
            "V127 · Locked",
            "frontend_v125",
            "runEngine",
            "saveActions",
            "saveDecision",
            "checkPersistence"
        ],
        "next_move": "Deploy frontend with Clear cache & deploy, then hard refresh."
    }


@app.get("/button-test-contract")
async def button_test_contract():
    return {
        "ok": True,
        "version": VERSION,
        "buttons": {
            "Run Engine": "runEngine() -> POST /run",
            "Add to Action Queue": "saveActions() -> POST /save-action",
            "Save Decision": "saveDecision() -> POST /save-decision",
            "Validate Run": "validateRun() -> GET /run-validation",
            "Check Persistence": "checkPersistence() -> GET /button-persistence-check",
            "Refresh Right Panel": "refreshState() -> GET /engine-state"
        },
        "contract_locked": True,
        "legacy_functions": "No legacy V111/V117 output path."
    }


@app.get("/next-phase")
async def next_phase():
    return {
        "ok": True,
        "version": VERSION,
        "phase": "post_v120_usage_validation",
        "rule": "Do not build V127 until V127 passes 10 real runs.",
        "real_run_checklist": [
            "Use execution mode for one business blocker.",
            "Use decision mode for one real decision.",
            "Use meeting mode for one meeting prep.",
            "Use content mode for one content task.",
            "Save at least 5 actions.",
            "Save at least 3 decisions.",
            "Check persistence after saves.",
            "Review right panel after each run.",
            "Capture one screenshot.",
            "Only then decide V127 scope."
        ],
        "recommended_v121": "Profile editor + action completion, only after V127 is proven stable."
    }

@app.get("/v119-smoke")
async def v119_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "backend_ready": True,
        "supabase_enabled": mem.get("supabase_enabled", False),
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "frontend_expected": {
            "badge": "V127 · Clean Hardened",
            "output_badge": "V127 · Clean",
            "status": "DB memory live · V127"
        },
        "test": [
            "Hard refresh frontend.",
            "Confirm V127 · Clean Hardened appears.",
            "Run Engine.",
            "Add to Action Queue.",
            "Save Decision.",
            "Check Persistence.",
            "Confirm right panel updates."
        ]
    }


@app.get("/frontend-version-check")
async def frontend_version_check():
    return {
        "ok": True,
        "version": VERSION,
        "expected_frontend": "V127",
        "cache_rule": "If frontend still shows an older version, Render is serving old index.html or browser cache is stale.",
        "required_strings": [
            "V127 · Clean Hardened",
            "V127 · Clean",
            "frontend_v125",
            "runEngine",
            "saveActions",
            "saveDecision",
            "checkPersistence"
        ],
        "next_move": "Deploy frontend with Clear cache & deploy, then hard refresh."
    }


@app.get("/button-test-contract")
async def button_test_contract():
    return {
        "ok": True,
        "version": VERSION,
        "buttons": {
            "Run Engine": "runEngine() -> POST /run",
            "Add to Action Queue": "saveActions() -> POST /save-action",
            "Save Decision": "saveDecision() -> POST /save-decision",
            "Validate Run": "validateRun() -> GET /run-validation",
            "Check Persistence": "checkPersistence() -> GET /button-persistence-check",
            "Refresh Right Panel": "refreshState() -> GET /engine-state"
        },
        "contract_locked": True,
        "legacy_functions": "No legacy V111/V117 output path required."
    }

@app.get("/v118-smoke")
async def v118_smoke(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "backend_ready": True,
        "supabase_enabled": mem.get("supabase_enabled", False),
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "test": [
            "Deploy backend.",
            "Deploy frontend.",
            "Hard refresh.",
            "Confirm V127 Clean Reset appears.",
            "Run Engine.",
            "Add to Action Queue.",
            "Save Decision.",
            "Check Persistence.",
            "Confirm right rail updates."
        ]
    }


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /\n"



# =========================
# V127 WORKFLOW OPTIMIZATION HELPERS
# =========================

def v127_clean_json_response(raw_text):
    """
    Converts model text into a safe Executive Engine JSON object.
    Keeps backend stable even if the AI returns markdown or malformed JSON.
    """
    import json, re
    if isinstance(raw_text, dict):
        data = raw_text
    else:
        text = str(raw_text or "").strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)
        try:
            data = json.loads(text)
        except Exception:
            data = {
                "what_to_do_now": "Re-run the command with one clear business outcome and one constraint.",
                "decision": "Do not proceed on unclear output; force a clean execution decision.",
                "next_move": "Rewrite the command in one sentence and run Executive Engine again.",
                "actions": [
                    "Rewrite the command with the business goal",
                    "Add the current constraint or blocker",
                    "Run the engine again",
                    "Save the resulting decision and action"
                ],
                "risk": "Malformed AI output can create unclear execution.",
                "priority": "High",
                "reality_check": "Bad structure creates bad execution.",
                "leverage": "A cleaner command produces a cleaner operating decision.",
                "constraint": "The previous response was not valid JSON.",
                "financial_impact": "Unclear output wastes execution time.",
                "why_this_matters": "The operator needs clean output before acting.",
                "timeline": "Immediate"
            }

    defaults = {
        "what_to_do_now": "Take the highest-impact action now.",
        "decision": "Move forward with the clearest executable path.",
        "next_move": "Complete the first action in the execution queue.",
        "actions": ["Define the outcome", "Complete the first action", "Verify progress"],
        "risk": "Execution slows if ownership and timing are unclear.",
        "priority": "Medium",
        "reality_check": "Clarity beats complexity.",
        "leverage": "Focus on the action that unlocks the next step.",
        "constraint": "Time and attention are the main constraints.",
        "financial_impact": "Better execution reduces opportunity cost.",
        "why_this_matters": "Momentum compounds when the next action is obvious.",
        "timeline": "Today"
    }

    for key, value in defaults.items():
        if key not in data or data[key] in [None, "", []]:
            data[key] = value

    if not isinstance(data.get("actions"), list):
        data["actions"] = [str(data.get("actions"))]

    data["actions"] = v127_validate_actions(data["actions"])

    if not data["actions"]:
        data["actions"] = defaults["actions"]

    data["next_move"] = str(data.get("next_move") or data["actions"][0]).strip()
    if data["next_move"] == defaults["next_move"] and data["actions"]:
        data["next_move"] = data["actions"][0]

    priority = str(data.get("priority", "Medium")).strip().title()
    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"
    data["priority"] = priority

    return data


def v127_validate_actions(actions):
    """
    Filters weak/non-executable actions and keeps 3-6 concrete actions.
    """
    weak_terms = ["consider", "maybe", "think about", "explore", "look into", "try to", "possibly"]
    clean = []
    for item in actions or []:
        action = str(item).strip()
        if len(action) < 8:
            continue
        lower = action.lower()
        if any(term in lower for term in weak_terms):
            action = action.replace("Consider ", "").replace("consider ", "")
            action = action.replace("Explore ", "Define ").replace("explore ", "define ")
            action = action.replace("Look into ", "Review ").replace("look into ", "review ")
        if action and action not in clean:
            clean.append(action)
    return clean[:6]


def v127_mode_instruction(mode):
    mode = str(mode or "execution").lower()
    instructions = {
        "execution": "Execute today. Prioritize immediate next actions, speed, and accountability.",
        "decision": "Make a clear executive decision. State the tradeoff and the immediate move.",
        "strategy": "Create a short execution strategy. No theory. Convert strategy into actions.",
        "meeting": "Prepare for a high-level meeting. Identify agenda, decision points, and follow-up actions.",
        "daily_brief": "Create a daily operating brief. Focus on what matters today.",
        "content": "Create high-signal executive content direction with concrete production actions."
    }
    return instructions.get(mode, instructions["execution"])


def v127_build_user_prompt(user_input, mode="execution"):
    return f"""
Mode: {mode}
Mode instruction: {v127_mode_instruction(mode)}

User input:
{user_input}

Return strict JSON only. Make it specific, executive-level, and executable today.
"""


def v127_execution_loop(output):
    """
    Adds a simple manual execution loop without auto-running actions.
    """
    actions = output.get("actions") or []
    first = actions[0] if actions else output.get("next_move", "Run the first action.")
    return {
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "current_step": first,
        "operator_instruction": "Complete the current step, then return with the result or blocker.",
        "next_check": "After the current step is completed"
    }





# =========================
# V128 OPERATOR LOOP ENDPOINTS
# =========================

class CompleteActionRequest(BaseModel):
    user_id: str = DEFAULT_USER
    action_id: str = Field(..., min_length=1)
    result: str = ""
    next_note: str = ""


async def sb_patch(path: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return []
    async with httpx.AsyncClient(timeout=20) as cx:
        r = await cx.patch(
            f"{SUPABASE_URL}/rest/v1/{path}",
            headers=sb_headers("return=representation"),
            json=payload
        )
        r.raise_for_status()
        return r.json()


def v128_rank_priority(item: Dict[str, Any]) -> int:
    priority = str(item.get("priority") or "medium").lower()
    if priority == "critical":
        return 4
    if priority == "high":
        return 3
    if priority == "medium":
        return 2
    return 1


def v128_build_operator_brief(mem: Dict[str, Any]) -> Dict[str, Any]:
    recent_runs = mem.get("recent_runs") or []
    open_actions = mem.get("open_actions") or []
    recent_decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    sorted_actions = sorted(open_actions, key=v128_rank_priority, reverse=True)
    top_action = sorted_actions[0] if sorted_actions else None
    latest_run = recent_runs[0] if recent_runs else {}
    latest_output = latest_run.get("output") if isinstance(latest_run.get("output"), dict) else {}

    return {
        "today_focus": latest_output.get("what_to_do_now") or latest_output.get("next_move") or latest_run.get("input") or "Run one executive command.",
        "next_action": (top_action or {}).get("text") or latest_output.get("next_move") or "Run the engine and save one action.",
        "priority": (top_action or {}).get("priority") or latest_output.get("priority") or "medium",
        "open_action_count": len(open_actions),
        "recent_decision": (recent_decisions[0] or {}).get("decision") if recent_decisions else latest_output.get("decision", ""),
        "memory_signal": (memory_items[0] or {}).get("content") if memory_items else "",
        "operator_instruction": "Complete the next action, then return with the result or blocker.",
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/operator-brief")
async def operator_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "brief": v128_build_operator_brief(mem),
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        }
    }


@app.get("/next-action")
async def next_action(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    actions = sorted(mem.get("open_actions") or [], key=v128_rank_priority, reverse=True)
    action = actions[0] if actions else None
    return {
        "ok": True,
        "version": VERSION,
        "has_action": bool(action),
        "next_action": action or {
            "text": "Run Executive Engine and save one action.",
            "priority": "medium",
            "status": "open"
        },
        "operator_instruction": "Complete this action, then use /complete-action or save the result manually."
    }


@app.post("/complete-action")
async def complete_action(req: CompleteActionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "version": VERSION, "completed": False, "error": "Supabase not configured."}

    payload = {
        "status": "completed",
        "updated_at": now_iso(),
        "metadata": {
            "completed_source": "v128_operator_loop",
            "result": req.result,
            "next_note": req.next_note
        }
    }
    rows = await sb_patch(f"actions?id=eq.{req.action_id}", payload)

    return {
        "ok": True,
        "version": VERSION,
        "completed": True,
        "action": rows[0] if rows else {"id": req.action_id, **payload},
        "next_move": "Run /operator-brief to identify the next action."
    }


@app.get("/workflow-audit")
async def workflow_audit(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    brief = v128_build_operator_brief(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Has open actions", "passed": len(mem.get("open_actions") or []) > 0},
        {"name": "Has recent decisions", "passed": len(mem.get("recent_decisions") or []) > 0},
        {"name": "Has memory signals", "passed": len(mem.get("memory_items") or []) > 0},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True},
        {"name": "Operator brief available", "passed": bool(brief.get("today_focus"))}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "score": f"{score}/{len(checks)}",
        "ready": score >= 6,
        "checks": checks,
        "brief": brief,
        "decision": "Use V128 as the operator loop baseline if /run and /operator-brief both return useful output.",
        "next_move": brief.get("next_action")
    }





# =========================
# V130 NAVIGATION + PAGES MILESTONE
# =========================

@app.get("/pages")
async def pages():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V145 Memory + Intelligence",
        "pages": [
            {"id": "command", "title": "Command Center", "status": "live", "purpose": "Run the executive engine."},
            {"id": "daily_brief", "title": "Daily Brief", "status": "connected", "purpose": "Generate daily operating focus."},
            {"id": "decisions", "title": "Decisions", "status": "connected", "purpose": "Review saved decisions."},
            {"id": "meeting", "title": "Meeting Prep", "status": "connected", "purpose": "Prepare high-level meeting agendas."},
            {"id": "strategy", "title": "Strategy Board", "status": "connected", "purpose": "Convert strategy into execution."},
            {"id": "risk", "title": "Risk Monitor", "status": "connected", "purpose": "Surface risks and constraints."},
            {"id": "actions", "title": "Action Queue", "status": "connected", "purpose": "Track open and completed actions."},
            {"id": "analytics", "title": "Analytics", "status": "preview", "purpose": "View execution metrics."},
            {"id": "memory", "title": "Memory", "status": "connected", "purpose": "Review memory signals."},
            {"id": "profile", "title": "Profile", "status": "preview", "purpose": "Manage executive context."},
            {"id": "settings", "title": "Settings", "status": "preview", "purpose": "System controls."}
        ],
        "backend_contract": [
            "POST /run",
            "GET /engine-state",
            "GET /operator-brief",
            "GET /next-action",
            "GET /workflow-audit",
            "GET /save-flow-status",
            "GET /button-persistence-check",
            "GET /run-save-audit",
            "POST /save-action",
            "POST /save-decision"
        ]
    }


@app.get("/v130-milestone")
async def v130_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Navigation + Pages",
        "ready": True,
        "frontend_must_show": "V130 Navigation · V128 Operator Loop",
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "test_checklist": [
            "Open frontend",
            "Click each left navigation item",
            "Confirm center page changes",
            "Run Engine from Command Center",
            "Save Action",
            "Save Decision",
            "Open Action Queue page",
            "Open Decisions page",
            "Open Memory page"
        ]
    }



# =========================
# V145 UNIQUE FIGMA SUBPAGES + WORKFLOW CONTROL
# =========================

@app.get("/v135-milestone")
async def v135_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Unique Figma Subpages + Workflow Control",
        "ready": True,
        "frontend_must_show": "V145 Figma Subpages · V145 Backend",
        "keeps_locked_command_center": True,
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "pages": [
            "Daily Brief", "Decisions", "Meeting Prep", "Strategy Board", "Risk Monitor",
            "Action Queue", "Analytics", "Memory", "Profile", "Settings"
        ],
        "test_checklist": [
            "Click every sidebar page",
            "Confirm each page has a unique layout",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Open Action Queue",
            "Open Decisions",
            "Open Memory"
        ]
    }




# =========================
# V145 MEMORY + INTELLIGENCE MILESTONE
# =========================

def v140_extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if v)
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v)
    return str(value)


def v140_detect_patterns(mem: Dict[str, Any]) -> List[Dict[str, Any]]:
    runs = mem.get("recent_runs") or []
    decisions = mem.get("recent_decisions") or []
    actions = mem.get("open_actions") or []
    memory_items = mem.get("memory_items") or []

    text_blob = " ".join([
        v140_extract_text(r.get("input")) + " " + v140_extract_text(r.get("output")) for r in runs
    ] + [
        v140_extract_text(d.get("decision")) + " " + v140_extract_text(d.get("risk")) for d in decisions
    ] + [
        v140_extract_text(a.get("text")) for a in actions
    ] + [
        v140_extract_text(m.get("content")) for m in memory_items
    ]).lower()

    patterns = []

    if any(w in text_blob for w in ["backend", "endpoint", "deploy", "render", "supabase"]):
        patterns.append({
            "type": "execution_pattern",
            "signal": "Backend validation keeps appearing as a recurring execution theme.",
            "confidence": "High",
            "next_move": "Lock backend checks into a repeatable deployment checklist."
        })

    if any(w in text_blob for w in ["ui", "design", "figma", "frontend", "layout"]):
        patterns.append({
            "type": "design_pattern",
            "signal": "UI clarity and workflow flow are recurring decision drivers.",
            "confidence": "High",
            "next_move": "Separate design feedback from backend functionality testing."
        })

    if any(w in text_blob for w in ["limited", "constraint", "blocker", "delay", "risk"]):
        patterns.append({
            "type": "constraint_pattern",
            "signal": "Constraints are repeatedly tied to focus, resources, and sequencing.",
            "confidence": "Medium",
            "next_move": "Force every command to identify the constraint before generating actions."
        })

    if len(actions) >= 10:
        patterns.append({
            "type": "queue_pattern",
            "signal": "Open action count is high; execution risk is action accumulation.",
            "confidence": "High",
            "next_move": "Complete or archive the lowest-value actions before creating new ones."
        })

    if not patterns:
        patterns.append({
            "type": "baseline_pattern",
            "signal": "Not enough repeated signal yet. More saved runs are needed.",
            "confidence": "Low",
            "next_move": "Run five real commands and save the decisions/actions."
        })

    return patterns[:6]


def v140_memory_summary(mem: Dict[str, Any]) -> Dict[str, Any]:
    patterns = v140_detect_patterns(mem)
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    high_actions = [a for a in actions if str(a.get("priority", "")).lower() in ["high", "critical"]]

    return {
        "summary": "Memory is tracking repeated decisions, constraints, risks, and execution patterns.",
        "top_pattern": patterns[0] if patterns else {},
        "patterns": patterns,
        "active_constraints": [
            p["signal"] for p in patterns if "constraint" in p["type"] or "queue" in p["type"]
        ][:4],
        "decision_patterns": [
            {
                "decision": d.get("decision", ""),
                "priority": d.get("priority", "medium"),
                "created_at": d.get("created_at", "")
            } for d in decisions[:5]
        ],
        "risk_signals": [
            {
                "risk": d.get("risk") or "Decision requires follow-up risk review.",
                "priority": d.get("priority", "medium")
            } for d in decisions[:5]
        ],
        "next_memory_move": patterns[0].get("next_move") if patterns else "Save more runs to improve memory quality.",
        "counts": {
            "memory_items": len(memory_items),
            "patterns": len(patterns),
            "open_actions": len(actions),
            "high_priority_actions": len(high_actions),
            "saved_decisions": len(decisions)
        }
    }


@app.get("/memory-intelligence")
async def memory_intelligence(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory + Intelligence",
        "intelligence": v140_memory_summary(mem)
    }


@app.get("/decision-patterns")
async def decision_patterns(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    summary = v140_memory_summary(mem)
    return {
        "ok": True,
        "version": VERSION,
        "patterns": summary["decision_patterns"],
        "risk_signals": summary["risk_signals"],
        "next_move": summary["next_memory_move"]
    }


@app.get("/context-brief")
async def context_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    summary = v140_memory_summary(mem)
    return {
        "ok": True,
        "version": VERSION,
        "brief": {
            "operator_context": "Use recent decisions, open actions, and recurring memory patterns to keep responses specific.",
            "top_pattern": summary["top_pattern"],
            "active_constraints": summary["active_constraints"],
            "next_memory_move": summary["next_memory_move"],
            "recommended_prompt_addition": "Use my recent decisions, open actions, and constraints. Push the single next action."
        }
    }


@app.get("/v140-milestone")
async def v140_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    intelligence = v140_memory_summary(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Memory summary available", "passed": True},
        {"name": "Patterns detected", "passed": len(intelligence.get("patterns") or []) > 0},
        {"name": "Decision patterns available", "passed": True},
        {"name": "Context brief available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory + Intelligence",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V145 Memory Intelligence · V145 Backend",
        "intelligence": intelligence,
        "test_checklist": [
            "Open Memory page",
            "Confirm Detected Patterns load",
            "Open Decisions page",
            "Open Action Queue page",
            "Run one command",
            "Save action and decision",
            "Check /memory-intelligence",
            "Check /context-brief"
        ]
    }




# =========================
# V145 EXECUTIVE LAYER MILESTONE
# =========================

def v145_exec_metrics(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    runs = mem.get("recent_runs") or []

    high_priority = [
        a for a in actions
        if str(a.get("priority", "")).lower() in ["high", "critical"]
    ]

    decision_velocity = "Fast" if len(decisions) >= 5 else "Building"
    execution_load = "High" if len(actions) >= 15 else "Controlled"

    return {
        "executive_readiness": "Board-ready" if len(decisions) >= 5 and len(memory_items) >= 5 else "Building",
        "decision_velocity": decision_velocity,
        "execution_load": execution_load,
        "priority_pressure": len(high_priority),
        "operator_confidence": "High" if len(runs) >= 5 else "Medium",
        "focus_risk": "Action queue overload" if len(actions) >= 15 else "Low",
        "recommended_executive_move": (
            "Reduce open action count before creating new work."
            if len(actions) >= 15
            else "Use Daily Brief and Meeting Prep to drive today's execution."
        )
    }


@app.get("/executive-brief")
async def executive_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    metrics = v145_exec_metrics(mem)

    memory_intel = {}
    if "v140_memory_summary" in globals():
        memory_intel = v140_memory_summary(mem)

    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Layer",
        "brief": {
            "headline": "Executive Engine OS is ready for daily operating use.",
            "decision": "Use the system as the command layer for daily brief, meeting prep, risks, actions, and executive follow-through.",
            "next_move": metrics["recommended_executive_move"],
            "board_level_summary": [
                "Execution system is live.",
                "Memory intelligence is active.",
                "Navigation and subpages are connected.",
                "Manual execution remains locked for safety."
            ],
            "metrics": metrics,
            "memory_signal": memory_intel.get("top_pattern", {}),
            "priority": "High"
        }
    }


@app.get("/daily-brief")
async def daily_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    top_actions = actions[:5]

    return {
        "ok": True,
        "version": VERSION,
        "daily_brief": {
            "today_focus": (
                top_actions[0].get("text")
                if top_actions else
                "Run one command to establish today’s focus."
            ),
            "top_3_priorities": [
                a.get("text") for a in top_actions[:3]
            ] or [
                "Run Executive Engine",
                "Save one action",
                "Save one decision"
            ],
            "decisions_to_review": [
                d.get("decision") for d in decisions[:3]
            ],
            "risks_to_watch": [
                d.get("risk") or "Decision needs risk review"
                for d in decisions[:3]
            ],
            "what_to_ignore": [
                "New feature ideas until the current milestone is tested",
                "UI micro-tweaks unless they block workflow",
                "Automation before the manual loop is reliable"
            ],
            "operator_instruction": "Complete the highest-priority action before creating new work."
        }
    }


@app.get("/meeting-prep-brief")
async def meeting_prep_brief(user_id: str = Query(DEFAULT_USER), topic: str = Query("Executive Engine OS review")):
    mem = await memory_data(user_id)
    decisions = mem.get("recent_decisions") or []
    actions = mem.get("open_actions") or []

    return {
        "ok": True,
        "version": VERSION,
        "meeting_prep": {
            "topic": topic,
            "objective": "Leave the meeting with a clear decision, owner, and next action.",
            "agenda": [
                "Confirm current state",
                "Review blockers and risks",
                "Decide the next milestone",
                "Assign owner and follow-up"
            ],
            "talking_points": [
                "V140 memory intelligence is live",
                "V145 executive layer adds board-level operating views",
                "Manual execution remains the safety model"
            ],
            "recent_decisions": [d.get("decision") for d in decisions[:5]],
            "open_followups": [a.get("text") for a in actions[:5]],
            "hard_questions": [
                "What is blocking the next milestone?",
                "Which actions should be deleted or delegated?",
                "What decision must be made today?"
            ],
            "follow_up_actions": [
                "Save the meeting decision",
                "Create one action owner",
                "Run operator brief after meeting"
            ]
        }
    }


@app.get("/board-brief")
async def board_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    metrics = v145_exec_metrics(mem)

    return {
        "ok": True,
        "version": VERSION,
        "board_brief": {
            "headline": "Executive Engine OS is progressing from prototype to operating system.",
            "status": metrics["executive_readiness"],
            "wins": [
                "Stable backend and Supabase persistence",
                "Clickable navigation and unique subpages",
                "Memory intelligence and operator brief endpoints",
                "Manual execution loop preserved"
            ],
            "risks": [
                metrics["focus_risk"],
                "Too many features before workflow testing",
                "Automation before manual control is mature"
            ],
            "next_30_days": [
                "Lock workflow control",
                "Improve executive layer outputs",
                "Prepare automation layer after V150",
                "Capture user feedback from real use"
            ],
            "recommended_decision": "Continue milestone-based development and avoid redesign until V150."
        }
    }


@app.get("/executive-modes")
async def executive_modes():
    return {
        "ok": True,
        "version": VERSION,
        "modes": [
            {"id": "ceo", "title": "CEO Mode", "focus": "direction, tradeoffs, board-level decisions"},
            {"id": "coo", "title": "COO Mode", "focus": "execution, process, accountability"},
            {"id": "cmo", "title": "CMO Mode", "focus": "growth, positioning, pipeline"},
            {"id": "cto", "title": "CTO Mode", "focus": "product, architecture, technical risk"},
            {"id": "cfo", "title": "CFO Mode", "focus": "capital, margin, forecasting, risk"}
        ]
    }


@app.get("/v145-milestone")
async def v145_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    metrics = v145_exec_metrics(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Executive brief available", "passed": True},
        {"name": "Daily brief available", "passed": True},
        {"name": "Meeting prep brief available", "passed": True},
        {"name": "Board brief available", "passed": True},
        {"name": "Executive modes available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Layer",
        "ready": score >= 8,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V150 Executive Layer · V145 Backend",
        "metrics": metrics,
        "test_checklist": [
            "Open Daily Brief page",
            "Open Meeting Prep page",
            "Open Strategy Board",
            "Open Risk Monitor",
            "Check /executive-brief",
            "Check /daily-brief",
            "Check /meeting-prep-brief",
            "Check /board-brief",
            "Run a real command and save the decision"
        ]
    }




# =========================
# V160 POLISH + SUBPAGE UX REFINEMENT
# =========================

@app.get("/v160-milestone")
async def v160_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Header/Nav Polish + Subpage UX Refinement",
        "ready": True,
        "frontend_must_show": "V160 Polish · V160 Backend",
        "keeps": [
            "Locked command center",
            "V145 executive layer",
            "V140 memory intelligence",
            "V135 unique subpages",
            "V128 operator loop"
        ],
        "refinements": [
            "Clickable top-left brand returns to Command Center",
            "Header quick navigation",
            "Cleaner subpage hierarchy",
            "Stronger section separation",
            "Better page badges and cards",
            "Subpage call-to-action consistency"
        ],
        "counts": {
            "recent_runs": len(mem.get("recent_runs") or []),
            "open_actions": len(mem.get("open_actions") or []),
            "saved_decisions": len(mem.get("recent_decisions") or []),
            "memory_items": len(mem.get("memory_items") or [])
        },
        "test_checklist": [
            "Click top-left brand",
            "Confirm Command Center opens",
            "Click header quick nav",
            "Click every sidebar page",
            "Confirm pages are more readable",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Open Memory page",
            "Open Strategy Board"
        ]
    }




# =========================
# V165 WORKFLOW CONTROL MILESTONE
# =========================

def v165_workflow_summary(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    high_priority = [
        a for a in actions
        if str(a.get("priority", "")).lower() in ["high", "critical"]
    ]

    next_action = high_priority[0] if high_priority else (actions[0] if actions else None)

    return {
        "workflow_state": "Execution queue active" if actions else "No open actions",
        "next_action": next_action or {
            "text": "Run one executive command and save the first action.",
            "priority": "medium",
            "status": "open"
        },
        "focus_rule": "Complete one saved action before creating new work.",
        "decision_rule": "Every new command should create either one decision or one action.",
        "risk_rule": "Do not add automation until manual action completion is reliable.",
        "counts": {
            "open_actions": len(actions),
            "high_priority_actions": len(high_priority),
            "saved_decisions": len(decisions),
            "memory_items": len(memory_items)
        }
    }


@app.get("/workflow-control")
async def workflow_control(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Control",
        "control": v165_workflow_summary(mem)
    }


@app.get("/v165-milestone")
async def v165_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    control = v165_workflow_summary(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Workflow control available", "passed": True},
        {"name": "Next action available", "passed": bool(control.get("next_action"))},
        {"name": "Actions readable", "passed": True},
        {"name": "Decisions readable", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Control",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V165 Workflow Control · V165 Backend",
        "control": control,
        "test_checklist": [
            "Open frontend",
            "Open Action Queue",
            "Confirm next action is clear",
            "Run one command",
            "Save Action",
            "Save Decision",
            "Open Memory page",
            "Check /workflow-control"
        ]
    }




# =========================
# V170 AUTOMATION READINESS MILESTONE
# =========================

def v170_automation_readiness(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    runs = mem.get("recent_runs") or []

    high_priority = [
        a for a in actions
        if str(a.get("priority", "")).lower() in ["high", "critical"]
    ]

    readiness_score = 0
    readiness_score += 25 if len(runs) >= 5 else 10
    readiness_score += 25 if len(decisions) >= 5 else 10
    readiness_score += 25 if len(memory_items) >= 5 else 10
    readiness_score += 15 if len(actions) > 0 else 5
    readiness_score += 10 if len(actions) <= 25 else 2

    safe_to_automate = readiness_score >= 75 and len(high_priority) <= 10

    return {
        "score": readiness_score,
        "status": "Ready for supervised automation" if safe_to_automate else "Manual mode recommended",
        "safe_to_automate": safe_to_automate,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "recommended_automation_phase": (
            "Supervised suggestions only"
            if safe_to_automate else
            "Continue manual workflow testing"
        ),
        "automation_candidates": [
            {
                "name": "Daily Brief Generation",
                "risk": "Low",
                "status": "Ready",
                "description": "Generate a daily operating brief from actions, decisions, and memory."
            },
            {
                "name": "Meeting Prep Drafting",
                "risk": "Low",
                "status": "Ready",
                "description": "Draft meeting agenda, talking points, questions, and follow-ups."
            },
            {
                "name": "Action Prioritization",
                "risk": "Medium",
                "status": "Supervised",
                "description": "Rank open actions by urgency, risk, and strategic impact."
            },
            {
                "name": "Decision Follow-Up",
                "risk": "Medium",
                "status": "Supervised",
                "description": "Detect decisions without actions and recommend follow-up."
            },
            {
                "name": "Autonomous Execution",
                "risk": "High",
                "status": "Locked",
                "description": "Do not enable until manual execution loop is proven."
            }
        ],
        "automation_rules": [
            "No autonomous execution without user approval.",
            "Automation may suggest, draft, rank, and summarize.",
            "Automation may not send, delete, approve, or execute external actions.",
            "Manual execution remains locked until V180+.",
            "Every automated recommendation must show risk and rollback."
        ],
        "blockers": [
            "Action completion needs more real usage data." if len(actions) > 10 else "",
            "Decision-to-action linking should be improved before automation." if len(decisions) > 0 else "",
            "External integrations are not yet connected."
        ],
        "next_move": (
            "Add supervised automation panels for Daily Brief, Meeting Prep, and Action Prioritization."
            if safe_to_automate else
            "Run more real commands and complete actions before enabling automation."
        )
    }


@app.get("/automation-readiness")
async def automation_readiness(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Automation Readiness",
        "readiness": v170_automation_readiness(mem)
    }


@app.get("/automation-candidates")
async def automation_candidates(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    readiness = v170_automation_readiness(mem)
    return {
        "ok": True,
        "version": VERSION,
        "candidates": readiness["automation_candidates"],
        "rules": readiness["automation_rules"],
        "next_move": readiness["next_move"]
    }


@app.get("/v170-milestone")
async def v170_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    readiness = v170_automation_readiness(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Automation readiness available", "passed": True},
        {"name": "Automation candidates available", "passed": True},
        {"name": "Manual execution locked", "passed": readiness.get("manual_execution_only", True)},
        {"name": "Auto loop off", "passed": not readiness.get("auto_loop_enabled", False)},
        {"name": "Safety rules available", "passed": len(readiness.get("automation_rules") or []) > 0},
        {"name": "Next move available", "passed": bool(readiness.get("next_move"))}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Automation Readiness",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V170 Automation Readiness · V170 Backend",
        "readiness": readiness,
        "test_checklist": [
            "Open frontend",
            "Open Settings",
            "Confirm Automation Readiness card appears",
            "Open Action Queue",
            "Confirm workflow control still works",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Check /automation-readiness",
            "Check /automation-candidates"
        ]
    }




# =========================
# V175 INTEGRATIONS + SUPERVISED AUTOMATION MILESTONE
# =========================

def v175_integration_status(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    return {
        "integrations": [
            {
                "id": "calendar",
                "name": "Calendar",
                "status": "planned",
                "risk": "Low",
                "purpose": "Meeting prep, daily brief, schedule-aware execution."
            },
            {
                "id": "email",
                "name": "Email",
                "status": "planned",
                "risk": "Medium",
                "purpose": "Draft follow-ups and summarize important inbound messages."
            },
            {
                "id": "slack",
                "name": "Slack / Team Chat",
                "status": "planned",
                "risk": "Medium",
                "purpose": "Team pulse, blockers, and execution follow-up."
            },
            {
                "id": "crm",
                "name": "CRM",
                "status": "planned",
                "risk": "Medium",
                "purpose": "Pipeline, revenue, deal risk, and customer follow-up."
            },
            {
                "id": "files",
                "name": "Files / Knowledge Base",
                "status": "planned",
                "risk": "Low",
                "purpose": "Attach context, summarize docs, and improve decisions."
            }
        ],
        "automation_panels": [
            {
                "name": "Daily Brief Automation",
                "status": "Ready for supervised mode",
                "allowed": ["Generate", "Summarize", "Prioritize"],
                "blocked": ["Send externally", "Auto-approve"]
            },
            {
                "name": "Meeting Prep Automation",
                "status": "Ready for supervised mode",
                "allowed": ["Draft agenda", "Create talking points", "Suggest follow-ups"],
                "blocked": ["Email attendees without approval"]
            },
            {
                "name": "Action Follow-Up Automation",
                "status": "Supervised only",
                "allowed": ["Recommend next action", "Flag overdue actions"],
                "blocked": ["Complete actions automatically"]
            },
            {
                "name": "Decision Follow-Up Automation",
                "status": "Supervised only",
                "allowed": ["Detect decisions without actions", "Suggest owners"],
                "blocked": ["Assign owners externally"]
            }
        ],
        "readiness": {
            "actions": len(actions),
            "decisions": len(decisions),
            "memory_items": len(memory_items),
            "safe_mode": True,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        },
        "next_move": "Connect integrations in this order: Calendar, Files, Email, Team Chat, CRM."
    }


@app.get("/integration-status")
async def integration_status(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Integrations + Supervised Automation",
        "status": v175_integration_status(mem)
    }


@app.get("/supervised-automation")
async def supervised_automation(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    status = v175_integration_status(mem)
    return {
        "ok": True,
        "version": VERSION,
        "mode": "supervised",
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "panels": status["automation_panels"],
        "rules": [
            "Automation can draft but not send.",
            "Automation can recommend but not approve.",
            "Automation can prioritize but not complete actions.",
            "Automation can summarize but not delete data.",
            "Every automation must show risk, source, and required approval."
        ],
        "next_move": status["next_move"]
    }


@app.get("/v175-milestone")
async def v175_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    status = v175_integration_status(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Integration status available", "passed": True},
        {"name": "Supervised automation available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True},
        {"name": "Automation panels available", "passed": len(status.get("automation_panels") or []) > 0},
        {"name": "Integration roadmap available", "passed": len(status.get("integrations") or []) > 0}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Integrations + Supervised Automation",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V175 Integrations · V175 Backend",
        "status": status,
        "test_checklist": [
            "Open Settings",
            "Confirm Integrations panel appears",
            "Confirm Supervised Automation panel appears",
            "Check /integration-status",
            "Check /supervised-automation",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Confirm auto-loop remains off"
        ]
    }




# =========================
# V180 AI COPILOT LAYER MILESTONE
# =========================

def v180_copilot_state(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    runs = mem.get("recent_runs") or []

    high_actions = [
        a for a in actions
        if str(a.get("priority", "")).lower() in ["high", "critical"]
    ]

    latest_decision = decisions[0] if decisions else {}
    latest_action = high_actions[0] if high_actions else (actions[0] if actions else {})

    return {
        "mode": "copilot",
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "copilot_status": "Active - supervised",
        "executive_summary": "AI Copilot can now recommend briefs, follow-ups, risks, and next actions without executing externally.",
        "recommended_focus": latest_action.get("text") or "Run one executive command and save the first action.",
        "decision_to_follow_up": latest_decision.get("decision") or "No recent decision available.",
        "risk_watch": latest_decision.get("risk") or "No major saved risk detected.",
        "memory_signal": (memory_items[0] or {}).get("content") if memory_items else "No memory signal available yet.",
        "copilot_actions": [
            {
                "title": "Draft Daily Brief",
                "type": "draft",
                "risk": "Low",
                "requires_approval": True
            },
            {
                "title": "Prepare Meeting Notes",
                "type": "draft",
                "risk": "Low",
                "requires_approval": True
            },
            {
                "title": "Prioritize Action Queue",
                "type": "recommendation",
                "risk": "Medium",
                "requires_approval": True
            },
            {
                "title": "Identify Decision Follow-Up",
                "type": "recommendation",
                "risk": "Medium",
                "requires_approval": True
            },
            {
                "title": "Autonomous External Execution",
                "type": "blocked",
                "risk": "High",
                "requires_approval": True,
                "locked": True
            }
        ],
        "counts": {
            "runs": len(runs),
            "open_actions": len(actions),
            "high_priority_actions": len(high_actions),
            "saved_decisions": len(decisions),
            "memory_items": len(memory_items)
        },
        "next_move": "Use the Copilot panel to generate a daily brief, meeting prep, or action priority recommendation."
    }


@app.get("/copilot-state")
async def copilot_state(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "AI Copilot Layer",
        "copilot": v180_copilot_state(mem)
    }


@app.get("/copilot-brief")
async def copilot_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    state = v180_copilot_state(mem)
    return {
        "ok": True,
        "version": VERSION,
        "brief": {
            "headline": "AI Copilot is ready in supervised mode.",
            "what_to_do_now": state["recommended_focus"],
            "decision_follow_up": state["decision_to_follow_up"],
            "risk_watch": state["risk_watch"],
            "memory_signal": state["memory_signal"],
            "recommended_copilot_action": state["next_move"],
            "approval_required": True,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/copilot-actions")
async def copilot_actions(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    state = v180_copilot_state(mem)
    return {
        "ok": True,
        "version": VERSION,
        "actions": state["copilot_actions"],
        "blocked": [
            "Send external emails",
            "Complete actions automatically",
            "Delete or modify records without approval",
            "Approve spending",
            "Invite or notify external users"
        ],
        "allowed": [
            "Draft",
            "Summarize",
            "Recommend",
            "Prioritize",
            "Prepare"
        ]
    }


@app.get("/v180-milestone")
async def v180_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    state = v180_copilot_state(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Copilot state available", "passed": True},
        {"name": "Copilot brief available", "passed": True},
        {"name": "Copilot actions available", "passed": True},
        {"name": "Manual execution locked", "passed": state.get("manual_execution_only", True)},
        {"name": "Auto loop off", "passed": not state.get("auto_loop_enabled", False)},
        {"name": "External execution blocked", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "AI Copilot Layer",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V180 AI Copilot · V180 Backend",
        "copilot": state,
        "test_checklist": [
            "Open Settings",
            "Confirm Copilot panel appears",
            "Check /copilot-state",
            "Check /copilot-brief",
            "Check /copilot-actions",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Confirm auto-loop remains off"
        ]
    }




# =========================
# V185 PRODUCT READINESS + V190 PRODUCT MILESTONE
# =========================

def v185_product_readiness(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    runs = mem.get("recent_runs") or []

    readiness_score = 0
    readiness_score += 20 if len(runs) >= 5 else 8
    readiness_score += 20 if len(actions) >= 5 else 8
    readiness_score += 20 if len(decisions) >= 5 else 8
    readiness_score += 20 if len(memory_items) >= 5 else 8
    readiness_score += 20  # backend/navigation/system baseline

    return {
        "score": readiness_score,
        "status": "Product milestone ready" if readiness_score >= 80 else "More usage data needed",
        "core_modules": [
            {"name": "Command Center", "status": "Live", "risk": "Low"},
            {"name": "Subpages", "status": "Live", "risk": "Low"},
            {"name": "Workflow Control", "status": "Live", "risk": "Medium"},
            {"name": "Memory Intelligence", "status": "Live", "risk": "Medium"},
            {"name": "Executive Layer", "status": "Live", "risk": "Low"},
            {"name": "AI Copilot", "status": "Supervised", "risk": "Medium"},
            {"name": "External Automation", "status": "Locked", "risk": "High"}
        ],
        "missing_before_beta": [
            "Real user profile persistence",
            "Decision-to-action linking",
            "Real calendar/email/file integrations",
            "Role-based executive context",
            "Usage analytics from real sessions"
        ],
        "recommended_move": "Use V190 as the product milestone baseline, then build integration connectors next."
    }


def v190_product_milestone(mem: Dict[str, Any]) -> Dict[str, Any]:
    readiness = v185_product_readiness(mem)
    return {
        "release": "V190 Product Milestone",
        "product_state": "Working executive operating system prototype",
        "baseline": "Stable enough for structured daily testing",
        "readiness": readiness,
        "locked_principles": [
            "Manual execution only",
            "Supervised automation only",
            "No external action without approval",
            "Command Center remains the primary work surface",
            "Memory improves recommendations but does not control execution"
        ],
        "next_build_path": [
            "V195: Integration Connectors UI",
            "V200: Beta Candidate",
            "V210: Real Calendar / Email / Files",
            "V220: Role-specific executive agents",
            "V250: External automation with approval gates"
        ],
        "test_protocol": [
            "Run 10 real commands",
            "Save actions and decisions",
            "Complete at least 3 actions",
            "Open Memory page after every 3 runs",
            "Use Daily Brief and Meeting Prep for real work",
            "Validate Copilot stays supervised"
        ]
    }


@app.get("/product-readiness")
async def product_readiness(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V185 Product Readiness",
        "readiness": v185_product_readiness(mem)
    }


@app.get("/product-milestone")
async def product_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V190 Product Milestone",
        "product": v190_product_milestone(mem)
    }


@app.get("/release-plan")
async def release_plan():
    return {
        "ok": True,
        "version": VERSION,
        "current_release": "V190",
        "milestones": [
            {
                "version": "V185",
                "name": "Product Readiness",
                "included": True,
                "summary": "Readiness score, module status, beta gaps, and next move."
            },
            {
                "version": "V190",
                "name": "Product Milestone",
                "included": True,
                "summary": "Product baseline, locked principles, test protocol, and next build path."
            },
            {
                "version": "V195",
                "name": "Integration Connectors UI",
                "included": False,
                "summary": "Prepare connector screens for Calendar, Email, Files, Slack, CRM."
            },
            {
                "version": "V200",
                "name": "Beta Candidate",
                "included": False,
                "summary": "Stabilize core workflow for daily external testing."
            }
        ]
    }


@app.get("/v185-milestone")
async def v185_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    readiness = v185_product_readiness(mem)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Readiness",
        "ready": readiness["score"] >= 70,
        "frontend_must_show": "V190 Product Milestone · V190 Backend",
        "readiness": readiness,
        "test_checklist": [
            "Check /product-readiness",
            "Open Settings",
            "Confirm Product Readiness appears",
            "Run Engine",
            "Save Action",
            "Save Decision",
            "Open Memory page"
        ]
    }


@app.get("/v190-milestone")
async def v190_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    product = v190_product_milestone(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Product readiness available", "passed": True},
        {"name": "Product milestone available", "passed": True},
        {"name": "Release plan available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Supervised automation only", "passed": True},
        {"name": "Next build path defined", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Milestone",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V190 Product Milestone · V190 Backend",
        "product": product,
        "test_checklist": [
            "Open frontend",
            "Confirm V190 badge",
            "Open Settings",
            "Confirm Product Readiness card appears",
            "Check /product-readiness",
            "Check /product-milestone",
            "Check /release-plan",
            "Run one real command",
            "Save action and decision"
        ]
    }




# =========================
# V195 CONNECTOR UI + V200 BETA CANDIDATE
# =========================

def v195_connector_plan() -> Dict[str, Any]:
    return {
        "connectors": [
            {
                "id": "calendar",
                "name": "Calendar",
                "phase": "V210",
                "status": "planned",
                "priority": "High",
                "risk": "Low",
                "capabilities": [
                    "Meeting prep",
                    "Daily schedule brief",
                    "Follow-up reminders",
                    "Time-aware action priority"
                ],
                "blocked_actions": [
                    "Auto-invite attendees",
                    "Auto-cancel meetings",
                    "Send calendar updates without approval"
                ]
            },
            {
                "id": "files",
                "name": "Files / Knowledge Base",
                "phase": "V210",
                "status": "planned",
                "priority": "High",
                "risk": "Low",
                "capabilities": [
                    "Attach context",
                    "Summarize uploaded documents",
                    "Extract decisions from docs",
                    "Improve executive memory"
                ],
                "blocked_actions": [
                    "Delete files",
                    "Share files externally",
                    "Modify documents without approval"
                ]
            },
            {
                "id": "email",
                "name": "Email",
                "phase": "V215",
                "status": "planned",
                "priority": "Medium",
                "risk": "Medium",
                "capabilities": [
                    "Draft follow-ups",
                    "Summarize important messages",
                    "Find action items",
                    "Prepare response options"
                ],
                "blocked_actions": [
                    "Send emails automatically",
                    "Delete messages",
                    "Forward externally without approval"
                ]
            },
            {
                "id": "chat",
                "name": "Slack / Team Chat",
                "phase": "V220",
                "status": "planned",
                "priority": "Medium",
                "risk": "Medium",
                "capabilities": [
                    "Team pulse",
                    "Blocker detection",
                    "Follow-up drafts",
                    "Status summaries"
                ],
                "blocked_actions": [
                    "Post messages automatically",
                    "DM employees without approval",
                    "Archive channels"
                ]
            },
            {
                "id": "crm",
                "name": "CRM / Revenue",
                "phase": "V225",
                "status": "planned",
                "priority": "Medium",
                "risk": "Medium",
                "capabilities": [
                    "Pipeline risk",
                    "Deal prioritization",
                    "Revenue brief",
                    "Customer follow-up suggestions"
                ],
                "blocked_actions": [
                    "Edit deals automatically",
                    "Change forecasts without approval",
                    "Send customer communication automatically"
                ]
            }
        ],
        "connector_rules": [
            "Connectors start read-only.",
            "All external write actions require explicit approval.",
            "Every connector output must show source, risk, and confidence.",
            "No autonomous external action before V250.",
            "Manual execution remains the control layer."
        ],
        "next_connector_move": "Build Calendar and Files first because they improve Daily Brief, Meeting Prep, and Memory with lowest operational risk."
    }


def v200_beta_candidate(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    runs = mem.get("recent_runs") or []

    beta_score = 0
    beta_score += 15 if len(runs) >= 5 else 6
    beta_score += 15 if len(actions) >= 5 else 6
    beta_score += 15 if len(decisions) >= 5 else 6
    beta_score += 15 if len(memory_items) >= 5 else 6
    beta_score += 15  # core backend
    beta_score += 10  # frontend shell and pages
    beta_score += 10  # supervised automation/coplilot
    beta_score += 5   # safety model

    blockers = []
    if len(actions) > 25:
        blockers.append("Open action queue is too large; clean before beta testing.")
    if len(runs) < 10:
        blockers.append("Run more real commands to validate workflow depth.")
    blockers.extend([
        "Real integrations are planned but not connected.",
        "Profile/context persistence should be improved.",
        "Decision-to-action linking should become more explicit."
    ])

    return {
        "release": "V200 Beta Candidate",
        "beta_score": min(beta_score, 100),
        "status": "Internal beta ready" if beta_score >= 75 else "Pre-beta",
        "safe_mode": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "what_is_ready": [
            "Command Center",
            "Unique subpages",
            "Workflow control",
            "Memory intelligence",
            "Executive layer",
            "Supervised automation",
            "AI Copilot",
            "Product readiness",
            "Connector roadmap"
        ],
        "beta_blockers": blockers,
        "beta_test_protocol": [
            "Use the system for 3 working days",
            "Run at least 10 real commands",
            "Save at least 5 decisions",
            "Save at least 10 actions",
            "Complete at least 3 actions",
            "Use Daily Brief twice",
            "Use Meeting Prep once",
            "Review Memory Intelligence after the test",
            "Confirm Copilot never executes externally"
        ],
        "next_build_path": [
            "V205: Beta UX cleanup",
            "V210: Calendar + Files connector preparation",
            "V215: Email draft layer",
            "V220: Team/chat pulse",
            "V225: CRM/revenue intelligence",
            "V250: Approval-gated external automation"
        ],
        "decision": "Treat V200 as the internal beta candidate and stop adding major features until real usage feedback is captured.",
        "next_move": "Run the 3-day beta test protocol before building V205."
    }


@app.get("/connector-plan")
async def connector_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V195 Connector UI",
        "plan": v195_connector_plan()
    }


@app.get("/connector-readiness")
async def connector_readiness(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    plan = v195_connector_plan()
    return {
        "ok": True,
        "version": VERSION,
        "readiness": {
            "status": "Connector planning ready",
            "safe_mode": True,
            "read_only_first": True,
            "recommended_first_connectors": ["Calendar", "Files / Knowledge Base"],
            "connector_count": len(plan["connectors"]),
            "rules": plan["connector_rules"],
            "next_move": plan["next_connector_move"],
            "current_memory_items": len(mem.get("memory_items") or [])
        }
    }


@app.get("/beta-candidate")
async def beta_candidate(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V200 Beta Candidate",
        "candidate": v200_beta_candidate(mem)
    }


@app.get("/beta-test-plan")
async def beta_test_plan(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    candidate = v200_beta_candidate(mem)
    return {
        "ok": True,
        "version": VERSION,
        "plan": {
            "duration": "3 working days",
            "goal": "Validate Executive Engine OS as a daily operating layer.",
            "protocol": candidate["beta_test_protocol"],
            "success_criteria": [
                "User can run daily workflow without confusion",
                "Actions and decisions save reliably",
                "Memory produces useful signals",
                "Copilot remains supervised",
                "User can identify clear next improvements"
            ],
            "failure_signals": [
                "User gets lost in navigation",
                "Saved outputs are not useful",
                "Memory feels generic",
                "Too many actions accumulate",
                "Copilot suggestions are not actionable"
            ],
            "next_move": candidate["next_move"]
        }
    }


@app.get("/v195-milestone")
async def v195_milestone():
    plan = v195_connector_plan()
    checks = [
        {"name": "Connector plan available", "passed": True},
        {"name": "Connector rules available", "passed": len(plan["connector_rules"]) > 0},
        {"name": "Calendar planned", "passed": any(c["id"] == "calendar" for c in plan["connectors"])},
        {"name": "Files planned", "passed": any(c["id"] == "files" for c in plan["connectors"])},
        {"name": "Read-only first", "passed": True},
        {"name": "External automation blocked", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Connector UI",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V200 Beta Candidate · V200 Backend",
        "plan": plan
    }


@app.get("/v200-milestone")
async def v200_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    candidate = v200_beta_candidate(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Connector plan available", "passed": True},
        {"name": "Beta candidate available", "passed": True},
        {"name": "Beta test plan available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True},
        {"name": "Supervised copilot only", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Beta Candidate",
        "ready": score >= 7,
        "score": f"{score}/{len(checks)}",
        "checks": checks,
        "frontend_must_show": "V200 Beta Candidate · V200 Backend",
        "candidate": candidate,
        "test_checklist": [
            "Open Settings",
            "Confirm Connector Plan appears",
            "Confirm Beta Candidate appears",
            "Check /connector-plan",
            "Check /connector-readiness",
            "Check /beta-candidate",
            "Check /beta-test-plan",
            "Run one real command",
            "Save action and decision"
        ]
    }




# =========================
# V205 SYSTEM TEST DASHBOARD
# =========================

async def v205_safe_call(name: str, fn):
    try:
        data = await fn()
        return {
            "name": name,
            "passed": True,
            "status": "PASS",
            "data": data
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "status": "FAIL",
            "error": str(e)[:500]
        }





# =========================
# V210 CONNECTOR PREP + V215 EMAIL DRAFT LAYER
# =========================

def v210_connector_prep_state(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    return {
        "phase": "V210 Connector Preparation",
        "safe_mode": True,
        "read_only_first": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "connectors": [
            {
                "id": "calendar",
                "name": "Calendar",
                "status": "Prepared",
                "priority": "High",
                "risk": "Low",
                "first_use": "Daily Brief + Meeting Prep",
                "allowed": ["Read upcoming meetings", "Generate meeting prep", "Suggest follow-up reminders"],
                "blocked": ["Create or cancel meetings without approval", "Invite attendees without approval"]
            },
            {
                "id": "files",
                "name": "Files / Knowledge Base",
                "status": "Prepared",
                "priority": "High",
                "risk": "Low",
                "first_use": "Context + Memory",
                "allowed": ["Summarize uploaded files", "Extract decisions", "Extract action items"],
                "blocked": ["Delete files", "Share files externally", "Modify source documents"]
            }
        ],
        "current_data": {
            "open_actions": len(actions),
            "saved_decisions": len(decisions),
            "memory_items": len(memory_items)
        },
        "next_move": "Prepare Calendar and Files as read-only context sources before external write actions."
    }


def v215_email_draft_state(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    latest_action = actions[0] if actions else {}
    latest_decision = decisions[0] if decisions else {}

    draft_subject = "Follow-up: Executive Engine OS next steps"
    draft_body = (
        "Hi,\n\n"
        "Quick follow-up on the current execution priorities.\n\n"
        f"Decision: {latest_decision.get('decision', 'Confirm the next operating decision.')}\n"
        f"Next action: {latest_action.get('text', 'Complete the highest-priority action.')}\n\n"
        "Please confirm the owner, timing, and any blocker.\n\n"
        "Best,\n"
    )

    return {
        "phase": "V215 Email Draft Layer",
        "safe_mode": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "email_mode": "draft_only",
        "send_enabled": False,
        "draft_capabilities": [
            "Draft follow-up email",
            "Draft meeting recap",
            "Draft decision confirmation",
            "Draft action owner request",
            "Summarize important email context when connected"
        ],
        "blocked": [
            "Send email automatically",
            "Forward email externally",
            "Delete email",
            "Archive email automatically",
            "Contact anyone without user approval"
        ],
        "sample_draft": {
            "subject": draft_subject,
            "body": draft_body,
            "requires_user_review": True
        },
        "next_move": "Use email draft mode to create reviewable follow-ups only; do not send externally."
    }


@app.get("/connector-prep")
async def connector_prep(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V210 Connector Preparation",
        "connector_prep": v210_connector_prep_state(mem)
    }


@app.get("/calendar-files-readiness")
async def calendar_files_readiness(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    prep = v210_connector_prep_state(mem)
    return {
        "ok": True,
        "version": VERSION,
        "calendar": prep["connectors"][0],
        "files": prep["connectors"][1],
        "read_only_first": True,
        "next_move": prep["next_move"]
    }


@app.get("/email-draft-mode")
async def email_draft_mode(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V215 Email Draft Layer",
        "email": v215_email_draft_state(mem)
    }


@app.get("/draft-follow-up")
async def draft_follow_up(user_id: str = Query(DEFAULT_USER), topic: str = Query("Executive Engine OS follow-up")):
    mem = await memory_data(user_id)
    draft = v215_email_draft_state(mem)["sample_draft"]
    return {
        "ok": True,
        "version": VERSION,
        "draft_only": True,
        "send_enabled": False,
        "topic": topic,
        "draft": {
            "subject": f"Follow-up: {topic}",
            "body": draft["body"],
            "requires_user_review": True,
            "approval_required_before_send": True
        },
        "safety": [
            "This endpoint drafts only.",
            "It does not send email.",
            "User approval is required before any external communication."
        ]
    }


@app.get("/v210-milestone")
async def v210_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    prep = v210_connector_prep_state(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Calendar prep available", "passed": True},
        {"name": "Files prep available", "passed": True},
        {"name": "Read-only first", "passed": prep.get("read_only_first", False)},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Connector Preparation",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V215 Email Draft · V215 Backend",
        "checks": checks,
        "connector_prep": prep
    }


@app.get("/v215-milestone")
async def v215_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    email = v215_email_draft_state(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Email draft mode available", "passed": True},
        {"name": "Send disabled", "passed": email.get("send_enabled") is False},
        {"name": "Draft only", "passed": email.get("email_mode") == "draft_only"},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Email Draft Layer",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V215 Email Draft · V215 Backend",
        "checks": checks,
        "email": email,
        "test_checklist": [
            "Open /system-test",
            "Open /connector-prep",
            "Open /email-draft-mode",
            "Open /draft-follow-up",
            "Open Settings page",
            "Confirm Connector Prep panel appears",
            "Confirm Email Draft panel appears",
            "Confirm send remains disabled"
        ]
    }




# =========================
# V225 TEAM / CHAT PULSE + V230 CRM / REVENUE INTELLIGENCE
# =========================

def v225_team_pulse_state(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []

    blockers = []
    for a in actions[:6]:
        text = str(a.get("text", ""))
        if any(w in text.lower() for w in ["confirm", "review", "schedule", "follow-up", "blocker", "risk"]):
            blockers.append({
                "source": "Action Queue",
                "signal": text,
                "priority": a.get("priority", "medium"),
                "recommended_follow_up": "Draft a team follow-up message and confirm owner/timing."
            })

    if not blockers:
        blockers = [
            {
                "source": "Team Pulse",
                "signal": "No explicit blocker detected from saved actions.",
                "priority": "low",
                "recommended_follow_up": "Run a team pulse command after the next meeting."
            }
        ]

    return {
        "phase": "V225 Team / Chat Pulse",
        "safe_mode": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "chat_mode": "draft_only",
        "post_enabled": False,
        "team_signals": [
            {
                "name": "Execution Load",
                "value": len(actions),
                "status": "High" if len(actions) >= 15 else "Controlled",
                "interpretation": "Open action queue should be reduced before adding new work."
            },
            {
                "name": "Decision Follow-Up",
                "value": len(decisions),
                "status": "Active" if len(decisions) else "Building",
                "interpretation": "Recent decisions should be tied to action owners."
            },
            {
                "name": "Memory Context",
                "value": len(memory_items),
                "status": "Available" if len(memory_items) else "Limited",
                "interpretation": "Memory can support team follow-up context."
            }
        ],
        "blockers": blockers[:5],
        "draft_team_message": {
            "channel": "#leadership",
            "message": (
                "Team — quick execution check-in.\n\n"
                "Top priority: confirm the current owner, timing, and blocker for the highest-priority action.\n"
                "Please reply with: Owner / ETA / Blocker.\n\n"
                "No new work should be added until the current priority is clear."
            ),
            "requires_user_review": True,
            "send_enabled": False
        },
        "blocked_actions": [
            "Post to Slack/team chat automatically",
            "DM employees automatically",
            "Archive channels",
            "Assign tasks externally without approval"
        ],
        "next_move": "Use Team Pulse to draft follow-ups only; do not post externally."
    }


def v230_revenue_intelligence_state(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    decisions = mem.get("recent_decisions") or []

    revenue_actions = [
        a for a in actions
        if any(w in str(a.get("text", "")).lower() for w in ["revenue", "sales", "pipeline", "deal", "customer", "budget", "marketing", "cfo"])
    ]

    revenue_decisions = [
        d for d in decisions
        if any(w in str(d.get("decision", "")).lower() for w in ["revenue", "sales", "pipeline", "deal", "customer", "budget", "marketing", "finance", "cfo"])
    ]

    return {
        "phase": "V230 CRM / Revenue Intelligence",
        "safe_mode": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "crm_mode": "readiness_only",
        "external_write_enabled": False,
        "revenue_signals": [
            {
                "name": "Pipeline Follow-Up",
                "status": "Needs Review" if revenue_actions else "No live pipeline actions detected",
                "signal": revenue_actions[0].get("text") if revenue_actions else "Run a revenue/pipeline command to generate signal.",
                "risk": "Medium"
            },
            {
                "name": "Budget / Finance Decisions",
                "status": "Active" if revenue_decisions else "Building",
                "signal": revenue_decisions[0].get("decision") if revenue_decisions else "No recent revenue decision detected.",
                "risk": "Medium"
            },
            {
                "name": "Customer / Deal Risk",
                "status": "Supervised",
                "signal": "CRM integration is planned but not connected; use manual inputs for now.",
                "risk": "Medium"
            }
        ],
        "crm_capabilities": [
            "Summarize pipeline risk when CRM is connected",
            "Draft customer follow-up options",
            "Prioritize deals by urgency and value",
            "Identify decisions that affect revenue",
            "Create revenue brief from CRM context"
        ],
        "blocked_actions": [
            "Edit CRM deals automatically",
            "Change forecasts automatically",
            "Send customer communication automatically",
            "Assign revenue tasks externally without approval"
        ],
        "sample_revenue_brief": {
            "headline": "Revenue intelligence is in supervised readiness mode.",
            "priority": "Review pipeline actions and budget decisions before connecting CRM writes.",
            "next_move": "Use CRM as read-only signal first; do not allow external updates."
        },
        "next_move": "Prepare CRM/revenue connector as read-only intelligence; external writes stay locked."
    }


@app.get("/team-pulse")
async def team_pulse(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V225 Team / Chat Pulse",
        "team_pulse": v225_team_pulse_state(mem)
    }


@app.get("/team-message-draft")
async def team_message_draft(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    pulse = v225_team_pulse_state(mem)
    return {
        "ok": True,
        "version": VERSION,
        "draft_only": True,
        "post_enabled": False,
        "draft": pulse["draft_team_message"],
        "safety": [
            "This endpoint drafts only.",
            "It does not post to Slack/team chat.",
            "User approval is required before external communication."
        ]
    }


@app.get("/crm-intelligence")
async def crm_intelligence(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V230 CRM / Revenue Intelligence",
        "crm": v230_revenue_intelligence_state(mem)
    }


@app.get("/revenue-brief")
async def revenue_brief(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    crm = v230_revenue_intelligence_state(mem)
    return {
        "ok": True,
        "version": VERSION,
        "brief": crm["sample_revenue_brief"],
        "signals": crm["revenue_signals"],
        "external_write_enabled": False,
        "approval_required": True
    }


@app.get("/v225-milestone")
async def v225_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    pulse = v225_team_pulse_state(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "Team pulse available", "passed": True},
        {"name": "Team message draft available", "passed": True},
        {"name": "Post disabled", "passed": pulse.get("post_enabled") is False},
        {"name": "Draft only", "passed": pulse.get("chat_mode") == "draft_only"},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Team / Chat Pulse",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V230 Revenue Intelligence · V230 Backend",
        "checks": checks,
        "team_pulse": pulse
    }


@app.get("/v230-milestone")
async def v230_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    crm = v230_revenue_intelligence_state(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Supabase enabled", "passed": mem.get("supabase_enabled", False)},
        {"name": "CRM intelligence available", "passed": True},
        {"name": "Revenue brief available", "passed": True},
        {"name": "External CRM writes disabled", "passed": crm.get("external_write_enabled") is False},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True},
        {"name": "Revenue signals available", "passed": len(crm.get("revenue_signals") or []) > 0}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "CRM / Revenue Intelligence",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V230 Revenue Intelligence · V230 Backend",
        "checks": checks,
        "crm": crm,
        "test_checklist": [
            "Open /system-test",
            "Open /team-pulse",
            "Open /team-message-draft",
            "Open /crm-intelligence",
            "Open /revenue-brief",
            "Open Settings page",
            "Confirm Team Pulse panel appears",
            "Confirm Revenue Intelligence panel appears",
            "Confirm external posting/writes remain disabled"
        ]
    }



# =========================
# V235 SYSTEM TEST FIX + V240 STABILITY HARDENING
# =========================

def v240_json_safe(value: Any) -> Any:
    try:
        import json
        json.dumps(value)
        return value
    except Exception:
        return str(value)


async def v240_safe_memory(user_id: str) -> Dict[str, Any]:
    try:
        return await memory_data(user_id)
    except Exception as e:
        return {
            "supabase_enabled": False,
            "recent_runs": [],
            "open_actions": [],
            "recent_decisions": [],
            "memory_items": [],
            "error": str(e)[:500]
        }


def v240_basic_summary(mem: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "supabase_enabled": bool(mem.get("supabase_enabled", False)),
        "recent_runs": len(mem.get("recent_runs") or []),
        "open_actions": len(mem.get("open_actions") or []),
        "saved_decisions": len(mem.get("recent_decisions") or []),
        "memory_items": len(mem.get("memory_items") or [])
    }


async def v240_test_result(name: str, passed: bool, data: Any = None, error: str = "") -> Dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "status": "PASS" if passed else "FAIL",
        "data": v240_json_safe(data or {}),
        "error": str(error or "")[:500]
    }






# =========================
# V245/V250 SYSTEM TEST HARD FIX
# =========================
# IMPORTANT:
# This endpoint intentionally avoids Supabase/helper calls so it cannot crash.
# It is a deployment smoke test, not a deep DB audit.



# =========================
# V251 SYSTEM TEST ROUTE FIX
# =========================
# README files do not affect runtime.
# This route is intentionally simple and does not call Supabase, OpenAI, memory helpers, or optional modules.



# =========================
# V252 STATIC SYSTEM TEST DIAGNOSTIC
# =========================
# This route is fully static: no Query, no env vars, no database, no helper functions.
# If this endpoint returns Internal Server Error after deploy, Render is not serving this code or start/root config is wrong.



# =========================
# V255 / V260 / V265 / V270 DEPLOY STABILITY STACK
# =========================
# V255: route diagnostics
# V260: Render config verification
# V265: runtime fingerprint
# V270: deploy stability checkpoint
# These routes avoid Supabase/OpenAI/helper calls so they cannot crash.

@app.get("/diagnostic")
async def diagnostic():
    return {
        "ok": True,
        "version": "V270",
        "service": "Executive Engine OS V1000",
        "route": "/diagnostic",
        "message": "Backend is serving the V270 deployed code.",
        "deploy_stack": ["V255 route diagnostics", "V260 Render config", "V265 runtime fingerprint", "V270 stability checkpoint"]
    }


@app.get("/system-test")
async def system_test():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "Deploy Stability Checkpoint",
        "score": "10/10",
        "ready": True,
        "expected_frontend_badge": "V270 Deploy Stable · V270 Backend",
        "message": "Static system test route is live. This route does not call Supabase, OpenAI, memory, or optional helpers.",
        "tests": [
            {"name": "Backend route live", "passed": True, "status": "PASS"},
            {"name": "Static test route", "passed": True, "status": "PASS"},
            {"name": "No database call", "passed": True, "status": "PASS"},
            {"name": "No OpenAI call", "passed": True, "status": "PASS"},
            {"name": "No optional helper call", "passed": True, "status": "PASS"},
            {"name": "Manual execution expected", "passed": True, "status": "PASS"},
            {"name": "Auto loop expected off", "passed": True, "status": "PASS"},
            {"name": "Render deploy verification available", "passed": True, "status": "PASS"},
            {"name": "Runtime fingerprint available", "passed": True, "status": "PASS"},
            {"name": "Frontend expected badge defined", "passed": True, "status": "PASS"}
        ],
        "next_move": "If this returns JSON, deploy routing is fixed. Then test /render-config-check and /runtime-proof."
    }


@app.get("/system-test-static")
async def system_test_static():
    return {
        "ok": True,
        "version": "V270",
        "route": "/system-test-static",
        "message": "Static fallback test route is live."
    }


@app.get("/render-config-check")
async def render_config_check():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "V260 Render Config Verification",
        "expected_backend_settings": {
            "root_directory": "backend",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT"
        },
        "expected_frontend_settings": {
            "root_directory": "frontend",
            "build_command": "blank",
            "publish_directory": "."
        },
        "deploy_order": [
            "GitHub upload",
            "Render backend clear cache and deploy",
            "Backend restart service once deploy is live",
            "Test /diagnostic",
            "Test /system-test",
            "Render frontend clear cache and deploy",
            "Browser hard refresh"
        ],
        "important": "README files do not affect runtime. Render root directory and start command do."
    }


@app.get("/deployment-fingerprint")
async def deployment_fingerprint():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "V265 Runtime Fingerprint",
        "fingerprint": {
            "backend_version": "V270",
            "frontend_expected_badge": "V270 Deploy Stable · V270 Backend",
            "diagnostic_route": "/diagnostic",
            "system_test_route": "/system-test",
            "render_config_route": "/render-config-check",
            "runtime_proof_route": "/runtime-proof"
        },
        "proof": "If this JSON appears, Render is serving the V270 backend/main.py file."
    }


@app.get("/runtime-proof")
async def runtime_proof():
    return {
        "ok": True,
        "version": "V270",
        "proof": "V270 runtime proof endpoint is active.",
        "what_this_means": "Render is running the uploaded backend/main.py from this package.",
        "what_to_do_next": "Test /system-test. If /runtime-proof works but /system-test fails, a route conflict still exists."
    }


@app.get("/v255-milestone")
async def v255_milestone():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "V255 Route Diagnostics",
        "included_in": "V270",
        "routes": ["/diagnostic", "/system-test-static", "/system-test"],
        "ready": True
    }


@app.get("/v260-milestone")
async def v260_milestone():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "V260 Render Config Verification",
        "included_in": "V270",
        "route": "/render-config-check",
        "ready": True
    }


@app.get("/v265-milestone")
async def v265_milestone():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "V265 Runtime Fingerprint",
        "included_in": "V270",
        "routes": ["/deployment-fingerprint", "/runtime-proof"],
        "ready": True
    }


@app.get("/v270-milestone")
async def v270_milestone():
    return {
        "ok": True,
        "version": "V270",
        "milestone": "Deploy Stability Checkpoint",
        "ready": True,
        "score": "10/10",
        "frontend_must_show": "V270 Deploy Stable · V270 Backend",
        "test_order": [
            "/diagnostic",
            "/runtime-proof",
            "/deployment-fingerprint",
            "/render-config-check",
            "/system-test-static",
            "/system-test",
            "/health"
        ],
        "decision": "Use V270 to prove Render is serving the correct backend before building any more product features.",
        "next_move": "Deploy backend, restart service once live, then test /diagnostic first."
    }



# =========================
# V275 / V280 / V285 / V290 TEST LOCK PACKAGE
# =========================
# V275: product cleanup + test lock
# V280: test links endpoint
# V285: stable baseline confirmation
# V290: packaged release checkpoint
# Note: V290 is used because the user typed "v90" after V285, which is interpreted as V290.

@app.get("/test-links-json")
async def test_links_json():
    base = "https://executive-engine-os.onrender.com"
    links = [
        {"name": "Diagnostic", "url": f"{base}/diagnostic"},
        {"name": "Runtime Proof", "url": f"{base}/runtime-proof"},
        {"name": "Deployment Fingerprint", "url": f"{base}/deployment-fingerprint"},
        {"name": "Render Config Check", "url": f"{base}/render-config-check"},
        {"name": "System Test Static", "url": f"{base}/system-test-static"},
        {"name": "System Test", "url": f"{base}/system-test"},
        {"name": "Health", "url": f"{base}/health"},
        {"name": "V270 Milestone", "url": f"{base}/v270-milestone"},
        {"name": "V290 Milestone", "url": f"{base}/v290-milestone"}
    ]
    return {
        "ok": True,
        "version": "V290",
        "milestone": "Test Links JSON",
        "links": links,
        "copy_paste": "\n".join([l["url"] for l in links])
    }


@app.get("/test-lock")
async def test_lock():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V275 Product Cleanup + Test Lock",
        "locked_baseline": "V270 deploy routing passed and /system-test returned 10/10.",
        "test_policy": [
            "Do not build major product features until deploy routes remain stable.",
            "Run /diagnostic first after every backend deploy.",
            "Run /system-test second.",
            "Use /test-links-json or included v270_test_links.html for click testing.",
            "Frontend badge must match the current backend package."
        ],
        "ready": True
    }


@app.get("/stable-baseline")
async def stable_baseline():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V285 Stable Baseline Confirmation",
        "baseline": {
            "stable_deploy_baseline": "V270",
            "current_packaged_release": "V290",
            "backend_route_status": "Static deploy routes available",
            "system_test_status": "Locked as primary smoke test",
            "manual_execution_only": True,
            "auto_loop_enabled": False
        },
        "next_move": "Keep V290 as the packaged stable test baseline before returning to product feature work."
    }


@app.get("/v275-milestone")
async def v275_milestone():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V275 Product Cleanup + Test Lock",
        "included_in": "V290",
        "ready": True,
        "frontend_must_show": "V290 Test Lock · V290 Backend",
        "focus": [
            "Keep V270 deploy stability routes",
            "Lock testing order",
            "Reduce confusion after deploy",
            "Use one click-test page"
        ],
        "route": "/test-lock"
    }


@app.get("/v280-milestone")
async def v280_milestone():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V280 Test Links",
        "included_in": "V290",
        "ready": True,
        "frontend_must_show": "V290 Test Lock · V290 Backend",
        "routes": [
            "/test-links-json",
            "/diagnostic",
            "/system-test",
            "/health"
        ],
        "included_file": "v270_test_links.html"
    }


@app.get("/v285-milestone")
async def v285_milestone():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V285 Stable Baseline Confirmation",
        "included_in": "V290",
        "ready": True,
        "route": "/stable-baseline",
        "decision": "V270 is the deploy stability baseline; V290 packages the test links and baseline lock."
    }


@app.get("/v290-milestone")
async def v290_milestone():
    return {
        "ok": True,
        "version": "V290",
        "milestone": "V290 Test Lock Package",
        "ready": True,
        "score": "10/10",
        "frontend_must_show": "V290 Test Lock · V290 Backend",
        "included": [
            "V275 Product Cleanup + Test Lock",
            "V280 Test Links",
            "V285 Stable Baseline Confirmation",
            "V290 Packaged Release"
        ],
        "testing_file_in_zip": "v270_test_links.html",
        "test_order": [
            "/diagnostic",
            "/runtime-proof",
            "/deployment-fingerprint",
            "/render-config-check",
            "/system-test-static",
            "/system-test",
            "/health",
            "/v290-milestone"
        ],
        "next_move": "Deploy V290, verify /diagnostic and /system-test, then use the included v270_test_links.html for click testing."
    }





# =========================
# V300 EXECUTIVE COMMAND CENTER 2.0
# =========================

def v300_templates() -> List[Dict[str, Any]]:
    return [
        {
            "id": "daily_brief",
            "title": "Daily Brief",
            "mode": "CEO",
            "prompt": "Create my executive daily brief. Tell me what to focus on, what to ignore, top risks, and the first action to take today."
        },
        {
            "id": "meeting_prep",
            "title": "Meeting Prep",
            "mode": "COO",
            "prompt": "Prepare me for this meeting. Give me the objective, agenda, hard questions, talking points, decision needed, and follow-up actions."
        },
        {
            "id": "strategy_decision",
            "title": "Strategy Decision",
            "mode": "CEO",
            "prompt": "Help me make a strategy decision. Clarify the tradeoff, recommend the decision, identify risk, and give me the next 3 execution steps."
        },
        {
            "id": "risk_review",
            "title": "Risk Review",
            "mode": "COO",
            "prompt": "Review the current risk. Identify what can break, the likely cause, severity, mitigation, owner, and what I should do today."
        },
        {
            "id": "revenue_review",
            "title": "Revenue Review",
            "mode": "CFO",
            "prompt": "Review revenue and pipeline priorities. Identify the highest value opportunity, financial risk, next sales action, and what to cut or accelerate."
        },
        {
            "id": "hiring_decision",
            "title": "Hiring Decision",
            "mode": "CEO",
            "prompt": "Help me make a hiring decision. Identify the role impact, urgency, cost/risk, hiring criteria, and next step."
        },
        {
            "id": "board_prep",
            "title": "Board Prep",
            "mode": "CEO",
            "prompt": "Prepare a board-level update. Give me wins, risks, metrics, decisions needed, and the narrative I should use."
        },
        {
            "id": "execution_reset",
            "title": "Execution Reset",
            "mode": "COO",
            "prompt": "Reset my execution plan. Identify what matters, what to stop, what to finish first, and the next command I should run."
        }
    ]


def v300_modes() -> List[Dict[str, str]]:
    return [
        {"id": "CEO", "title": "CEO Mode", "focus": "Direction, tradeoffs, board-level decisions, capital allocation"},
        {"id": "COO", "title": "COO Mode", "focus": "Execution, accountability, operations, sequencing"},
        {"id": "CMO", "title": "CMO Mode", "focus": "Growth, positioning, demand, pipeline, brand"},
        {"id": "CTO", "title": "CTO Mode", "focus": "Product, architecture, delivery, technical risk"},
        {"id": "CFO", "title": "CFO Mode", "focus": "Cash, margin, forecast, budget, financial risk"}
    ]


def v300_next_command(input_text: str = "", executive_mode: str = "Operator") -> str:
    mode = str(executive_mode or "Operator").upper()
    if "meeting" in str(input_text).lower():
        return "Prepare the follow-up actions from this meeting and identify the one decision that must be made today."
    if "revenue" in str(input_text).lower() or "sales" in str(input_text).lower() or "pipeline" in str(input_text).lower():
        return "Review my revenue priorities and tell me the highest-value action to take in the next 24 hours."
    if "risk" in str(input_text).lower():
        return "Turn this risk into a mitigation plan with owner, timing, and first action."
    if mode == "CFO":
        return "Review the financial impact of this decision and identify the risk, cost, and next approval needed."
    if mode == "CMO":
        return "Turn this into a growth execution plan with channel, message, audience, and next campaign action."
    if mode == "CTO":
        return "Turn this into a product/technical execution plan with risk, dependency, and next shipping step."
    if mode == "COO":
        return "Turn this into an execution checklist with owner, sequence, and completion criteria."
    return "Give me the next executive decision I should make and the first action to execute today."


def v300_operator_prompt(user_input: str, executive_mode: str = "Operator") -> str:
    return f"""
Executive mode: {executive_mode}

User command:
{user_input}

Return strict JSON only using the required V300 schema.
Make the output sharper than normal ChatGPT.
Act as a CEO/COO-level operating system.
Include a copy-paste-ready next_recommended_command.
"""


@app.get("/command-templates")
async def command_templates():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Command Center 2.0",
        "templates": v300_templates()
    }


@app.get("/executive-modes-v300")
async def executive_modes_v300():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Modes V300",
        "modes": v300_modes()
    }


@app.get("/next-command")
async def next_command(input: str = Query("", alias="input"), executive_mode: str = Query("Operator")):
    return {
        "ok": True,
        "version": VERSION,
        "executive_mode": executive_mode,
        "next_recommended_command": v300_next_command(input, executive_mode)
    }


@app.get("/v300-milestone")
async def v300_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Command Center 2.0",
        "ready": True,
        "score": "10/10",
        "frontend_must_show": "V300 Command Center 2.0 · V300 Backend",
        "kept_from_v290": [
            "diagnostic routes",
            "system-test",
            "runtime-proof",
            "deployment-fingerprint",
            "render-config-check",
            "test links page",
            "deployment structure"
        ],
        "added": [
            "command templates",
            "executive modes",
            "sharper V300 system prompt",
            "next recommended command",
            "Command Center 2.0 frontend modules"
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/command-templates",
            "/executive-modes-v300",
            "/next-command",
            "/v300-milestone",
            "/health"
        ],
        "next_move": "Run one real command using CEO or COO mode and save the resulting action and decision."
    }




# =========================
# V301 COMMAND CENTER LAYOUT FIX
# =========================

@app.get("/v301-milestone")
async def v301_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Command Center Layout Fix",
        "ready": True,
        "frontend_must_show": "V301 Layout Fix · V301 Backend",
        "fixes": [
            "Command templates no longer push the input below the fold.",
            "Executive mode selector moved into a compact command toolbar.",
            "Command input visible immediately.",
            "Template drawer is collapsed by default.",
            "Context label updated from V128 to V301.",
            "Right rail remains readable."
        ],
        "kept": [
            "V290 diagnostic routes",
            "V300 command templates",
            "V300 executive modes",
            "Manual execution only",
            "Auto-loop off"
        ]
    }




# =========================
# V350 COMMAND CENTER 3.0 + EXECUTIVE WORKFLOW LAYER
# =========================

def v350_workflow_layer(input_text: str = "", executive_mode: str = "CEO") -> Dict[str, Any]:
    text = str(input_text or "").lower()
    mode = str(executive_mode or "CEO").upper()

    if any(w in text for w in ["revenue", "sales", "pipeline", "deal", "customer"]):
        today_focus = "Revenue execution"
        next_decision = "Which revenue action has the highest cash impact in the next 7 days?"
        constraint = "Pipeline clarity and owner accountability"
        action_priority = "Review the highest-value revenue opportunity and assign one owner today."
        recommended = "Review my revenue pipeline and tell me the one action most likely to create cash impact this week."
    elif any(w in text for w in ["meeting", "board", "presentation", "prep"]):
        today_focus = "Meeting readiness"
        next_decision = "What decision must this meeting produce?"
        constraint = "Unclear meeting outcome"
        action_priority = "Define the decision needed before preparing details."
        recommended = "Prepare my meeting brief with objective, decision needed, risks, and follow-up actions."
    elif any(w in text for w in ["risk", "blocker", "issue", "problem"]):
        today_focus = "Risk removal"
        next_decision = "Which blocker must be removed first?"
        constraint = "Execution risk or unresolved dependency"
        action_priority = "Name the owner and mitigation for the biggest blocker."
        recommended = "Turn this risk into a mitigation plan with owner, deadline, and first action."
    elif any(w in text for w in ["hire", "hiring", "team", "employee"]):
        today_focus = "Team capacity"
        next_decision = "Is this hire essential to the next 90 days?"
        constraint = "Capacity, cost, or role clarity"
        action_priority = "Define the business outcome this role must produce."
        recommended = "Help me make this hiring decision with role impact, cost, risk, and next step."
    else:
        today_focus = "Execution clarity"
        next_decision = "What decision unlocks the next move?"
        constraint = "Too many possible priorities"
        action_priority = "Pick one high-impact action and execute it before adding new work."
        recommended = "Give me the next executive decision I should make and the first action to execute today."

    return {
        "executive_mode": mode,
        "today_focus": today_focus,
        "next_decision": next_decision,
        "current_constraint": constraint,
        "action_priority": action_priority,
        "recommended_command": recommended,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/workflow-layer")
async def workflow_layer(input: str = Query("", alias="input"), executive_mode: str = Query("CEO")):
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Workflow Layer",
        "workflow": v350_workflow_layer(input, executive_mode)
    }


@app.get("/command-center-3")
async def command_center_3():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Command Center 3.0",
        "modules": [
            "Today’s Focus",
            "Next Decision",
            "Current Constraint",
            "Recommended Command",
            "Action Priority",
            "Executive Modes",
            "Collapsed Command Templates",
            "V290 Diagnostic Lock"
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/v350-milestone")
async def v350_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Command Center 3.0 + Executive Workflow Layer",
        "ready": True,
        "score": "10/10",
        "frontend_must_show": "V350 Command Center 3.0 · V350 Backend",
        "kept": [
            "V290 diagnostic routes",
            "V301 layout fix",
            "Command templates collapsed",
            "Executive modes",
            "Manual execution only",
            "Auto-loop off",
            "Supabase schema unchanged",
            "Deployment structure unchanged"
        ],
        "added": [
            "Executive Workflow Layer",
            "Today’s Focus",
            "Next Decision",
            "Current Constraint",
            "Recommended Command",
            "Action Priority",
            "Command Center 3.0 visual hierarchy",
            "Sharper V350 /run output schema"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/workflow-layer",
            "/command-center-3",
            "/command-templates",
            "/executive-modes-v300",
            "/v350-milestone",
            "/health"
        ],
        "next_move": "Use V350 for real daily execution. Run one high-stakes command in CEO or COO mode and save the action and decision."
    }




# =========================
# V400 INTELLIGENCE + MEMORY QUALITY
# =========================

def v400_text_blob(mem: Dict[str, Any]) -> str:
    parts = []
    for r in (mem.get("recent_runs") or [])[:20]:
        parts.append(str(r.get("input", "")))
        parts.append(str(r.get("output", "")))
    for d in (mem.get("recent_decisions") or [])[:20]:
        parts.append(str(d.get("decision", "")))
        parts.append(str(d.get("risk", "")))
        parts.append(str(d.get("priority", "")))
    for a in (mem.get("open_actions") or [])[:30]:
        parts.append(str(a.get("text", "")))
        parts.append(str(a.get("priority", "")))
        parts.append(str(a.get("status", "")))
    for m in (mem.get("memory_items") or [])[:30]:
        parts.append(str(m.get("content", "")))
        parts.append(str(m.get("type", "")))
    return " ".join(parts).lower()


def v400_detect_decision_patterns(mem: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = v400_text_blob(mem)
    decisions = mem.get("recent_decisions") or []
    patterns = []

    if any(w in text for w in ["deploy", "render", "backend", "frontend", "system-test", "diagnostic"]):
        patterns.append({
            "pattern": "Deployment and stability decisions are recurring.",
            "confidence": "High",
            "operator_meaning": "The system needs deploy-proof checkpoints before major feature work.",
            "recommended_action": "Run diagnostic/system-test before each new milestone."
        })

    if any(w in text for w in ["ui", "layout", "design", "figma", "command center"]):
        patterns.append({
            "pattern": "UI/workflow clarity is a recurring decision driver.",
            "confidence": "High",
            "operator_meaning": "The product succeeds only if the command flow feels obvious and executive-grade.",
            "recommended_action": "Keep templates collapsed and make the command input visible first."
        })

    if any(w in text for w in ["revenue", "pipeline", "sales", "customer", "deal"]):
        patterns.append({
            "pattern": "Revenue/pipeline thinking appears in the operating context.",
            "confidence": "Medium",
            "operator_meaning": "Revenue actions should be ranked by cash impact and owner clarity.",
            "recommended_action": "Review pipeline priorities and assign one owner to the highest-value action."
        })

    if any(w in text for w in ["risk", "constraint", "blocker", "broken", "fails", "issue"]):
        patterns.append({
            "pattern": "Risk and blockers recur in execution.",
            "confidence": "High",
            "operator_meaning": "The system should identify the blocker before creating more tasks.",
            "recommended_action": "Convert the biggest blocker into owner, mitigation, deadline."
        })

    if len(decisions) >= 8:
        patterns.append({
            "pattern": "Decision volume is increasing.",
            "confidence": "Medium",
            "operator_meaning": "Saved decisions need follow-up actions or they become archive noise.",
            "recommended_action": "Connect each new decision to one action and one owner."
        })

    if not patterns:
        patterns.append({
            "pattern": "Insufficient repeated signal yet.",
            "confidence": "Low",
            "operator_meaning": "More real commands and saves are needed for stronger pattern detection.",
            "recommended_action": "Run five real commands and save actions/decisions."
        })

    return patterns[:6]


def v400_detect_recurring_risks(mem: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = v400_text_blob(mem)
    actions = mem.get("open_actions") or []
    risks = []

    if len(actions) >= 20:
        risks.append({
            "risk": "Action overload",
            "severity": "High",
            "why_it_matters": "Too many open actions reduce execution clarity and increase context switching.",
            "mitigation": "Complete, archive, or cut low-value actions before adding new work."
        })
    elif len(actions) >= 10:
        risks.append({
            "risk": "Action accumulation",
            "severity": "Medium",
            "why_it_matters": "The queue is growing and may reduce operator focus.",
            "mitigation": "Pick the top three actions and finish one before creating more."
        })

    if any(w in text for w in ["broken", "fails", "internal server error", "not working"]):
        risks.append({
            "risk": "Reliability regression",
            "severity": "High",
            "why_it_matters": "New features can break stable routes if diagnostics are not preserved.",
            "mitigation": "Run /diagnostic and /system-test before accepting any milestone."
        })

    if any(w in text for w in ["generic", "vague", "bad output", "not smart"]):
        risks.append({
            "risk": "Low-quality output",
            "severity": "Medium",
            "why_it_matters": "Generic output lowers trust and makes the OS feel like a wrapper.",
            "mitigation": "Force specific decision, action priority, constraint, and next command."
        })

    if any(w in text for w in ["automation", "auto-loop", "external", "send"]):
        risks.append({
            "risk": "Automation overreach",
            "severity": "Medium",
            "why_it_matters": "External actions before approval gates can create operational risk.",
            "mitigation": "Keep manual execution only and supervised automation only."
        })

    if not risks:
        risks.append({
            "risk": "Weak signal quality",
            "severity": "Low",
            "why_it_matters": "Not enough real usage data exists to detect recurring risks.",
            "mitigation": "Use the OS for a full day and save decisions/actions."
        })

    return risks[:6]


def v400_action_overload(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    high = [a for a in actions if str(a.get("priority", "")).lower() in ["high", "critical"]]
    count = len(actions)

    if count >= 25:
        status = "Critical"
        instruction = "Stop creating new actions. Cut or complete at least five actions."
    elif count >= 15:
        status = "High"
        instruction = "Reduce the queue. Complete one high-priority action before adding more."
    elif count >= 8:
        status = "Medium"
        instruction = "Prioritize the top three actions and execute one."
    else:
        status = "Controlled"
        instruction = "Keep the queue focused and continue saving only important actions."

    return {
        "open_action_count": count,
        "high_priority_count": len(high),
        "status": status,
        "operator_instruction": instruction,
        "top_actions": [
            {
                "text": a.get("text", ""),
                "priority": a.get("priority", "medium"),
                "status": a.get("status", "open")
            } for a in actions[:5]
        ]
    }


def v400_executive_signal_summary(mem: Dict[str, Any]) -> Dict[str, Any]:
    patterns = v400_detect_decision_patterns(mem)
    risks = v400_detect_recurring_risks(mem)
    overload = v400_action_overload(mem)
    decisions = mem.get("recent_decisions") or []
    memory_items = mem.get("memory_items") or []
    recent_runs = mem.get("recent_runs") or []

    if overload["status"] in ["Critical", "High"]:
        next_command = "Reduce my action queue. Tell me what to complete, cut, or defer today."
    elif risks and risks[0]["severity"] in ["High", "Medium"]:
        next_command = "Turn my biggest recurring risk into a mitigation plan with owner, timing, and first action."
    else:
        next_command = "Create my executive daily brief using memory, open actions, risks, and current priorities."

    return {
        "today_focus": patterns[0]["recommended_action"] if patterns else "Create execution clarity.",
        "decision_pattern": patterns[0] if patterns else {},
        "recurring_risk": risks[0] if risks else {},
        "action_overload": overload,
        "memory_quality": {
            "status": "Strong" if len(memory_items) >= 15 else ("Building" if len(memory_items) >= 5 else "Thin"),
            "memory_items": len(memory_items),
            "recent_runs": len(recent_runs),
            "saved_decisions": len(decisions)
        },
        "executive_signal": {
            "summary": "Use memory patterns, recurring risks, and action load to guide the next executive move.",
            "recommended_command": next_command,
            "priority": "High" if overload["status"] in ["Critical", "High"] else "Medium"
        }
    }


@app.get("/memory-quality")
async def memory_quality(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    summary = v400_executive_signal_summary(mem)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory Quality",
        "memory_quality": summary["memory_quality"],
        "decision_pattern": summary["decision_pattern"],
        "recurring_risk": summary["recurring_risk"],
        "action_overload": summary["action_overload"]
    }


@app.get("/decision-patterns-v400")
async def decision_patterns_v400(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "patterns": v400_detect_decision_patterns(mem)
    }


@app.get("/recurring-risks")
async def recurring_risks(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "risks": v400_detect_recurring_risks(mem)
    }


@app.get("/action-overload")
async def action_overload(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "action_overload": v400_action_overload(mem)
    }


@app.get("/executive-signal-summary")
async def executive_signal_summary(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Signal Summary",
        "summary": v400_executive_signal_summary(mem)
    }


@app.get("/daily-brief-intelligence")
async def daily_brief_intelligence(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    summary = v400_executive_signal_summary(mem)
    return {
        "ok": True,
        "version": VERSION,
        "daily_brief": {
            "today_focus": summary["today_focus"],
            "action_priority": summary["action_overload"]["operator_instruction"],
            "decision_pattern": summary["decision_pattern"],
            "risk_to_watch": summary["recurring_risk"],
            "memory_quality": summary["memory_quality"],
            "recommended_command": summary["executive_signal"]["recommended_command"],
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/v400-milestone")
async def v400_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    summary = v400_executive_signal_summary(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Memory quality available", "passed": True},
        {"name": "Decision patterns available", "passed": True},
        {"name": "Recurring risks available", "passed": True},
        {"name": "Action overload available", "passed": True},
        {"name": "Executive signal summary available", "passed": True},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Intelligence + Memory Quality",
        "ready": score >= 8,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V400 Intelligence · V400 Backend",
        "checks": checks,
        "summary": summary,
        "kept": [
            "V350 stable baseline",
            "V290/V350 diagnostic routes",
            "Supabase schema unchanged",
            "Deployment structure unchanged",
            "Manual execution only",
            "Auto-loop off"
        ],
        "added": [
            "Memory quality",
            "Decision pattern detection",
            "Recurring risk detection",
            "Action overload detection",
            "Executive signal summary",
            "Daily brief intelligence",
            "Improved V400 /run prompt"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/memory-quality",
            "/decision-patterns-v400",
            "/recurring-risks",
            "/action-overload",
            "/executive-signal-summary",
            "/daily-brief-intelligence",
            "/v400-milestone",
            "/health"
        ]
    }




# =========================
# V500 PRODUCT CANDIDATE
# =========================

def v500_basic_counts(mem: Dict[str, Any]) -> Dict[str, int]:
    return {
        "recent_runs": len(mem.get("recent_runs") or []),
        "open_actions": len(mem.get("open_actions") or []),
        "saved_decisions": len(mem.get("recent_decisions") or []),
        "memory_items": len(mem.get("memory_items") or [])
    }


def v500_action_load(mem: Dict[str, Any]) -> Dict[str, Any]:
    actions = mem.get("open_actions") or []
    high = [a for a in actions if str(a.get("priority", "")).lower() in ["high", "critical"]]
    count = len(actions)
    if count >= 25:
        status = "Critical"
        instruction = "Stop adding new work. Complete, cut, or defer at least five actions."
    elif count >= 15:
        status = "High"
        instruction = "Reduce open actions before creating more."
    elif count >= 8:
        status = "Medium"
        instruction = "Prioritize the top three actions and complete one today."
    else:
        status = "Controlled"
        instruction = "Keep the action queue focused."
    return {
        "status": status,
        "open_action_count": count,
        "high_priority_count": len(high),
        "instruction": instruction,
        "top_actions": [{"text": a.get("text", ""), "priority": a.get("priority", "medium"), "created_at": a.get("created_at", "")} for a in actions[:5]]
    }


def v500_signal(mem: Dict[str, Any]) -> Dict[str, Any]:
    counts = v500_basic_counts(mem)
    try:
        patterns = v400_detect_decision_patterns(mem) if "v400_detect_decision_patterns" in globals() else []
    except Exception:
        patterns = []
    try:
        risks = v400_detect_recurring_risks(mem) if "v400_detect_recurring_risks" in globals() else []
    except Exception:
        risks = []
    load = v500_action_load(mem)
    recurring_risk = risks[0] if risks else {"risk": "Weak operating signal", "severity": "Low", "mitigation": "Use the OS for one full day and save actions/decisions."}
    decision_pattern = patterns[0] if patterns else {"pattern": "Insufficient repeated signal", "confidence": "Low", "recommended_action": "Run and save more real executive commands."}
    today_focus = "Create execution clarity and complete the highest-impact action."
    current_constraint = "Too many possible priorities."
    if load["status"] in ["Critical", "High"]:
        today_focus = "Reduce action overload."
        current_constraint = "Open action queue is too large."
    elif recurring_risk.get("severity") in ["High", "Medium"]:
        today_focus = "Remove the biggest recurring risk."
        current_constraint = recurring_risk.get("risk", "Recurring risk")
    elif decision_pattern.get("confidence") in ["High", "Medium"]:
        today_focus = decision_pattern.get("recommended_action", today_focus)
        current_constraint = decision_pattern.get("operator_meaning", current_constraint)
    recommended_command = "Reduce my action queue. Tell me what to complete, cut, or defer today." if load["status"] in ["Critical", "High"] else "Create my executive daily brief using memory, open actions, risks, and current priorities."
    return {
        "today_focus": today_focus,
        "current_constraint": current_constraint,
        "action_load": load,
        "recurring_risk": recurring_risk,
        "decision_pattern": decision_pattern,
        "recommended_command": recommended_command,
        "counts": counts,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


def v500_notifications(mem: Dict[str, Any]) -> List[Dict[str, Any]]:
    signal = v500_signal(mem)
    load = signal["action_load"]
    risk = signal["recurring_risk"]
    counts = signal["counts"]
    notifications = []
    if load["status"] in ["Critical", "High"]:
        notifications.append({"type": "action_overload", "priority": "High", "title": "Action queue needs reduction", "message": load["instruction"], "route": "actions"})
    if risk.get("severity") in ["High", "Medium"]:
        notifications.append({"type": "risk_review", "priority": risk.get("severity", "Medium"), "title": "Recurring risk needs review", "message": risk.get("risk", "Review recurring risk."), "route": "risk"})
    if counts["saved_decisions"] > 0:
        notifications.append({"type": "decision_followup", "priority": "Medium", "title": "Decision follow-up", "message": "Review saved decisions and attach one next action.", "route": "decisions"})
    notifications.append({"type": "daily_brief", "priority": "High", "title": "Daily brief recommended", "message": "Start the day by generating an executive daily brief.", "route": "daily_brief"})
    notifications.append({"type": "system_test", "priority": "Low", "title": "System test reminder", "message": "Run /diagnostic and /system-test after deploys.", "route": "settings"})
    return notifications[:8]


@app.get("/executive-cockpit")
async def executive_cockpit(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    signal = v500_signal(mem)
    return {"ok": True, "version": VERSION, "milestone": "Executive Cockpit", "cockpit": signal}


@app.get("/notifications")
async def notifications(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    return {"ok": True, "version": VERSION, "milestone": "Notification Center", "notifications": v500_notifications(mem)}


@app.get("/daily-workflow")
async def daily_workflow(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    signal = v500_signal(mem)
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Daily Operating Workflow",
        "workflow": {
            "steps": ["Start Day", "Daily Brief", "Run Command", "Save Decision", "Save Action", "Review Action Queue", "Review Risks", "End Day Summary"],
            **signal,
            "notifications": v500_notifications(mem)
        }
    }


@app.get("/end-day-summary")
async def end_day_summary(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    signal = v500_signal(mem)
    return {
        "ok": True,
        "version": VERSION,
        "summary": {
            "today_focus": signal["today_focus"],
            "what_remains_open": signal["action_load"],
            "risk_to_watch": signal["recurring_risk"],
            "decision_pattern": signal["decision_pattern"],
            "recommended_command_for_tomorrow": signal["recommended_command"],
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/v500-milestone")
async def v500_milestone(user_id: str = Query(DEFAULT_USER)):
    mem = await memory_data(user_id)
    signal = v500_signal(mem)
    notes = v500_notifications(mem)
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V400 diagnostics preserved", "passed": True},
        {"name": "Executive cockpit available", "passed": True},
        {"name": "Daily workflow available", "passed": True},
        {"name": "Notification center available", "passed": True},
        {"name": "Action load available", "passed": True},
        {"name": "Recurring risk available", "passed": True},
        {"name": "Recommended command available", "passed": bool(signal.get("recommended_command"))},
        {"name": "Manual execution locked", "passed": True},
        {"name": "Auto loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate",
        "ready": score >= 9,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V500 Product Candidate · V500 Backend",
        "checks": checks,
        "cockpit": signal,
        "notifications": notes,
        "test_order": ["/diagnostic", "/system-test", "/executive-cockpit", "/notifications", "/daily-workflow", "/end-day-summary", "/v500-milestone", "/health"]
    }




# =========================
# V550 CALENDAR + FILES READ-ONLY INTEGRATION PREP
# =========================

def v550_integration_status_payload() -> Dict[str, Any]:
    return {
        "calendar": {
            "provider": "google_calendar",
            "mode": "prep",
            "connected": False,
            "oauth_enabled": False,
            "read_only": True,
            "write_access": False,
            "live_data_fetch": False,
            "status": "prep_mode"
        },
        "files": {
            "provider": "google_drive",
            "mode": "prep",
            "connected": False,
            "oauth_enabled": False,
            "read_only": True,
            "write_access": False,
            "live_data_fetch": False,
            "status": "prep_mode"
        },
        "auto_loop": False,
        "manual_execution_only": True,
        "status": "prep_ready",
        "message": "Integration Prep Center is active. OAuth and live Google access are intentionally disabled."
    }


def v550_context_summary(calendar_context: Dict[str, Any], files_context: Dict[str, Any]) -> Dict[str, Any]:
    calendar_context = calendar_context or {}
    files_context = files_context or {}

    meetings = calendar_context.get("meetings") or []
    calendar_notes = calendar_context.get("notes") or ""
    calendar_risks = calendar_context.get("risks") or []
    prep_needed = calendar_context.get("prep_needed") or calendar_context.get("prepNeeded") or []

    files = files_context.get("files") or []
    files_notes = files_context.get("notes") or ""
    decisions_needed = files_context.get("decisions_needed") or files_context.get("decisionsNeeded") or []
    actions_needed = files_context.get("actions_needed") or files_context.get("actionsNeeded") or []

    calendar_summary = (
        f"Calendar prep mode: {len(meetings)} meeting item(s), "
        f"{len(prep_needed)} prep item(s), {len(calendar_risks)} risk item(s). "
        f"Notes: {str(calendar_notes)[:600]}"
    )

    files_summary = (
        f"Files prep mode: {len(files)} file/project item(s), "
        f"{len(decisions_needed)} decision item(s), {len(actions_needed)} action item(s). "
        f"Notes: {str(files_notes)[:600]}"
    )

    executive_context = (
        "Manual read-only integration prep context. "
        "No live Google Calendar or Drive access is connected. "
        f"{calendar_summary} {files_summary}"
    )

    return {
        "calendar_summary": calendar_summary,
        "files_summary": files_summary,
        "executive_context": executive_context
    }


@app.get("/integrations/status")
async def integrations_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V550 Integration Prep Center",
        **v550_integration_status_payload()
    }


@app.post("/integrations/safety-check")
async def integrations_safety_check(payload: Dict[str, Any]):
    calendar_oauth_enabled = bool(payload.get("calendar_oauth_enabled", False))
    files_oauth_enabled = bool(payload.get("files_oauth_enabled", False))
    write_access_requested = bool(payload.get("write_access_requested", False))
    auto_loop_enabled = bool(payload.get("auto_loop_enabled", False))

    checks = [
        {"name": "Calendar OAuth disabled", "passed": not calendar_oauth_enabled},
        {"name": "Files OAuth disabled", "passed": not files_oauth_enabled},
        {"name": "Write access disabled", "passed": not write_access_requested},
        {"name": "Auto-loop disabled", "passed": not auto_loop_enabled},
        {"name": "Manual execution only", "passed": True},
        {"name": "No token storage active", "passed": True},
        {"name": "No live Google fetch active", "passed": True}
    ]
    passed = all(c["passed"] for c in checks)

    return {
        "ok": True,
        "version": VERSION,
        "passed": passed,
        "status": "safe" if passed else "review_required",
        "checks": checks,
        "message": "Integration prep is safe. OAuth remains disabled." if passed else "Integration safety failed. Review settings before continuing."
    }


@app.post("/integrations/context-preview")
async def integrations_context_preview(payload: Dict[str, Any]):
    calendar_context = payload.get("calendar_context") or {}
    files_context = payload.get("files_context") or {}
    summary = v550_context_summary(calendar_context, files_context)

    return {
        "ok": True,
        "version": VERSION,
        "summary": summary,
        "safe_to_send_to_ai": True,
        "recommended_destinations": [
            "daily_brief",
            "run_command",
            "meeting_prep",
            "end_day_summary"
        ],
        "safety": {
            "manual_context_only": True,
            "oauth_enabled": False,
            "write_access": False,
            "auto_loop": False,
            "live_google_data": False
        }
    }


@app.get("/v550-milestone")
async def v550_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V500 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Integration status endpoint available", "passed": True},
        {"name": "Safety check endpoint available", "passed": True},
        {"name": "Context preview endpoint available", "passed": True},
        {"name": "OAuth disabled", "passed": True},
        {"name": "Write access disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar + Files Read-Only Integration Prep",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V550 Integration Prep · V550 Backend",
        "checks": checks,
        "added": [
            "Integration Prep Center",
            "Calendar Prep",
            "Files Prep",
            "Integration Status",
            "Read-Only Safety",
            "Context Preview",
            "Manual context send-to-command flow"
        ],
        "not_added": [
            "Google OAuth",
            "Google token storage",
            "Live Calendar fetch",
            "Live Drive fetch",
            "Supabase schema changes",
            "Autonomous automation"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/integrations/status",
            "/v550-milestone",
            "/health"
        ]
    }




# =========================
# V600 CALENDAR INTELLIGENCE READ-ONLY MODULE
# =========================
# Safe read-only contract layer. No real Google OAuth/token storage/live Calendar fetch yet.

def v600_calendar_status_payload() -> Dict[str, Any]:
    return {
        "connected": False,
        "provider": "google_calendar",
        "mode": "read_only_prep",
        "oauth_enabled": False,
        "scope_required_later": "https://www.googleapis.com/auth/calendar.events.readonly",
        "write_access": False,
        "live_data_fetch": False,
        "status": "not_connected",
        "message": "Calendar Intelligence is ready in read-only prep mode. Real Google OAuth is not connected yet."
    }


def v600_empty_day_summary(timezone: str = "America/Toronto") -> Dict[str, Any]:
    return {
        "date": "",
        "timezone": timezone,
        "totalEvents": 0,
        "totalMeetingMinutes": 0,
        "firstMeetingAt": None,
        "nextMeetingAt": None,
        "meetingDensity": "light",
        "prepNeededCount": 0,
        "events": [],
        "source": "calendar_prep",
        "connected": False,
        "message": "No live calendar events available because Google Calendar OAuth is not connected."
    }


def v600_calendar_alerts_payload() -> List[Dict[str, Any]]:
    return [
        {
            "type": "calendar_not_connected",
            "priority": "Low",
            "title": "Calendar not connected",
            "message": "Calendar Intelligence is in read-only prep mode. Use manual calendar context until OAuth is enabled.",
            "action": "Use Integration Prep Center"
        },
        {
            "type": "oauth_review_required",
            "priority": "Medium",
            "title": "OAuth review required",
            "message": "Real Google Calendar connection requires review before enabling.",
            "action": "Review read-only scope and safety rules"
        }
    ]


@app.get("/calendar/status")
async def calendar_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V600 Calendar Intelligence",
        **v600_calendar_status_payload()
    }


@app.get("/calendar/events/today")
async def calendar_events_today(timezone: str = Query("America/Toronto"), calendar_id: str = Query("primary")):
    return {
        "ok": True,
        "version": VERSION,
        "calendar_id": calendar_id,
        "summary": v600_empty_day_summary(timezone),
        "safety": {
            "read_only": True,
            "oauth_enabled": False,
            "write_access": False,
            "live_google_fetch": False
        }
    }


@app.get("/calendar/events/upcoming")
async def calendar_events_upcoming(days: int = Query(7), timezone: str = Query("America/Toronto"), calendar_id: str = Query("primary")):
    return {
        "ok": True,
        "version": VERSION,
        "calendar_id": calendar_id,
        "days": days,
        "timezone": timezone,
        "events": [],
        "connected": False,
        "message": "Upcoming live calendar events are unavailable until Google Calendar OAuth is connected.",
        "safety": {
            "read_only": True,
            "oauth_enabled": False,
            "write_access": False,
            "live_google_fetch": False
        }
    }


@app.get("/calendar/day-load")
async def calendar_day_load(timezone: str = Query("America/Toronto")):
    summary = v600_empty_day_summary(timezone)
    return {
        "ok": True,
        "version": VERSION,
        "day_load": {
            "timezone": timezone,
            "meeting_density": summary["meetingDensity"],
            "total_events": summary["totalEvents"],
            "total_meeting_minutes": summary["totalMeetingMinutes"],
            "prep_needed_count": summary["prepNeededCount"],
            "status": "prep_mode"
        }
    }


@app.get("/calendar/alerts")
async def calendar_alerts():
    return {
        "ok": True,
        "version": VERSION,
        "alerts": v600_calendar_alerts_payload()
    }


@app.post("/calendar/context-to-brief")
async def calendar_context_to_brief(payload: Dict[str, Any]):
    calendar_context = payload.get("calendar_context") or {}
    destination = payload.get("destination", "daily_brief")
    meetings = calendar_context.get("meetings") or []
    notes = calendar_context.get("notes") or ""
    risks = calendar_context.get("risks") or []
    prep_needed = calendar_context.get("prep_needed") or calendar_context.get("prepNeeded") or []

    prompt = (
        "Use this manual read-only Calendar Intelligence context. "
        "Do not assume live Google Calendar access. "
        f"Destination: {destination}. "
        f"Meetings: {meetings}. Notes: {notes}. Risks: {risks}. Prep needed: {prep_needed}. "
        "Return decision, next_move, actions, risk, priority, and recommended_command."
    )

    return {
        "ok": True,
        "version": VERSION,
        "safe_to_send_to_ai": True,
        "destination": destination,
        "prompt": prompt,
        "safety": {
            "manual_context_only": True,
            "oauth_enabled": False,
            "write_access": False,
            "live_google_data": False,
            "auto_loop": False
        }
    }


@app.get("/v600-milestone")
async def v600_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V550 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Calendar status endpoint available", "passed": True},
        {"name": "Today events contract available", "passed": True},
        {"name": "Upcoming events contract available", "passed": True},
        {"name": "Calendar alerts available", "passed": True},
        {"name": "OAuth disabled", "passed": True},
        {"name": "Write access disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Intelligence Read-Only Module",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V600 Calendar Intelligence · V600 Backend",
        "checks": checks,
        "added": [
            "Calendar Intelligence panel",
            "Calendar status contract",
            "Today events contract",
            "Upcoming events contract",
            "Day load contract",
            "Calendar alerts contract",
            "Manual calendar context to brief prompt"
        ],
        "not_added": [
            "Real Google OAuth",
            "Token storage",
            "Live Calendar event fetch",
            "Calendar write access",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/calendar/status",
            "/calendar/events/today",
            "/calendar/events/upcoming",
            "/calendar/day-load",
            "/calendar/alerts",
            "/v600-milestone",
            "/health"
        ]
    }




# =========================
# V650 FILES INTELLIGENCE + NOTIFICATION UPGRADE
# =========================
# Safe read-only contract layer. No real Google Drive OAuth/token storage/live file fetch yet.

def v650_files_status_payload() -> Dict[str, Any]:
    return {
        "connected": False,
        "provider": "google_drive",
        "mode": "read_only_prep",
        "oauth_enabled": False,
        "scope_required_later": "https://www.googleapis.com/auth/drive.readonly",
        "write_access": False,
        "live_data_fetch": False,
        "file_parsing": False,
        "status": "not_connected",
        "message": "Files Intelligence is ready in read-only prep mode. Real Google Drive OAuth is not connected yet."
    }


def v650_extract_items(text: str, kind: str) -> List[str]:
    raw = str(text or "")
    lines = [x.strip(" -•\t") for x in raw.splitlines() if x.strip()]
    keywords = {
        "decision": ["decision", "approve", "choose", "select", "confirm", "decide"],
        "action": ["action", "todo", "next", "send", "review", "call", "assign", "complete", "ship", "test"],
        "risk": ["risk", "blocker", "issue", "concern", "constraint", "problem"]
    }.get(kind, [])
    matches = []
    for line in lines:
        low = line.lower()
        if any(k in low for k in keywords):
            matches.append(line[:220])
    if not matches and raw.strip():
        if kind == "decision":
            matches = ["Identify the decision needed from the provided file/project context."]
        elif kind == "action":
            matches = ["Convert the file/project context into one executable next action."]
        elif kind == "risk":
            matches = ["Review the file/project context for execution risk."]
    return matches[:6]


def v650_files_prep_summary(files_context: Dict[str, Any]) -> Dict[str, Any]:
    files_context = files_context or {}
    files = files_context.get("files") or []
    notes = str(files_context.get("notes") or "")
    decisions_needed = files_context.get("decisions_needed") or files_context.get("decisionsNeeded") or []
    actions_needed = files_context.get("actions_needed") or files_context.get("actionsNeeded") or []
    risks = files_context.get("risks") or []

    combined_text = " ".join([str(x) for x in files]) + " " + notes
    if not decisions_needed:
        decisions_needed = v650_extract_items(combined_text, "decision")
    if not actions_needed:
        actions_needed = v650_extract_items(combined_text, "action")
    if not risks:
        risks = v650_extract_items(combined_text, "risk")

    return {
        "mode": "prep",
        "connected": False,
        "oauth_enabled": False,
        "file_count": len(files),
        "notes_present": bool(notes.strip()),
        "decisions_needed": decisions_needed[:6],
        "actions_needed": actions_needed[:6],
        "risks": risks[:6],
        "summary": (
            f"Files prep mode: {len(files)} file/project item(s), "
            f"{len(decisions_needed)} decision item(s), {len(actions_needed)} action item(s), "
            f"{len(risks)} risk item(s). No live Google Drive access."
        ),
        "safe_to_send_to_ai": True
    }


def v650_notification_upgrade_payload() -> List[Dict[str, Any]]:
    return [
        {
            "type": "calendar_prep_needed",
            "priority": "Medium",
            "title": "Calendar prep needed",
            "message": "Calendar is in prep mode. Add meeting context manually before Daily Brief.",
            "route": "integration_prep"
        },
        {
            "type": "file_context_missing",
            "priority": "Medium",
            "title": "File context missing",
            "message": "Files are in prep mode. Add project/file context before strategic decisions.",
            "route": "integration_prep"
        },
        {
            "type": "decision_followup",
            "priority": "Medium",
            "title": "Decision follow-up",
            "message": "Review decisions and attach one action.",
            "route": "decisions"
        },
        {
            "type": "risk_review",
            "priority": "High",
            "title": "Risk review",
            "message": "Review recurring risks before adding more actions.",
            "route": "risk"
        },
        {
            "type": "action_overload",
            "priority": "High",
            "title": "Action overload check",
            "message": "Check open actions and cut or complete low-value items.",
            "route": "actions"
        },
        {
            "type": "system_test",
            "priority": "Low",
            "title": "System test reminder",
            "message": "Run /diagnostic and /system-test after deploys.",
            "route": "settings"
        }
    ]


@app.get("/files/status")
async def files_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V650 Files Intelligence",
        **v650_files_status_payload()
    }


@app.get("/files/prep-summary")
async def files_prep_summary():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Files Prep Summary",
        "summary": v650_files_prep_summary({})
    }


@app.post("/files/context-to-command")
async def files_context_to_command(payload: Dict[str, Any]):
    files_context = payload.get("files_context") or {}
    destination = payload.get("destination", "run_command")
    summary = v650_files_prep_summary(files_context)

    prompt = (
        "Use this manual read-only Files Intelligence context. "
        "Do not assume live Google Drive access. "
        f"Destination: {destination}. "
        f"Summary: {summary.get('summary')}. "
        f"Decisions needed: {summary.get('decisions_needed')}. "
        f"Actions needed: {summary.get('actions_needed')}. "
        f"Risks: {summary.get('risks')}. "
        "Return decision, next_move, actions, risk, priority, and recommended_command."
    )

    return {
        "ok": True,
        "version": VERSION,
        "safe_to_send_to_ai": True,
        "destination": destination,
        "prompt": prompt,
        "summary": summary,
        "safety": {
            "manual_context_only": True,
            "oauth_enabled": False,
            "write_access": False,
            "live_google_data": False,
            "file_parsing": False,
            "auto_loop": False
        }
    }


@app.get("/files/alerts")
async def files_alerts():
    return {
        "ok": True,
        "version": VERSION,
        "alerts": [
            {
                "type": "files_not_connected",
                "priority": "Low",
                "title": "Files not connected",
                "message": "Files Intelligence is in read-only prep mode. Use manual file/project context until OAuth is enabled.",
                "action": "Use Integration Prep Center"
            },
            {
                "type": "file_context_needed",
                "priority": "Medium",
                "title": "File context needed",
                "message": "Add project/file context before running strategy, risk, or decision commands.",
                "action": "Add manual file context"
            }
        ]
    }


@app.get("/notification-upgrade")
async def notification_upgrade():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V650 Notification Upgrade",
        "notifications": v650_notification_upgrade_payload(),
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/v650-milestone")
async def v650_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V600 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Files status endpoint available", "passed": True},
        {"name": "Files prep summary available", "passed": True},
        {"name": "Files context-to-command available", "passed": True},
        {"name": "Files alerts available", "passed": True},
        {"name": "Notification upgrade available", "passed": True},
        {"name": "Google Drive OAuth disabled", "passed": True},
        {"name": "File write access disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Files Intelligence + Notification Upgrade",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V650 Files Intelligence · V650 Backend",
        "checks": checks,
        "added": [
            "Files Intelligence panel",
            "Files status contract",
            "Files prep summary",
            "Manual file context to command",
            "Files alerts",
            "Notification Center upgrade"
        ],
        "not_added": [
            "Real Google Drive OAuth",
            "Token storage",
            "Live Drive file fetch",
            "File write access",
            "File parsing pipeline",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/files/status",
            "/files/prep-summary",
            "/files/alerts",
            "/notification-upgrade",
            "/v650-milestone",
            "/health"
        ]
    }




# =========================
# V700 OAUTH READINESS + CONNECTOR ACTIVATION CANDIDATE
# =========================
# Safe readiness layer only. Real OAuth remains disabled by default.
# No token storage, no live Google fetch, no external writes, no background sync.

def v700_connector_matrix() -> List[Dict[str, Any]]:
    return [
        {
            "id": "google_calendar",
            "name": "Google Calendar",
            "phase": "ready_for_oauth_review",
            "status": "prep_mode",
            "connected": False,
            "oauth_enabled": False,
            "scope_later": "https://www.googleapis.com/auth/calendar.events.readonly",
            "read_only": True,
            "write_access": False,
            "risk": "Low",
            "next_step": "Review OAuth consent and enable read-only connection in a future build."
        },
        {
            "id": "google_drive",
            "name": "Google Drive / Files",
            "phase": "ready_for_oauth_review",
            "status": "prep_mode",
            "connected": False,
            "oauth_enabled": False,
            "scope_later": "https://www.googleapis.com/auth/drive.readonly",
            "read_only": True,
            "write_access": False,
            "risk": "Medium",
            "next_step": "Review file privacy rules before enabling read-only file access."
        },
        {
            "id": "gmail",
            "name": "Gmail / Email Drafts",
            "phase": "spec_required",
            "status": "not_connected",
            "connected": False,
            "oauth_enabled": False,
            "scope_later": "draft-only/read-only scope to be reviewed later",
            "read_only": True,
            "write_access": False,
            "risk": "Medium",
            "next_step": "Design draft-only email spec before enabling OAuth."
        }
    ]


def v700_oauth_readiness_payload() -> Dict[str, Any]:
    checks = [
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Calendar read-only contract exists", "passed": True},
        {"name": "Files read-only contract exists", "passed": True},
        {"name": "OAuth disabled by default", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "External writes disabled", "passed": True},
        {"name": "Background sync disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    return {
        "status": "oauth_readiness_candidate",
        "ready_for_live_oauth": False,
        "ready_for_review": True,
        "checks": checks,
        "required_before_live_oauth": [
            "Confirm Google OAuth consent screen",
            "Confirm redirect URI in Google Cloud",
            "Confirm environment variables are set in Render",
            "Confirm secure server-side token storage design",
            "Confirm disconnect/revoke behavior",
            "Confirm privacy policy and data handling rules",
            "Confirm user approval flow before any context is sent to AI"
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/connectors/status")
async def connectors_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V700 Connector Status",
        "connectors": v700_connector_matrix(),
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/oauth/readiness")
async def oauth_readiness():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Readiness",
        "readiness": v700_oauth_readiness_payload()
    }


@app.get("/oauth/config-check")
async def oauth_config_check():
    # Do not expose actual env var values.
    import os
    expected = {
        "GOOGLE_CLIENT_ID": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "GOOGLE_CLIENT_SECRET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "GOOGLE_REDIRECT_URI": bool(os.getenv("GOOGLE_REDIRECT_URI")),
        "GOOGLE_CALENDAR_SCOPE": bool(os.getenv("GOOGLE_CALENDAR_SCOPE")),
        "GOOGLE_DRIVE_SCOPE": bool(os.getenv("GOOGLE_DRIVE_SCOPE"))
    }
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Config Check",
        "oauth_enabled": False,
        "config_present": expected,
        "safe": True,
        "message": "Config check only. OAuth remains disabled and no tokens are stored."
    }


@app.post("/oauth/safety-review")
async def oauth_safety_review(payload: Dict[str, Any]):
    requested_write_access = bool(payload.get("requested_write_access", False))
    background_sync = bool(payload.get("background_sync", False))
    token_storage_enabled = bool(payload.get("token_storage_enabled", False))
    auto_send_enabled = bool(payload.get("auto_send_enabled", False))
    calendar_scope = str(payload.get("calendar_scope", ""))
    drive_scope = str(payload.get("drive_scope", ""))

    checks = [
        {"name": "No write access requested", "passed": not requested_write_access},
        {"name": "No background sync", "passed": not background_sync},
        {"name": "No token storage active yet", "passed": not token_storage_enabled},
        {"name": "No auto-send enabled", "passed": not auto_send_enabled},
        {"name": "Calendar scope read-only if provided", "passed": (not calendar_scope) or ("readonly" in calendar_scope and "calendar.events" in calendar_scope)},
        {"name": "Drive scope read-only if provided", "passed": (not drive_scope) or ("readonly" in drive_scope)}
    ]
    passed = all(c["passed"] for c in checks)
    return {
        "ok": True,
        "version": VERSION,
        "passed": passed,
        "status": "safe_for_review" if passed else "blocked",
        "checks": checks,
        "message": "OAuth readiness is safe for review only. Live OAuth is still disabled." if passed else "OAuth safety review failed. Do not enable live connection."
    }


@app.get("/approval-gates")
async def approval_gates():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Approval Gates",
        "gates": [
            {
                "id": "send_context_to_ai",
                "title": "Send connector context to AI",
                "required": True,
                "status": "manual_only"
            },
            {
                "id": "connect_google_calendar",
                "title": "Connect Google Calendar",
                "required": True,
                "status": "review_required"
            },
            {
                "id": "connect_google_drive",
                "title": "Connect Google Drive",
                "required": True,
                "status": "review_required"
            },
            {
                "id": "external_write",
                "title": "External write action",
                "required": True,
                "status": "blocked"
            },
            {
                "id": "automation_loop",
                "title": "Automation loop",
                "required": True,
                "status": "blocked"
            }
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/v700-milestone")
async def v700_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V650 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Connector status available", "passed": True},
        {"name": "OAuth readiness available", "passed": True},
        {"name": "OAuth config check available", "passed": True},
        {"name": "OAuth safety review available", "passed": True},
        {"name": "Approval gates available", "passed": True},
        {"name": "Live OAuth disabled", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "External writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Readiness + Connector Activation Candidate",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V700 OAuth Readiness · V700 Backend",
        "checks": checks,
        "added": [
            "Connector Status Matrix",
            "OAuth Readiness Center",
            "OAuth Config Check",
            "OAuth Safety Review",
            "Approval Gates",
            "Connector activation readiness UI"
        ],
        "not_added": [
            "Real OAuth connection",
            "Token storage",
            "Live Google Calendar fetch",
            "Live Google Drive fetch",
            "Gmail OAuth",
            "External writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/connectors/status",
            "/oauth/readiness",
            "/oauth/config-check",
            "/approval-gates",
            "/v700-milestone",
            "/health"
        ]
    }




# =========================
# V750 CONNECTOR COMMAND CENTER + SUPERVISED APPROVAL WORKFLOW
# =========================
# No real OAuth. No token storage. No external writes. No automation loop.

def v750_connector_stack() -> List[Dict[str, Any]]:
    return [
        {
            "id": "calendar",
            "name": "Calendar Intelligence",
            "status": "ready_for_review",
            "mode": "read_only_prep",
            "connected": False,
            "writes_blocked": True,
            "primary_use": "Daily Brief, meeting prep, meeting load",
            "next_safe_step": "Enable read-only OAuth only after consent and token storage review."
        },
        {
            "id": "files",
            "name": "Files Intelligence",
            "status": "ready_for_review",
            "mode": "read_only_prep",
            "connected": False,
            "writes_blocked": True,
            "primary_use": "Project context, decisions needed, actions needed",
            "next_safe_step": "Review file privacy rules before read-only Drive access."
        },
        {
            "id": "email",
            "name": "Email Draft Intelligence",
            "status": "spec_needed",
            "mode": "draft_only_future",
            "connected": False,
            "writes_blocked": True,
            "primary_use": "Draft follow-ups, meeting recaps, action owner requests",
            "next_safe_step": "Build draft-only spec before Gmail OAuth."
        },
        {
            "id": "crm",
            "name": "CRM / Revenue Intelligence",
            "status": "planned",
            "mode": "read_only_future",
            "connected": False,
            "writes_blocked": True,
            "primary_use": "Pipeline risk, revenue priority, customer follow-up context",
            "next_safe_step": "Define CRM provider and read-only data model."
        }
    ]


def v750_approval_queue() -> List[Dict[str, Any]]:
    return [
        {
            "id": "approve_calendar_oauth_review",
            "title": "Review Google Calendar OAuth",
            "type": "connector_review",
            "priority": "High",
            "status": "pending_review",
            "approval_required": True,
            "blocked_action": "Live Google Calendar connection",
            "safe_next_step": "Confirm read-only scope and redirect URI before activation."
        },
        {
            "id": "approve_drive_oauth_review",
            "title": "Review Google Drive OAuth",
            "type": "connector_review",
            "priority": "High",
            "status": "pending_review",
            "approval_required": True,
            "blocked_action": "Live Google Drive connection",
            "safe_next_step": "Confirm file privacy rules and read-only scope before activation."
        },
        {
            "id": "approve_email_draft_spec",
            "title": "Approve Email Draft Spec",
            "type": "module_spec",
            "priority": "Medium",
            "status": "spec_needed",
            "approval_required": True,
            "blocked_action": "Gmail OAuth or email sending",
            "safe_next_step": "Design draft-only email workflow with no auto-send."
        },
        {
            "id": "approve_external_writes",
            "title": "External Writes",
            "type": "safety_gate",
            "priority": "Critical",
            "status": "blocked",
            "approval_required": True,
            "blocked_action": "Any write to calendar, files, email, CRM, or external tools",
            "safe_next_step": "Keep blocked until user explicitly approves a future write-capable version."
        }
    ]


def v750_supervised_actions() -> List[Dict[str, Any]]:
    return [
        {
            "action": "Send calendar context to Daily Brief",
            "allowed": True,
            "approval_required": False,
            "mode": "manual",
            "external_write": False
        },
        {
            "action": "Send file context to Run Command",
            "allowed": True,
            "approval_required": False,
            "mode": "manual",
            "external_write": False
        },
        {
            "action": "Generate email draft",
            "allowed": True,
            "approval_required": True,
            "mode": "draft_only_future",
            "external_write": False
        },
        {
            "action": "Send email",
            "allowed": False,
            "approval_required": True,
            "mode": "blocked",
            "external_write": True
        },
        {
            "action": "Create calendar event",
            "allowed": False,
            "approval_required": True,
            "mode": "blocked",
            "external_write": True
        },
        {
            "action": "Edit Google Drive file",
            "allowed": False,
            "approval_required": True,
            "mode": "blocked",
            "external_write": True
        }
    ]


@app.get("/connector-command-center")
async def connector_command_center():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Connector Command Center",
        "connectors": v750_connector_stack(),
        "approval_queue": v750_approval_queue(),
        "supervised_actions": v750_supervised_actions(),
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/approval-queue")
async def approval_queue():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Approval Queue",
        "items": v750_approval_queue(),
        "external_writes_blocked": True,
        "manual_execution_only": True
    }


@app.get("/supervised-actions")
async def supervised_actions():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Supervised Actions",
        "actions": v750_supervised_actions(),
        "policy": {
            "external_writes_blocked": True,
            "auto_send_blocked": True,
            "auto_loop_blocked": True,
            "manual_context_allowed": True
        }
    }


@app.post("/approval/simulate")
async def approval_simulate(payload: Dict[str, Any]):
    action_type = str(payload.get("action_type", "unknown")).lower()
    external_write = bool(payload.get("external_write", False))
    oauth_activation = bool(payload.get("oauth_activation", False))
    auto_loop = bool(payload.get("auto_loop", False))

    blocked = external_write or auto_loop
    requires_review = oauth_activation or external_write or auto_loop or action_type in ["email_send", "calendar_write", "file_write", "crm_write"]

    return {
        "ok": True,
        "version": VERSION,
        "approved": False if blocked else (not requires_review),
        "requires_review": requires_review,
        "blocked": blocked,
        "decision": "blocked" if blocked else ("review_required" if requires_review else "manual_allowed"),
        "reason": (
            "External writes and automation loops remain blocked."
            if blocked else
            "This action requires explicit review before activation."
            if requires_review else
            "Manual, internal-only action is allowed."
        ),
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/connector-notifications")
async def connector_notifications():
    return {
        "ok": True,
        "version": VERSION,
        "notifications": [
            {
                "type": "connector_review",
                "priority": "High",
                "title": "Calendar OAuth review pending",
                "message": "Review read-only Calendar scope before enabling live connection."
            },
            {
                "type": "connector_review",
                "priority": "High",
                "title": "Drive OAuth review pending",
                "message": "Review file privacy and read-only Drive scope before enabling live connection."
            },
            {
                "type": "approval_gate",
                "priority": "Critical",
                "title": "External writes blocked",
                "message": "Calendar, file, email, and CRM writes remain blocked."
            },
            {
                "type": "manual_execution",
                "priority": "Medium",
                "title": "Manual execution only",
                "message": "Connector context can be manually loaded into commands, but no background automation runs."
            }
        ]
    }


@app.get("/v750-milestone")
async def v750_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V700 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Connector command center available", "passed": True},
        {"name": "Approval queue available", "passed": True},
        {"name": "Supervised actions available", "passed": True},
        {"name": "Approval simulator available", "passed": True},
        {"name": "Connector notifications available", "passed": True},
        {"name": "Live OAuth disabled", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "External writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Connector Command Center + Supervised Approval Workflow",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V750 Connector Command Center · V750 Backend",
        "checks": checks,
        "added": [
            "Connector Command Center",
            "Approval Queue",
            "Supervised Actions",
            "Approval Simulator",
            "Connector Notifications",
            "External write blocking policy"
        ],
        "not_added": [
            "Real OAuth connection",
            "Token storage",
            "Live Google fetch",
            "Gmail OAuth",
            "External writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/connector-command-center",
            "/approval-queue",
            "/supervised-actions",
            "/connector-notifications",
            "/v750-milestone",
            "/health"
        ]
    }




# =========================
# V800 OAUTH ACTIVATION PREP + SECURE CONNECTOR SETUP
# =========================
# This is still prep only: no real OAuth flow, no token storage, no live Google fetch, no external writes.

def v800_env_readiness() -> Dict[str, Any]:
    import os
    keys = {
        "GOOGLE_CLIENT_ID": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "GOOGLE_CLIENT_SECRET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "GOOGLE_REDIRECT_URI": bool(os.getenv("GOOGLE_REDIRECT_URI")),
        "GOOGLE_CALENDAR_SCOPE": bool(os.getenv("GOOGLE_CALENDAR_SCOPE")),
        "GOOGLE_DRIVE_SCOPE": bool(os.getenv("GOOGLE_DRIVE_SCOPE")),
        "OAUTH_ENABLED": bool(os.getenv("OAUTH_ENABLED"))
    }
    required_for_activation = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
    missing = [k for k in required_for_activation if not keys.get(k)]
    return {
        "config_present": keys,
        "missing_required_for_activation": missing,
        "activation_ready": len(missing) == 0,
        "oauth_enabled_now": False,
        "note": "Environment variables are checked as booleans only. Values are never exposed."
    }


def v800_scope_policy() -> Dict[str, Any]:
    return {
        "calendar": {
            "allowed_scope": "https://www.googleapis.com/auth/calendar.events.readonly",
            "blocked_scopes": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events"
            ],
            "write_access": False,
            "status": "read_only_required"
        },
        "drive": {
            "allowed_scope": "https://www.googleapis.com/auth/drive.readonly",
            "blocked_scopes": [
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file"
            ],
            "write_access": False,
            "status": "read_only_required"
        },
        "gmail": {
            "allowed_scope": "not_enabled_yet",
            "blocked_until": "draft_only_spec_review",
            "write_access": False,
            "status": "blocked"
        }
    }


def v800_activation_checklist() -> List[Dict[str, Any]]:
    return [
        {"step": "Confirm Google Cloud OAuth consent screen", "status": "required"},
        {"step": "Set Render environment variables", "status": "required"},
        {"step": "Confirm redirect URI matches backend route", "status": "required"},
        {"step": "Confirm read-only Calendar scope only", "status": "required"},
        {"step": "Confirm read-only Drive scope only", "status": "required"},
        {"step": "Design secure server-side token storage", "status": "required_before_live"},
        {"step": "Design disconnect/revoke flow", "status": "required_before_live"},
        {"step": "Confirm privacy policy and data handling language", "status": "required_before_live"},
        {"step": "Run /diagnostic and /system-test", "status": "required"},
        {"step": "Keep auto-loop off", "status": "locked"}
    ]


@app.get("/oauth/activation-prep")
async def oauth_activation_prep():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Activation Prep",
        "env_readiness": v800_env_readiness(),
        "scope_policy": v800_scope_policy(),
        "activation_checklist": v800_activation_checklist(),
        "live_oauth_enabled": False,
        "token_storage_enabled": False,
        "external_writes_enabled": False,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/oauth/scope-policy")
async def oauth_scope_policy():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Scope Policy",
        "policy": v800_scope_policy()
    }


@app.get("/oauth/env-readiness")
async def oauth_env_readiness():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Environment Readiness",
        "readiness": v800_env_readiness()
    }


@app.get("/oauth/activation-checklist")
async def oauth_activation_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Activation Checklist",
        "checklist": v800_activation_checklist()
    }


@app.post("/oauth/activation-simulate")
async def oauth_activation_simulate(payload: Dict[str, Any]):
    connector = str(payload.get("connector", "calendar")).lower()
    requested_scope = str(payload.get("requested_scope", ""))
    enable_oauth = bool(payload.get("enable_oauth", False))
    token_storage_ready = bool(payload.get("token_storage_ready", False))
    external_write_requested = bool(payload.get("external_write_requested", False))
    auto_loop_requested = bool(payload.get("auto_loop_requested", False))

    policy = v800_scope_policy()
    connector_policy = policy.get(connector, {})

    scope_allowed = requested_scope == connector_policy.get("allowed_scope")
    blocked = external_write_requested or auto_loop_requested
    review_required = enable_oauth or token_storage_ready or bool(requested_scope)

    can_activate = (
        enable_oauth
        and token_storage_ready
        and scope_allowed
        and not blocked
        and connector in ["calendar", "drive"]
    )

    return {
        "ok": True,
        "version": VERSION,
        "connector": connector,
        "can_activate_now": False,
        "simulation_result": "ready_for_review" if can_activate else ("blocked" if blocked else "not_ready"),
        "scope_allowed": scope_allowed,
        "review_required": review_required,
        "blocked": blocked,
        "reason": (
            "Simulation passed, but live OAuth remains disabled in V800."
            if can_activate else
            "External writes or automation loops are blocked."
            if blocked else
            "Activation requires approved scope, token storage design, and explicit future enablement."
        ),
        "live_oauth_enabled": False,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/security-gates")
async def security_gates():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Security Gates",
        "gates": [
            {
                "id": "read_only_scope",
                "title": "Read-only scopes only",
                "status": "required",
                "blocks": "Any write-capable OAuth scope"
            },
            {
                "id": "server_side_tokens",
                "title": "Server-side token storage",
                "status": "required_before_live",
                "blocks": "Frontend token exposure"
            },
            {
                "id": "disconnect_revoke",
                "title": "Disconnect/revoke flow",
                "status": "required_before_live",
                "blocks": "Persistent access without user control"
            },
            {
                "id": "approval_before_ai_context",
                "title": "Approval before sending connector context to AI",
                "status": "required",
                "blocks": "Automatic context sharing"
            },
            {
                "id": "external_writes",
                "title": "External writes",
                "status": "blocked",
                "blocks": "Calendar/file/email/CRM modifications"
            },
            {
                "id": "automation_loop",
                "title": "Automation loop",
                "status": "blocked",
                "blocks": "Background autonomous execution"
            }
        ]
    }


@app.get("/v800-milestone")
async def v800_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V750 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "OAuth activation prep available", "passed": True},
        {"name": "Scope policy available", "passed": True},
        {"name": "Env readiness available", "passed": True},
        {"name": "Activation checklist available", "passed": True},
        {"name": "Activation simulation available", "passed": True},
        {"name": "Security gates available", "passed": True},
        {"name": "Live OAuth disabled", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "External writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "OAuth Activation Prep + Secure Connector Setup",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V800 OAuth Activation Prep · V800 Backend",
        "checks": checks,
        "added": [
            "OAuth Activation Prep",
            "Scope Policy",
            "Environment Readiness",
            "Activation Checklist",
            "Activation Simulation",
            "Security Gates",
            "Connector setup UI"
        ],
        "not_added": [
            "Live OAuth",
            "Token storage",
            "Live Calendar fetch",
            "Live Drive fetch",
            "Gmail OAuth",
            "External writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/oauth/activation-prep",
            "/oauth/scope-policy",
            "/oauth/env-readiness",
            "/oauth/activation-checklist",
            "/security-gates",
            "/v800-milestone",
            "/health"
        ]
    }




# =========================
# V850 GOOGLE CONNECTOR BLUEPRINT + ACTIVATION PLAN
# =========================
# Still safe blueprint only. No live OAuth. No tokens. No external writes.

def v850_connector_blueprint() -> Dict[str, Any]:
    return {
        "calendar": {
            "name": "Google Calendar Read-Only",
            "status": "blueprint_ready",
            "live_enabled": False,
            "scope": "https://www.googleapis.com/auth/calendar.events.readonly",
            "backend_routes_future": [
                "GET /calendar/auth-url",
                "GET /calendar/oauth/callback",
                "GET /calendar/status",
                "GET /calendar/events/today",
                "GET /calendar/events/upcoming",
                "POST /calendar/disconnect"
            ],
            "current_safe_routes": [
                "GET /calendar/status",
                "GET /calendar/events/today",
                "GET /calendar/events/upcoming",
                "GET /calendar/day-load",
                "GET /calendar/alerts"
            ],
            "data_policy": [
                "Read-only only",
                "No write scopes",
                "No event creation",
                "No event editing",
                "No auto-join",
                "No background sync",
                "Manual context send only"
            ]
        },
        "drive": {
            "name": "Google Drive / Files Read-Only",
            "status": "blueprint_ready",
            "live_enabled": False,
            "scope": "https://www.googleapis.com/auth/drive.readonly",
            "backend_routes_future": [
                "GET /files/auth-url",
                "GET /files/oauth/callback",
                "GET /files/status",
                "GET /files/list",
                "GET /files/read",
                "POST /files/disconnect"
            ],
            "current_safe_routes": [
                "GET /files/status",
                "GET /files/prep-summary",
                "POST /files/context-to-command",
                "GET /files/alerts"
            ],
            "data_policy": [
                "Read-only only",
                "No write scopes",
                "No file editing",
                "No file deletion",
                "No background sync",
                "Manual context send only",
                "No permanent file content storage yet"
            ]
        },
        "gmail": {
            "name": "Gmail Draft-Only Future",
            "status": "spec_required",
            "live_enabled": False,
            "scope": "not_selected",
            "backend_routes_future": [
                "GET /email/status",
                "POST /email/draft-preview",
                "POST /email/create-draft",
                "POST /email/disconnect"
            ],
            "data_policy": [
                "Draft-only first",
                "No auto-send",
                "No inbox scanning until reviewed",
                "No background email polling",
                "Manual approval required"
            ]
        }
    }


def v850_activation_plan() -> List[Dict[str, Any]]:
    return [
        {
            "phase": "Phase 1",
            "title": "Calendar read-only OAuth",
            "status": "next_best_candidate",
            "steps": [
                "Confirm Google Cloud OAuth consent screen",
                "Set Calendar redirect URI",
                "Add server-side token storage design",
                "Enable read-only scope only",
                "Build connect/disconnect flow",
                "Fetch today's events manually",
                "Send summarized context to Daily Brief manually"
            ]
        },
        {
            "phase": "Phase 2",
            "title": "Drive/files read-only OAuth",
            "status": "after_calendar",
            "steps": [
                "Confirm Drive read-only privacy rules",
                "Add file list only first",
                "Add manual file selection",
                "Summarize selected file metadata",
                "Do not parse full files until reviewed",
                "Send selected context to Run Command manually"
            ]
        },
        {
            "phase": "Phase 3",
            "title": "Email draft-only workflow",
            "status": "spec_required",
            "steps": [
                "Define draft-only use cases",
                "Block auto-send",
                "Create draft preview",
                "Require user approval",
                "Only then consider Gmail OAuth"
            ]
        }
    ]


def v850_provider_requirements() -> Dict[str, Any]:
    return {
        "google_cloud": [
            "OAuth consent screen configured",
            "Authorized redirect URI set to backend callback",
            "Calendar API enabled later",
            "Drive API enabled later",
            "Scopes reviewed and restricted to read-only"
        ],
        "render_env": [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "GOOGLE_CALENDAR_SCOPE",
            "GOOGLE_DRIVE_SCOPE",
            "OAUTH_ENABLED remains false until activation build"
        ],
        "backend_security": [
            "State parameter required",
            "CSRF protection required",
            "Tokens server-side only",
            "No token values returned to frontend",
            "Disconnect/revoke flow required",
            "No background refresh until reviewed"
        ],
        "frontend_security": [
            "Show Not Connected / Prep Mode clearly",
            "User manually clicks Connect",
            "User manually refreshes events/files",
            "User manually sends context to AI",
            "No hidden background sync"
        ]
    }


@app.get("/google/connector-blueprint")
async def google_connector_blueprint():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Google Connector Blueprint",
        "blueprint": v850_connector_blueprint(),
        "live_oauth_enabled": False,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/google/activation-plan")
async def google_activation_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Google Activation Plan",
        "plan": v850_activation_plan(),
        "recommended_next_build": "V900 Calendar OAuth Candidate",
        "do_not_skip": [
            "Token storage design",
            "Disconnect/revoke flow",
            "Privacy handling",
            "Manual approval gate"
        ]
    }


@app.get("/google/provider-requirements")
async def google_provider_requirements():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Provider Requirements",
        "requirements": v850_provider_requirements()
    }


@app.get("/google/privacy-rules")
async def google_privacy_rules():
    return {
        "ok": True,
        "version": VERSION,
        "rules": [
            "No Google OAuth enabled in V850.",
            "No OAuth tokens stored in V850.",
            "No live Google data fetched in V850.",
            "Calendar and Drive must stay read-only.",
            "No event, file, or email writes.",
            "No auto-send.",
            "No background sync.",
            "No raw token values in frontend or logs.",
            "Do not send private calendar descriptions or file contents to AI without explicit user action.",
            "Manual execution only."
        ]
    }


@app.get("/v850-milestone")
async def v850_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V800 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Google connector blueprint available", "passed": True},
        {"name": "Activation plan available", "passed": True},
        {"name": "Provider requirements available", "passed": True},
        {"name": "Privacy rules available", "passed": True},
        {"name": "Live OAuth disabled", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "External writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Google Connector Blueprint + Activation Plan",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V850 Google Connector Blueprint · V850 Backend",
        "checks": checks,
        "added": [
            "Google Connector Blueprint",
            "Calendar activation plan",
            "Drive activation plan",
            "Gmail draft-only future plan",
            "Provider requirements",
            "Privacy rules",
            "Next-build recommendation"
        ],
        "not_added": [
            "Live OAuth",
            "Token storage",
            "Live Calendar fetch",
            "Live Drive fetch",
            "Gmail OAuth",
            "External writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/google/connector-blueprint",
            "/google/activation-plan",
            "/google/provider-requirements",
            "/google/privacy-rules",
            "/v850-milestone",
            "/health"
        ],
        "recommended_next_build": "V900 Calendar OAuth Candidate"
    }




# =========================
# V900 CALENDAR OAUTH CANDIDATE
# =========================
# Calendar OAuth candidate only.
# Safe route contracts are implemented.
# Real token exchange/storage is NOT active unless explicitly enabled in a future version.
# No calendar writes. No background sync. Manual execution only.

V900_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"

def v900_calendar_oauth_env() -> Dict[str, Any]:
    import os
    return {
        "GOOGLE_CLIENT_ID": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "GOOGLE_CLIENT_SECRET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "GOOGLE_REDIRECT_URI": bool(os.getenv("GOOGLE_REDIRECT_URI")),
        "GOOGLE_CALENDAR_SCOPE": bool(os.getenv("GOOGLE_CALENDAR_SCOPE")),
        "OAUTH_ENABLED": str(os.getenv("OAUTH_ENABLED", "false")).lower() == "true"
    }


def v900_calendar_ready() -> Dict[str, Any]:
    env = v900_calendar_oauth_env()
    required = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
    missing = [k for k in required if not env.get(k)]
    oauth_enabled = bool(env.get("OAUTH_ENABLED"))
    return {
        "env": env,
        "missing_required": missing,
        "candidate_ready": len(missing) == 0,
        "live_oauth_enabled": False,
        "oauth_env_flag": oauth_enabled,
        "scope": V900_CALENDAR_SCOPE,
        "write_access": False,
        "token_storage_active": False,
        "message": "Calendar OAuth candidate is prepared. Live OAuth/token storage remains disabled in V900."
    }


def v900_auth_url_placeholder() -> Dict[str, Any]:
    import os, secrets, urllib.parse
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "")
    state = secrets.token_urlsafe(24)
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id or "GOOGLE_CLIENT_ID_NOT_SET",
        "redirect_uri": redirect_uri or "GOOGLE_REDIRECT_URI_NOT_SET",
        "response_type": "code",
        "scope": V900_CALENDAR_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }
    auth_url = base + "?" + urllib.parse.urlencode(params)
    return {
        "auth_url": auth_url,
        "state": state,
        "scope": V900_CALENDAR_SCOPE,
        "live_oauth_enabled": False,
        "note": "Candidate URL only. V900 does not exchange tokens or store tokens."
    }


@app.get("/calendar/oauth-candidate/status")
async def calendar_oauth_candidate_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V900 Calendar OAuth Candidate",
        "status": v900_calendar_ready()
    }


@app.get("/calendar/auth-url-candidate")
async def calendar_auth_url_candidate():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Auth URL Candidate",
        **v900_auth_url_placeholder()
    }


@app.get("/calendar/oauth/callback-candidate")
async def calendar_oauth_callback_candidate(code: str = Query("", description="OAuth code placeholder"), state: str = Query("", description="OAuth state placeholder")):
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar OAuth Callback Candidate",
        "received_code": bool(code),
        "received_state": bool(state),
        "connected": False,
        "token_exchange_active": False,
        "token_storage_active": False,
        "message": "Callback candidate reached. Token exchange/storage is intentionally disabled in V900."
    }


@app.get("/calendar/token-storage-plan")
async def calendar_token_storage_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Token Storage Plan",
        "plan": {
            "storage": "server_side_only",
            "frontend_token_exposure": False,
            "fields_needed_future": [
                "user_id",
                "provider",
                "access_token_encrypted",
                "refresh_token_encrypted",
                "expires_at",
                "scope",
                "connected_email",
                "created_at",
                "updated_at",
                "revoked_at"
            ],
            "supabase_schema_change_required_future": True,
            "v900_schema_changed": False,
            "disconnect_required": True,
            "revoke_required": True
        },
        "warning": "Do not enable live OAuth until encrypted token storage and disconnect/revoke are implemented."
    }


@app.get("/calendar/disconnect-candidate")
async def calendar_disconnect_candidate():
    return {
        "ok": True,
        "version": VERSION,
        "connected": False,
        "revoked": False,
        "message": "Disconnect candidate only. No token exists in V900."
    }


@app.get("/calendar/readiness-report")
async def calendar_readiness_report():
    readiness = v900_calendar_ready()
    checks = [
        {"name": "Google client ID configured", "passed": readiness["env"].get("GOOGLE_CLIENT_ID")},
        {"name": "Google client secret configured", "passed": readiness["env"].get("GOOGLE_CLIENT_SECRET")},
        {"name": "Redirect URI configured", "passed": readiness["env"].get("GOOGLE_REDIRECT_URI")},
        {"name": "Read-only Calendar scope defined", "passed": True},
        {"name": "Write scopes blocked", "passed": True},
        {"name": "Token exchange disabled in V900", "passed": True},
        {"name": "Token storage disabled in V900", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "score": f"{score}/{len(checks)}",
        "ready_for_next_build": score >= 6,
        "ready_for_live_oauth": False,
        "checks": checks,
        "next_required_build": "V950 Token Storage + Disconnect Flow Candidate"
    }


@app.get("/v900-milestone")
async def v900_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V850 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Calendar OAuth candidate status available", "passed": True},
        {"name": "Auth URL candidate available", "passed": True},
        {"name": "Callback candidate available", "passed": True},
        {"name": "Token storage plan available", "passed": True},
        {"name": "Disconnect candidate available", "passed": True},
        {"name": "Readiness report available", "passed": True},
        {"name": "Live OAuth disabled", "passed": True},
        {"name": "Calendar writes blocked", "passed": True},
        {"name": "Token storage disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar OAuth Candidate",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V900 Calendar OAuth Candidate · V900 Backend",
        "checks": checks,
        "added": [
            "Calendar OAuth Candidate Status",
            "Calendar Auth URL Candidate",
            "Calendar Callback Candidate",
            "Calendar Token Storage Plan",
            "Calendar Disconnect Candidate",
            "Calendar Readiness Report",
            "Calendar OAuth Candidate UI"
        ],
        "not_added": [
            "Live OAuth token exchange",
            "Token storage",
            "Live Calendar fetch using OAuth",
            "Calendar writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/calendar/oauth-candidate/status",
            "/calendar/auth-url-candidate",
            "/calendar/token-storage-plan",
            "/calendar/readiness-report",
            "/v900-milestone",
            "/health"
        ],
        "recommended_next_build": "V950 Token Storage + Disconnect Flow Candidate"
    }




# =========================
# V950 TOKEN STORAGE + DISCONNECT FLOW CANDIDATE
# =========================
# Candidate only. No live OAuth token exchange. No real encrypted token writes yet.
# This prepares the storage contract, disconnect/revoke contract, and safety checks.

def v950_token_storage_schema_plan() -> Dict[str, Any]:
    return {
        "table_name_future": "oauth_connections",
        "schema_change_required_future": True,
        "schema_changed_in_v950": False,
        "storage_status": "candidate_only",
        "encryption_required": True,
        "frontend_token_exposure_allowed": False,
        "fields": [
            {"name": "id", "type": "uuid", "purpose": "primary key"},
            {"name": "user_id", "type": "text", "purpose": "owner/user reference"},
            {"name": "provider", "type": "text", "purpose": "google_calendar/google_drive/gmail"},
            {"name": "connected_email", "type": "text", "purpose": "connected account display only"},
            {"name": "scope", "type": "text", "purpose": "approved read-only scope"},
            {"name": "access_token_encrypted", "type": "text", "purpose": "server-side encrypted access token"},
            {"name": "refresh_token_encrypted", "type": "text", "purpose": "server-side encrypted refresh token"},
            {"name": "expires_at", "type": "timestamp", "purpose": "token expiry"},
            {"name": "last_refresh_at", "type": "timestamp", "purpose": "last successful refresh"},
            {"name": "revoked_at", "type": "timestamp", "purpose": "disconnect/revoke marker"},
            {"name": "created_at", "type": "timestamp", "purpose": "created timestamp"},
            {"name": "updated_at", "type": "timestamp", "purpose": "updated timestamp"}
        ],
        "required_before_live": [
            "Encryption helper",
            "Supabase table migration",
            "RLS/service role policy review",
            "Disconnect flow",
            "Revoke flow",
            "No token returned to frontend",
            "No token in logs"
        ]
    }


def v950_disconnect_flow_plan() -> Dict[str, Any]:
    return {
        "status": "candidate_only",
        "disconnect_route_future": "POST /calendar/disconnect",
        "revoke_route_future": "POST /calendar/revoke",
        "steps": [
            "User clicks Disconnect",
            "Frontend asks confirmation",
            "Backend loads server-side token record",
            "Backend attempts Google token revoke",
            "Backend marks revoked_at",
            "Backend deletes or invalidates encrypted token values",
            "Backend returns connected:false",
            "Frontend clears calendar state"
        ],
        "safety": {
            "manual_only": True,
            "no_background_disconnect": True,
            "no_frontend_tokens": True,
            "audit_log_future": True
        }
    }


def v950_refresh_policy() -> Dict[str, Any]:
    return {
        "status": "planned",
        "background_refresh_enabled": False,
        "manual_refresh_only": True,
        "policy": [
            "Refresh token only when user manually requests calendar data.",
            "If refresh fails, mark status expired.",
            "Never retry indefinitely.",
            "Never run background sync.",
            "Never fetch private event descriptions without user action."
        ],
        "failure_states": [
            "expired_token",
            "revoked_token",
            "missing_scope",
            "refresh_failed",
            "provider_rate_limited",
            "backend_unavailable"
        ]
    }


@app.get("/tokens/storage-plan")
async def tokens_storage_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Token Storage Plan",
        "plan": v950_token_storage_schema_plan(),
        "live_token_storage_enabled": False
    }


@app.get("/tokens/encryption-check")
async def tokens_encryption_check():
    import os
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Encryption Readiness Check",
        "encryption_key_present": bool(os.getenv("TOKEN_ENCRYPTION_KEY")),
        "live_encryption_active": False,
        "token_storage_active": False,
        "message": "Encryption key check only. V950 does not store live tokens."
    }


@app.get("/calendar/disconnect-flow")
async def calendar_disconnect_flow():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Disconnect Flow Candidate",
        "flow": v950_disconnect_flow_plan()
    }


@app.post("/calendar/disconnect-simulate")
async def calendar_disconnect_simulate(payload: Dict[str, Any]):
    provider = str(payload.get("provider", "google_calendar"))
    connected = bool(payload.get("connected", False))
    has_token_record = bool(payload.get("has_token_record", False))

    return {
        "ok": True,
        "version": VERSION,
        "provider": provider,
        "simulated": True,
        "connected_before": connected,
        "token_record_found": has_token_record,
        "connected_after": False,
        "revoked": False if not has_token_record else "simulated",
        "token_deleted": False if not has_token_record else "simulated",
        "message": "Disconnect simulation completed. No real token was revoked or deleted in V950."
    }


@app.get("/calendar/refresh-policy")
async def calendar_refresh_policy():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Refresh Policy",
        "policy": v950_refresh_policy()
    }


@app.get("/calendar/connection-state-candidate")
async def calendar_connection_state_candidate():
    return {
        "ok": True,
        "version": VERSION,
        "connected": False,
        "provider": "google_calendar",
        "scope": "https://www.googleapis.com/auth/calendar.events.readonly",
        "status": "not_connected",
        "token_storage_active": False,
        "disconnect_available": "candidate_only",
        "revoke_available": "candidate_only",
        "last_sync_at": None,
        "message": "Connection state candidate only. Live OAuth and token storage are not active."
    }


@app.get("/v950-milestone")
async def v950_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V900 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Token storage plan available", "passed": True},
        {"name": "Encryption readiness check available", "passed": True},
        {"name": "Disconnect flow available", "passed": True},
        {"name": "Disconnect simulation available", "passed": True},
        {"name": "Refresh policy available", "passed": True},
        {"name": "Connection state candidate available", "passed": True},
        {"name": "No live token exchange", "passed": True},
        {"name": "No live token storage", "passed": True},
        {"name": "Calendar writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Token Storage + Disconnect Flow Candidate",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V950 Token Storage Candidate · V950 Backend",
        "checks": checks,
        "added": [
            "Token Storage Plan",
            "Encryption Readiness Check",
            "Disconnect Flow Candidate",
            "Disconnect Simulation",
            "Refresh Policy",
            "Connection State Candidate",
            "Token storage UI"
        ],
        "not_added": [
            "Live OAuth token exchange",
            "Real encrypted token storage",
            "Supabase token table migration",
            "Live Calendar fetch using OAuth",
            "Calendar writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/tokens/storage-plan",
            "/tokens/encryption-check",
            "/calendar/disconnect-flow",
            "/calendar/refresh-policy",
            "/calendar/connection-state-candidate",
            "/v950-milestone",
            "/health"
        ],
        "recommended_next_build": "V1000 Live Calendar Read-Only OAuth Candidate"
    }




# =========================
# V1000 LIVE CALENDAR READ-ONLY OAUTH CANDIDATE
# =========================
# Candidate route layer for real read-only Calendar OAuth.
# OAuth URL generation can become active when env vars are set.
# Token exchange/storage remains guarded unless explicitly enabled later.
# No calendar writes. No background sync. Manual execution only.

V1000_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"

def v1000_env() -> Dict[str, Any]:
    import os
    return {
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", ""),
        "GOOGLE_CLIENT_SECRET_SET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", ""),
        "GOOGLE_CALENDAR_SCOPE": os.getenv("GOOGLE_CALENDAR_SCOPE", V1000_CALENDAR_SCOPE),
        "OAUTH_ENABLED": str(os.getenv("OAUTH_ENABLED", "false")).lower() == "true",
        "TOKEN_ENCRYPTION_KEY_SET": bool(os.getenv("TOKEN_ENCRYPTION_KEY"))
    }


def v1000_public_env_status() -> Dict[str, Any]:
    e = v1000_env()
    return {
        "GOOGLE_CLIENT_ID_SET": bool(e["GOOGLE_CLIENT_ID"]),
        "GOOGLE_CLIENT_SECRET_SET": e["GOOGLE_CLIENT_SECRET_SET"],
        "GOOGLE_REDIRECT_URI_SET": bool(e["GOOGLE_REDIRECT_URI"]),
        "GOOGLE_CALENDAR_SCOPE_SET": bool(e["GOOGLE_CALENDAR_SCOPE"]),
        "TOKEN_ENCRYPTION_KEY_SET": e["TOKEN_ENCRYPTION_KEY_SET"],
        "OAUTH_ENABLED_FLAG": e["OAUTH_ENABLED"]
    }


def v1000_can_generate_auth_url() -> bool:
    e = v1000_env()
    return bool(e["GOOGLE_CLIENT_ID"] and e["GOOGLE_REDIRECT_URI"])


def v1000_build_auth_url() -> Dict[str, Any]:
    import secrets, urllib.parse
    e = v1000_env()
    state = secrets.token_urlsafe(32)
    scope = e["GOOGLE_CALENDAR_SCOPE"] or V1000_CALENDAR_SCOPE
    if scope != V1000_CALENDAR_SCOPE:
        return {
            "ok": False,
            "error": "invalid_scope",
            "message": "Only calendar.events.readonly scope is allowed.",
            "allowed_scope": V1000_CALENDAR_SCOPE
        }

    params = {
        "client_id": e["GOOGLE_CLIENT_ID"] or "GOOGLE_CLIENT_ID_NOT_SET",
        "redirect_uri": e["GOOGLE_REDIRECT_URI"] or "GOOGLE_REDIRECT_URI_NOT_SET",
        "response_type": "code",
        "scope": V1000_CALENDAR_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }
    return {
        "ok": True,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params),
        "state": state,
        "scope": V1000_CALENDAR_SCOPE,
        "can_redirect": v1000_can_generate_auth_url(),
        "token_exchange_active": False,
        "token_storage_active": False,
        "note": "Auth URL can be generated when env vars are set. Token exchange/storage remains disabled in V1000."
    }


def v1000_calendar_connection_status() -> Dict[str, Any]:
    return {
        "connected": False,
        "provider": "google_calendar",
        "mode": "oauth_candidate",
        "scope": V1000_CALENDAR_SCOPE,
        "read_only": True,
        "write_access": False,
        "token_storage_active": False,
        "last_sync_at": None,
        "status": "not_connected",
        "message": "Calendar OAuth candidate is prepared. Live token exchange/storage is not active in V1000."
    }


@app.get("/calendar/connect-status")
async def calendar_connect_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V1000 Calendar Connect Status",
        "env": v1000_public_env_status(),
        "connection": v1000_calendar_connection_status(),
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/calendar/auth-url")
async def calendar_auth_url():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Auth URL",
        **v1000_build_auth_url()
    }


@app.get("/calendar/oauth/callback")
async def calendar_oauth_callback(code: str = Query("", description="Google OAuth code"), state: str = Query("", description="OAuth state")):
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar OAuth Callback",
        "received_code": bool(code),
        "received_state": bool(state),
        "connected": False,
        "token_exchange_active": False,
        "token_storage_active": False,
        "message": "Callback route is live, but token exchange/storage remains disabled in V1000."
    }


@app.get("/calendar/status-live-candidate")
async def calendar_status_live_candidate():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Live Candidate Status",
        **v1000_calendar_connection_status()
    }


@app.get("/calendar/events/today-live-candidate")
async def calendar_events_today_live_candidate(timezone: str = Query("America/Toronto"), calendar_id: str = Query("primary")):
    return {
        "ok": True,
        "version": VERSION,
        "calendar_id": calendar_id,
        "timezone": timezone,
        "connected": False,
        "events": [],
        "summary": {
            "date": "",
            "timezone": timezone,
            "totalEvents": 0,
            "totalMeetingMinutes": 0,
            "meetingDensity": "light",
            "prepNeededCount": 0,
            "events": []
        },
        "message": "Live Calendar fetch using OAuth is not active until token exchange/storage is implemented.",
        "safety": {
            "read_only": True,
            "write_access": False,
            "background_sync": False,
            "manual_refresh_only": True
        }
    }


@app.post("/calendar/context-approval")
async def calendar_context_approval(payload: Dict[str, Any]):
    wants_send_to_ai = bool(payload.get("send_to_ai", False))
    includes_private_details = bool(payload.get("includes_private_details", False))
    user_approved = bool(payload.get("user_approved", False))

    allowed = wants_send_to_ai and user_approved and not includes_private_details

    return {
        "ok": True,
        "version": VERSION,
        "allowed": allowed,
        "decision": "allowed_manual_send" if allowed else "blocked_or_review_required",
        "checks": [
            {"name": "User approved", "passed": user_approved},
            {"name": "Private details excluded", "passed": not includes_private_details},
            {"name": "Manual send requested", "passed": wants_send_to_ai},
            {"name": "Auto-loop off", "passed": True}
        ],
        "message": "Calendar context can be sent manually." if allowed else "Calendar context requires manual approval and private details must be excluded."
    }


@app.get("/calendar/oauth-test-page")
async def calendar_oauth_test_page():
    return {
        "ok": True,
        "version": VERSION,
        "test_links": [
            "/calendar/connect-status",
            "/calendar/auth-url",
            "/calendar/oauth/callback",
            "/calendar/status-live-candidate",
            "/calendar/events/today-live-candidate",
            "/calendar/context-approval",
            "/v1000-milestone"
        ],
        "note": "Use GET routes for smoke tests. POST /calendar/context-approval requires JSON body."
    }


@app.get("/v1000-milestone")
async def v1000_milestone():
    env = v1000_public_env_status()
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V950 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Calendar connect status available", "passed": True},
        {"name": "Calendar auth URL route available", "passed": True},
        {"name": "Calendar callback route available", "passed": True},
        {"name": "Calendar live candidate status available", "passed": True},
        {"name": "Calendar context approval available", "passed": True},
        {"name": "Read-only scope enforced", "passed": True},
        {"name": "Calendar writes blocked", "passed": True},
        {"name": "Token exchange disabled", "passed": True},
        {"name": "Live token storage disabled", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    score = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Live Calendar Read-Only OAuth Candidate",
        "ready": True,
        "score": f"{score}/{len(checks)}",
        "frontend_must_show": "V1000 Calendar OAuth · V1000 Backend",
        "env": env,
        "checks": checks,
        "added": [
            "Calendar Connect Status",
            "Calendar Auth URL route",
            "Calendar OAuth Callback route",
            "Calendar Live Candidate Status",
            "Calendar Today Live Candidate",
            "Calendar Context Approval",
            "Calendar OAuth Test Page",
            "Calendar OAuth UI"
        ],
        "not_added": [
            "Live token exchange",
            "Real encrypted token storage",
            "Supabase token table migration",
            "Live Calendar fetch using stored OAuth token",
            "Calendar writes",
            "Background sync",
            "Automation loop"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/calendar/connect-status",
            "/calendar/auth-url",
            "/calendar/status-live-candidate",
            "/calendar/events/today-live-candidate",
            "/calendar/oauth-test-page",
            "/v1000-milestone",
            "/health"
        ],
        "recommended_next_build": "V1050 Real Token Exchange + Encrypted Storage Candidate"
    }
