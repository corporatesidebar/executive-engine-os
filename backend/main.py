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


VERSION = "V125"
SERVICE_NAME = "Executive Engine OS V125"

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

app = FastAPI(title=SERVICE_NAME, version="125.0.0")

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
        "what_to_ignore": "Do not add bots, external automation, or new dashboards until the V125 loop passes.",
        "questions_to_answer": ["Did the run save?", "Did the actions save?", "Did the decision save?", "Did the right rail refresh?"],
        "delegation": "Keep manual execution. Do not delegate to bots yet.",
        "timeline": "Today: validate loop. Next 2-3 days: run real use cases. Next 2-3 weeks: polish and expand.",
        "success_metric": "One prompt produces a useful output and saves at least one action and one decision.",
        "strategic_read": "Stability is the strategy right now.",
        "follow_up_prompt": "What is the single highest-leverage improvement after this run?",
        "execution_loop": {
            "current_focus": "V125 clean reset validation",
            "next_action": "Run one command and persist the result.",
            "next_prompt": "What is the next move after validating V125?",
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
You are Executive Engine OS V125, an elite COO/operator system.

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
    if not client:
        return fallback_output(req.input, req.mode)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.3,
            max_tokens=OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Act as an elite COO/operator. Return strict JSON only. No markdown. No text outside JSON."
                },
                {"role": "user", "content": build_prompt(req, memory)}
            ],
            timeout=OPENAI_TIMEOUT_SECONDS
        )
        content = response.choices[0].message.content or "{}"
        return normalize_output(json.loads(content), req.input, req.mode)
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
            "badge": "V125 · Ship Lock",
            "output_badge": "V125 · Locked",
            "status": "DB memory live · V125"
        },
        "test": [
            "Hard refresh frontend.",
            "Confirm V125 · Ship Lock appears.",
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
        "decision": "Use V125 as the stable baseline if the frontend smoke test passes.",
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
        "fix": "Stability audit lock. V125 keeps the V123 save-flow fix and adds final run/save audit endpoints.",
        "supabase_enabled": mem.get("supabase_enabled", False),
        "required_frontend_badge": "V125 · Stability Lock",
        "test_prompt": "V125 final test — create one action called \"Review V125 system tomorrow\" and one decision called \"Lock V125 as stable baseline.\"",
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
        "frontend_must_show": "V125 · Stability Lock",
        "backend_must_show": "Executive Engine OS V125",
        "do_not_build_next": "Do not build V126 until V125 passes 10 real commands.",
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
        "test_prompt": "V125 final test — create one action called \"Review V125 system tomorrow\" and one decision called \"Lock V125 as stable baseline.\"",
        "required_frontend_badge": "V125 · Save Flow Lock",
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
        "test_prompt": "V125 final test — create one action called \"Review V125 system tomorrow\" and one decision called \"Lock V125 as stable baseline.\"",
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
        "test_prompt": "V125 final test — create one action called \"Review V125 system tomorrow\" and one decision called \"Lock V125 as stable baseline.\""
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
        "decision": "Ship V125 as the stable baseline if the frontend smoke test passes.",
        "next_move": "Use the system for 10 real runs before adding new features."
    }


@app.get("/frontend-version-check")
async def frontend_version_check():
    return {
        "ok": True,
        "version": VERSION,
        "expected_frontend": "V125",
        "cache_rule": "If frontend still shows an older version, Render is serving old index.html or browser cache is stale.",
        "required_strings": [
            "V125 · Ship Lock",
            "V125 · Locked",
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
        "rule": "Do not build V125 until V125 passes 10 real runs.",
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
            "Only then decide V125 scope."
        ],
        "recommended_v121": "Profile editor + action completion, only after V125 is proven stable."
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
            "badge": "V125 · Clean Hardened",
            "output_badge": "V125 · Clean",
            "status": "DB memory live · V125"
        },
        "test": [
            "Hard refresh frontend.",
            "Confirm V125 · Clean Hardened appears.",
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
        "expected_frontend": "V125",
        "cache_rule": "If frontend still shows an older version, Render is serving old index.html or browser cache is stale.",
        "required_strings": [
            "V125 · Clean Hardened",
            "V125 · Clean",
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
            "Confirm V125 Clean Reset appears.",
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
