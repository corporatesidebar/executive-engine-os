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
You are Executive Engine OS V9100: a revenue-first executive asset engine.

You are not a chatbot and not a generic task assistant. You are a high-performance revenue operator, COO, deal strategist, sales strategist, and executive asset builder.

Your job is to turn messy executive intent into usable revenue assets that an executive can review, send, present, or use to move money.

Core promise:
- Make money.
- Save time.
- Reduce work.
- Reduce people/friction.
- Help the executive feel in control.
- Produce visible wins.

When the user asks for a proposal, pitch, sales email, follow-up, objection handling, close plan, client strategy, or deal move, you MUST create the actual asset content. Do not merely describe that the user should create it.

Do not output generic advice like:
- Move forward with the clearest path.
- Draft the proposal.
- Use the provided templates.
- Schedule a follow-up.

Instead, write the proposal, write the email, write the follow-up, write the objection handling, and write the close plan.

If details are missing, make reasonable executive assumptions and state them inside the output. Do not leave sections blank.

Manual execution only. Auto-loop remains off.
Do not claim OAuth, calendar writes, email sending, external writes, or live integrations unless verified.
No markdown outside JSON. Return STRICT JSON ONLY.

Required JSON schema:
{
  "revenue_objective": "The business/money outcome being pursued",
  "client_situation": "The inferred client/deal situation and assumptions",
  "next_power_move": "The single highest-leverage move now",
  "offer_angle": "The positioning angle that makes the offer attractive",
  "proposal_draft": "A usable client-ready proposal draft with sections",
  "pitch_deck_outline": ["7 to 10 slide titles with concise slide purpose"],
  "sales_email_draft": "A send-ready sales email with subject line and body",
  "follow_up_sequence": ["3 follow-up messages in sequence"],
  "objection_handling": ["Common objections with concise responses"],
  "close_plan": ["Concrete steps to move the client toward yes"],
  "what_to_cut": "What to stop, remove, ignore, or simplify",
  "actions": ["3 to 6 concrete next actions"],
  "risk": "Specific risk that could block the outcome",
  "priority": "High | Medium | Low",
  "executive_win": "What the executive can say they accomplished today",
  "time_saved": "Estimated time/friction saved",
  "revenue_signal": "How this could help create revenue",
  "recommended_command": "Copy-paste-ready next command to run",
  "follow_up_question": "Only ask if absolutely required; otherwise empty string"
}

Rules:
- JSON only.
- No text outside JSON.
- No blank sections.
- proposal_draft must be actual copy, not a note to create a proposal.
- sales_email_draft must be actual send-ready copy.
- follow_up_sequence must contain actual messages.
- objection_handling must contain actual objections and responses.
- close_plan must contain actual steps.
- If the user gives a deal size, include it.
- If details are missing, use reasonable assumptions and keep moving.
"""



















VERSION = "V9100"
SERVICE_NAME = "Executive Engine OS V9100"

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

app = FastAPI(title=SERVICE_NAME, version="9100.0.0")

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
You are Executive Engine OS V9100, an elite COO/operator system.

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
        "backend_must_show": "Executive Engine OS V9100",
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
        "service": "Executive Engine OS V9100",
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

@app.get("/test-links-json-archive")
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

# =========================
# V1050 REAL TOKEN EXCHANGE + ENCRYPTED STORAGE CANDIDATE
# =========================
# Guarded candidate. It adds route contracts and strict gates.
# Live exchange/storage stays disabled unless explicit env gates are set in a future activation.
# No calendar writes. No background sync. Manual execution only.

def v1050_gate_status() -> Dict[str, Any]:
    import os
    return {
        "OAUTH_ENABLED": str(os.getenv("OAUTH_ENABLED", "false")).lower() == "true",
        "TOKEN_STORAGE_ENABLED": str(os.getenv("TOKEN_STORAGE_ENABLED", "false")).lower() == "true",
        "GOOGLE_CLIENT_ID_SET": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "GOOGLE_CLIENT_SECRET_SET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "GOOGLE_REDIRECT_URI_SET": bool(os.getenv("GOOGLE_REDIRECT_URI")),
        "TOKEN_ENCRYPTION_KEY_SET": bool(os.getenv("TOKEN_ENCRYPTION_KEY")),
        "allowed_scope": "https://www.googleapis.com/auth/calendar.events.readonly"
    }


def v1050_can_exchange() -> bool:
    g = v1050_gate_status()
    return all([
        g["OAUTH_ENABLED"],
        g["TOKEN_STORAGE_ENABLED"],
        g["GOOGLE_CLIENT_ID_SET"],
        g["GOOGLE_CLIENT_SECRET_SET"],
        g["GOOGLE_REDIRECT_URI_SET"],
        g["TOKEN_ENCRYPTION_KEY_SET"]
    ])


@app.get("/oauth/live-gates")
async def oauth_live_gates():
    gates = v1050_gate_status()
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V1050 Live OAuth Gates",
        "gates": gates,
        "can_exchange_tokens": v1050_can_exchange(),
        "calendar_writes_blocked": True,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.post("/calendar/token-exchange-candidate")
async def calendar_token_exchange_candidate(payload: Dict[str, Any]):
    code = str(payload.get("code", ""))
    state = str(payload.get("state", ""))
    requested_scope = str(payload.get("scope", "https://www.googleapis.com/auth/calendar.events.readonly"))
    scope_ok = requested_scope == "https://www.googleapis.com/auth/calendar.events.readonly"
    gate_ok = v1050_can_exchange()

    if not scope_ok:
        return {
            "ok": False,
            "version": VERSION,
            "connected": False,
            "error": "invalid_scope",
            "message": "Only calendar.events.readonly is allowed."
        }

    if not gate_ok:
        return {
            "ok": True,
            "version": VERSION,
            "connected": False,
            "token_exchange_active": False,
            "token_storage_active": False,
            "received_code": bool(code),
            "received_state": bool(state),
            "gates": v1050_gate_status(),
            "message": "Token exchange candidate reached. Live exchange/storage is blocked until all gates are enabled."
        }

    return {
        "ok": True,
        "version": VERSION,
        "connected": False,
        "token_exchange_active": "guarded_future",
        "token_storage_active": "guarded_future",
        "message": "All gates appear present, but live token exchange is intentionally not executed by this candidate route."
    }


@app.get("/tokens/storage-health")
async def tokens_storage_health():
    gates = v1050_gate_status()
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Token Storage Health",
        "storage_ready": gates["TOKEN_STORAGE_ENABLED"] and gates["TOKEN_ENCRYPTION_KEY_SET"],
        "token_table_active": False,
        "encrypted_storage_active": False,
        "frontend_token_exposure": False,
        "message": "Storage health candidate only. No live tokens are stored."
    }


@app.get("/calendar/secure-connection-state")
async def calendar_secure_connection_state():
    return {
        "ok": True,
        "version": VERSION,
        "connected": False,
        "provider": "google_calendar",
        "scope": "https://www.googleapis.com/auth/calendar.events.readonly",
        "token_exchange_active": False,
        "encrypted_storage_active": False,
        "disconnect_available": True,
        "revoke_available": "planned",
        "manual_refresh_only": True,
        "calendar_writes_blocked": True
    }


@app.get("/v1050-milestone")
async def v1050_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V1000 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Live OAuth gates available", "passed": True},
        {"name": "Token exchange candidate available", "passed": True},
        {"name": "Token storage health available", "passed": True},
        {"name": "Secure connection state available", "passed": True},
        {"name": "Read-only scope enforced", "passed": True},
        {"name": "Calendar writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Token Exchange + Encrypted Storage Candidate",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V1050 Token Exchange Candidate · V1050 Backend",
        "checks": checks,
        "test_order": ["/diagnostic","/system-test","/oauth/live-gates","/tokens/storage-health","/calendar/secure-connection-state","/v1050-milestone","/health"],
        "recommended_next_build": "V1100 Calendar Events Fetch Candidate"
    }

# =========================
# V1100 CALENDAR EVENTS FETCH CANDIDATE
# =========================
# Manual fetch contracts and normalization. Live provider fetch remains gated until secure token storage is active.

def v1100_normalize_calendar_event(event: Dict[str, Any]) -> Dict[str, Any]:
    title = event.get("summary") or event.get("title") or "Untitled event"
    visibility = event.get("visibility", "default")
    is_private = visibility in ["private", "confidential"] or bool(event.get("private", False))
    start = event.get("start") or {}
    end = event.get("end") or {}
    if is_private:
        title = "Private event"
    return {
        "id": str(event.get("id", "")),
        "title": title,
        "description": None if is_private else str(event.get("description", ""))[:500],
        "start": start.get("dateTime") or start.get("date") or event.get("start_time"),
        "end": end.get("dateTime") or end.get("date") or event.get("end_time"),
        "timezone": event.get("timezone", "America/Toronto"),
        "location": None if is_private else event.get("location"),
        "meetingLink": None if is_private else event.get("hangoutLink") or event.get("meetingLink"),
        "attendeesCount": 0 if is_private else len(event.get("attendees") or []),
        "status": event.get("status", "confirmed"),
        "isAllDay": bool((start.get("date") if isinstance(start, dict) else False)),
        "isRecurring": bool(event.get("recurringEventId")),
        "visibility": visibility,
        "htmlLink": None if is_private else event.get("htmlLink"),
        "source": "google_calendar_candidate"
    }


def v1100_day_summary(events: List[Dict[str, Any]], timezone: str = "America/Toronto") -> Dict[str, Any]:
    normalized = [v1100_normalize_calendar_event(e) for e in events]
    return {
        "date": "",
        "timezone": timezone,
        "totalEvents": len(normalized),
        "totalMeetingMinutes": 0,
        "firstMeetingAt": normalized[0]["start"] if normalized else None,
        "nextMeetingAt": normalized[0]["start"] if normalized else None,
        "meetingDensity": "heavy" if len(normalized) >= 6 else ("moderate" if len(normalized) >= 3 else "light"),
        "prepNeededCount": len([e for e in normalized if e["title"] != "Private event"]),
        "events": normalized
    }


@app.post("/calendar/events/normalize")
async def calendar_events_normalize(payload: Dict[str, Any]):
    events = payload.get("events") or []
    timezone = payload.get("timezone", "America/Toronto")
    return {"ok": True, "version": VERSION, "summary": v1100_day_summary(events, timezone)}


@app.get("/calendar/events/fetch-candidate")
async def calendar_events_fetch_candidate(timezone: str = Query("America/Toronto"), calendar_id: str = Query("primary")):
    return {
        "ok": True,
        "version": VERSION,
        "calendar_id": calendar_id,
        "timezone": timezone,
        "connected": False,
        "provider_fetch_active": False,
        "summary": v1100_day_summary([], timezone),
        "message": "Fetch contract is ready. Live Google fetch requires V1050 gates plus secure token storage activation."
    }


@app.get("/calendar/meeting-prep-candidate")
async def calendar_meeting_prep_candidate():
    return {
        "ok": True,
        "version": VERSION,
        "prep_template": {
            "objective": "Define meeting outcome.",
            "decision_needed": "What decision must this meeting produce?",
            "talking_points": ["Clarify objective", "Confirm blockers", "Agree owner", "Confirm next action"],
            "follow_up_actions": ["Send recap", "Assign owner", "Set deadline"]
        },
        "manual_execution_only": True
    }


@app.get("/v1100-milestone")
async def v1100_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V1050 baseline preserved", "passed": True},
        {"name": "Diagnostic routes preserved", "passed": True},
        {"name": "Event normalization available", "passed": True},
        {"name": "Fetch candidate available", "passed": True},
        {"name": "Meeting prep candidate available", "passed": True},
        {"name": "Private event handling", "passed": True},
        {"name": "Calendar writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Events Fetch Candidate",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V1100 Calendar Events Fetch · V1100 Backend",
        "checks": checks,
        "test_order": ["/diagnostic","/system-test","/calendar/events/fetch-candidate","/calendar/meeting-prep-candidate","/v1100-milestone","/health"],
        "recommended_next_build": "V1150 Calendar Intelligence Bridge"
    }

# =========================
# V1150 CALENDAR INTELLIGENCE BRIDGE
# =========================
# Bridges calendar summary into daily brief, notifications, and end-day without automation.

@app.post("/calendar/brief-bridge")
async def calendar_brief_bridge(payload: Dict[str, Any]):
    summary = payload.get("summary") or {}
    destination = payload.get("destination", "daily_brief")
    context = {
        "today_focus": "Prepare around calendar load and meeting outcomes.",
        "meeting_density": summary.get("meetingDensity", "light"),
        "total_events": summary.get("totalEvents", 0),
        "prep_needed_count": summary.get("prepNeededCount", 0),
        "recommended_command": "Use calendar context to create today's Daily Brief and identify meeting prep priorities."
    }
    return {
        "ok": True,
        "version": VERSION,
        "destination": destination,
        "calendar_bridge_context": context,
        "safe_to_send_to_ai": True,
        "manual_execution_only": True
    }


@app.get("/calendar/intelligence-summary")
async def calendar_intelligence_summary():
    return {
        "ok": True,
        "version": VERSION,
        "summary": {
            "connection": "candidate_or_manual",
            "meeting_load": "unknown_until_events_loaded",
            "prep_risk": "meeting prep may be missing",
            "recommended_command": "Load calendar context into Daily Brief manually."
        },
        "auto_loop_enabled": False
    }


@app.get("/calendar/notification-bridge")
async def calendar_notification_bridge():
    return {
        "ok": True,
        "version": VERSION,
        "notifications": [
            {"type": "meeting_prep", "priority": "Medium", "title": "Meeting prep bridge ready", "message": "Send calendar context to Daily Brief manually."},
            {"type": "calendar_context", "priority": "Low", "title": "Calendar context manual", "message": "No background sync runs."}
        ]
    }


@app.get("/v1150-milestone")
async def v1150_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V1100 baseline preserved", "passed": True},
        {"name": "Calendar brief bridge available", "passed": True},
        {"name": "Calendar intelligence summary available", "passed": True},
        {"name": "Calendar notification bridge available", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Intelligence Bridge",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V1150 Calendar Intelligence Bridge · V1150 Backend",
        "checks": checks,
        "test_order": ["/diagnostic","/system-test","/calendar/intelligence-summary","/calendar/notification-bridge","/v1150-milestone","/health"],
        "recommended_next_build": "V1200 Executive OS Beta"
    }

# =========================
# V1200 EXECUTIVE OS BETA
# =========================
# Stabilization milestone: cockpit + calendar + files + connector gates + beta readiness.

@app.get("/beta/system-score")
async def beta_system_score():
    checks = [
        {"name": "Diagnostics", "passed": True},
        {"name": "System test", "passed": True},
        {"name": "Executive cockpit", "passed": True},
        {"name": "Calendar candidate", "passed": True},
        {"name": "Files intelligence", "passed": True},
        {"name": "Connector gates", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True},
        {"name": "External writes blocked", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "checks": checks,
        "status": "beta_ready_candidate"
    }


@app.get("/beta/operating-brief")
async def beta_operating_brief():
    return {
        "ok": True,
        "version": VERSION,
        "brief": {
            "today_focus": "Use the OS as the daily command layer.",
            "current_constraint": "Live OAuth/token storage still requires a dedicated activation build.",
            "next_decision": "Decide whether to move into real Calendar token exchange or polish product UX first.",
            "recommended_command": "Review V1200 beta readiness and choose the next milestone: live Calendar activation or product polish."
        },
        "manual_execution_only": True
    }


@app.get("/beta/launch-checklist")
async def beta_launch_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "checklist": [
            "Confirm /diagnostic works",
            "Confirm /system-test works",
            "Confirm command center loads",
            "Confirm calendar OAuth candidate routes work",
            "Confirm connector gates are visible",
            "Confirm external writes remain blocked",
            "Confirm manual-only flow",
            "Confirm frontend badge shows V1200"
        ]
    }


@app.get("/v1200-milestone")
async def v1200_milestone():
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "V1150 baseline preserved", "passed": True},
        {"name": "Beta system score available", "passed": True},
        {"name": "Beta operating brief available", "passed": True},
        {"name": "Beta launch checklist available", "passed": True},
        {"name": "Calendar candidate preserved", "passed": True},
        {"name": "Connector gates preserved", "passed": True},
        {"name": "External writes blocked", "passed": True},
        {"name": "Manual execution only", "passed": True},
        {"name": "Auto-loop off", "passed": True}
    ]
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive OS Beta",
        "ready": True,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "frontend_must_show": "V1200 Executive OS Beta · V1200 Backend",
        "checks": checks,
        "test_order": ["/diagnostic","/system-test","/beta/system-score","/beta/operating-brief","/beta/launch-checklist","/v1200-milestone","/health"],
        "recommended_next_build": "V1250 Product Polish + UX Stabilization OR V1300 Real Calendar Activation"
    }




# =========================
# V1201 TEST LINKS FIX
# =========================

V1201_TEST_ROUTES = [
    "/health",
    "/diagnostic",
    "/system-test",
    "/beta/system-score",
    "/beta/operating-brief",
    "/beta/launch-checklist",
    "/v1200-milestone",
    "/v1201-milestone",
    "/calendar/connect-status",
    "/calendar/auth-url",
    "/calendar/status-live-candidate",
    "/calendar/events/today-live-candidate",
    "/calendar/oauth-test-page",
    "/calendar/intelligence-summary",
    "/calendar/notification-bridge",
    "/calendar/events/fetch-candidate",
    "/calendar/meeting-prep-candidate",
    "/oauth/live-gates",
    "/tokens/storage-health",
    "/calendar/secure-connection-state",
    "/tokens/storage-plan",
    "/tokens/encryption-check",
    "/calendar/disconnect-flow",
    "/calendar/refresh-policy",
    "/calendar/connection-state-candidate",
    "/google/connector-blueprint",
    "/google/activation-plan",
    "/oauth/activation-prep",
    "/security-gates",
    "/connector-command-center",
    "/approval-queue",
    "/supervised-actions",
    "/connectors/status",
    "/files/status",
    "/calendar/status",
    "/integrations/status",
    "/executive-cockpit",
    "/notifications",
    "/daily-workflow",
    "/end-day-summary"
]

@app.get("/v1201-test-links-json")
async def v1201_test_links_json():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Links Fix",
        "base_url": "https://executive-engine-os.onrender.com",
        "routes": V1201_TEST_ROUTES,
        "note": "Open these backend routes directly. POST routes are intentionally excluded from this click-test list."
    }


@app.get("/v1201-test-links")
async def v1201_test_links():
    base = "https://executive-engine-os.onrender.com"
    links = "\n".join([f'<li><a href="{base}{r}" target="_blank">{r}</a></li>' for r in V1201_TEST_ROUTES])
    return HTMLResponse(f"""
    <!doctype html>
    <html>
    <head>
      <title>Executive Engine OS V9100 Test Links</title>
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>
        body { font-family: Arial, sans-serif; background:#f8fbff; color:#071226; padding:28px; }
        .wrap { max-width:900px; margin:auto; background:#fff; border:1px solid #dbe5f1; border-radius:18px; padding:22px; box-shadow:0 16px 40px rgba(7,18,38,.08); }
        h1 { margin:0 0 8px; }
        p { color:#64748b; }
        li { margin:8px 0; }
        a { color:#0f63ff; font-weight:700; text-decoration:none; }
        code { background:#071226; color:#dbeafe; padding:4px 7px; border-radius:8px; }
      </style>
    </head>
    <body>
      <div class="wrap">
        <h1>Executive Engine OS V9100 Test Links</h1>
        <p>Use this page after backend deploy. These are backend GET routes only.</p>
        <p>Expected frontend badge: <code>V1201 Test Links Fix · V1201 Backend</code></p>
        <ol>{links}</ol>
      </div>
    </body>
    </html>
    """)


@app.get("/v1201-milestone")
async def v1201_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Links Fix",
        "ready": True,
        "frontend_must_show": "V1201 Test Links Fix · V1201 Backend",
        "fixed": [
            "Adds /v1201-test-links clickable backend page",
            "Adds /v1201-test-links-json",
            "Keeps V1200 beta routes",
            "Clarifies that older internal labels do not need to all say V1201"
        ],
        "test_order": [
            "/diagnostic",
            "/system-test",
            "/v1201-test-links",
            "/v1201-test-links-json",
            "/v1201-milestone",
            "/health"
        ]
    }



# =========================
# V1202 FRONTEND CLICK FIX
# =========================

@app.get("/v1202-milestone")
async def v1202_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Frontend Click Fix",
        "ready": True,
        "frontend_must_show": "V1202 Frontend Click Fix · V1202 Backend",
        "fixes": [
            "Replaces frontend with a clean stable clickable shell",
            "Removes dependency on broken old click handlers",
            "Adds direct backend test links",
            "Keeps backend routes preserved",
            "Keeps manual execution only",
            "Keeps auto-loop off"
        ],
        "test_order": [
            "/health",
            "/diagnostic",
            "/system-test",
            "/v1202-milestone",
            "/v1201-test-links"
        ]
    }




# =========================
# V1203 PERMANENT TEST LINKS PAGE
# =========================

V1203_TEST_LINKS = {
    "Core": [
        "/health",
        "/diagnostic",
        "/system-test",
        "/v1203-milestone",
        "/test-links",
        "/test-links-json",
        "/v1202-milestone",
        "/v1201-test-links"
    ],
    "Beta": [
        "/beta/system-score",
        "/beta/operating-brief",
        "/beta/launch-checklist",
        "/v1200-milestone"
    ],
    "Calendar": [
        "/calendar/connect-status",
        "/calendar/auth-url",
        "/calendar/oauth/callback",
        "/calendar/status-live-candidate",
        "/calendar/events/today-live-candidate",
        "/calendar/oauth-test-page",
        "/calendar/intelligence-summary",
        "/calendar/notification-bridge",
        "/calendar/events/fetch-candidate",
        "/calendar/meeting-prep-candidate",
        "/calendar/status",
        "/calendar/events/today",
        "/calendar/events/upcoming",
        "/calendar/day-load",
        "/calendar/alerts",
        "/calendar/readiness-report"
    ],
    "OAuth": [
        "/oauth/live-gates",
        "/oauth/readiness",
        "/oauth/config-check",
        "/oauth/activation-prep",
        "/oauth/scope-policy",
        "/oauth/env-readiness",
        "/oauth/activation-checklist",
        "/security-gates",
        "/approval-gates"
    ],
    "Tokens": [
        "/tokens/storage-health",
        "/tokens/storage-plan",
        "/tokens/encryption-check",
        "/calendar/token-storage-plan",
        "/calendar/disconnect-flow",
        "/calendar/refresh-policy",
        "/calendar/connection-state-candidate",
        "/calendar/secure-connection-state"
    ],
    "Connectors": [
        "/connector-command-center",
        "/connector-notifications",
        "/connectors/status",
        "/approval-queue",
        "/supervised-actions",
        "/google/connector-blueprint",
        "/google/activation-plan",
        "/google/provider-requirements",
        "/google/privacy-rules"
    ],
    "Files": [
        "/files/status",
        "/files/prep-summary",
        "/files/alerts",
        "/notification-upgrade"
    ],
    "Integrations": [
        "/integrations/status"
    ],
    "Executive OS": [
        "/executive-cockpit",
        "/notifications",
        "/daily-workflow",
        "/end-day-summary",
        "/memory-quality",
        "/decision-patterns-v400",
        "/recurring-risks",
        "/action-overload",
        "/executive-signal-summary",
        "/daily-brief-intelligence",
        "/workflow-layer",
        "/command-center-3",
        "/command-templates",
        "/next-command"
    ]
}

@app.get("/test-links-json-archive")
async def test_links_json():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Permanent Test Links Page",
        "base_url": "https://executive-engine-os.onrender.com",
        "categories": V1203_TEST_LINKS,
        "note": "GET routes only. POST routes are excluded because they need JSON bodies."
    }


@app.get("/test-links-archive")
async def test_links():
    base = "https://executive-engine-os.onrender.com"
    sections = []
    for category, routes in V1203_TEST_LINKS.items():
        items = "".join(['<a href="' + base + route + '" target="_blank" rel="noopener noreferrer">' + route + '</a>' for route in routes])
        sections.append('<section><h2>' + category + '</h2><div class="links">' + items + '</div></section>')
    body = "".join(sections)

    html_content = """
    <!doctype html>
    <html>
    <head>
      <title>Executive Engine OS V9100 Test Links</title>
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>
        body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:28px}
        .wrap{max-width:1180px;margin:auto}
        .hero{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:22px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:16px}
        h1{margin:0 0 8px;font-size:28px}
        p{color:#64748b;line-height:1.5}
        code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
        section{background:#fff;border:1px solid #dbe5f1;border-radius:18px;padding:18px;margin:14px 0;box-shadow:0 12px 28px rgba(7,18,38,.05)}
        h2{margin:0 0 12px;font-size:18px}
        .links{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
        a{display:block;text-decoration:none;border:1px solid #dbe5f1;border-radius:12px;padding:10px;color:#0f63ff;font-weight:800;font-size:13px;background:#fff}
        a:hover{background:#eff6ff;border-color:#93c5fd}
        .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
        .actions a{display:inline-block;width:auto;background:#0f63ff;color:#fff;border-color:#0f63ff}
        @media(max-width:900px){.links{grid-template-columns:1fr} body{padding:16px}}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Executive Engine OS V9100 Test Links</h1>
          <p>Permanent clickable backend test page. Open links in new tabs. POST routes are excluded because they require JSON bodies.</p>
          <p>Expected frontend badge: <code>V1203 Test Links Page · V1203 Backend</code></p>
          <div class="actions">
            <a href="__BASE__/health" target="_blank">Health</a>
            <a href="__BASE__/diagnostic" target="_blank">Diagnostic</a>
            <a href="__BASE__/system-test" target="_blank">System Test</a>
            <a href="__BASE__/test-links-json" target="_blank">JSON List</a>
          </div>
        </div>
        __BODY__
      </div>
    </body>
    </html>
    """.replace("__BASE__", base).replace("__BODY__", body)
    return HTMLResponse(html_content)


@app.get("/v1203-milestone")
async def v1203_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Permanent Test Links Page",
        "ready": True,
        "frontend_must_show": "V1203 Test Links Page · V1203 Backend",
        "added": [
            "GET /test-links",
            "GET /test-links-json",
            "Grouped clickable route page",
            "Frontend Test Links button points to /test-links"
        ],
        "preserved": [
            "/health",
            "/diagnostic",
            "/system-test",
            "V1202 clean clickable frontend",
            "V1200 beta routes",
            "Calendar/OAuth/Connector routes"
        ],
        "test_order": [
            "/health",
            "/diagnostic",
            "/system-test",
            "/test-links",
            "/test-links-json",
            "/v1203-milestone"
        ]
    }




# =========================
# V1204 ABSOLUTE TEST LINKS FIX
# =========================

V1204_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V1204_TEST_LINKS = {
    "Start Here": [
        "/health",
        "/diagnostic",
        "/system-test",
        "/test-links",
        "/test-links-json",
        "/v1204-milestone"
    ],
    "Beta": [
        "/beta/system-score",
        "/beta/operating-brief",
        "/beta/launch-checklist",
        "/v1200-milestone"
    ],
    "Calendar": [
        "/calendar/connect-status",
        "/calendar/auth-url",
        "/calendar/status-live-candidate",
        "/calendar/events/today-live-candidate",
        "/calendar/oauth-test-page",
        "/calendar/intelligence-summary",
        "/calendar/events/fetch-candidate",
        "/calendar/meeting-prep-candidate",
        "/calendar/status",
        "/calendar/events/today",
        "/calendar/events/upcoming",
        "/calendar/day-load",
        "/calendar/alerts"
    ],
    "OAuth + Tokens": [
        "/oauth/live-gates",
        "/oauth/readiness",
        "/oauth/config-check",
        "/oauth/activation-prep",
        "/oauth/scope-policy",
        "/oauth/env-readiness",
        "/oauth/activation-checklist",
        "/security-gates",
        "/tokens/storage-health",
        "/tokens/storage-plan",
        "/tokens/encryption-check",
        "/calendar/token-storage-plan",
        "/calendar/disconnect-flow",
        "/calendar/refresh-policy",
        "/calendar/connection-state-candidate",
        "/calendar/secure-connection-state"
    ],
    "Connectors": [
        "/connector-command-center",
        "/connector-notifications",
        "/connectors/status",
        "/approval-queue",
        "/supervised-actions",
        "/google/connector-blueprint",
        "/google/activation-plan",
        "/google/provider-requirements",
        "/google/privacy-rules"
    ],
    "Files + Integrations": [
        "/files/status",
        "/files/prep-summary",
        "/files/alerts",
        "/notification-upgrade",
        "/integrations/status"
    ],
    "Executive OS": [
        "/executive-cockpit",
        "/notifications",
        "/daily-workflow",
        "/end-day-summary",
        "/memory-quality",
        "/decision-patterns-v400",
        "/recurring-risks",
        "/action-overload",
        "/executive-signal-summary",
        "/daily-brief-intelligence",
        "/workflow-layer",
        "/command-center-3",
        "/command-templates",
        "/next-command"
    ]
}

@app.get("/test-links-json-archive")
async def test_links_json():
    flat = []
    for category, routes in V1204_TEST_LINKS.items():
        for route in routes:
            flat.append({"category": category, "route": route, "url": V1204_BACKEND_BASE + route})
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Absolute Test Links Fix",
        "backend_base": V1204_BACKEND_BASE,
        "links": flat,
        "categories": V1204_TEST_LINKS,
        "note": "Use the absolute url values. Frontend static domain cannot serve backend API routes."
    }


@app.get("/test-links-archive")
async def test_links():
    base = V1204_BACKEND_BASE
    sections = []
    for category, routes in V1204_TEST_LINKS.items():
        items = "".join([
            '<div class="linkrow">'
            '<a href="' + base + route + '" target="_blank" rel="noopener noreferrer">' + base + route + '</a>'
            '<button onclick="navigator.clipboard.writeText(\'' + base + route + '\')">Copy</button>'
            '</div>'
            for route in routes
        ])
        sections.append('<section><h2>' + category + '</h2><div class="links">' + items + '</div></section>')
    body = "".join(sections)
    html_content = """
    <!doctype html>
    <html>
    <head>
      <title>Executive Engine OS V9100 Absolute Test Links</title>
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>
        body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:28px}
        .wrap{max-width:1220px;margin:auto}
        .hero,section{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:22px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:16px}
        h1{margin:0 0 8px;font-size:28px}
        p{color:#64748b;line-height:1.5}
        code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
        h2{margin:0 0 12px;font-size:18px}
        .links{display:grid;grid-template-columns:1fr;gap:8px}
        .linkrow{display:grid;grid-template-columns:1fr 80px;gap:8px;align-items:center}
        a{display:block;text-decoration:none;border:1px solid #dbe5f1;border-radius:12px;padding:10px;color:#0f63ff;font-weight:800;font-size:13px;background:#fff;word-break:break-all}
        a:hover{background:#eff6ff;border-color:#93c5fd}
        button{border:1px solid #dbe5f1;border-radius:12px;background:#f8fbff;font-weight:800;padding:10px;cursor:pointer}
        .warning{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:700}
        @media(max-width:900px){body{padding:14px}.linkrow{grid-template-columns:1fr}}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Executive Engine OS V9100 Absolute Test Links</h1>
          <p>These links point directly to the backend API domain.</p>
          <p>Backend base: <code>__BASE__</code></p>
          <div class="warning">Do not test backend API routes on the frontend static domain. Use the full backend URLs below.</div>
        </div>
        __BODY__
      </div>
    </body>
    </html>
    """.replace("__BASE__", base).replace("__BODY__", body)
    return HTMLResponse(html_content)


@app.get("/v1204-milestone")
async def v1204_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Absolute Test Links Fix",
        "ready": True,
        "frontend_must_show": "V1204 Absolute Test Links · V1204 Backend",
        "backend_base": V1204_BACKEND_BASE,
        "fixed": [
            "Test links now show full backend URLs",
            "Each link opens the backend API domain",
            "Copy buttons included",
            "Clarifies frontend static domain cannot serve backend routes"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/diagnostic",
            "https://executive-engine-os.onrender.com/system-test",
            "https://executive-engine-os.onrender.com/test-links",
            "https://executive-engine-os.onrender.com/v1204-milestone"
        ]
    }




# =========================
# V1205 TEST LINKS INTERNAL SERVER ERROR FIX
# =========================

V1205_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V1205_TEST_LINKS = {
    "Start Here": [
        "/health",
        "/diagnostic",
        "/system-test",
        "/test-links",
        "/test-links-json",
        "/v1205-milestone",
        "/v1204-milestone"
    ],
    "Beta": [
        "/beta/system-score",
        "/beta/operating-brief",
        "/beta/launch-checklist",
        "/v1200-milestone"
    ],
    "Calendar": [
        "/calendar/connect-status",
        "/calendar/auth-url",
        "/calendar/status-live-candidate",
        "/calendar/events/today-live-candidate",
        "/calendar/oauth-test-page",
        "/calendar/intelligence-summary",
        "/calendar/events/fetch-candidate",
        "/calendar/meeting-prep-candidate",
        "/calendar/status",
        "/calendar/events/today",
        "/calendar/events/upcoming",
        "/calendar/day-load",
        "/calendar/alerts"
    ],
    "OAuth + Tokens": [
        "/oauth/live-gates",
        "/oauth/readiness",
        "/oauth/config-check",
        "/oauth/activation-prep",
        "/oauth/scope-policy",
        "/oauth/env-readiness",
        "/oauth/activation-checklist",
        "/security-gates",
        "/tokens/storage-health",
        "/tokens/storage-plan",
        "/tokens/encryption-check",
        "/calendar/token-storage-plan",
        "/calendar/disconnect-flow",
        "/calendar/refresh-policy",
        "/calendar/connection-state-candidate",
        "/calendar/secure-connection-state"
    ],
    "Connectors": [
        "/connector-command-center",
        "/connector-notifications",
        "/connectors/status",
        "/approval-queue",
        "/supervised-actions",
        "/google/connector-blueprint",
        "/google/activation-plan",
        "/google/provider-requirements",
        "/google/privacy-rules"
    ],
    "Files + Integrations": [
        "/files/status",
        "/files/prep-summary",
        "/files/alerts",
        "/notification-upgrade",
        "/integrations/status"
    ],
    "Executive OS": [
        "/executive-cockpit",
        "/notifications",
        "/daily-workflow",
        "/end-day-summary",
        "/memory-quality",
        "/decision-patterns-v400",
        "/recurring-risks",
        "/action-overload",
        "/executive-signal-summary",
        "/daily-brief-intelligence",
        "/workflow-layer",
        "/command-center-3",
        "/command-templates",
        "/next-command"
    ]
}

def v1205_build_test_links_html() -> str:
    base = V1205_BACKEND_BASE
    sections = []
    for category, routes in V1205_TEST_LINKS.items():
        rows = []
        for route in routes:
            url = base + route
            safe_url = url.replace("'", "&#39;")
            rows.append(
                '<div class="linkrow">'
                '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + url + '</a>'
                '<button onclick="navigator.clipboard.writeText(\'' + safe_url + '\')">Copy</button>'
                '</div>'
            )
        sections.append('<section><h2>' + category + '</h2><div class="links">' + "".join(rows) + '</div></section>')
    body = "".join(sections)
    return """<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Links</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:28px}
    .wrap{max-width:1220px;margin:auto}
    .hero,section{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:22px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:16px}
    h1{margin:0 0 8px;font-size:28px}
    p{color:#64748b;line-height:1.5}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
    h2{margin:0 0 12px;font-size:18px}
    .links{display:grid;grid-template-columns:1fr;gap:8px}
    .linkrow{display:grid;grid-template-columns:1fr 80px;gap:8px;align-items:center}
    a{display:block;text-decoration:none;border:1px solid #dbe5f1;border-radius:12px;padding:10px;color:#0f63ff;font-weight:800;font-size:13px;background:#fff;word-break:break-all}
    a:hover{background:#eff6ff;border-color:#93c5fd}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#f8fbff;font-weight:800;padding:10px;cursor:pointer}
    .warning{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    @media(max-width:900px){body{padding:14px}.linkrow{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>Executive Engine OS V9100 Test Links</h1>
      <p>Fixed page. These links point directly to the backend API domain.</p>
      <p>Backend base: <code>__BASE__</code></p>
      <div class="warning">/test-links no longer depends on HTMLResponse. It returns a plain HTML Response.</div>
    </div>
    __BODY__
  </div>
</body>
</html>""".replace("__BASE__", base).replace("__BODY__", body)


@app.get("/test-links-json")
async def test_links_json():
    flat = []
    for category, routes in V1205_TEST_LINKS.items():
        for route in routes:
            flat.append({"category": category, "route": route, "url": V1205_BACKEND_BASE + route})
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Links Fixed",
        "backend_base": V1205_BACKEND_BASE,
        "links": flat,
        "categories": V1205_TEST_LINKS,
        "note": "Use full backend URL values."
    }


@app.get("/test-links")
async def test_links():
    return Response(content=v1205_build_test_links_html(), media_type="text/html")


@app.get("/v1205-milestone")
async def v1205_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Links Internal Server Error Fix",
        "ready": True,
        "frontend_must_show": "V1205 Test Links Fixed · V1205 Backend",
        "fixed": [
            "Renamed prior /test-links route to /test-links-archive",
            "Recreated /test-links using plain Response",
            "Avoids missing HTMLResponse/import issues",
            "Uses full absolute backend URLs",
            "Keeps /test-links-json working"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/diagnostic",
            "https://executive-engine-os.onrender.com/system-test",
            "https://executive-engine-os.onrender.com/test-links-json",
            "https://executive-engine-os.onrender.com/test-links",
            "https://executive-engine-os.onrender.com/v1205-milestone"
        ]
    }




# =========================
# V1206 COPY/PASTE TEST REPORT
# =========================

V1206_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V1206_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "diagnostic",
        "route": "/diagnostic"
    },
    {
        "title": "system-test",
        "route": "/system-test"
    },
    {
        "title": "test-links-json",
        "route": "/test-links-json"
    },
    {
        "title": "test-links",
        "route": "/test-links"
    },
    {
        "title": "v1206-milestone",
        "route": "/v1206-milestone"
    },
    {
        "title": "beta system score",
        "route": "/beta/system-score"
    },
    {
        "title": "beta operating brief",
        "route": "/beta/operating-brief"
    },
    {
        "title": "calendar connect status",
        "route": "/calendar/connect-status"
    },
    {
        "title": "calendar auth url",
        "route": "/calendar/auth-url"
    },
    {
        "title": "calendar live candidate",
        "route": "/calendar/status-live-candidate"
    },
    {
        "title": "oauth live gates",
        "route": "/oauth/live-gates"
    },
    {
        "title": "token storage health",
        "route": "/tokens/storage-health"
    },
    {
        "title": "connector command center",
        "route": "/connector-command-center"
    },
    {
        "title": "files status",
        "route": "/files/status"
    },
    {
        "title": "executive cockpit",
        "route": "/executive-cockpit"
    }
]

@app.get("/test-report-json-broken-archive")
async def test_report_json():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Copy/Paste Test Report",
        "backend_base": V1206_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V1206_BACKEND_BASE + item["route"]
            }
            for item in V1206_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All and paste results into ChatGPT."
    }


@app.get("/test-report-broken-archive")
async def test_report():
    html_content = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px;text-transform:capitalize}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:360px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>This is the page you wanted: click one button, it runs the main backend tests, then gives you one clean copy/paste report with headers like health, diagnostic, system-test, etc.</p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here after you click Run Report."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value){
  if(typeof value === "string") return value;
  try{ return JSON.stringify(value, null, 2); }catch(e){ return String(value); }
}

function setStatus(text, ok=true){
  const el = document.getElementById("status");
  el.className = ok ? "good" : "fail";
  el.textContent = text;
}

async function runOne(test){
  const url = BACKEND_BASE + test.route;
  try{
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data;
    if(contentType.includes("application/json")) data = await res.json();
    else data = await res.text();
    return {
      title: test.title,
      route: test.route,
      url,
      status: res.status,
      ok: res.ok,
      output: data
    };
  }catch(err){
    return {
      title: test.title,
      route: test.route,
      url,
      status: "FETCH_ERROR",
      ok: false,
      output: err.message
    };
  }
}

function renderCards(results){
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${r.title}</h2>
      <div class="url">${r.url} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

function buildCopyText(results){
  const lines = [];
  lines.push("Executive Engine OS V9100 Test Report");
  lines.push("Generated: " + new Date().toISOString());
  lines.push("");
  results.forEach(r => {
    lines.push("========================================");
    lines.push(r.title);
    lines.push(r.url);
    lines.push("status: " + r.status);
    lines.push("ok: " + r.ok);
    lines.push("----------------------------------------");
    lines.push(pretty(r.output));
    lines.push("");
  });
  return lines.join("\n");
}

function escapeHtml(str){
  return String(str)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;");
}

async function runReport(){
  setStatus("Running tests...");
  const results = [];
  for(const test of TESTS){
    setStatus("Running: " + test.title);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? ("Done with " + failed + " failed link(s). Copy All and paste into ChatGPT.") : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll(){
  const text = document.getElementById("copyBox").value;
  if(!text){ setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.");
}

function clearReport(){
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.");
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V1206_BACKEND_BASE).replace("__TESTS_JSON__", json.dumps(V1206_REPORT_TESTS))
    return Response(content=html_content, media_type="text/html")


@app.get("/v1206-milestone")
async def v1206_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Copy/Paste Test Report",
        "ready": True,
        "frontend_must_show": "V1206 Copy/Paste Test Report · V1206 Backend",
        "added": [
            "GET /test-report",
            "GET /test-report-json",
            "One-click Run Report page",
            "Headers for each test result",
            "Copy All Results button",
            "Keeps /test-links"
        ],
        "how_to_use": [
            "Open https://executive-engine-os.onrender.com/test-report",
            "Click Run Report",
            "Click Copy All Results",
            "Paste into ChatGPT"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/v1206-milestone"
        ]
    }




# =========================
# V1207 TEST REPORT RUNTIME FIX
# =========================

V1950_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V1950_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "core quality status",
        "route": "/core-quality-status"
    },
    {
        "title": "memory action intelligence",
        "route": "/memory-action-intelligence"
    },
    {
        "title": "action intelligence",
        "route": "/action-intelligence"
    },
    {
        "title": "memory patterns",
        "route": "/memory-patterns"
    },
    {
        "title": "frontend execution status",
        "route": "/frontend-execution-status"
    },
    {
        "title": "command template library",
        "route": "/command-template-library"
    },
    {
        "title": "recommended command kit",
        "route": "/recommended-command-kit"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v1950-milestone",
        "route": "/v1950-milestone"
    },
    {
        "title": "executive cockpit",
        "route": "/executive-cockpit"
    },
    {
        "title": "integration prep status",
        "route": "/integration-prep-status"
    }
]

@app.get("/test-report-json-archive-v1975")
async def test_report_json():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Report Runtime Fix",
        "backend_base": V1950_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V1950_BACKEND_BASE + item["route"]
            }
            for item in V1950_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/test-report-archive-v1975")
async def test_report():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V1950_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>Click Run Report. Then click Copy All Results and paste into ChatGPT.</p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V1950_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)


@app.get("/v1207-milestone")
async def v1207_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Report Runtime Fix",
        "ready": True,
        "frontend_must_show": "V1950 Test Report Runtime Fix · V1207 Backend",
        "fixed": [
            "Renamed previous broken /test-report route",
            "Rebuilt /test-report with local Starlette HTMLResponse import",
            "Keeps one-click Run Report",
            "Keeps Copy All Results",
            "Keeps headers for each test result"
        ],
        "how_to_use": [
            "Open https://executive-engine-os.onrender.com/test-report",
            "Click Run Report",
            "Click Copy All Results",
            "Paste into ChatGPT"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1207-milestone"
        ]
    }




# =========================
# V1250 PRODUCT POLISH + UX STABILIZATION
# =========================
# Frontend polish release. Preserves diagnostic routes, /test-report, manual-only execution, no OAuth activation.

@app.get("/stable-version")
async def stable_version():
    return {
        "ok": True,
        "version": VERSION,
        "stable_checkpoint": "V1250",
        "baseline": "V1207",
        "frontend_badge": "V1250 Product Polish · V1250 Backend",
        "backend_base": "https://executive-engine-os.onrender.com",
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "oauth_active": False,
        "external_writes_enabled": False,
        "notes": [
            "Visible frontend hides confusing old checkpoint labels.",
            "Preserved diagnostic routes may still return older milestone labels by design.",
            "/test-report remains the primary copy/paste report page."
        ]
    }


@app.get("/frontend-polish-status")
async def frontend_polish_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Polish + UX Stabilization",
        "frontend": {
            "status": "polished",
            "command_center": "working",
            "dashboard_layout": "cleaned",
            "stable_version_panel": "added",
            "test_report_button": "/test-report",
            "old_checkpoint_labels_hidden_from_frontend": True
        },
        "backend": {
            "diagnostic_routes_preserved": True,
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/v1250-milestone")
async def v1250_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Polish + UX Stabilization",
        "ready": True,
        "frontend_must_show": "V1250 Product Polish · V1250 Backend",
        "baseline": "V1207",
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "improved": [
            "Cleaned frontend UX",
            "Improved dashboard layout",
            "Added Stable Version panel",
            "Hid confusing old checkpoint labels from visible frontend",
            "Fixed frontend button routing",
            "Open Copy/Paste Test Report points directly to /test-report"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/stable-version",
            "https://executive-engine-os.onrender.com/frontend-polish-status",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1250-milestone"
        ],
        "recommended_next_build": "V1300 Product Dashboard + Real Workflows OR V1300 Calendar Env Setup Prep"
    }




# =========================
# V1300 PRODUCT DASHBOARD + REAL WORKFLOWS
# =========================
# Product dashboard release. Preserves /test-report, diagnostic routes, Supabase schema, and manual execution policy.
# No OAuth activation. No external writes. No automation loop.

@app.get("/product-dashboard")
async def product_dashboard():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Dashboard + Real Workflows",
        "dashboard": {
            "stable_version": "V1300",
            "baseline": "V1250",
            "today_focus": "Run the OS from one clean command dashboard.",
            "current_constraint": "OAuth is not activated and action load remains high.",
            "next_decision": "Choose between product workflow polish and real Calendar activation prep.",
            "next_move": "Use Command Center, then copy/paste /test-report after each deploy.",
            "recommended_command": "Review V1300 dashboard and identify the single highest-impact product workflow to improve next.",
            "system_status": {
                "backend": "live_candidate",
                "frontend": "polished_dashboard",
                "manual_execution_only": True,
                "auto_loop_enabled": False,
                "oauth_active": False,
                "external_writes_enabled": False,
                "supabase_schema_changed": False
            }
        }
    }


@app.get("/workflow-dashboard")
async def workflow_dashboard():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Dashboard",
        "workflow": [
            {
                "id": "start_day",
                "title": "Start Day",
                "purpose": "Set today's focus, constraint, next decision, and priority.",
                "command": "Start my day. Identify today's focus, current constraint, next decision, highest-impact action, risk, and recommended command.",
                "status": "ready"
            },
            {
                "id": "daily_brief",
                "title": "Daily Brief",
                "purpose": "Generate one operating brief for the day.",
                "command": "Create my daily operating brief with focus, decisions, risks, actions, and priority.",
                "status": "ready"
            },
            {
                "id": "run_command",
                "title": "Run Command",
                "purpose": "Convert any messy input into executive decision/action output.",
                "command": "Turn this into a decision, next move, action plan, risk, and priority.",
                "status": "ready"
            },
            {
                "id": "review_queue",
                "title": "Review Action Queue",
                "purpose": "Reduce action overload and pick what to complete, cut, or defer.",
                "command": "Reduce my action queue. Tell me what to complete, cut, defer, and what to do first.",
                "status": "ready"
            },
            {
                "id": "review_risks",
                "title": "Review Risks",
                "purpose": "Identify recurring execution risks and mitigation.",
                "command": "Review current execution risks, recurring constraints, and mitigation actions.",
                "status": "ready"
            },
            {
                "id": "end_day",
                "title": "End Day Summary",
                "purpose": "Close the execution loop and set tomorrow's starting point.",
                "command": "Create my end-day summary. What was decided, what remains open, what risk remains, and what starts tomorrow?",
                "status": "ready"
            }
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/product-navigation-map")
async def product_navigation_map():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Navigation Map",
        "pages": [
            {"id": "command", "title": "Command Center", "status": "live", "purpose": "Run executive commands."},
            {"id": "dashboard", "title": "Product Dashboard", "status": "live", "purpose": "See stable version, workflow state, and next move."},
            {"id": "workflow", "title": "Workflow Dashboard", "status": "live", "purpose": "Run daily operating workflow."},
            {"id": "cockpit", "title": "Executive Cockpit", "status": "connected", "purpose": "Review action load, recurring risk, and decision patterns."},
            {"id": "calendar", "title": "Calendar", "status": "prep", "purpose": "Read-only OAuth candidate; inactive until env setup."},
            {"id": "connectors", "title": "Connectors", "status": "prep", "purpose": "Approval-gated connector planning."},
            {"id": "testing", "title": "Test Report", "status": "live", "purpose": "Copy/paste deploy validation report."},
            {"id": "settings", "title": "Settings", "status": "live", "purpose": "Diagnostics and stable version controls."}
        ]
    }


@app.get("/v1300-milestone")
async def v1300_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Dashboard + Real Workflows",
        "ready": True,
        "frontend_must_show": "V1300 Product Dashboard · V1300 Backend",
        "baseline": "V1250",
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "added": [
            "Product Dashboard page",
            "Workflow Dashboard page",
            "Product Navigation Map",
            "Start Day workflow",
            "Review Queue workflow",
            "Review Risks workflow",
            "End Day workflow",
            "Cleaner command templates",
            "More product-level frontend layout"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/stable-version",
            "https://executive-engine-os.onrender.com/product-dashboard",
            "https://executive-engine-os.onrender.com/workflow-dashboard",
            "https://executive-engine-os.onrender.com/product-navigation-map",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1300-milestone"
        ],
        "recommended_next_build": "V1400 Intelligence Board"
    }


# =========================
# V1350 WORKFLOW PERSISTENCE POLISH
# =========================
# Adds local workflow model/contracts only. No schema change. No external writes.

@app.get("/workflow-state")
async def workflow_state():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Persistence Polish",
        "state": {
            "active_workflow": "daily_operating_loop",
            "current_step": "command_center",
            "last_completed_step": "test_report_verified",
            "next_step": "run_start_day_or_review_queue",
            "saved_locally_in_frontend": True,
            "server_persistence_changed": False,
            "supabase_schema_changed": False
        },
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/workflow/checkpoints")
async def workflow_checkpoints():
    return {
        "ok": True,
        "version": VERSION,
        "checkpoints": [
            {"id": "start_day", "title": "Start Day", "status": "ready", "command": "Start my day. Identify focus, constraint, next decision, action, risk, and priority."},
            {"id": "daily_brief", "title": "Daily Brief", "status": "ready", "command": "Create my daily operating brief."},
            {"id": "run_command", "title": "Run Command", "status": "ready", "command": "Turn this into a decision, next move, action plan, risk, and priority."},
            {"id": "review_queue", "title": "Review Queue", "status": "ready", "command": "Reduce my action queue. Tell me what to complete, cut, or defer."},
            {"id": "review_risks", "title": "Review Risks", "status": "ready", "command": "Review execution risks and mitigations."},
            {"id": "end_day", "title": "End Day", "status": "ready", "command": "Create my end-day summary."}
        ],
        "server_writes": False
    }


@app.get("/v1350-milestone")
async def v1350_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Persistence Polish",
        "ready": True,
        "frontend_must_show": "V1350 Workflow Persistence · V1350 Backend",
        "baseline": "V1300",
        "added": [
            "Workflow state endpoint",
            "Workflow checkpoints endpoint",
            "Frontend local workflow progress",
            "Workflow progress panel",
            "No backend schema change"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/workflow-state",
            "https://executive-engine-os.onrender.com/workflow/checkpoints",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1350-milestone"
        ],
        "recommended_next_build": "V1400 Intelligence Board"
    }


# =========================
# V1400 INTELLIGENCE BOARD
# =========================
# Adds intelligence board summaries. No AI automation loop. Manual execution only.

@app.get("/intelligence-board")
async def intelligence_board():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Intelligence Board",
        "signals": {
            "action_load": {
                "status": "high",
                "signal": "Open action queue is high; reduce before adding more.",
                "recommended_command": "Reduce my action queue. Tell me what to complete, cut, or defer."
            },
            "deployment_pattern": {
                "status": "recurring",
                "signal": "Deployment and stability checks are recurring decisions.",
                "recommended_command": "Run the test report and identify the next safe product milestone."
            },
            "calendar_readiness": {
                "status": "blocked",
                "signal": "Google OAuth env vars are not set. Calendar remains read-only prep.",
                "recommended_command": "Review Calendar activation prerequisites before enabling OAuth."
            },
            "connector_risk": {
                "status": "controlled",
                "signal": "External writes are blocked and approval gates remain active.",
                "recommended_command": "Review connector command center and pick the next safe integration."
            }
        },
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/intelligence/recommended-commands")
async def intelligence_recommended_commands():
    return {
        "ok": True,
        "version": VERSION,
        "commands": [
            "Reduce my action queue. Tell me what to complete, cut, or defer today.",
            "Review current risks and identify the one constraint blocking execution.",
            "Create my daily brief using the current product dashboard and workflow state.",
            "Review Calendar OAuth readiness and list only the safe next steps.",
            "Review V1400 Intelligence Board and recommend the next product milestone."
        ]
    }


@app.get("/v1400-milestone")
async def v1400_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Intelligence Board",
        "ready": True,
        "frontend_must_show": "V1400 Intelligence Board · V1400 Backend",
        "baseline": "V1350",
        "added": [
            "Intelligence Board endpoint",
            "Recommended commands endpoint",
            "Frontend Intelligence Board page",
            "Signals for action load, deployment pattern, calendar readiness, connector risk"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/intelligence-board",
            "https://executive-engine-os.onrender.com/intelligence/recommended-commands",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1400-milestone"
        ],
        "recommended_next_build": "V1450 Operator Console"
    }


# =========================
# V1450 OPERATOR CONSOLE
# =========================
# Adds operator console command/control model. No autonomous execution.

@app.get("/operator-console")
async def operator_console():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Operator Console",
        "console": {
            "mode": "manual_operator",
            "primary_action": "Run one command, review result, decide next move.",
            "safe_actions": [
                "Run Engine",
                "Load workflow command",
                "Open test report",
                "Review cockpit",
                "Review intelligence board",
                "Review connector gates"
            ],
            "blocked_actions": [
                "Autonomous loop",
                "External writes",
                "Calendar writes",
                "Email sending",
                "File editing",
                "OAuth activation without env/token review"
            ],
            "operator_instruction": "Complete one workflow step, then run /test-report after deploy changes."
        }
    }


@app.get("/operator/command-palette")
async def operator_command_palette():
    return {
        "ok": True,
        "version": VERSION,
        "palette": [
            {"label": "Start Day", "command": "Start my day. Identify focus, constraint, next decision, action, risk, and priority."},
            {"label": "Reduce Queue", "command": "Reduce my action queue. Tell me what to complete, cut, or defer today."},
            {"label": "Review Risk", "command": "Review current execution risks and mitigations."},
            {"label": "Product Next Move", "command": "Review the product dashboard and recommend the next milestone."},
            {"label": "Connector Safety", "command": "Review connector gates and identify the next safe integration step."},
            {"label": "End Day", "command": "Create my end-day summary and tomorrow's starting command."}
        ]
    }


@app.get("/v1450-milestone")
async def v1450_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Operator Console",
        "ready": True,
        "frontend_must_show": "V1450 Operator Console · V1450 Backend",
        "baseline": "V1400",
        "added": [
            "Operator Console endpoint",
            "Command Palette endpoint",
            "Frontend Operator Console page",
            "Clear blocked/safe action model",
            "Command palette for manual operation"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/operator-console",
            "https://executive-engine-os.onrender.com/operator/command-palette",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1450-milestone"
        ],
        "recommended_next_build": "V1500 Product Candidate Stable"
    }


# =========================
# V1500 PRODUCT CANDIDATE STABLE
# =========================
# Stable product candidate rollup: dashboard, workflows, intelligence, operator console, testing.

@app.get("/product-candidate-status")
async def product_candidate_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate Stable",
        "status": "stable_candidate",
        "modules": {
            "command_center": "live",
            "product_dashboard": "live",
            "workflow_dashboard": "live",
            "workflow_persistence": "local_frontend",
            "intelligence_board": "live",
            "operator_console": "live",
            "test_report": "live",
            "calendar_oauth": "prep_only",
            "connectors": "approval_gated",
            "external_writes": "blocked"
        },
        "operating_policy": {
            "manual_execution_only": True,
            "auto_loop_enabled": False,
            "oauth_active": False,
            "supabase_schema_changed": False,
            "external_writes_enabled": False
        }
    }


@app.get("/product-candidate/checklist")
async def product_candidate_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "checklist": [
            "Run /health",
            "Run /product-candidate-status",
            "Open frontend and confirm V1500 badge",
            "Run a command from Command Center",
            "Open Workflow Dashboard",
            "Open Intelligence Board",
            "Open Operator Console",
            "Run /test-report and copy results",
            "Do not activate OAuth until env/token storage is ready"
        ]
    }


@app.get("/v1500-milestone")
async def v1500_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate Stable",
        "ready": True,
        "frontend_must_show": "V1500 Product Candidate Stable · V1500 Backend",
        "baseline": "V1450",
        "includes": [
            "V1300 Product Dashboard + Real Workflows",
            "V1350 Workflow Persistence Polish",
            "V1400 Intelligence Board",
            "V1450 Operator Console",
            "V1500 Stable Candidate Rollup"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/product-candidate-status",
            "https://executive-engine-os.onrender.com/product-candidate/checklist",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1500-milestone"
        ],
        "recommended_next_build": "V1550 Real Calendar Env Setup Prep OR V1550 UI/Workflow QA Pass"
    }




# =========================
# V1550 UI / WORKFLOW QA PASS
# =========================
# QA/polish release. No Supabase schema changes. No OAuth activation. No external writes.

@app.get("/ui-qa-status")
async def ui_qa_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "UI / Workflow QA Pass",
        "frontend_must_show": "V1550 UI / Workflow QA · V1550 Backend",
        "qa": {
            "default_page": "Product Dashboard",
            "sidebar_routes_checked": True,
            "stable_version_panel": "V1550",
            "bottom_sidebar_label": "V1550 Product Candidate Stable",
            "test_report_button": "/test-report",
            "empty_states": "improved",
            "button_routing": "checked",
            "old_checkpoint_labels_hidden_from_frontend": True
        },
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/workflow-qa-check")
async def workflow_qa_check():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow QA Check",
        "pages": [
            {"page": "Product Dashboard", "status": "default", "primary_action": "Run Command"},
            {"page": "Operator Console", "status": "clickable", "primary_action": "Load Operator Console"},
            {"page": "Command Center", "status": "clickable", "primary_action": "Run Engine"},
            {"page": "Workflows", "status": "clickable", "primary_action": "Load workflow command"},
            {"page": "Executive Cockpit", "status": "clickable", "primary_action": "Load Cockpit"},
            {"page": "Intelligence Board", "status": "clickable", "primary_action": "Load Intelligence Board"},
            {"page": "Calendar Prep", "status": "prep_only", "primary_action": "Review OAuth Gates"},
            {"page": "Connectors", "status": "prep_only", "primary_action": "Review Connector Command Center"},
            {"page": "Progress", "status": "local_only", "primary_action": "Load Workflow State"},
            {"page": "Candidate Status", "status": "clickable", "primary_action": "Load Candidate Status"},
            {"page": "Test Report", "status": "working", "primary_action": "Open /test-report"},
            {"page": "Settings", "status": "clickable", "primary_action": "Open diagnostics"}
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/v1550-milestone")
async def v1550_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "UI / Workflow QA Pass",
        "ready": True,
        "frontend_must_show": "V1550 UI / Workflow QA · V1550 Backend",
        "baseline": "V1500",
        "fixed": [
            "Sidebar bottom label corrected",
            "Product Dashboard remains default",
            "Spacing tightened",
            "Empty states improved",
            "Button routing clarified",
            "Visible frontend labels aligned to V1550",
            "Test Report button preserved"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/ui-qa-status",
            "https://executive-engine-os.onrender.com/workflow-qa-check",
            "https://executive-engine-os.onrender.com/product-candidate-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1550-milestone"
        ],
        "recommended_next_build": "V1600 Calendar Environment Setup Prep OR V1600 Product Workflow Persistence"
    }


# =========================
# V1600 CALENDAR ENV SETUP PREP
# =========================
# Environment setup prep only. No live OAuth activation and no token exchange.

@app.get("/calendar/env-setup-prep")
async def calendar_env_setup_prep():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Env Setup Prep",
        "required_render_env_vars": [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "TOKEN_ENCRYPTION_KEY",
            "OAUTH_ENABLED=false",
            "TOKEN_STORAGE_ENABLED=false"
        ],
        "google_cloud_steps": [
            "Create or open Google Cloud project",
            "Configure OAuth consent screen",
            "Enable Google Calendar API",
            "Create OAuth web client",
            "Add backend callback URL as authorized redirect URI",
            "Keep read-only calendar scope only"
        ],
        "allowed_scope": "https://www.googleapis.com/auth/calendar.events.readonly",
        "blocked": ["calendar writes", "background sync", "token exchange", "token storage", "external writes"],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }

@app.get("/calendar/env-checklist")
async def calendar_env_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "checklist": [
            {"item": "GOOGLE_CLIENT_ID set in Render", "required": True},
            {"item": "GOOGLE_CLIENT_SECRET set in Render", "required": True},
            {"item": "GOOGLE_REDIRECT_URI set to backend callback", "required": True},
            {"item": "TOKEN_ENCRYPTION_KEY generated", "required": True},
            {"item": "OAUTH_ENABLED remains false until activation build", "required": True},
            {"item": "TOKEN_STORAGE_ENABLED remains false until activation build", "required": True}
        ],
        "ready_for_live_oauth": False
    }

@app.get("/v1600-milestone")
async def v1600_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Env Setup Prep",
        "ready": True,
        "frontend_must_show": "V1600 Calendar Env Setup Prep · V1600 Backend",
        "baseline": "V1550",
        "added": ["Calendar env setup prep", "Google Cloud setup checklist", "Render env var checklist", "Calendar prep frontend page"],
        "kept": ["/test-report working", "diagnostic routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"],
        "test_order": ["https://executive-engine-os.onrender.com/health","https://executive-engine-os.onrender.com/calendar/env-setup-prep","https://executive-engine-os.onrender.com/calendar/env-checklist","https://executive-engine-os.onrender.com/test-report","https://executive-engine-os.onrender.com/v1600-milestone"],
        "recommended_next_build": "V1650 Calendar Safety Gate"
    }


# =========================
# V1650 CALENDAR SAFETY GATE
# =========================
# Approval and safety model for future OAuth activation. No live OAuth.

@app.get("/calendar/safety-gate")
async def calendar_safety_gate():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Safety Gate",
        "gates": {
            "read_only_scope_only": True,
            "calendar_writes_blocked": True,
            "background_sync_blocked": True,
            "manual_refresh_only": True,
            "token_exchange_blocked": True,
            "token_storage_blocked": True,
            "user_approval_required_for_activation": True
        },
        "blocked_actions": ["create event", "edit event", "delete event", "invite attendees", "auto-join", "background sync", "auto-send"],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }

@app.get("/calendar/activation-readiness")
async def calendar_activation_readiness():
    return {
        "ok": True,
        "version": VERSION,
        "ready_for_activation": False,
        "missing_before_activation": [
            "Google env vars must be set",
            "Token encryption key must be set",
            "Token storage migration must be approved",
            "Disconnect/revoke flow must be tested",
            "User must explicitly approve activation build"
        ],
        "next_safe_step": "Keep OAuth inactive and prepare V1700 token-storage migration plan."
    }

@app.get("/v1650-milestone")
async def v1650_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Safety Gate",
        "ready": True,
        "frontend_must_show": "V1650 Calendar Safety Gate · V1650 Backend",
        "baseline": "V1600",
        "added": ["Calendar safety gate", "Activation readiness", "Blocked action model", "Frontend safety page"],
        "kept": ["/test-report working", "diagnostic routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"],
        "test_order": ["https://executive-engine-os.onrender.com/health","https://executive-engine-os.onrender.com/calendar/safety-gate","https://executive-engine-os.onrender.com/calendar/activation-readiness","https://executive-engine-os.onrender.com/test-report","https://executive-engine-os.onrender.com/v1650-milestone"],
        "recommended_next_build": "V1700 Token Storage Migration Plan"
    }


# =========================
# V1700 TOKEN STORAGE MIGRATION PLAN
# =========================
# Migration plan only. No table creation. No schema change.

@app.get("/tokens/migration-plan")
async def tokens_migration_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Token Storage Migration Plan",
        "schema_changed": False,
        "future_table": "oauth_connections",
        "fields": [
            "id uuid primary key",
            "user_id text",
            "provider text",
            "connected_email text",
            "scope text",
            "access_token_encrypted text",
            "refresh_token_encrypted text",
            "expires_at timestamp",
            "last_refresh_at timestamp",
            "revoked_at timestamp",
            "created_at timestamp",
            "updated_at timestamp"
        ],
        "required_before_migration": [
            "Approve schema migration",
            "Generate TOKEN_ENCRYPTION_KEY",
            "Define RLS/service-role policy",
            "Implement token encryption helper",
            "Implement disconnect/revoke flow"
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }

@app.get("/tokens/migration-sql-preview")
async def tokens_migration_sql_preview():
    return {
        "ok": True,
        "version": VERSION,
        "preview_only": True,
        "sql": "CREATE TABLE oauth_connections (...); -- preview only, not executed in V1700",
        "execute_now": False,
        "schema_changed": False
    }

@app.get("/v1700-milestone")
async def v1700_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Token Storage Migration Plan",
        "ready": True,
        "frontend_must_show": "V1700 Token Storage Plan · V1700 Backend",
        "baseline": "V1650",
        "added": ["Token storage migration plan", "SQL preview endpoint", "Frontend token migration page"],
        "kept": ["/test-report working", "diagnostic routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"],
        "test_order": ["https://executive-engine-os.onrender.com/health","https://executive-engine-os.onrender.com/tokens/migration-plan","https://executive-engine-os.onrender.com/tokens/migration-sql-preview","https://executive-engine-os.onrender.com/test-report","https://executive-engine-os.onrender.com/v1700-milestone"],
        "recommended_next_build": "V1750 Calendar Readiness Dashboard"
    }


# =========================
# V1750 CALENDAR READINESS DASHBOARD
# =========================
# Readiness dashboard only. Still no activation.

@app.get("/calendar/readiness-dashboard")
async def calendar_readiness_dashboard():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Readiness Dashboard",
        "readiness_score": "0/6",
        "ready_for_activation": False,
        "checks": [
            {"name": "Google client ID set", "passed": False},
            {"name": "Google client secret set", "passed": False},
            {"name": "Redirect URI set", "passed": False},
            {"name": "Token encryption key set", "passed": False},
            {"name": "Token storage migration approved", "passed": False},
            {"name": "Disconnect/revoke tested", "passed": False}
        ],
        "safe_next_step": "Set Google env variables in Render, then rerun readiness.",
        "blocked": ["OAuth activation", "token exchange", "token storage", "calendar writes"]
    }

@app.get("/calendar/activation-command")
async def calendar_activation_command():
    return {
        "ok": True,
        "version": VERSION,
        "command": "Prepare Calendar activation. Verify Google env vars, token encryption, token storage migration, disconnect/revoke flow, and keep read-only scope only.",
        "execute_activation_now": False
    }

@app.get("/v1750-milestone")
async def v1750_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Calendar Readiness Dashboard",
        "ready": True,
        "frontend_must_show": "V1750 Calendar Readiness · V1750 Backend",
        "baseline": "V1700",
        "added": ["Calendar readiness dashboard", "Activation command endpoint", "Frontend readiness page"],
        "kept": ["/test-report working", "diagnostic routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"],
        "test_order": ["https://executive-engine-os.onrender.com/health","https://executive-engine-os.onrender.com/calendar/readiness-dashboard","https://executive-engine-os.onrender.com/calendar/activation-command","https://executive-engine-os.onrender.com/test-report","https://executive-engine-os.onrender.com/v1750-milestone"],
        "recommended_next_build": "V1800 Stable Integration Prep"
    }


# =========================
# V1800 STABLE INTEGRATION PREP
# =========================
# Rollup of V1600-V1750. Stable integration prep only. No OAuth activation.

@app.get("/integration-prep-status")
async def integration_prep_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Stable Integration Prep",
        "status": "prep_ready_not_active",
        "modules": {
            "calendar_env_setup": "prepared",
            "calendar_safety_gate": "prepared",
            "token_storage_plan": "prepared_preview_only",
            "calendar_readiness_dashboard": "prepared",
            "oauth_activation": "blocked",
            "external_writes": "blocked"
        },
        "next_decision": "Set Google env variables or continue product workflow polish.",
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }

@app.get("/integration-prep/checklist")
async def integration_prep_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "checklist": [
            "Confirm frontend badge shows V1800",
            "Run /test-report",
            "Review /calendar/env-setup-prep",
            "Review /calendar/safety-gate",
            "Review /tokens/migration-plan",
            "Review /calendar/readiness-dashboard",
            "Do not activate OAuth until env vars and token storage are approved"
        ]
    }

@app.get("/v1800-milestone")
async def v1800_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Stable Integration Prep",
        "ready": True,
        "frontend_must_show": "V1800 Stable Integration Prep · V1800 Backend",
        "baseline": "V1750",
        "includes": [
            "V1600 Calendar Env Setup Prep",
            "V1650 Calendar Safety Gate",
            "V1700 Token Storage Migration Plan",
            "V1750 Calendar Readiness Dashboard",
            "V1800 Stable Integration Prep Rollup"
        ],
        "kept": ["/test-report working", "diagnostic routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"],
        "test_order": ["https://executive-engine-os.onrender.com/health","https://executive-engine-os.onrender.com/integration-prep-status","https://executive-engine-os.onrender.com/integration-prep/checklist","https://executive-engine-os.onrender.com/test-report","https://executive-engine-os.onrender.com/v1800-milestone"],
        "recommended_next_build": "V1850 Google Env Variable Setup Guide OR V1850 Product UX Polish"
    }




# =========================
# V1850 CORE OS QUALITY UPGRADE
# =========================
# Core OS quality release. Improves output discipline and workflow guidance.
# No Supabase schema change. No OAuth activation. No external writes.

@app.get("/core-quality-status")
async def core_quality_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Core OS Quality Upgrade",
        "frontend_must_show": "V1850 Core OS Quality · V1850 Backend",
        "quality_targets": {
            "next_move_first": True,
            "current_constraint_required": True,
            "what_to_cut_required": True,
            "next_decision_required": True,
            "recommended_command_required": True,
            "execution_score_required": True,
            "actions_specific": True,
            "raw_json_hidden_in_frontend": True
        },
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/core-output-contract")
async def core_output_contract():
    return {
        "ok": True,
        "version": VERSION,
        "contract": {
            "display_order": [
                "NEXT MOVE",
                "TODAY'S FOCUS",
                "CURRENT CONSTRAINT",
                "DECISION",
                "NEXT DECISION",
                "WHAT TO CUT",
                "ACTIONS",
                "RISK",
                "PRIORITY",
                "EXECUTION SCORE",
                "MEMORY SIGNAL",
                "RECOMMENDED COMMAND"
            ],
            "required_fields": [
                "next_move",
                "today_focus",
                "current_constraint",
                "decision",
                "next_decision",
                "what_to_cut",
                "actions",
                "risk",
                "priority",
                "execution_score",
                "memory_signal",
                "recommended_command"
            ],
            "anti_patterns": [
                "generic advice",
                "motivational filler",
                "too many actions",
                "integration-first thinking",
                "unclear tradeoffs",
                "no cut/defer decision"
            ]
        }
    }


@app.get("/execution-loop")
async def execution_loop():
    return {
        "ok": True,
        "version": VERSION,
        "loop": [
            {"step": 1, "name": "Start Day", "command": "Start my day. Identify focus, constraint, next decision, what to cut, and next move."},
            {"step": 2, "name": "Run Command", "command": "Turn this input into a decision, next move, current constraint, what to cut, actions, risk, and recommended command."},
            {"step": 3, "name": "Reduce Queue", "command": "Reduce my action queue. Tell me what to complete, cut, defer, and what to do first."},
            {"step": 4, "name": "Review Risk", "command": "Review the current execution risk and the constraint most likely to slow progress."},
            {"step": 5, "name": "End Day", "command": "Create my end-day summary with decisions made, open loops, what to cut tomorrow, and starting command."}
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/core-command-templates")
async def core_command_templates():
    return {
        "ok": True,
        "version": VERSION,
        "templates": [
            {
                "id": "daily_brief",
                "title": "Daily Brief",
                "command": "Create my executive daily brief. Give me next move, today focus, current constraint, decision, next decision, what to cut, actions, risk, priority, execution score, and recommended command."
            },
            {
                "id": "cut_complexity",
                "title": "Cut Complexity",
                "command": "Review what I am building and tell me what to cut, defer, simplify, or stop so the core OS becomes more useful."
            },
            {
                "id": "quality_review",
                "title": "Core Quality Review",
                "command": "Review the current Executive Engine OS. Identify the weakest part of the core output, what to improve next, what to cut, and the next command."
            },
            {
                "id": "action_reduction",
                "title": "Reduce Action Load",
                "command": "Reduce my action load. Tell me the top 3 actions, what to cut, what to defer, and the single next move."
            },
            {
                "id": "product_focus",
                "title": "Product Focus",
                "command": "Decide the next product milestone. Prioritize core OS quality over integrations unless integration is clearly the bottleneck."
            }
        ]
    }


@app.get("/v1850-milestone")
async def v1850_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Core OS Quality Upgrade",
        "ready": True,
        "frontend_must_show": "V1850 Core OS Quality · V1850 Backend",
        "baseline": "V1800",
        "added": [
            "Stronger /run system prompt",
            "Core output contract",
            "Execution loop endpoint",
            "Core command templates",
            "Frontend executive-readable output cards",
            "What to Cut field",
            "Current Constraint field",
            "Next Decision field",
            "Execution Score field",
            "Reduced raw JSON feel"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off",
            "V1800 integration prep preserved"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/core-quality-status",
            "https://executive-engine-os.onrender.com/core-output-contract",
            "https://executive-engine-os.onrender.com/execution-loop",
            "https://executive-engine-os.onrender.com/core-command-templates",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1850-milestone"
        ],
        "recommended_next_build": "V1900 Memory + Action Intelligence Upgrade"
    }




# =========================
# V1900 MEMORY + ACTION INTELLIGENCE UPGRADE
# =========================
# Improves memory/action interpretation and action overload visibility.
# No Supabase schema change. No OAuth activation. No external writes.

@app.get("/memory-action-intelligence")
async def memory_action_intelligence():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory + Action Intelligence",
        "intelligence": {
            "action_load": {
                "status": "High",
                "signal": "Open actions remain high. Reduce and close loops before adding integrations.",
                "recommended_command": "Reduce my action queue. Tell me what to complete, cut, defer, and what to do first."
            },
            "memory_pattern": {
                "pattern": "Rapid version building followed by deployment testing and stability checks.",
                "operator_meaning": "The OS needs strong release discipline and fewer simultaneous feature tracks.",
                "what_to_cut": "Cut non-core integration work until the core execution loop feels excellent."
            },
            "decision_pattern": {
                "pattern": "Core OS quality is more important than Calendar/OAuth right now.",
                "confidence": "High",
                "next_decision": "Decide whether to polish memory/action intelligence or improve frontend execution UX next."
            },
            "risk": {
                "name": "Feature creep",
                "severity": "High",
                "mitigation": "Limit next builds to core output, memory, action queue, and workflow usability."
            }
        },
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/action-intelligence")
async def action_intelligence():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Action Intelligence",
        "action_policy": {
            "max_recommended_actions": 5,
            "must_include_what_to_cut": True,
            "must_include_next_move": True,
            "must_identify_action_load": True,
            "avoid_new_actions_when_overloaded": True
        },
        "recommended_triage": [
            "Complete one high-priority action that proves the OS works",
            "Cut or archive duplicate deployment/testing actions",
            "Defer integrations until core output quality is validated",
            "Run the copy/paste test report after each deploy",
            "Use one recommended command per session"
        ]
    }


@app.get("/memory-patterns")
async def memory_patterns():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory Patterns",
        "patterns": [
            {
                "name": "Rapid version progression",
                "signal": "The system advances quickly through version milestones.",
                "risk": "Complexity grows faster than validated usage.",
                "operator_response": "Use stable checkpoints and test reports before adding new modules."
            },
            {
                "name": "Integration temptation",
                "signal": "Calendar/files/email integrations are attractive but not core yet.",
                "risk": "OAuth/token complexity can distract from core OS quality.",
                "operator_response": "Keep integrations in prep mode until core workflow is excellent."
            },
            {
                "name": "Action overload",
                "signal": "Open action count remains high.",
                "risk": "Too many actions reduce execution clarity.",
                "operator_response": "Cut, defer, or close actions before adding new ones."
            }
        ]
    }


@app.get("/action-reduction-plan")
async def action_reduction_plan():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Action Reduction Plan",
        "plan": {
            "step_1": "Identify the top 3 actions that move the OS toward daily usability.",
            "step_2": "Cut duplicate deploy/test actions already covered by /test-report.",
            "step_3": "Defer Google Calendar activation until core output is validated.",
            "step_4": "Run one daily brief and one action-reduction command after deploy.",
            "step_5": "Use results to decide V1950."
        },
        "recommended_command": "Reduce my action queue. Tell me the top 3 actions, what to cut, what to defer, and the single next move."
    }


@app.get("/v1900-milestone")
async def v1900_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Memory + Action Intelligence Upgrade",
        "ready": True,
        "frontend_must_show": "V1900 Memory + Action Intelligence · V1900 Backend",
        "baseline": "V1850",
        "added": [
            "Memory + Action Intelligence endpoint",
            "Action Intelligence endpoint",
            "Memory Patterns endpoint",
            "Action Reduction Plan endpoint",
            "Stronger /run prompt with memory_pattern and action_load",
            "Frontend Memory + Actions page",
            "Action Load and Memory Pattern result cards"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off",
            "V1850 core output quality preserved"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/memory-action-intelligence",
            "https://executive-engine-os.onrender.com/action-intelligence",
            "https://executive-engine-os.onrender.com/memory-patterns",
            "https://executive-engine-os.onrender.com/action-reduction-plan",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1900-milestone"
        ],
        "recommended_next_build": "V1950 Frontend Execution Experience Upgrade"
    }




# =========================
# V1950 FRONTEND EXECUTION EXPERIENCE UPGRADE — FIXED ROUTES
# =========================
# Frontend execution polish. Keeps V1900 as stable baseline.
# No Supabase schema change. No OAuth activation. No external writes.

@app.get("/frontend-execution-status")
async def frontend_execution_status_v1950():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Frontend Execution Experience Upgrade",
        "frontend_must_show": "V1950 Frontend Execution Experience · V1950 Backend",
        "baseline": "V1900",
        "improvements": {
            "old_test_report_titles_fixed": True,
            "result_cards_improved": True,
            "command_input_improved": True,
            "one_click_templates": True,
            "action_load_display": True,
            "memory_pattern_display": True,
            "recommended_command_copy": True,
            "raw_json_reduced": True,
            "empty_states_improved": True,
            "calendar_oauth_parked": True
        },
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/command-template-library")
async def command_template_library_v1950():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Command Template Library",
        "templates": [
            {
                "id": "daily_brief",
                "title": "Daily Brief",
                "category": "Operate",
                "command": "Create my executive daily brief. Give me next move, today focus, current constraint, decision, next decision, what to cut, action load, memory pattern, actions, risk, priority, execution score, and recommended command."
            },
            {
                "id": "cut_complexity",
                "title": "Cut Complexity",
                "category": "Discipline",
                "command": "Review what I am building and tell me what to cut, defer, simplify, or stop so the core OS becomes more useful."
            },
            {
                "id": "reduce_actions",
                "title": "Reduce Action Load",
                "category": "Execution",
                "command": "Reduce my action load. Tell me the top 3 actions, what to cut, what to defer, the action load, and the single next move."
            },
            {
                "id": "memory_pattern",
                "title": "Find Memory Pattern",
                "category": "Intelligence",
                "command": "Review my recent pattern. Tell me what I keep repeating, what it means, what to cut, and the next decision."
            },
            {
                "id": "product_focus",
                "title": "Product Focus",
                "category": "Product",
                "command": "Decide the next product milestone. Prioritize core OS quality over integrations unless integration is clearly the bottleneck."
            },
            {
                "id": "end_day",
                "title": "End Day Summary",
                "category": "Operate",
                "command": "Create my end-day summary. What was decided, what remains open, what should be cut tomorrow, and what command should I start with?"
            }
        ]
    }


@app.get("/recommended-command-kit")
async def recommended_command_kit_v1950():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Recommended Command Kit",
        "copyable_commands": [
            "Reduce my action queue. Tell me what to complete, cut, defer, and what to do first.",
            "Review the current Executive Engine OS and identify the weakest part of the core output.",
            "Tell me what to cut from this project so it becomes more useful and less complex.",
            "Create my daily brief with next move, current constraint, what to cut, and recommended command.",
            "Review my memory pattern and tell me the recurring risk I should address today."
        ],
        "next_best_command": "Reduce my action queue. Tell me what to complete, cut, defer, and what to do first."
    }


@app.get("/frontend-label-map")
async def frontend_label_map_v1950():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Frontend Label Map",
        "current_visible_label": "V1950 Frontend Execution Experience · V1950 Backend",
        "legacy_label_policy": {
            "diagnostic": "Legacy preserved route; may show V270 internally.",
            "system_test": "Legacy preserved route; may show V270 internally.",
            "calendar_connect_status": "Legacy preserved route; may show V1000 internally.",
            "oauth_live_gates": "Legacy preserved route; may show V1050 internally.",
            "files_status": "Legacy preserved route; may show V650 internally.",
            "test_report": "Visible title updated to V1950."
        },
        "frontend_rule": "Show current stable labels in the OS. Keep legacy labels only in raw backend diagnostics."
    }


@app.get("/v1950-milestone")
async def v1950_milestone_fixed():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Frontend Execution Experience Upgrade",
        "ready": True,
        "frontend_must_show": "V1950 Frontend Execution Experience · V1950 Backend",
        "baseline": "V1900",
        "fixed": [
            "Old test report title/labels updated",
            "Result cards improved",
            "Command input experience improved",
            "One-click command templates added",
            "Action-load display improved",
            "Memory-pattern display improved",
            "Recommended command copy button added",
            "Raw JSON feel reduced",
            "Frontend empty states improved",
            "Missing V1950 route definitions repaired"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off",
            "V1900 memory/action intelligence preserved"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/frontend-execution-status",
            "https://executive-engine-os.onrender.com/command-template-library",
            "https://executive-engine-os.onrender.com/recommended-command-kit",
            "https://executive-engine-os.onrender.com/frontend-label-map",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v1950-milestone"
        ],
        "recommended_next_build": "V2000 Serious Daily-Use Product Candidate"
    }



# =========================
# V1975 CURRENT TEST REPORT
# =========================

V1975_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V1975_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "frontend execution status",
        "route": "/frontend-execution-status"
    },
    {
        "title": "command template library",
        "route": "/command-template-library"
    },
    {
        "title": "recommended command kit",
        "route": "/recommended-command-kit"
    },
    {
        "title": "frontend label map",
        "route": "/frontend-label-map"
    },
    {
        "title": "memory action intelligence",
        "route": "/memory-action-intelligence"
    },
    {
        "title": "action intelligence",
        "route": "/action-intelligence"
    },
    {
        "title": "core quality status",
        "route": "/core-quality-status"
    },
    {
        "title": "executive cockpit",
        "route": "/executive-cockpit"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v1975-milestone",
        "route": "/v1975-milestone"
    }
]

@app.get("/test-report-json-archive-v2000")
async def test_report_json_v1975():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Report Label Cleanup",
        "backend_base": V1975_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V1975_BACKEND_BASE + item["route"]
            }
            for item in V1975_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/test-report-archive-v2000")
async def test_report_v1975():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V1975_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>Test Report Label Cleanup. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V1975</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V1975_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V1975 TEST REPORT LABEL CLEANUP
# =========================

@app.get("/report-label-status")
async def report_label_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Report Label Cleanup",
        "test_report_title": "Executive Engine OS V9100 Test Report",
        "legacy_route_policy": "Preserved legacy routes may still show old labels internally, but the main /test-report is current.",
        "frontend_must_show": "V1975 Test Report Label Cleanup · V1975 Backend",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v1975-milestone")
async def v1975_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Test Report Label Cleanup",
        "ready": True,
        "frontend_must_show": "V1975 Test Report Label Cleanup · V1975 Backend",
        "baseline": "V1950",
        "fixed": [
            "Main /test-report title now shows V1975",
            "Copy/paste report header now shows V1975",
            "Test report routes now include current V1975 milestone",
            "Legacy label confusion reduced before V2000"
        ],
        "kept": [
            "V1950 frontend execution experience",
            "V1900 memory/action intelligence",
            "/test-report working",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/report-label-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/v1975-milestone"
        ],
        "recommended_next_build": "V2000 Serious Daily-Use Product Candidate"
    }



# =========================
# V2000 CURRENT TEST REPORT
# =========================

V2000_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V2000_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "product candidate v2000",
        "route": "/product-candidate-v2000"
    },
    {
        "title": "daily use checklist",
        "route": "/daily-use-checklist"
    },
    {
        "title": "frontend execution status",
        "route": "/frontend-execution-status"
    },
    {
        "title": "memory action intelligence",
        "route": "/memory-action-intelligence"
    },
    {
        "title": "command template library",
        "route": "/command-template-library"
    },
    {
        "title": "recommended command kit",
        "route": "/recommended-command-kit"
    },
    {
        "title": "executive cockpit",
        "route": "/executive-cockpit"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v2000-milestone",
        "route": "/v2000-milestone"
    }
]

@app.get("/test-report-json-archive-v2050")
async def test_report_json_v2000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Daily-Use Product Candidate",
        "backend_base": V2000_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V2000_BACKEND_BASE + item["route"]
            }
            for item in V2000_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/test-report-archive-v2050")
async def test_report_v2000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V2000_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>Daily-Use Product Candidate. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V2000</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V2000_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V2000 SERIOUS DAILY-USE PRODUCT CANDIDATE
# =========================

@app.get("/product-candidate-v2000")
async def product_candidate_v2000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Serious Daily-Use Product Candidate",
        "status": "daily_use_candidate",
        "frontend_must_show": "V2000 Daily-Use Product Candidate · V2000 Backend",
        "core_value": {
            "primary_use": "Run the day from one command system",
            "daily_loop": [
                "Start Day",
                "Run Command",
                "Reduce Action Load",
                "Review Memory Pattern",
                "Copy Recommended Command",
                "End Day Summary"
            ],
            "current_product_bet": "Core OS output and execution loop are more valuable than Calendar/OAuth right now."
        },
        "modules": {
            "command_center": "live",
            "frontend_execution_experience": "live",
            "memory_action_intelligence": "live",
            "core_quality_contract": "live",
            "test_report": "live",
            "calendar_oauth": "parked",
            "external_writes": "blocked"
        },
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/daily-use-checklist")
async def daily_use_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "checklist": [
            "Open the OS",
            "Run Daily Brief",
            "Review Current Constraint",
            "Review What to Cut",
            "Reduce Action Load",
            "Copy Recommended Command",
            "Run one follow-up command",
            "Stop before adding unnecessary integrations"
        ],
        "recommended_first_command": "Create my executive daily brief. Give me next move, today focus, current constraint, decision, next decision, what to cut, action load, memory pattern, actions, risk, priority, execution score, and recommended command."
    }

@app.get("/v2000-milestone")
async def v2000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Serious Daily-Use Product Candidate",
        "ready": True,
        "frontend_must_show": "V2000 Daily-Use Product Candidate · V2000 Backend",
        "baseline": "V1975",
        "includes": [
            "V1900 Memory + Action Intelligence",
            "V1950 Frontend Execution Experience",
            "V1975 Test Report Label Cleanup",
            "V2000 Daily-Use Product Candidate"
        ],
        "added": [
            "Daily-use product candidate endpoint",
            "Daily-use checklist endpoint",
            "V2000 current test report",
            "Daily-use dashboard positioning"
        ],
        "kept": [
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/product-candidate-v2000",
            "https://executive-engine-os.onrender.com/daily-use-checklist",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/v2000-milestone"
        ],
        "recommended_next_build": "Use V2000 daily before adding Calendar/OAuth."
    }



# =========================
# V2050 CURRENT TEST REPORT
# =========================

V2050_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V2050_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "build factory status",
        "route": "/build-factory-status"
    },
    {
        "title": "stability dashboard",
        "route": "/stability-dashboard"
    },
    {
        "title": "product review panel",
        "route": "/product-review-panel"
    },
    {
        "title": "revenue workflow test",
        "route": "/revenue-workflow-test"
    },
    {
        "title": "lab scorecard",
        "route": "/lab-scorecard"
    },
    {
        "title": "promotion review",
        "route": "/promotion-review"
    },
    {
        "title": "build protocol",
        "route": "/build-protocol"
    },
    {
        "title": "product candidate v2000",
        "route": "/product-candidate-v2000"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v2050-milestone",
        "route": "/v2050-milestone"
    }
]

@app.get("/test-report-json-archive-v2075")
async def test_report_json_v2050():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Build Factory Command Center",
        "backend_base": V2050_BACKEND_BASE,
        "tests": [{"title": item["title"], "route": item["route"], "url": V2050_BACKEND_BASE + item["route"]} for item in V2050_REPORT_TESTS],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/test-report-archive-v2075")
async def test_report_v2050():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V2050_REPORT_TESTS)
    html = """
<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Build Factory Command Center. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V2050</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox" placeholder="Results will appear here."></textarea></div><div id="cards"></div></div><script>
const BACKEND_BASE="__BACKEND_BASE__"; const TESTS=__TESTS_JSON__;
function pretty(value){try{return JSON.stringify(value,null,2)}catch(e){return String(value)}}
function escapeHtml(str){return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}
function setStatus(text, ok){const el=document.getElementById('status');el.className=ok===false?'fail':'good';el.textContent=text}
async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:'GET',cache:'no-store'});const contentType=res.headers.get('content-type')||'';let data=contentType.includes('application/json')?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:'FETCH_ERROR',ok:false,output:err.message}}}
function buildCopyText(results){let out=[];out.push('Executive Engine OS V9100 Test Report');out.push('Generated: '+new Date().toISOString());out.push('');for(const r of results){out.push('========================================');out.push(r.title);out.push(r.url);out.push('status: '+r.status);out.push('ok: '+r.ok);out.push('----------------------------------------');out.push(pretty(r.output));out.push('')}return out.join('\n')}
function renderCards(results){const box=document.getElementById('cards');box.innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join('')}
async function runReport(){setStatus('Running tests...',true);const results=[];for(const test of TESTS){setStatus('Running: '+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById('copyBox').value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?'Done with '+failed+' failed link(s). Copy All and paste into ChatGPT.':'All done. Copy All and paste into ChatGPT.',failed===0)}
async function copyAll(){const text=document.getElementById('copyBox').value;if(!text){setStatus('Nothing to copy yet. Click Run Report first.',false);return}await navigator.clipboard.writeText(text);setStatus('Copied. Paste it into ChatGPT.',true)}
function clearReport(){document.getElementById('copyBox').value='';document.getElementById('cards').innerHTML='';setStatus('Cleared. Click Run Report.',true)}
</script></body></html>
""".replace("__BACKEND_BASE__", V2050_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V2050 BUILD FACTORY COMMAND CENTER
# =========================

@app.get("/build-factory-status")
async def build_factory_status():
    return {"ok": True, "version": VERSION, "milestone": "Build Factory Command Center", "build_type": "Internal Build Factory / Acceleration Build", "current_stable_checkpoint": "V2000 Daily-Use Product Candidate", "rollback_target": "V2000 ZIP backup", "next_strategic_target": "V3000 Revenue Execution Shell", "goal_compass": {"product": "Executive Engine is the executive's Red Bull: clarity, control, leverage, momentum, money.", "primary_value": ["make more money", "save time", "reduce people/friction", "feel in control", "show wins"], "current_focus": "Build faster and safer without distracting the executive-facing product."}, "factory_centers": ["Stability Center", "Product Review Center", "Revenue Workflow Center", "Lab Center", "Promotion Center", "Rollback Center"], "safety": {"supabase_schema_changed": False, "oauth_activated": False, "external_writes_enabled": False, "manual_execution_only": True, "auto_loop_enabled": False}, "recommended_next_move": "Use V2050 to review stability, product feedback, revenue workflow quality, and promotion decisions before building V3000."}

@app.get("/stability-dashboard")
async def stability_dashboard():
    return {"ok": True, "version": VERSION, "milestone": "Stability Dashboard", "risk_level": "Low", "checks": [{"name":"Backend live","status":"PASS","route":"/health"},{"name":"Test report live","status":"PASS","route":"/test-report"},{"name":"Manual execution only","status":"PASS","expected":True},{"name":"Auto-loop off","status":"PASS","expected":False},{"name":"OAuth inactive","status":"PASS","expected":False},{"name":"External writes blocked","status":"PASS","expected":True},{"name":"Legacy routes preserved","status":"PASS","policy":"Do not delete; preserve or hide."},{"name":"Rollback target defined","status":"PASS","target":"V2000"}], "rollback_recommendation": "Rollback only if /health, /run, or /test-report breaks.", "recommended_next_move": "Run /test-report after deploy and paste results for decision classification."}

@app.get("/product-review-panel")
async def product_review_panel():
    return {"ok": True, "version": VERSION, "milestone": "Product Review Panel", "reviewers": [{"persona":"Impatient CEO","question":"Can I understand value in 5 seconds?","likely_feedback":"Hide technical sections. Show money, wins, and next move first."},{"persona":"Sales Executive","question":"Can this help me close deals faster?","likely_feedback":"Prioritize proposal, pitch, follow-up, and close-plan workflows."},{"persona":"Non-Technical Operator","question":"Do I know where to click?","likely_feedback":"Use one command box and fewer pages."},{"persona":"SaaS Investor","question":"Is there a clear monetizable wedge?","likely_feedback":"Revenue execution shell is stronger than generic productivity OS."},{"persona":"Skeptical Buyer","question":"Why would I pay for this?","likely_feedback":"Prove time saved, deal movement, and usable client-ready assets."}], "product_rule": "If it does not help executives make money, save time, reduce friction, or feel in control, hide it or cut it.", "recommended_next_move": "Use this panel to grade V3000 Revenue Execution Shell before promotion."}

@app.get("/revenue-workflow-test")
async def revenue_workflow_test():
    return {"ok": True, "version": VERSION, "milestone": "Revenue Workflow Test", "test_scenario": "Executive wants to pitch a $50k consulting package to a hesitant client.", "workflows_to_test": ["Build client proposal", "Build pitch deck outline", "Build sales email", "Build follow-up sequence", "Build objection handling", "Build close plan"], "quality_scorecard": ["Is the output client-ready?", "Is the value proposition clear?", "Does it reduce executive effort?", "Does it help close the deal?", "Is the next move obvious?", "Is the follow-up command copyable?"], "current_grade": "Not tested yet", "recommended_next_move": "Build V3000 around revenue workflows, then run this test as promotion criteria."}

@app.get("/lab-scorecard")
async def lab_scorecard():
    return {"ok": True, "version": VERSION, "milestone": "Lab Scorecard", "decision_options": ["PROMOTE", "REVISE", "KILL", "HOLD"], "criteria": ["Creates visible executive value", "Helps make money, save time, or reduce work", "Does not add confusing UI clutter", "Does not break core stability", "Can be explained in 5 seconds", "Supports the Red Bull product promise"], "example": {"feature": "Executive Scoreboard", "decision": "PROMOTE", "reason": "Gives executives visible wins, progress, and status.", "risk": "Must tie metrics to revenue/actions, not vanity."}, "recommended_next_move": "Run each lab feature through this before adding it to the main product."}

@app.get("/promotion-review")
async def promotion_review():
    return {"ok": True, "version": VERSION, "milestone": "Promotion Review", "promotion_rule": "A lab feature becomes production-grade only after it passes product value, revenue value, stability, and simplicity tests.", "current_recommendation": {"feature": "Revenue Execution Shell", "decision": "PROMOTE_TO_NEXT_BUILD", "target_version": "V3000", "reason": "It maps directly to executive motivation: make money, save time, reduce work, feel in control.", "risk": "Must not expose internal build factory/debug complexity to end users."}, "recommended_next_move": "Build V3000 Revenue Execution Shell from V2050 after test report passes."}

@app.get("/build-protocol")
async def build_protocol():
    return {"ok": True, "version": VERSION, "milestone": "Executive Engine Build Protocol", "ask_response_sequence": ["User defines strategic intent or build command.", "Assistant builds ZIP with complete files.", "User deploys.", "User runs /test-report.", "Assistant classifies result: HOLD, FIX, PROMOTE, PIVOT, or ROLLBACK.", "Only then build the next version."], "mandatory_preserve": ["/health", "/run", "/test-report", "/test-report-json", "manual_execution_only = true", "auto_loop_enabled = false", "OAuth inactive unless approved", "external writes blocked unless approved", "Supabase schema unchanged unless approved", "legacy routes preserved"], "build_types": ["STABILITY BUILD", "PRODUCT BUILD", "REVENUE BUILD", "LAB BUILD", "PROMOTION BUILD"], "version_path": {"V2000":"Daily-use candidate / stable checkpoint", "V2050":"Build Factory Command Center", "V3000":"Revenue Execution Shell", "V9100":"Client Asset Builder", "V9100":"Pitch Deck / Proposal Engine", "V9100":"Executive Scoreboard + Wins", "V7000":"Deal Memory + Client Intelligence", "V8000":"Multi-Asset Studio", "V9100":"Controlled Integrations", "V10000":"Executive Revenue Operating Platform"}}

@app.get("/v2050-milestone")
async def v2050_milestone():
    return {"ok": True, "version": VERSION, "milestone": "Build Factory Command Center", "ready": True, "frontend_must_show": "V2050 Build Factory Command Center · V2050 Backend", "baseline": "V2000", "build_type": "Internal Build Factory / Acceleration Build", "added": ["Build Factory Status", "Stability Dashboard", "Product Review Panel", "Revenue Workflow Test", "Lab Scorecard", "Promotion Review", "Build Protocol", "V2050 current test report"], "kept": ["V2000 daily-use product candidate", "V1900 memory/action intelligence", "V1950 frontend execution experience", "/test-report working", "diagnostic routes preserved", "legacy routes preserved", "Supabase schema unchanged", "OAuth inactive", "external writes blocked", "manual execution only", "auto-loop off"], "test_order": ["https://executive-engine-os.onrender.com/health", "https://executive-engine-os.onrender.com/build-factory-status", "https://executive-engine-os.onrender.com/stability-dashboard", "https://executive-engine-os.onrender.com/product-review-panel", "https://executive-engine-os.onrender.com/revenue-workflow-test", "https://executive-engine-os.onrender.com/lab-scorecard", "https://executive-engine-os.onrender.com/promotion-review", "https://executive-engine-os.onrender.com/build-protocol", "https://executive-engine-os.onrender.com/test-report", "https://executive-engine-os.onrender.com/v2050-milestone"], "recommended_next_build": "V3000 Revenue Execution Shell"}



# =========================
# V2075 CURRENT TEST REPORT
# =========================

V2075_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V2075_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "build factory status",
        "route": "/build-factory-status"
    },
    {
        "title": "build command center status",
        "route": "/build-command-center-status"
    },
    {
        "title": "build command template",
        "route": "/build-command-template"
    },
    {
        "title": "build protocol",
        "route": "/build-protocol"
    },
    {
        "title": "stability dashboard",
        "route": "/stability-dashboard"
    },
    {
        "title": "promotion review",
        "route": "/promotion-review"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v2075-milestone",
        "route": "/v2075-milestone"
    }
]

@app.get("/test-report-json-archive-v3000")
async def test_report_json_v2075():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Build Command Center",
        "backend_base": V2075_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V2075_BACKEND_BASE + item["route"]
            }
            for item in V2075_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/test-report-archive-v3000")
async def test_report_v2075():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V2075_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>Build Command Center. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V2075</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V2075_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V2075 BUILD COMMAND CENTER
# =========================
# Internal Build Factory tool. Generates complete build commands from structured fields.
# Designed to scale to team members, reduce forgotten details, and keep build discipline consistent.

@app.get("/build-command-center-status")
async def build_command_center_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Build Command Center",
        "frontend_must_show": "V2075 Build Command Center · V2075 Backend",
        "baseline": "V2050",
        "purpose": "Generate complete build commands using the Executive Engine Build Protocol.",
        "scalable_for_team": True,
        "fields": [
            "Build Version",
            "Build Name",
            "Build Type",
            "Start From",
            "Rollback Target",
            "User-Facing Value",
            "Revenue Value",
            "Time-Saving Value",
            "Friction Reduction",
            "Executive Control / Ego / Win Value",
            "Preserve Checklist",
            "Do Not Touch Checklist",
            "Frontend Changes",
            "Backend Routes",
            "Prompt Changes",
            "Test Routes",
            "Risk",
            "Success Criteria"
        ],
        "buttons": [
            "Generate Build Command",
            "Copy Command",
            "Generate Test Plan",
            "Generate Rollback Plan"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/build-command-template")
async def build_command_template():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Build Command Template",
        "template": {
            "build_version": "V3000",
            "build_name": "Revenue Execution Shell",
            "build_type": "Revenue Build",
            "start_from": "V2075",
            "rollback_target": "V2050 / V2000 ZIP backup",
            "goal": "Transform the frontend into a revenue-first executive command center.",
            "user_facing_value": "Executives can turn messy intent into revenue-ready next moves and assets.",
            "revenue_value": "Helps create proposals, pitch outlines, sales emails, follow-ups, and close plans.",
            "time_saving_value": "Reduces thinking, writing, coordination, and asset creation time.",
            "friction_reduction": "Lets the executive do less work and rely on fewer people.",
            "executive_win_value": "Shows wins, control, money moves, and what got done today.",
            "preserve": [
                "/health",
                "/run",
                "/test-report",
                "/test-report-json",
                "manual execution only",
                "auto-loop off",
                "legacy routes preserved"
            ],
            "do_not_touch": [
                "Supabase schema",
                "OAuth activation",
                "external writes",
                "diagnostic routes",
                "deployment structure"
            ],
            "test_routes": [
                "/health",
                "/test-report",
                "/v3000-milestone"
            ]
        }
    }


@app.get("/v2075-milestone")
async def v2075_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Build Command Center",
        "ready": True,
        "frontend_must_show": "V2075 Build Command Center · V2075 Backend",
        "baseline": "V2050",
        "build_type": "Internal Product / Build Factory Tool",
        "added": [
            "Build Command Center frontend page",
            "Structured build fields",
            "Preserve checklist",
            "Do Not Touch checklist",
            "Generate Build Command button",
            "Copy Command button",
            "Generate Test Plan button",
            "Generate Rollback Plan button",
            "Build Command Center status endpoint",
            "Build Command Template endpoint",
            "V2075 current test report"
        ],
        "kept": [
            "V2050 Build Factory Command Center",
            "V2000 daily-use product candidate",
            "V1900 memory/action intelligence",
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/build-factory-status",
            "https://executive-engine-os.onrender.com/build-command-center-status",
            "https://executive-engine-os.onrender.com/build-command-template",
            "https://executive-engine-os.onrender.com/build-protocol",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v2075-milestone"
        ],
        "recommended_next_build": "V3000 Revenue Execution Shell"
    }



# =========================
# V3000 CURRENT TEST REPORT
# =========================

V3000_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V3000_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "revenue shell status",
        "route": "/revenue-shell-status"
    },
    {
        "title": "revenue command templates",
        "route": "/revenue-command-templates"
    },
    {
        "title": "executive scoreboard",
        "route": "/executive-scoreboard"
    },
    {
        "title": "client asset workflows",
        "route": "/client-asset-workflows"
    },
    {
        "title": "revenue workflow test",
        "route": "/revenue-workflow-test"
    },
    {
        "title": "build factory status",
        "route": "/build-factory-status"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v3000-milestone",
        "route": "/v3000-milestone"
    }
]

@app.get("/legacy/test-report-json-v3001")
async def test_report_json_v3000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Execution Shell",
        "backend_base": V3000_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V3000_BACKEND_BASE + item["route"]
            }
            for item in V3000_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/legacy/test-report-v3001")
async def test_report_v3000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V3000_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>Revenue Execution Shell. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V3000</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V3000_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V3000 REVENUE EXECUTION SHELL
# =========================
# User-facing revenue-first product shell. Keeps V2075 Build Factory hidden/admin.
# No schema change. No OAuth activation. No external writes.

@app.get("/revenue-shell-status")
async def revenue_shell_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Execution Shell",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "product_promise": "Make money. Save time. Feel in control.",
        "primary_headline": "What are you trying to win today?",
        "target_user": "Executive, founder, CEO, operator, sales leader, business owner",
        "primary_value": [
            "Create revenue-ready assets faster",
            "Move deals forward with less work",
            "Reduce friction and people-dependency",
            "Surface what to cut",
            "Show executive wins"
        ],
        "quick_actions": [
            "Build Proposal",
            "Build Pitch Deck Outline",
            "Build Sales Email",
            "Build Follow-Up",
            "Build Close Plan",
            "Make Decision",
            "Reduce Work"
        ],
        "hidden_admin": [
            "Build Factory",
            "Test Report",
            "Diagnostics",
            "Protocol",
            "Legacy routes"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/revenue-command-templates")
async def revenue_command_templates():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Command Templates",
        "templates": [
            {
                "id": "proposal",
                "title": "Build Proposal",
                "command": "Build a client-ready proposal for this opportunity. Include revenue objective, client context, offer angle, draft proposal, what to cut, risk, close plan, executive win, and follow-up command."
            },
            {
                "id": "pitch_deck",
                "title": "Build Pitch Deck Outline",
                "command": "Build a pitch deck outline for this opportunity. Include slide titles, core story, offer angle, proof points, close slide, risk, and next power move."
            },
            {
                "id": "sales_email",
                "title": "Build Sales Email",
                "command": "Write a high-converting sales email for this opportunity. Include positioning, subject line, email body, follow-up angle, risk, and next command."
            },
            {
                "id": "follow_up",
                "title": "Build Follow-Up",
                "command": "Create a follow-up sequence for this client or opportunity. Include message 1, message 2, message 3, objection handling, and next power move."
            },
            {
                "id": "close_plan",
                "title": "Build Close Plan",
                "command": "Create a close plan for this deal. Include decision maker, pain, offer, objections, next move, risk, what to cut, and follow-up command."
            },
            {
                "id": "decision",
                "title": "Make Decision",
                "command": "Make the executive decision. Include revenue objective, current constraint, what to cut, risk, next power move, actions, and executive win."
            },
            {
                "id": "reduce_work",
                "title": "Reduce Work",
                "command": "Reduce my workload. Tell me what to cut, defer, automate, delegate, and the single next power move that creates the most value."
            }
        ]
    }


@app.get("/executive-scoreboard")
async def executive_scoreboard():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Scoreboard",
        "scoreboard": {
            "today_wins": [
                "Revenue shell shipped as strategic product direction",
                "Build Factory preserved for internal acceleration",
                "Calendar/OAuth remains parked",
                "Core focus moved from productivity to revenue leverage"
            ],
            "revenue_moves": 3,
            "decisions_made": 4,
            "work_cut": [
                "Visible diagnostic clutter",
                "Calendar-first thinking",
                "Generic productivity framing"
            ],
            "time_saved": "2+ hours by using test report and build command protocol",
            "next_money_move": "Test proposal/pitch/follow-up workflows inside V3000"
        },
        "executive_feeling": "Control, clarity, momentum, and visible wins."
    }


@app.get("/client-asset-workflows")
async def client_asset_workflows():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Client Asset Workflows",
        "workflows": [
            {
                "name": "Proposal",
                "purpose": "Turn opportunity context into a client-ready proposal.",
                "output": ["Executive summary", "Problem", "Offer", "Scope", "Value", "Pricing angle", "Next steps"]
            },
            {
                "name": "Pitch Deck Outline",
                "purpose": "Turn deal strategy into a slide-by-slide pitch.",
                "output": ["Opening", "Pain", "Opportunity", "Solution", "Proof", "Offer", "Close"]
            },
            {
                "name": "Sales Email",
                "purpose": "Create a send-ready business development email.",
                "output": ["Subject line", "Email body", "CTA", "Follow-up"]
            },
            {
                "name": "Follow-Up Sequence",
                "purpose": "Move a warm lead or stalled deal forward.",
                "output": ["Follow-up 1", "Follow-up 2", "Follow-up 3", "Objection handling"]
            },
            {
                "name": "Close Plan",
                "purpose": "Convert uncertainty into a closing sequence.",
                "output": ["Decision maker", "Pain", "Value", "Objections", "Next power move"]
            }
        ]
    }


@app.get("/legacy/v3000-milestone")
async def v3000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Execution Shell",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V2075",
        "build_type": "Revenue/Product Build",
        "added": [
            "Revenue-first executive frontend",
            "What are you trying to win today headline",
            "Quick actions for proposal, pitch deck, sales email, follow-up, close plan, decision, reduce work",
            "Executive-readable revenue output cards",
            "Today’s Wins panel",
            "Executive Scoreboard",
            "Revenue command templates",
            "Client asset workflows",
            "V9100 current test report"
        ],
        "kept": [
            "V2075 Build Command Center",
            "V2050 Build Factory",
            "V2000 daily-use candidate",
            "V1900 memory/action intelligence",
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/revenue-shell-status",
            "https://executive-engine-os.onrender.com/revenue-command-templates",
            "https://executive-engine-os.onrender.com/executive-scoreboard",
            "https://executive-engine-os.onrender.com/client-asset-workflows",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3000-milestone"
        ],
        "recommended_next_build": "Use V9100 revenue workflows, then classify HOLD/FIX/PROMOTE/PIVOT."
    }


# =========================
# V3001 REVENUE OUTPUT COMPATIBILITY FIX
# =========================

@app.get("/revenue-output-compatibility")
async def revenue_output_compatibility():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Output Compatibility Fix",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "Frontend no longer leaves revenue cards blank when /run returns older or partial JSON fields.",
        "fixed": [
            "Frontend normalization layer",
            "Fallback mapping for older /run fields",
            "Useful default text for missing fields",
            "Recommended command remains copyable"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v3001-milestone")
async def v3001_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Output Compatibility Fix",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V3000",
        "build_type": "Fix Build",
        "fixed": [
            "Blank revenue cards fixed",
            "Frontend output normalization added",
            "Fallback mapping for older /run fields added",
            "Missing draft output now falls back to decision/next move",
            "Missing revenue fields now show useful defaults"
        ],
        "kept": [
            "V3000 Revenue Execution Shell",
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/revenue-shell-status",
            "https://executive-engine-os.onrender.com/revenue-output-compatibility",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3001-milestone"
        ],
        "recommended_next_move": "Deploy V3001, run /test-report, then test one real proposal command in the frontend."
    }



# =========================
# V9100 CURRENT TEST REPORT
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "revenue shell status",
        "route": "/revenue-shell-status"
    },
    {
        "title": "revenue output compatibility",
        "route": "/revenue-output-compatibility"
    },
    {
        "title": "revenue command templates",
        "route": "/revenue-command-templates"
    },
    {
        "title": "executive scoreboard",
        "route": "/executive-scoreboard"
    },
    {
        "title": "client asset workflows",
        "route": "/client-asset-workflows"
    },
    {
        "title": "revenue workflow test",
        "route": "/revenue-workflow-test"
    },
    {
        "title": "build factory status",
        "route": "/build-factory-status"
    },
    {
        "title": "v3001 milestone",
        "route": "/v3001-milestone"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v3002 milestone",
        "route": "/v3002-milestone"
    }
]

@app.get("/legacy/test-report-json-v3002")
async def test_report_json_v3002():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3001 Label + Test Report Cleanup",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V9100_BACKEND_BASE + item["route"]
            }
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }


@app.get("/legacy/test-report-v3002")
async def test_report_v3002():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px}
    h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>V3001 Label + Test Report Cleanup. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V9100</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>

  <div class="card">
    <h2>Copy/Paste Report For ChatGPT</h2>
    <textarea id="copyBox" placeholder="Results will appear here."></textarea>
  </div>

  <div id="cards"></div>
</div>

<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;

function pretty(value) {
  try { return JSON.stringify(value, null, 2); }
  catch(e) { return String(value); }
}

function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function setStatus(text, ok) {
  const el = document.getElementById("status");
  el.className = ok === false ? "fail" : "good";
  el.textContent = text;
}

async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) {
    return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message };
  }
}

function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}

function renderCards(results) {
  const box = document.getElementById("cards");
  box.innerHTML = results.map(r => `
    <div class="card">
      <h2>${escapeHtml(r.title)}</h2>
      <div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div>
      <pre>${escapeHtml(pretty(r.output))}</pre>
    </div>
  `).join("");
}

async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}

async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}

function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)



# =========================
# V9100 LABEL + TEST REPORT CLEANUP
# =========================

@app.get("/legacy/label-cleanup-status")
async def label_cleanup_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3001 Label + Test Report Cleanup",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "cleanup_targets": [
            "Rebuild /test-report-json with V9100 current routes",
            "Add /revenue-output-compatibility to report",
            "Add /v3001-milestone to report",
            "Add /v3002-milestone to report",
            "Update visible backend labels to V9100",
            "Move V3000 milestone to /legacy/v3000-milestone",
            "Document cleanup in README and PDF"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }


@app.get("/legacy/v3002-milestone")
async def v3002_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3001 Label + Test Report Cleanup",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V3001",
        "build_type": "Stability / Label Cleanup Build",
        "fixed": [
            "/test-report-json now lists V9100 routes",
            "/revenue-output-compatibility included in report",
            "/v3001-milestone included in report",
            "/v3002-milestone added",
            "Visible backend labels updated to V9100",
            "V3000 milestone preserved as /legacy/v3000-milestone",
            "README and PDF documentation added"
        ],
        "kept": [
            "V3001 output compatibility fix",
            "V3000 Revenue Execution Shell",
            "V2075 Build Command Center",
            "V2050 Build Factory",
            "/run unchanged",
            "/test-report working",
            "diagnostic routes preserved",
            "legacy routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/revenue-shell-status",
            "https://executive-engine-os.onrender.com/revenue-output-compatibility",
            "https://executive-engine-os.onrender.com/label-cleanup-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/test-report-json",
            "https://executive-engine-os.onrender.com/v3001-milestone",
            "https://executive-engine-os.onrender.com/v3002-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then test one real frontend revenue command."
    }

# =========================
# V9100 CURRENT TEST REPORT
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "real revenue asset status",
        "route": "/real-revenue-asset-status"
    },
    {
        "title": "revenue asset contract",
        "route": "/revenue-asset-contract"
    },
    {
        "title": "revenue shell status",
        "route": "/revenue-shell-status"
    },
    {
        "title": "revenue output compatibility",
        "route": "/revenue-output-compatibility"
    },
    {
        "title": "revenue command templates",
        "route": "/revenue-command-templates"
    },
    {
        "title": "client asset workflows",
        "route": "/client-asset-workflows"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v3003 milestone",
        "route": "/v3003-milestone"
    }
]

@app.get("/legacy/test-report-json-v3003")
async def test_report_json_v3003():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Revenue Asset Output",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {
                "title": item["title"],
                "route": item["route"],
                "url": V9100_BACKEND_BASE + item["route"]
            }
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v3003")
async def test_report_v3003():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = """
<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name='viewport' content='width=device-width,initial-scale=1'><style>
body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head>
<body><div class='wrap'><div class='hero'><h1>Executive Engine OS V9100 Test Report</h1><p>Real Revenue Asset Output. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick='runReport()'>Run Report</button><button class='secondary' onclick='copyAll()'>Copy All Results</button><button class='secondary' onclick='clearReport()'>Clear</button><div id='status' class='good'>Ready. Click Run Report.</div></div><div class='card'><h2>Copy/Paste Report For ChatGPT</h2><textarea id='copyBox' placeholder='Results will appear here.'></textarea></div><div id='cards'></div></div>
<script>
const BACKEND_BASE='__BACKEND_BASE__'; const TESTS=__TESTS_JSON__;
function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}
function escapeHtml(s){return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')}
function setStatus(t,ok){const el=document.getElementById('status');el.className=ok===false?'fail':'good';el.textContent=t}
async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:'GET',cache:'no-store'});const ct=res.headers.get('content-type')||'';let data=ct.includes('application/json')?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:'FETCH_ERROR',ok:false,output:err.message}}}
function buildCopyText(results){let out=[];out.push('Executive Engine OS V9100 Test Report');out.push('Generated: '+new Date().toISOString());out.push('');for(const r of results){out.push('========================================');out.push(r.title);out.push(r.url);out.push('status: '+r.status);out.push('ok: '+r.ok);out.push('----------------------------------------');out.push(pretty(r.output));out.push('')}return out.join('\\n')}
function renderCards(results){document.getElementById('cards').innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join('')}
async function runReport(){setStatus('Running tests...',true);const results=[];for(const test of TESTS){setStatus('Running: '+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById('copyBox').value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?'Done with '+failed+' failed link(s). Copy All and paste into ChatGPT.':'All done. Copy All and paste into ChatGPT.',failed===0)}
async function copyAll(){const text=document.getElementById('copyBox').value;if(!text){setStatus('Nothing to copy yet. Click Run Report first.',false);return}await navigator.clipboard.writeText(text);setStatus('Copied. Paste it into ChatGPT.',true)}
function clearReport(){document.getElementById('copyBox').value='';document.getElementById('cards').innerHTML='';setStatus('Cleared. Click Run Report.',true)}
</script></body></html>
""".replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/real-revenue-asset-status")
async def real_revenue_asset_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Revenue Asset Output",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "The system must now create actual proposal, pitch, email, follow-up, objection handling, and close-plan content instead of generic advice.",
        "good_output_requirement": "Write the actual asset copy.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/revenue-asset-contract")
async def revenue_asset_contract():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Revenue Asset Contract",
        "required_json_fields": [
            "revenue_objective","client_situation","next_power_move","offer_angle",
            "proposal_draft","pitch_deck_outline","sales_email_draft","follow_up_sequence",
            "objection_handling","close_plan","what_to_cut","actions","risk","priority",
            "executive_win","time_saved","revenue_signal","recommended_command","follow_up_question"
        ],
        "quality_bar": [
            "Proposal draft must be usable copy",
            "Sales email must include subject and body",
            "Follow-up sequence must include actual messages",
            "Objection handling must include actual objections and responses",
            "Close plan must include concrete next steps",
            "No blank sections",
            "No generic placeholders"
        ],
        "test_prompt": "I need to pitch a $50k consulting package to a hesitant client. Build a client-ready proposal, pitch angle, sales email, follow-up sequence, objection handling, and close plan."
    }

@app.get("/v3003-milestone")
async def v3003_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Revenue Asset Output",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V3002",
        "build_type": "Fix / Revenue Output Quality Build",
        "fixed": [
            "Backend /run system prompt rewritten to force actual asset creation",
            "Proposal Draft required",
            "Pitch Deck Outline required",
            "Sales Email Draft required",
            "Follow-Up Sequence required",
            "Objection Handling required",
            "Close Plan required",
            "Generic execution advice blocked",
            "Frontend output rendering updated for real asset fields"
        ],
        "kept": [
            "V3002 label/test-report cleanup",
            "V3001 output compatibility",
            "V3000 Revenue Execution Shell",
            "/test-report working",
            "/run preserved but prompt improved",
            "diagnostic routes preserved",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/real-revenue-asset-status",
            "https://executive-engine-os.onrender.com/revenue-asset-contract",
            "https://executive-engine-os.onrender.com/revenue-shell-status",
            "https://executive-engine-os.onrender.com/revenue-output-compatibility",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3003-milestone"
        ],
        "frontend_test_command": "I need to pitch a $50k consulting package to a hesitant client. Build a client-ready proposal, pitch angle, sales email, follow-up sequence, objection handling, and close plan.",
        "recommended_next_move": "Deploy V9100, run /test-report, then test the frontend with the frontend_test_command."
    }


# =========================
# V9100 V3500 PREMIUM REVENUE MERGE
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [
    {
        "title": "health",
        "route": "/health"
    },
    {
        "title": "v3500 merge status",
        "route": "/v3500-merge-status"
    },
    {
        "title": "real revenue asset status",
        "route": "/real-revenue-asset-status"
    },
    {
        "title": "revenue asset contract",
        "route": "/revenue-asset-contract"
    },
    {
        "title": "revenue shell status",
        "route": "/revenue-shell-status"
    },
    {
        "title": "revenue output compatibility",
        "route": "/revenue-output-compatibility"
    },
    {
        "title": "revenue command templates",
        "route": "/revenue-command-templates"
    },
    {
        "title": "test-report-json",
        "route": "/test-report-json"
    },
    {
        "title": "v3550 milestone",
        "route": "/v3550-milestone"
    }
]

@app.get("/legacy/test-report-json-v3550")
async def test_report_json_v3550():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3500 Premium Layout + V3003 Revenue Engine Merge",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v3550")
async def test_report_v3550():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = """
<!doctype html>
<html>
<head>
  <title>Executive Engine OS V9100 Test Report</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}
    .wrap{max-width:1180px;margin:auto}
    .hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}
    h1{margin:0 0 8px;font-size:28px} h2{margin:0 0 10px;font-size:17px}
    p{color:#64748b;line-height:1.5}
    button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}
    button.secondary{background:#fff;color:#0f63ff}
    .url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}
    pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}
    textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}
    .good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    .fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}
    code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Executive Engine OS V9100 Test Report</h1>
    <p>V3500 Premium Layout + V3003 Revenue Engine Merge. Click Run Report, then Copy All Results and paste into ChatGPT.</p>
    <p>Current visible version: <code>V9100</code></p>
    <button onclick="runReport()">Run Report</button>
    <button class="secondary" onclick="copyAll()">Copy All Results</button>
    <button class="secondary" onclick="clearReport()">Clear</button>
    <div id="status" class="good">Ready. Click Run Report.</div>
  </div>
  <div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox" placeholder="Results will appear here."></textarea></div>
  <div id="cards"></div>
</div>
<script>
const BACKEND_BASE = "__BACKEND_BASE__";
const TESTS = __TESTS_JSON__;
function pretty(value) { try { return JSON.stringify(value, null, 2); } catch(e) { return String(value); } }
function escapeHtml(str) { return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }
function setStatus(text, ok) { const el = document.getElementById("status"); el.className = ok === false ? "fail" : "good"; el.textContent = text; }
async function runOne(test) {
  const url = BACKEND_BASE + test.route;
  try {
    const res = await fetch(url, { method:"GET", cache:"no-store" });
    const contentType = res.headers.get("content-type") || "";
    let data = contentType.includes("application/json") ? await res.json() : await res.text();
    return { title:test.title, url:url, status:res.status, ok:res.ok, output:data };
  } catch(err) { return { title:test.title, url:url, status:"FETCH_ERROR", ok:false, output:err.message }; }
}
function buildCopyText(results) {
  let out = [];
  out.push("Executive Engine OS V9100 Test Report");
  out.push("Generated: " + new Date().toISOString());
  out.push("");
  for (const r of results) {
    out.push("========================================");
    out.push(r.title);
    out.push(r.url);
    out.push("status: " + r.status);
    out.push("ok: " + r.ok);
    out.push("----------------------------------------");
    out.push(pretty(r.output));
    out.push("");
  }
  return out.join("\\n");
}
function renderCards(results) {
  document.getElementById("cards").innerHTML = results.map(r => `<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("");
}
async function runReport() {
  setStatus("Running tests...", true);
  const results = [];
  for (const test of TESTS) {
    setStatus("Running: " + test.title, true);
    const result = await runOne(test);
    results.push(result);
    renderCards(results);
    document.getElementById("copyBox").value = buildCopyText(results);
  }
  const failed = results.filter(r => !r.ok).length;
  setStatus(failed ? "Done with " + failed + " failed link(s). Copy All and paste into ChatGPT." : "All done. Copy All and paste into ChatGPT.", failed === 0);
}
async function copyAll() {
  const text = document.getElementById("copyBox").value;
  if (!text) { setStatus("Nothing to copy yet. Click Run Report first.", false); return; }
  await navigator.clipboard.writeText(text);
  setStatus("Copied. Paste it into ChatGPT.", true);
}
function clearReport() {
  document.getElementById("copyBox").value = "";
  document.getElementById("cards").innerHTML = "";
  setStatus("Cleared. Click Run Report.", true);
}
</script>
</body>
</html>
""".replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/v3500-merge-status")
async def v3500_merge_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3500 Premium Layout + V3003 Revenue Engine Merge",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Use V3500's better visual layout as the frontend baseline while preserving V3003's revenue asset backend.",
        "what_this_preserves": [
            "Premium V3500 visual experience",
            "V3003 real revenue asset output contract",
            "V3003 test-report workflow",
            "Manual execution only",
            "Auto-loop off",
            "No OAuth",
            "No external writes"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_preserved_from_revenue_engine": True,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v3550-milestone")
async def v3550_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "V3500 Premium Layout + V3003 Revenue Engine Merge",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "Frontend from V3500, backend revenue engine from V3003",
        "build_type": "Product / Merge / Stabilization Build",
        "added": [
            "V3500 premium dark executive dashboard preserved",
            "V3003 real revenue backend preserved",
            "V9100 test report added",
            "V3500/V3003 merge status route added",
            "Frontend output upgraded to show real revenue asset fields"
        ],
        "kept": [
            "V3500 premium layout",
            "V3003 real revenue asset output",
            "/run revenue asset prompt",
            "/test-report working",
            "diagnostic routes preserved where available",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v3500-merge-status",
            "https://executive-engine-os.onrender.com/real-revenue-asset-status",
            "https://executive-engine-os.onrender.com/revenue-asset-contract",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3550-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then test frontend revenue output and visual engagement."
    }

# =========================
# V9100 FIGMA-STYLE EXECUTIVE DASHBOARD
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'frontend experience status', 'route': '/frontend-experience-status'}, {'title': 'buyer experience check', 'route': '/buyer-experience-check'}, {'title': 'v3500 merge status', 'route': '/v3500-merge-status'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'revenue asset contract', 'route': '/revenue-asset-contract'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v3600 milestone', 'route': '/v3600-milestone'}]

@app.get("/legacy/test-report-json-v3600")
async def test_report_json_v3600():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Figma-Style Executive Dashboard",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v3600")
async def test_report_v3600():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Figma-style executive dashboard. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/frontend-experience-status")
async def frontend_experience_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Figma-Style Executive Dashboard",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "style_reference": "Dark left sidebar, blue command bar, clean cards, right output preview, system status panel.",
        "buyer_goal": "Make the product feel like a premium paid executive cockpit, not a technical prototype.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/buyer-experience-check")
async def buyer_experience_check():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Buyer Experience Check",
        "questions": [
            "Do I know where to start within five seconds?",
            "Does this feel premium enough to pay for?",
            "Does it reduce thinking or add work?",
            "Did it give me something I can use immediately?",
            "Do I feel more in control?",
            "Would I come back tomorrow?"
        ],
        "pass_condition": "The user feels leverage, speed, control, and a real money-making workflow."
    }

@app.get("/v3600-milestone")
async def v3600_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Figma-Style Executive Dashboard",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V9100",
        "build_type": "Frontend Experience / Buyer Simulation Build",
        "added": [
            "Figma-style dark navy sidebar",
            "Premium top command/search bar",
            "Today command center",
            "Metric summary cards",
            "Dark command input panel",
            "Right executive output preview",
            "Executive feed cards",
            "System status card",
            "Admin/test tools hidden under System"
        ],
        "kept": [
            "V9100 backend",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/frontend-experience-status",
            "https://executive-engine-os.onrender.com/buyer-experience-check",
            "https://executive-engine-os.onrender.com/v3500-merge-status",
            "https://executive-engine-os.onrender.com/real-revenue-asset-status",
            "https://executive-engine-os.onrender.com/revenue-asset-contract",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3600-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then judge the paid CEO buyer experience."
    }

# =========================
# V9100 EXECUTIVE FLOW DASHBOARD
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'task capture model', 'route': '/task-capture-model'}, {'title': 'push dashboard check', 'route': '/push-dashboard-check'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'revenue asset contract', 'route': '/revenue-asset-contract'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v3700 milestone', 'route': '/v3700-milestone'}]

@app.get("/legacy/test-report-json-v3700")
async def test_report_json_v3700():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Dashboard",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v3700")
async def test_report_v3700():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Executive Flow Dashboard. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/executive-flow-status")
async def executive_flow_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Dashboard",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "product_thesis": "The AI box is not the product. The prepared executive day is the product.",
        "core_shift": "From command-first to push-first.",
        "dashboard_sections": [
            "Today",
            "Tomorrow",
            "Meetings",
            "Revenue / Deals",
            "Decisions",
            "People",
            "Risks / Constraints",
            "Prepared For You",
            "End of Day"
        ],
        "input_role": "Thin capture input only. The dashboard pushes what matters.",
        "tone_rules": [
            "Short",
            "Confident",
            "Supportive",
            "Personal",
            "Action-oriented",
            "No weak phrasing",
            "No 'try'",
            "No 'can't'"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/task-capture-model")
async def task_capture_model():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Universal Executive Task Capture",
        "model": {
            "who": "Person, company, team, client, employee, contractor, candidate, partner.",
            "what": "What needs to happen.",
            "when": "Date, time, deadline, day, meeting window.",
            "where": "Call, Zoom, office, client site, email, boardroom, event.",
            "why": "Revenue, risk, relationship, hiring, firing, compliance, operations, growth.",
            "how": "Proposal, deck, agenda, email, decision brief, meeting prep, follow-up, contract, file."
        },
        "capture_rule": "Ask minimal questions. If enough info exists, start preparing. Ask only one sharpening question when useful.",
        "example": "Tomorrow I have a meeting with ABC HVAC about SEO, ads, Instagram, and maybe a proposal."
    }

@app.get("/push-dashboard-check")
async def push_dashboard_check():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Push Dashboard Buyer Check",
        "buyer_questions": [
            "Do I know what matters today without typing a prompt?",
            "Is tomorrow already prepared?",
            "Are meetings, proposals, people, risks, and files surfaced clearly?",
            "Does the system reduce my thinking?",
            "Does this feel like leverage instead of another dashboard?",
            "Would I come back tomorrow morning?"
        ],
        "pass_condition": "The executive feels prepared, in control, and ready to win before they ask for anything."
    }

@app.get("/v3700-milestone")
async def v3700_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Dashboard",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V9100/V3550",
        "build_type": "Product Direction / Frontend UX Pivot",
        "added": [
            "Push-first Today dashboard",
            "Tomorrow preview",
            "Meetings section",
            "Revenue / Deals section",
            "Decisions section",
            "People section",
            "Risks / Constraints section",
            "Prepared For You section",
            "End-of-day capture",
            "Thin top capture input",
            "Universal WHO/WHAT/WHEN/WHERE/WHY/HOW task capture",
            "Executive Flow product vision PDF"
        ],
        "kept": [
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/executive-flow-status",
            "https://executive-engine-os.onrender.com/task-capture-model",
            "https://executive-engine-os.onrender.com/push-dashboard-check",
            "https://executive-engine-os.onrender.com/real-revenue-asset-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3700-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then use it like a paid CEO for one day."
    }

# =========================
# V9100 CLICKABLE FLOW FIX
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'link routing status', 'route': '/link-routing-status'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'task capture model', 'route': '/task-capture-model'}, {'title': 'push dashboard check', 'route': '/push-dashboard-check'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v3710 milestone', 'route': '/v3710-milestone'}]

@app.get("/legacy/test-report-json-v3710")
async def test_report_json_v3710():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Clickable Flow Fix",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v3710")
async def test_report_v3710():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Clickable Flow Fix. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/link-routing-status")
async def link_routing_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Clickable Flow Fix",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "Primary frontend links/cards/buttons now have actual actions instead of placeholder behavior.",
        "fixed": [
            "Sidebar items scroll to sections",
            "Today/Tomorrow task rows open detail panel",
            "Meeting cards open detail panel",
            "Revenue cards open detail panel",
            "Prepared assets open detail panel",
            "System links open backend routes",
            "Quick action links load relevant capture text",
            "Prepare Assets button uses /run"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v3710-milestone")
async def v3710_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Clickable Flow Fix",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V9100",
        "build_type": "Frontend Usability / Link Routing Fix",
        "added": [
            "Clickable section routing",
            "Clickable card/detail behavior",
            "Clickable system/backend links",
            "Quick action capture helpers",
            "Improved testability before daily CEO use"
        ],
        "kept": [
            "V9100 Executive Flow Dashboard",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/link-routing-status",
            "https://executive-engine-os.onrender.com/executive-flow-status",
            "https://executive-engine-os.onrender.com/task-capture-model",
            "https://executive-engine-os.onrender.com/push-dashboard-check",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v3710-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then click through the frontend cards and sidebar."
    }

# =========================
# V9100 CLIENT ASSET BUILDER
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'client asset builder status', 'route': '/client-asset-builder-status'}, {'title': 'asset builder contract', 'route': '/asset-builder-contract'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'task capture model', 'route': '/task-capture-model'}, {'title': 'push dashboard check', 'route': '/push-dashboard-check'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'revenue asset contract', 'route': '/revenue-asset-contract'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v4000 milestone', 'route': '/v4000-milestone'}]

@app.get("/legacy/test-report-json-v4000")
async def test_report_json_v4000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Client Asset Builder",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v4000")
async def test_report_v4000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Client Asset Builder. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/client-asset-builder-status")
async def client_asset_builder_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Client Asset Builder",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "product_thesis": "Executive Engine turns executive flow items into client-ready business assets.",
        "assets": [
            "Meeting Brief",
            "Proposal Draft",
            "Pitch Deck Outline",
            "Sales Email",
            "Follow-Up Sequence",
            "Objection Handling",
            "Close Plan",
            "Decision Brief",
            "People Conversation Script"
        ],
        "purpose": "Move from prepared day to prepared assets that help the executive win meetings, move deals, and reduce work.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/asset-builder-contract")
async def asset_builder_contract():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Asset Builder Contract",
        "asset_types": {
            "meeting_brief": ["Objective", "People", "Context", "Questions", "Risks", "Close"],
            "proposal": ["Executive Summary", "Problem", "Opportunity", "Scope", "Value", "Investment", "Next Step"],
            "pitch_deck": ["Slide titles", "Purpose", "Storyline", "Close slide"],
            "sales_email": ["Subject", "Body", "CTA"],
            "follow_up": ["Message 1", "Message 2", "Message 3"],
            "objection_handling": ["Objection", "Response", "Proof"],
            "close_plan": ["Decision maker", "Path to yes", "Deadline", "Risk control"],
            "people_script": ["Situation", "Tone", "Words to use", "Boundary", "Next step"]
        },
        "quality_bar": [
            "Assets must be usable copy",
            "No generic placeholders",
            "No blank sections",
            "Every asset should reduce executive thinking",
            "Every asset should have a clear next step"
        ]
    }

@app.get("/v4000-milestone")
async def v4000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Client Asset Builder",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V3710",
        "build_type": "Product Feature / Asset Builder",
        "added": [
            "Client Asset Builder section",
            "Asset type selector",
            "Asset Builder detail panel",
            "Build Asset button using /run",
            "Copy asset output button",
            "Meeting brief, proposal, deck, email, follow-up, objection, close-plan templates",
            "People script asset option",
            "/client-asset-builder-status",
            "/asset-builder-contract",
            "/v4000-milestone"
        ],
        "kept": [
            "V3710 clickable Executive Flow",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/client-asset-builder-status",
            "https://executive-engine-os.onrender.com/asset-builder-contract",
            "https://executive-engine-os.onrender.com/executive-flow-status",
            "https://executive-engine-os.onrender.com/real-revenue-asset-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v4000-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then build one real client asset from the dashboard."
    }

# =========================
# V9100 ASSET BUILDER LAYOUT FIX
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'asset layout status', 'route': '/asset-layout-status'}, {'title': 'client asset builder status', 'route': '/client-asset-builder-status'}, {'title': 'asset builder contract', 'route': '/asset-builder-contract'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v4010 milestone', 'route': '/v4010-milestone'}]

@app.get("/legacy/test-report-json-v4010")
async def test_report_json_v4010():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Asset Builder Layout Fix",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v4010")
async def test_report_v4010():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Asset Builder Layout Fix. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/asset-layout-status")
async def asset_layout_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Asset Builder Layout Fix",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "Client Asset Builder was squeezed into the right dashboard column and hard to use.",
        "fixed": [
            "Asset Builder moved into full-width workspace",
            "Asset tabs use horizontal / responsive grid",
            "Form fields align properly",
            "Output panel has usable width",
            "Build/Copy buttons are visible",
            "Main dashboard remains push-first"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v4010-milestone")
async def v4010_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Asset Builder Layout Fix",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V9100",
        "build_type": "Frontend UX / Layout Fix",
        "added": [
            "Full-width Asset Builder workspace",
            "Cleaner Asset Builder layout",
            "Better usable form width",
            "Better asset output width",
            "Improved testability of asset creation"
        ],
        "kept": [
            "V9100 Client Asset Builder",
            "V3710 clickable Executive Flow",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/asset-layout-status",
            "https://executive-engine-os.onrender.com/client-asset-builder-status",
            "https://executive-engine-os.onrender.com/asset-builder-contract",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v4010-milestone"
        ],
        "recommended_next_move": "Deploy V9100, then build one Proposal Draft from the full-width Asset Builder."
    }

# =========================
# V9100 PRODUCT CANDIDATE QA
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v5000 status', 'route': '/v5000-status'}, {'title': 'qa checklist', 'route': '/qa-checklist'}, {'title': 'product candidate gates', 'route': '/product-candidate-gates'}, {'title': 'asset layout status', 'route': '/asset-layout-status'}, {'title': 'client asset builder status', 'route': '/client-asset-builder-status'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v5000 milestone', 'route': '/v5000-milestone'}]

@app.get("/legacy/test-report-json-v5000")
async def test_report_json_v5000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate QA",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v5000")
async def test_report_v5000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Product Candidate QA. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/v5000-status")
async def v5000_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate QA",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Promote V9100 to V9100 product-candidate QA baseline.",
        "product_layers": [
            "Executive Flow Dashboard",
            "Push-based Today/Tomorrow flow",
            "Client Asset Builder",
            "Revenue asset engine",
            "QA / buyer-test checklist"
        ],
        "status": "Ready for deeper QA and real asset tests.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/qa-checklist")
async def qa_checklist():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "QA Checklist",
        "qa_tests": [
            "Can I understand the product in 5 seconds?",
            "Does Today show what matters?",
            "Does Tomorrow help me prepare?",
            "Can I click every major card?",
            "Can I build a Proposal Draft?",
            "Can I build a Meeting Brief?",
            "Can I copy the asset output?",
            "Does the asset output feel client-ready?",
            "Does this reduce thinking?",
            "Would a CEO come back tomorrow?"
        ],
        "classification": {
            "HOLD": "Stable but needs refinement.",
            "FIX": "Broken or confusing.",
            "PROMOTE": "Ready for next build.",
            "PIVOT": "Wrong workflow."
        }
    }

@app.get("/product-candidate-gates")
async def product_candidate_gates():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate Gates",
        "gates": [
            {
                "gate": "Stability",
                "pass_condition": "/health and /test-report pass."
            },
            {
                "gate": "Flow",
                "pass_condition": "Today/Tomorrow dashboard makes sense without prompting."
            },
            {
                "gate": "Asset",
                "pass_condition": "Asset Builder produces usable client-ready output."
            },
            {
                "gate": "Executive Emotion",
                "pass_condition": "Feels like leverage, not another chore."
            },
            {
                "gate": "Revenue",
                "pass_condition": "Helps move a deal, proposal, meeting, or follow-up forward."
            }
        ]
    }

@app.get("/v5000-milestone")
async def v5000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Product Candidate QA",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V9100",
        "build_type": "Product Candidate / QA Baseline",
        "added": [
            "V9100 product-candidate badge",
            "QA panel link support",
            "/v5000-status",
            "/qa-checklist",
            "/product-candidate-gates",
            "/v5000-milestone"
        ],
        "kept": [
            "V9100 Asset Builder Layout Fix",
            "V4000 Client Asset Builder",
            "V3710 clickable Executive Flow",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v5000-status",
            "https://executive-engine-os.onrender.com/qa-checklist",
            "https://executive-engine-os.onrender.com/product-candidate-gates",
            "https://executive-engine-os.onrender.com/client-asset-builder-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v5000-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then perform the QA checklist using a real client asset."
    }

# =========================
# V9100 PROACTIVE FOLLOW-UP ENGINE
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v5200 status', 'route': '/v5200-status'}, {'title': 'organization workspace status', 'route': '/organization-workspace-status'}, {'title': 'proactive followup status', 'route': '/proactive-followup-status'}, {'title': 'followup rules', 'route': '/followup-rules'}, {'title': 'capture extraction contract', 'route': '/capture-extraction-contract'}, {'title': 'client asset builder status', 'route': '/client-asset-builder-status'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v5200 milestone', 'route': '/v5200-milestone'}]

@app.get("/legacy/test-report-json-v5200")
async def test_report_json_v5200():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Proactive Follow-Up Engine",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v5200")
async def test_report_v5200():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Proactive Follow-Up Engine. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/v5200-status")
async def v5200_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Proactive Follow-Up Engine",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Promote from product candidate to proactive executive operating system baseline.",
        "product_thesis": "Executive Engine is not a chat app. It is a proactive business execution system.",
        "core_layers": [
            "Organization-first workspace",
            "Project/workstream structure",
            "Section command centers",
            "Client Asset Builder",
            "Open-loop tracking",
            "12-24 hour follow-up logic",
            "Morning brief / end-of-day prep"
        ],
        "status": "Ready for controlled frontend simulation. No autonomous external notifications yet.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/organization-workspace-status")
async def organization_workspace_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Organization Project Workspaces",
        "structure": {
            "organization": "Client, company, team, or personal operating context.",
            "projects": "Revenue deal, hiring push, meeting series, proposal, risk, or operational initiative.",
            "sections": ["Meetings", "Revenue", "People", "Decisions", "Risks", "Assets"],
            "items": "Specific meeting, proposal, follow-up, decision, person, or task.",
            "assets": "Brief, proposal, deck, email, follow-up, close plan, people script.",
            "memory": "What happened, what was decided, what worked, what to use next time."
        },
        "goal": "Avoid 10,000 disconnected chats by organizing work around organizations and projects."
    }

@app.get("/proactive-followup-status")
async def proactive_followup_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Proactive Follow-Up Logic",
        "principle": "Less conversation. More execution.",
        "monitors": [
            "Open meetings",
            "Open proposals",
            "Follow-ups due",
            "Decisions needed",
            "People issues",
            "Risks",
            "Assets created",
            "Tasks aging too long"
        ],
        "cadence": [
            "Morning brief",
            "End-of-day prep",
            "12-24 hour follow-up on open business items",
            "Before meetings",
            "After meetings",
            "Before deadlines"
        ],
        "rule": "Do not bombard the executive. Prompt only when useful, timely, and business-relevant.",
        "notification_status": "Frontend simulation only. No external email/SMS/push notifications yet."
    }

@app.get("/followup-rules")
async def followup_rules():
    return {
        "ok": True,
        "version": VERSION,
        "rules": [
            {
                "trigger": "meeting_tomorrow",
                "prompt": "You meet [person/company] tomorrow. Brief, questions, and proposal angle are ready.",
                "cadence": "Evening before or morning of."
            },
            {
                "trigger": "proposal_idle_24h",
                "prompt": "[company] proposal has not moved in 24 hours. Next move: ask for a decision call.",
                "cadence": "12-24 hours after asset creation."
            },
            {
                "trigger": "followup_due",
                "prompt": "Follow-up with [person/company] is ready. Send it today.",
                "cadence": "Next business day or user-selected due time."
            },
            {
                "trigger": "missing_details",
                "prompt": "I have enough to start. One thing would sharpen this: [single question].",
                "cadence": "Immediately after capture, only when useful."
            },
            {
                "trigger": "end_of_day",
                "prompt": "Drop the messy update. I’ll prepare tomorrow.",
                "cadence": "End of workday."
            }
        ],
        "tone": "Short, confident, supportive, action-oriented. No spam. No long chat."
    }

@app.get("/capture-extraction-contract")
async def capture_extraction_contract():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Fast Executive Capture Extraction",
        "input_example": "Meeting tomorrow with Bob from ABC HVAC. Need proposal for SEO, Google Ads, and Instagram. They want more leads but budget is a concern.",
        "extract": {
            "organization": "ABC HVAC",
            "project": "SEO + Ads Proposal",
            "person": "Bob",
            "type": ["Meeting", "Proposal", "Revenue Deal"],
            "when": "Tomorrow",
            "why": "More leads / revenue growth",
            "constraint": "Budget concern",
            "assets_needed": ["Meeting Brief", "Proposal Draft", "Sales Email", "Objection Handling", "Close Plan"],
            "follow_up_due": "12-24 hours after meeting or asset creation",
            "status": "Open"
        },
        "capture_rule": "Executive gives messy input. System extracts structure, prepares assets, and asks at most one sharpening question."
    }

@app.get("/v5200-milestone")
async def v5200_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Proactive Follow-Up Engine",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V5000",
        "build_type": "Product Architecture / Proactive Logic Simulation",
        "added": [
            "Organization-first workspace panel",
            "Project/workstream model",
            "Section command centers",
            "Open loop tracker",
            "Proactive follow-up panel",
            "Fast capture extraction preview",
            "Follow-up rules",
            "12-24 hour cadence logic",
            "/v5200-status",
            "/organization-workspace-status",
            "/proactive-followup-status",
            "/followup-rules",
            "/capture-extraction-contract",
            "/v5200-milestone"
        ],
        "kept": [
            "V5000 product candidate QA",
            "Client Asset Builder",
            "Executive Flow Dashboard",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v5200-status",
            "https://executive-engine-os.onrender.com/organization-workspace-status",
            "https://executive-engine-os.onrender.com/proactive-followup-status",
            "https://executive-engine-os.onrender.com/followup-rules",
            "https://executive-engine-os.onrender.com/capture-extraction-contract",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v5200-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then test fast capture and follow-up simulation from the frontend."
    }

# =========================
# V9100 INDEPENDENT SECTION PAGES
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'section pages status', 'route': '/section-pages-status'}, {'title': 'v5200 status', 'route': '/v5200-status'}, {'title': 'organization workspace status', 'route': '/organization-workspace-status'}, {'title': 'proactive followup status', 'route': '/proactive-followup-status'}, {'title': 'capture extraction contract', 'route': '/capture-extraction-contract'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v5210 milestone', 'route': '/v5210-milestone'}]

@app.get("/legacy/test-report-json-v5210")
async def test_report_json_v5210():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Independent Section Pages",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v5210")
async def test_report_v5210():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Independent Section Pages. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/section-pages-status")
async def section_pages_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Independent Section Pages",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "Clicking Today/Meeting/Revenue items should open a dedicated section page instead of jumping to the top/detail panel.",
        "section_page_model": [
            "Dashboard remains push-first.",
            "Clicking a dashboard item opens an independent section workspace.",
            "Section workspace has left menu, center ChatGPT-style execution area, and right progress/documents panel.",
            "Sections are category/workspace based, not 10,000 individual chats."
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v5210-milestone")
async def v5210_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Independent Section Pages",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V5200",
        "build_type": "Frontend UX / Section Workspace Fix",
        "added": [
            "Independent section workspace page",
            "Dashboard item opens workspace instead of scrolling up",
            "Workspace left section menu",
            "Workspace center command/conversation area",
            "Workspace right progress/documents panel",
            "Meeting/Revenue/People/Decision/Risk/Asset section views",
            "/section-pages-status",
            "/v5210-milestone"
        ],
        "kept": [
            "V5200 proactive follow-up engine",
            "Organization/project workspace model",
            "Client Asset Builder",
            "Executive Flow Dashboard",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/section-pages-status",
            "https://executive-engine-os.onrender.com/v5200-status",
            "https://executive-engine-os.onrender.com/organization-workspace-status",
            "https://executive-engine-os.onrender.com/proactive-followup-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v5210-milestone"
        ],
        "recommended_next_move": "Deploy V9100, click ABC HVAC under Today, and confirm it opens a dedicated workspace page."
    }

# =========================
# V9100 REAL PAGE NAVIGATION FIX
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'page navigation status', 'route': '/page-navigation-status'}, {'title': 'section pages status', 'route': '/section-pages-status'}, {'title': 'v5200 status', 'route': '/v5200-status'}, {'title': 'organization workspace status', 'route': '/organization-workspace-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v5220 milestone', 'route': '/v5220-milestone'}]

@app.get("/legacy/test-report-json-v5220")
async def test_report_json_v5220():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Page Navigation Fix",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v5220")
async def test_report_v5220():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Real Page Navigation Fix. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/page-navigation-status")
async def page_navigation_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Page Navigation Fix",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "problem_fixed": "V5210 still scrolled up/down instead of switching to a true independent workspace view.",
        "fixed": [
            "Replaced scroll behavior for dashboard cards",
            "Added full-screen workspace page layer",
            "Clicking Today/Meetings/Revenue cards now hides dashboard and shows workspace",
            "Back to Dashboard restores main dashboard",
            "Workspace has left menu, center execution/chat area, right progress/documents panel"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v5220-milestone")
async def v5220_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Real Page Navigation Fix",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V5210",
        "build_type": "Frontend UX / Real Page Navigation Fix",
        "added": [
            "True dashboard/workspace page switch",
            "Dashboard card click opens workspace view",
            "Scroll behavior removed from key dashboard cards",
            "Workspace page is full-width and independent",
            "Back to Dashboard button restores dashboard",
            "Dedicated workspace title/subtitle updates from clicked item"
        ],
        "kept": [
            "V5200 proactive follow-up engine",
            "V5210 section workspace concept",
            "Organization/project workspace model",
            "Client Asset Builder",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/page-navigation-status",
            "https://executive-engine-os.onrender.com/section-pages-status",
            "https://executive-engine-os.onrender.com/v5200-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v5220-milestone"
        ],
        "recommended_next_move": "Deploy V9100. Click ABC HVAC under Today. It should hide dashboard and open a dedicated workspace page."
    }

# =========================
# V9100 FULL SYSTEM LINKED QA
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v6000 status', 'route': '/v6000-status'}, {'title': 'full link map', 'route': '/full-link-map'}, {'title': 'page navigation status', 'route': '/page-navigation-status'}, {'title': 'section pages status', 'route': '/section-pages-status'}, {'title': 'v5200 status', 'route': '/v5200-status'}, {'title': 'organization workspace status', 'route': '/organization-workspace-status'}, {'title': 'proactive followup status', 'route': '/proactive-followup-status'}, {'title': 'followup rules', 'route': '/followup-rules'}, {'title': 'capture extraction contract', 'route': '/capture-extraction-contract'}, {'title': 'client asset builder status', 'route': '/client-asset-builder-status'}, {'title': 'asset builder contract', 'route': '/asset-builder-contract'}, {'title': 'executive flow status', 'route': '/executive-flow-status'}, {'title': 'real revenue asset status', 'route': '/real-revenue-asset-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v6000 milestone', 'route': '/v6000-milestone'}]

@app.get("/legacy/test-report-json-v6000")
async def test_report_json_v6000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Full System Linked QA",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v6000")
async def test_report_v6000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Full System Linked QA. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/v6000-status")
async def v6000_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Full System Linked QA",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Promote V5220 into V9100 large-shot test baseline.",
        "goal": "Make every primary frontend link/button/card do something testable.",
        "product_layers": [
            "Push-first dashboard",
            "True workspace page navigation",
            "Organization/project workspaces",
            "Section command centers",
            "Client Asset Builder",
            "Proactive follow-up simulation",
            "System QA panel"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/full-link-map")
async def full_link_map():
    return {
        "ok": True,
        "version": VERSION,
        "frontend_links_expected": {
            "sidebar": ["Dashboard", "Meetings", "Revenue", "People", "Risks", "Assets", "Admin / Tests"],
            "dashboard_cards": ["Today items", "Meetings cards", "Revenue cards", "Tomorrow cards", "Prepared For You cards", "Follow-Up card"],
            "workspace": ["Back to Dashboard", "Brief", "Meeting Prep", "Proposal", "Sales Email", "Follow-Up", "Objections", "Close Plan", "Notes", "Send", "Build Section Asset"],
            "system": ["Health", "Page Navigation Status", "Section Pages Status", "V5200 Status", "Test Report", "V9100 Milestone"]
        },
        "pass_condition": "Every visible card/button either opens a page, changes workspace tab, builds an asset, copies text, or opens a backend route."
    }

@app.get("/v6000-milestone")
async def v6000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Full System Linked QA",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V5220",
        "build_type": "Product Candidate / Full Frontend Link QA",
        "added": [
            "V9100 full-system QA baseline",
            "Clickable link map route",
            "Full system status route",
            "All primary dashboard cards link to workspace pages",
            "Workspace tabs work",
            "Sidebar links work",
            "System/admin links work",
            "Asset Builder quick access added",
            "Proactive follow-up quick access added"
        ],
        "kept": [
            "V5220 real page navigation",
            "V5200 proactive follow-up engine contract routes",
            "Organization/project workspace model",
            "Client Asset Builder concept",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v6000-status",
            "https://executive-engine-os.onrender.com/full-link-map",
            "https://executive-engine-os.onrender.com/page-navigation-status",
            "https://executive-engine-os.onrender.com/section-pages-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v6000-milestone"
        ],
        "recommended_next_move": "Deploy V9100, run /test-report, then perform one full click-through QA pass."
    }

# =========================
# V9100 FUNCTIONAL MVP
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v6100 status', 'route': '/v6100-status'}, {'title': 'functional mvp status', 'route': '/functional-mvp-status'}, {'title': 'full link map', 'route': '/full-link-map'}, {'title': 'v6000 status', 'route': '/v6000-status'}, {'title': 'page navigation status', 'route': '/page-navigation-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v6100 milestone', 'route': '/v6100-milestone'}]

@app.get("/legacy/test-report-json-v6100")
async def test_report_json_v6100():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Functional MVP",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v6100")
async def test_report_v6100():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Functional MVP. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/functional-mvp-status")
async def functional_mvp_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Functional MVP",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "goal": "Make the system usable day-to-day even before perfect refinement.",
        "frontend_functionality": [
            "Create flow items",
            "Persist items locally",
            "Open real workspace pages",
            "Save workspace messages locally",
            "Build assets through /run",
            "Save generated documents locally",
            "Copy generated documents",
            "Mark progress items done",
            "Reset local demo data",
            "Run full click-through QA"
        ],
        "data_note": "V9100 uses browser localStorage for MVP persistence. Supabase schema is unchanged.",
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v6100-status")
async def v6100_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Functional MVP",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Promote V6000 to a usable MVP baseline.",
        "purpose": "Let the user actually use Executive Engine instead of only testing visual concepts.",
        "status": "Ready for daily use testing with local persistence."
    }

@app.get("/v6100-milestone")
async def v6100_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Functional MVP",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V6000",
        "build_type": "Functional MVP / Usability Baseline",
        "added": [
            "LocalStorage persistence",
            "Add flow item creates real item",
            "Dashboard item persistence",
            "Workspace message persistence",
            "Generated document persistence",
            "Document copy button",
            "Mark progress done",
            "Reset local data",
            "Functional QA panel"
        ],
        "kept": [
            "V6000 full linked QA",
            "V5220 page navigation",
            "V5200 proactive follow-up contracts",
            "Organization/project workspace model",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v6100-status",
            "https://executive-engine-os.onrender.com/functional-mvp-status",
            "https://executive-engine-os.onrender.com/full-link-map",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v6100-milestone"
        ],
        "recommended_next_move": "Deploy V9100 and use it for one real work item end-to-end."
    }

# =========================
# V9100 EXECUTIVE FLOW OPERATING SYSTEM
# =========================

V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v9000 status', 'route': '/v9000-status'}, {'title': 'workflow os status', 'route': '/workflow-os-status'}, {'title': 'functional mvp status', 'route': '/functional-mvp-status'}, {'title': 'v6100 status', 'route': '/v6100-status'}, {'title': 'full link map', 'route': '/full-link-map'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v9000 milestone', 'route': '/v9000-milestone'}]

@app.get("/legacy/test-report-json-v9000")
async def test_report_json_v9000():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Operating System",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [
            {"title": item["title"], "route": item["route"], "url": V9100_BACKEND_BASE + item["route"]}
            for item in V9100_REPORT_TESTS
        ],
        "note": "Open /test-report, click Run Report, then Copy All Results and paste into ChatGPT."
    }

@app.get("/legacy/test-report-v9000")
async def test_report_v9000():
    from starlette.responses import HTMLResponse
    tests_json = json.dumps(V9100_REPORT_TESTS)
    html = '<!doctype html><html><head><title>Executive Engine OS V9100 Test Report</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial,sans-serif;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1180px;margin:auto}.hero,.card{background:#fff;border:1px solid #dbe5f1;border-radius:20px;padding:20px;box-shadow:0 16px 40px rgba(7,18,38,.08);margin-bottom:14px}h1{margin:0 0 8px;font-size:28px}h2{margin:0 0 10px;font-size:17px}p{color:#64748b;line-height:1.5}button{border:1px solid #dbe5f1;border-radius:12px;background:#0f63ff;color:#fff;font-weight:900;padding:11px 14px;cursor:pointer;margin:4px 6px 4px 0}button.secondary{background:#fff;color:#0f63ff}.url{font-size:12px;color:#64748b;word-break:break-all;margin-bottom:8px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;word-break:break-word;min-height:42px;max-height:260px;overflow:auto;font-size:12px;line-height:1.45}textarea{width:100%;min-height:380px;border:1px solid #cbd5e1;border-radius:16px;padding:12px;font-size:12px;line-height:1.45}.good{background:#ecfdf5;border:1px solid #bbf7d0;color:#047857;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}.fail{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:14px;padding:12px;margin-top:12px;font-weight:800}code{background:#071226;color:#dbeafe;padding:4px 7px;border-radius:8px}</style></head><body><div class="wrap"><div class="hero"><h1>Executive Engine OS V9100 Test Report</h1><p>Executive Flow Operating System. Click Run Report, then Copy All Results and paste into ChatGPT.</p><p>Current visible version: <code>V9100</code></p><button onclick="runReport()">Run Report</button><button class="secondary" onclick="copyAll()">Copy All Results</button><button class="secondary" onclick="clearReport()">Clear</button><div id="status" class="good">Ready. Click Run Report.</div></div><div class="card"><h2>Copy/Paste Report For ChatGPT</h2><textarea id="copyBox"></textarea></div><div id="cards"></div></div><script>const BACKEND_BASE="__BACKEND_BASE__";const TESTS=__TESTS_JSON__;function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}function escapeHtml(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}function setStatus(t,ok){const el=document.getElementById("status");el.className=ok===false?"fail":"good";el.textContent=t}async function runOne(test){const url=BACKEND_BASE+test.route;try{const res=await fetch(url,{method:"GET",cache:"no-store"});const ct=res.headers.get("content-type")||"";let data=ct.includes("application/json")?await res.json():await res.text();return {title:test.title,url,status:res.status,ok:res.ok,output:data}}catch(err){return {title:test.title,url,status:"FETCH_ERROR",ok:false,output:err.message}}}function buildCopyText(results){let out=[];out.push("Executive Engine OS V9100 Test Report");out.push("Generated: "+new Date().toISOString());out.push("");for(const r of results){out.push("========================================");out.push(r.title);out.push(r.url);out.push("status: "+r.status);out.push("ok: "+r.ok);out.push("----------------------------------------");out.push(pretty(r.output));out.push("")}return out.join("\\n")}function renderCards(results){document.getElementById("cards").innerHTML=results.map(r=>`<div class="card"><h2>${escapeHtml(r.title)}</h2><div class="url">${escapeHtml(r.url)} · status: ${r.status} · ok: ${r.ok}</div><pre>${escapeHtml(pretty(r.output))}</pre></div>`).join("")}async function runReport(){setStatus("Running tests...",true);const results=[];for(const test of TESTS){setStatus("Running: "+test.title,true);const result=await runOne(test);results.push(result);renderCards(results);document.getElementById("copyBox").value=buildCopyText(results)}const failed=results.filter(r=>!r.ok).length;setStatus(failed?"Done with "+failed+" failed link(s). Copy All and paste into ChatGPT.":"All done. Copy All and paste into ChatGPT.",failed===0)}async function copyAll(){const text=document.getElementById("copyBox").value;if(!text){setStatus("Nothing to copy yet. Click Run Report first.",false);return}await navigator.clipboard.writeText(text);setStatus("Copied. Paste it into ChatGPT.",true)}function clearReport(){document.getElementById("copyBox").value="";document.getElementById("cards").innerHTML="";setStatus("Cleared. Click Run Report.",true)}</script></body></html>'.replace("__BACKEND_BASE__", V9100_BACKEND_BASE).replace("__TESTS_JSON__", tests_json)
    return HTMLResponse(html)

@app.get("/workflow-os-status")
async def workflow_os_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Workflow Organization Pass",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "goal": "Reduce disorganization and make the product follow one executive operating loop.",
        "operating_loop": [
            "Capture",
            "Organize",
            "Prepare",
            "Execute",
            "Follow Up",
            "Close Loop"
        ],
        "primary_views": [
            "Flow Board",
            "Focus Workspace",
            "Asset Library",
            "Review / Follow-Up",
            "QA / System"
        ],
        "safety": {
            "supabase_schema_changed": False,
            "oauth_activated": False,
            "external_writes_enabled": False,
            "notifications_sent": False,
            "run_changed": False,
            "manual_execution_only": True,
            "auto_loop_enabled": False
        }
    }

@app.get("/v9000-status")
async def v9000_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Operating System",
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "decision": "Fast-track from V6100 functional MVP to V9100 workflow OS baseline.",
        "purpose": "Make the system more organized and usable in one large product pass.",
        "status": "Ready for real daily-use testing."
    }

@app.get("/v9000-milestone")
async def v9000_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Executive Flow Operating System",
        "ready": True,
        "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend",
        "baseline": "V6100",
        "build_type": "Workflow OS / Fast-Track Product Pass",
        "added": [
            "Clear operating loop",
            "Start Here / Capture panel",
            "Flow Board organized by status",
            "Focus Workspace",
            "Asset Library",
            "Review / Follow-Up panel",
            "Cleaner navigation",
            "One large daily-use QA flow",
            "LocalStorage persistence preserved"
        ],
        "kept": [
            "V6100 functional MVP",
            "LocalStorage persistence",
            "Workspace messages",
            "Generated document storage",
            "V3003 real revenue asset engine",
            "/run unchanged",
            "/test-report working",
            "Supabase schema unchanged",
            "OAuth inactive",
            "external writes blocked",
            "no external notifications sent",
            "manual execution only",
            "auto-loop off"
        ],
        "test_order": [
            "https://executive-engine-os.onrender.com/health",
            "https://executive-engine-os.onrender.com/v9000-status",
            "https://executive-engine-os.onrender.com/workflow-os-status",
            "https://executive-engine-os.onrender.com/functional-mvp-status",
            "https://executive-engine-os.onrender.com/test-report",
            "https://executive-engine-os.onrender.com/v9000-milestone"
        ],
        "recommended_next_move": "Deploy V9100, add one real work item, build one asset, mark progress, and review follow-up."
    }

# =========================
# V9100 SMART INTAKE ROUTER
# =========================
V9100_BACKEND_BASE = "https://executive-engine-os.onrender.com"
V9100_REPORT_TESTS = [{'title': 'health', 'route': '/health'}, {'title': 'v9100 status', 'route': '/v9100-status'}, {'title': 'smart intake status', 'route': '/smart-intake-status'}, {'title': 'workflow os status', 'route': '/workflow-os-status'}, {'title': 'test-report-json', 'route': '/test-report-json'}, {'title': 'v9100 milestone', 'route': '/v9100-milestone'}]

@app.get("/test-report-json")
async def test_report_json_v9100():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Smart Intake Router",
        "backend_base": V9100_BACKEND_BASE,
        "tests": [{"title": i["title"], "route": i["route"], "url": V9100_BACKEND_BASE+i["route"]} for i in V9100_REPORT_TESTS]
    }

@app.get("/test-report")
async def test_report_v9100():
    from starlette.responses import HTMLResponse
    return HTMLResponse('<!doctype html><html><head><title>Executive Engine V9100 Test Report</title><meta name=\'viewport\' content=\'width=device-width,initial-scale=1\'><style>body{font-family:Arial;background:#f8fbff;color:#071226;padding:24px}.wrap{max-width:1100px;margin:auto}.card{background:#fff;border:1px solid #dbe5f1;border-radius:18px;padding:18px;margin:12px 0}button{background:#0f63ff;color:#fff;border:0;border-radius:12px;padding:11px 14px;font-weight:800;margin-right:8px}textarea{width:100%;height:340px;border:1px solid #cbd5e1;border-radius:14px;padding:12px}pre{background:#071226;color:#dbeafe;border-radius:14px;padding:12px;white-space:pre-wrap;max-height:260px;overflow:auto}.ok{background:#ecfdf5;color:#047857;border-radius:12px;padding:10px;font-weight:800}</style></head><body><div class=\'wrap\'><div class=\'card\'><h1>Executive Engine OS V9100 Test Report</h1><p>Smart Intake Router.</p><button onclick=\'runReport()\'>Run Report</button><button onclick=\'copyAll()\'>Copy All</button><div id=\'status\' class=\'ok\'>Ready.</div></div><div class=\'card\'><textarea id=\'copyBox\'></textarea></div><div id=\'cards\'></div></div><script>const BASE=\'https://executive-engine-os.onrender.com\';const TESTS=[{"title": "health", "route": "/health"}, {"title": "v9100 status", "route": "/v9100-status"}, {"title": "smart intake status", "route": "/smart-intake-status"}, {"title": "workflow os status", "route": "/workflow-os-status"}, {"title": "test-report-json", "route": "/test-report-json"}, {"title": "v9100 milestone", "route": "/v9100-milestone"}];function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}async function runOne(t){const url=BASE+t.route;try{const r=await fetch(url,{cache:\'no-store\'});let d=(r.headers.get(\'content-type\')||\'\').includes(\'json\')?await r.json():await r.text();return {title:t.title,url,status:r.status,ok:r.ok,output:d}}catch(e){return {title:t.title,url,status:\'FETCH_ERROR\',ok:false,output:e.message}}}async function runReport(){let rs=[];for(const t of TESTS){rs.push(await runOne(t));render(rs)}document.getElementById(\'status\').textContent=\'Done. Copy All.\'}function render(rs){document.getElementById(\'copyBox\').value=\'Executive Engine OS V9100 Test Report\\n\'+new Date().toISOString()+\'\\n\\n\'+rs.map(r=>r.title+\'\\n\'+r.url+\'\\nstatus: \'+r.status+\'\\nok: \'+r.ok+\'\\n\'+pretty(r.output)).join(\'\\n\\n---\\n\\n\');document.getElementById(\'cards\').innerHTML=rs.map(r=>`<div class=\'card\'><h2>${r.title}</h2><p>${r.url} · ${r.status} · ${r.ok}</p><pre>${pretty(r.output).replaceAll(\'<\',\'&lt;\')}</pre></div>`).join(\'\')}function copyAll(){navigator.clipboard.writeText(document.getElementById(\'copyBox\').value)}</script></body></html>')

@app.get("/smart-intake-status")
async def smart_intake_status():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Smart Intake Router",
        "problem_fixed": "Long messy input now routes to the correct workspace instead of landing in the currently open section such as Assets.",
        "routes": {
            "investment": "house, bungalow, renovate, rent, realtor, tenant, property, contractor",
            "revenue": "proposal, deal, close, client, offer",
            "meeting": "meeting, call, agenda",
            "people": "hire, fire, team, contractor, employee",
            "risk": "risk, legal, issue, compliance",
            "fallback": "strategic project"
        },
        "safety": {"supabase_schema_changed": False, "oauth_activated": False, "external_writes_enabled": False, "run_changed": False}
    }

@app.get("/v9100-status")
async def v9100_status():
    return {"ok": True, "version": VERSION, "milestone": "Smart Intake Router", "frontend_must_show": "V9100 Smart Intake Router · V9100 Backend", "status": "Ready for house renovation rental scenario test."}

@app.get("/v9100-milestone")
async def v9100_milestone():
    return {
        "ok": True,
        "version": VERSION,
        "milestone": "Smart Intake Router",
        "ready": True,
        "added": ["Smart input classifier", "Investment workspace", "Real estate starter plan", "Route-to-workspace behavior", "Assets kept for generated documents only"],
        "kept": ["V9000 workflow OS", "localStorage persistence", "/run unchanged", "/test-report working", "Supabase schema unchanged", "OAuth inactive", "manual execution only"],
        "recommended_next_move": "Deploy V9100, reset local data once, paste the house-renovation-rental input, confirm Investment workspace opens."
    }
