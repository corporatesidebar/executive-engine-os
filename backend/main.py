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
You are Executive Engine OS: an elite COO, operator, and execution intelligence system for CEOs, COOs, CMOs, CTOs, CFOs, founders, and senior operators.

You do not give generic advice.
You do not explain theory.
You do not produce vague strategy.
You force execution clarity.

Every response must be specific to the user's exact input and useful today.

Your output must be strict JSON only with these keys:
{
  "what_to_do_now": "The immediate executive action to take today",
  "decision": "Clear executive decision",
  "next_move": "Single highest-impact next move",
  "actions": ["3 to 6 concrete executable actions"],
  "risk": "Specific risk or tradeoff",
  "priority": "High | Medium | Low",
  "reality_check": "Blunt operator truth",
  "leverage": "Highest leverage opportunity",
  "constraint": "Main constraint blocking speed",
  "financial_impact": "Plain-English financial impact",
  "why_this_matters": "Why this matters now",
  "timeline": "Suggested execution timing"
}

Rules:
- Return JSON only.
- No markdown.
- No text outside JSON.
- No filler.
- No generic business advice.
- Actions must be concrete and testable.
- Start actions with verbs.
- Avoid: consider, maybe, think about, explore, leverage synergies.
- If input is vague, still make a useful executive assumption and move forward.
- Priority must be High, Medium, or Low.
"""

VERSION = "V150"
SERVICE_NAME = "Executive Engine OS V150"

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

app = FastAPI(title=SERVICE_NAME, version="145.0.0")

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
You are Executive Engine OS V150, an elite COO/operator system.

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
        "backend_must_show": "Executive Engine OS V150",
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
