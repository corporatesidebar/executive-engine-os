import os
import json
import re
import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from openai import AsyncOpenAI


APP_NAME = "Executive Engine OS V95.2"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2800"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title=APP_NAME, version="95.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    context: Optional[str] = None
    mode: Optional[str] = "execution"
    depth: Optional[str] = "standard"
    user_id: Optional[str] = "local_user"
    session_id: Optional[str] = None
    auto_save: Optional[bool] = True


class AutoLoopRequest(BaseModel):
    input: str = Field(..., min_length=1)
    context: Optional[str] = None
    mode: Optional[str] = "execution"
    depth: Optional[str] = "standard"
    user_id: Optional[str] = "local_user"
    session_id: Optional[str] = None
    max_steps: Optional[int] = Field(default=3, ge=1, le=5)


class SaveActionRequest(BaseModel):
    user_id: Optional[str] = "local_user"
    run_id: Optional[str] = None
    text: str
    priority: Optional[str] = "medium"
    status: Optional[str] = "open"
    owner: Optional[str] = None
    metadata: Optional[Dict] = None


class SaveDecisionRequest(BaseModel):
    user_id: Optional[str] = "local_user"
    run_id: Optional[str] = None
    decision: str
    risk: Optional[str] = None
    priority: Optional[str] = "medium"
    rationale: Optional[str] = None
    next_move: Optional[str] = None
    metadata: Optional[Dict] = None


class ProfileRequest(BaseModel):
    user_id: Optional[str] = "local_user"
    role: Optional[str] = None
    goals: Optional[str] = None
    experience: Optional[str] = None
    constraints: Optional[str] = None
    resume_context: Optional[str] = None
    preferences: Optional[Dict] = None


CANONICAL_SCHEMA = {
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
    "auto_execution": {
        "enabled": False,
        "next_prompt": "",
        "suggested_loop": [],
        "stop_condition": ""
    },
    "execution_loop": {
        "current_focus": "",
        "next_action": "",
        "next_prompt": "",
        "save_recommendation": {},
        "loop_steps": [],
        "stop_condition": ""
    },
    "reality_check": "",
    "leverage": "",
    "constraint": "",
    "financial_impact": ""
}

MODE_GUIDANCE = {
    "execution": "Turn a messy business issue, blocker, task, or vague situation into a direct execution plan.",
    "daily_brief": "Build an operating plan for the day: main focus, priority sequence, follow-ups, risks, and what to ignore.",
    "decision": "Make a clear recommendation with tradeoffs, risk, opportunity, missing information, and next move.",
    "meeting": "Prepare meeting objective, agenda, talking points, hard questions, stakeholder read, risks, and follow-up.",
    "personal": "Clarify messy personal, admin, communication, or life context with practical next moves.",
    "content": "Create content, scripts, social posts, Figma prompts, Canva briefs, landing page ideas, and marketing angles.",
    "learning": "Analyze patterns, bottlenecks, decision habits, and workflow recommendations."
}

DEPTH_GUIDANCE = {
    "quick": "Concise but useful. Actions: 3-4.",
    "standard": "Strong executive brief. Actions: 4-6. Each field adds useful context.",
    "deep": "Strategic operator brief. Actions: 6-8. Include sequence, hidden constraints, and tradeoffs.",
    "board_level": "Executive memo style. Actions: 6-10. Include risk, financial impact, delegation, timeline, and metrics."
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def fallback_response(reason="Backend fallback"):
    return {
        "executive_summary": "The full AI response was not completed, so use this fallback to keep execution moving.",
        "what_to_do_now": "Clarify the desired outcome, identify the biggest constraint, and execute the first concrete action immediately.",
        "decision": "Move forward with the clearest low-regret next step instead of waiting for perfect information.",
        "why_this_matters": "Execution velocity matters. Waiting for a perfect answer creates drag and prevents momentum.",
        "next_move": "Write the desired outcome in one sentence, list the top constraint, and take a 15-minute action that moves the situation forward.",
        "actions": [
            "Write the desired outcome in one clear sentence.",
            "Identify the one constraint blocking progress.",
            "Choose the first action that can be completed in 15 minutes.",
            "Execute it now, then reassess with better context.",
            "Retry the engine if a deeper strategic answer is still needed."
        ],
        "priority": "high",
        "risk": "The main risk is staying stuck because the input, backend, or decision context is incomplete.",
        "opportunity": "You can still create forward motion by reducing the situation to outcome, constraint, and first move.",
        "what_to_ignore": "Ignore perfect formatting, overthinking, and low-value details that do not change the immediate move.",
        "questions_to_answer": [
            "What outcome do you want?",
            "What is blocking progress?",
            "What decision needs to be made now?"
        ],
        "delegation": "If another person owns the blocker, assign them one clear deliverable and a deadline.",
        "timeline": "Immediate: define outcome and constraint. Next 15 minutes: take first action. Today: reassess and create the next step.",
        "success_metric": "A concrete action is completed and the next decision is clearer.",
        "strategic_read": "When uncertain, the operator move is to create clarity through action rather than wait for more information.",
        "follow_up_prompt": "Now turn this into a complete execution plan with owner, timeline, and success metric.",
        "auto_execution": {
            "enabled": False,
            "next_prompt": "Turn this fallback into a full execution plan.",
            "suggested_loop": ["Clarify outcome", "Identify constraint", "Execute first action"],
            "stop_condition": "Stop when the next physical or digital action is clear."
        },
        "reality_check": "The current response is a fallback, not a full strategic answer.",
        "leverage": "Momentum and clarity are the leverage points.",
        "constraint": reason,
        "financial_impact": "Slow execution creates opportunity cost; the immediate goal is to reduce that drag."
    }


def extract_json(text):
    if not text:
        raise ValueError("Empty model response")
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
    raise ValueError("No valid JSON object found")




def required_schema_keys() -> List[str]:
    return [
        "executive_summary", "what_to_do_now", "decision", "why_this_matters",
        "next_move", "actions", "priority", "risk", "opportunity",
        "what_to_ignore", "questions_to_answer", "delegation", "timeline",
        "success_metric", "strategic_read", "follow_up_prompt",
        "auto_execution", "execution_loop", "reality_check", "leverage",
        "constraint", "financial_impact"
    ]


def validate_output_shape(output: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantees /run always returns a full stable JSON object."""
    normalized = normalize_output(output)
    for key in required_schema_keys():
        if key not in normalized:
            normalized[key] = CANONICAL_SCHEMA.get(key, "")

    if not isinstance(normalized.get("actions"), list):
        normalized["actions"] = ensure_list(normalized.get("actions"))

    if not isinstance(normalized.get("questions_to_answer"), list):
        normalized["questions_to_answer"] = ensure_list(normalized.get("questions_to_answer"))

    if not isinstance(normalized.get("auto_execution"), dict):
        normalized["auto_execution"] = CANONICAL_SCHEMA["auto_execution"]

    if not isinstance(normalized.get("execution_loop"), dict):
        normalized["execution_loop"] = build_execution_loop(normalized)

    normalized["auto_execution"]["enabled"] = False
    normalized["manual_execution_only"] = True
    normalized["version"] = "V95"
    return normalized

def ensure_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_output(data, reason=""):
    base = fallback_response(reason or "Normalization fallback")

    if isinstance(data, dict):
        for key in CANONICAL_SCHEMA:
            value = data.get(key)
            if value not in [None, ""]:
                base[key] = value

    base["actions"] = ensure_list(base.get("actions")) or fallback_response()["actions"]
    base["questions_to_answer"] = ensure_list(base.get("questions_to_answer")) or fallback_response()["questions_to_answer"]

    priority = str(base.get("priority", "medium")).lower().strip()
    base["priority"] = priority if priority in {"low", "medium", "high", "critical"} else "medium"

    auto = base.get("auto_execution")
    if not isinstance(auto, dict):
        auto = {}

    base["auto_execution"] = {
        "enabled": False,
        "next_prompt": str(auto.get("next_prompt") or base.get("follow_up_prompt") or ""),
        "suggested_loop": ensure_list(auto.get("suggested_loop")) or base["actions"][:3],
        "stop_condition": str(auto.get("stop_condition") or "Stop when the next move is clear enough to execute.")
    }

    if not base.get("what_to_do_now"):
        base["what_to_do_now"] = base.get("executive_summary", "")
    if not base.get("next_move"):
        base["next_move"] = base["actions"][0] if base["actions"] else ""
    if not base.get("reality_check"):
        base["reality_check"] = base.get("why_this_matters", "")
    if not base.get("leverage"):
        base["leverage"] = base.get("opportunity", "")
    if not base.get("constraint"):
        base["constraint"] = base.get("risk", "")
    if not base.get("financial_impact"):
        base["financial_impact"] = "The financial impact depends on execution speed, decision quality, and whether the next move removes a real constraint."

    base["execution_loop"] = build_execution_loop(base)
    return base


def build_system_prompt(mode, depth, loop_mode=False):
    loop_rules = (
        "AUTO-EXECUTION LOOP: Provide the next internal prompt, suggested internal loop steps, and stop condition. Do not claim external actions were completed."
        if loop_mode
        else "AUTO-EXECUTION: Provide a useful next_prompt for the next run. Do not claim external actions were completed."
    )

    return f"""
You are Executive Engine OS V95.2.

ROLE:
Act like an elite CEO, COO, President, Chief of Staff, strategist, and operator.
Turn messy input into decisive executive execution using profile, recent runs, saved actions, saved decisions, and memory when available.

OUTPUT:
Return ONLY valid JSON.
No markdown.
No prose outside JSON.
Use this exact schema:
{json.dumps(CANONICAL_SCHEMA)}

QUALITY:
- Be specific, direct, and execution-focused.
- Do not give generic, shallow, obvious, or motivational advice.
- Every field must add distinct useful context.
- Use memory when available: profile, recent decisions, open actions, repeated constraints, and previous runs.
- Do not repeat old advice blindly; use memory to make the next move more relevant.
- Create a manual execution loop only: what to do now, what to save, what the user should run next, and when to stop. Do not create autonomous or scheduled actions.
- Each action must be executable today.
- Include reasoning, tradeoffs, risk, sequence, delegation, timeline, and success metric.
- If context is weak, still produce a useful answer and ask sharp questions.
- Do not claim DB, Gmail, Calendar, Canva, Figma, CRM, or external app access unless explicitly provided. Do not claim automation is running. Manual execution only.
- Make follow_up_prompt a copy/paste prompt the user can run next.

MODE:
{MODE_GUIDANCE.get(mode, MODE_GUIDANCE["execution"])}

DEPTH:
{DEPTH_GUIDANCE.get(depth, DEPTH_GUIDANCE["standard"])}

{loop_rules}
"""


def build_user_prompt(req, memory=None):
    return f"""
REQUEST:
user_id: {req.user_id or "local_user"}
session_id: {req.session_id or "none"}
mode: {req.mode or "execution"}
depth: {req.depth or "standard"}
timestamp: {now_iso()}

MEMORY:
{json.dumps(summarize_memory_for_prompt(memory or {}), indent=2)}

CONTEXT:
{req.context or "No additional context provided."}

USER INPUT:
{req.input}
"""


def supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


async def sb_get(table, query=""):
    if not SUPABASE_ENABLED:
        return []
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}{query}", headers=supabase_headers())
        r.raise_for_status()
        return r.json()


async def sb_insert(table, payload):
    if not SUPABASE_ENABLED:
        return None
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=supabase_headers(), json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data


async def sb_upsert(table, payload, conflict):
    if not SUPABASE_ENABLED:
        return None
    headers = supabase_headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict}", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data


async def get_or_create_user(external_user_id):
    if not SUPABASE_ENABLED:
        return None
    existing = await sb_get("users", f"?external_user_id=eq.{external_user_id}&limit=1")
    if existing:
        return existing[0]
    return await sb_insert("users", {"external_user_id": external_user_id})


async def load_memory(external_user_id):
    if not SUPABASE_ENABLED:
        return {"supabase_enabled": False}
    try:
        user = await get_or_create_user(external_user_id)
        user_id = user["id"]
        profile = await sb_get("profiles", f"?user_id=eq.{user_id}&limit=1")
        return {
            "supabase_enabled": True,
            "user": user,
            "profile": profile[0] if profile else None,
            "recent_runs": await sb_get("runs", f"?user_id=eq.{user_id}&order=created_at.desc&limit=5"),
            "recent_decisions": await sb_get("decisions", f"?user_id=eq.{user_id}&order=created_at.desc&limit=5"),
            "open_actions": await sb_get("actions", f"?user_id=eq.{user_id}&status=eq.open&order=created_at.desc&limit=10"),
            "memory_items": await sb_get("memory_items", f"?user_id=eq.{user_id}&order=importance.desc,created_at.desc&limit=10")
        }
    except Exception as exc:
        return {"supabase_enabled": False, "memory_error": str(exc)}




def summarize_memory_for_prompt(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Compact memory so prompts stay fast and useful."""
    if not memory or not memory.get("supabase_enabled"):
        return {"status": "no_db_memory"}

    profile = memory.get("profile") or {}
    recent_runs = memory.get("recent_runs") or []
    recent_decisions = memory.get("recent_decisions") or []
    open_actions = memory.get("open_actions") or []
    memory_items = memory.get("memory_items") or []

    return {
        "status": "db_memory_live",
        "profile": {
            "role": profile.get("role"),
            "goals": profile.get("goals"),
            "experience": profile.get("experience"),
            "constraints": profile.get("constraints"),
            "preferences": profile.get("preferences"),
            "resume_context_available": bool(profile.get("resume_context"))
        },
        "recent_context": [
            {
                "mode": r.get("mode"),
                "input": str(r.get("input") or "")[:240],
                "decision": str((r.get("output") or {}).get("decision") or "")[:240],
                "next_move": str((r.get("output") or {}).get("next_move") or "")[:240],
                "priority": (r.get("output") or {}).get("priority")
            }
            for r in recent_runs[:3]
        ],
        "open_actions": [
            {"text": a.get("text"), "priority": a.get("priority"), "status": a.get("status")}
            for a in open_actions[:10]
        ],
        "recent_decisions": [
            {"decision": d.get("decision"), "risk": d.get("risk"), "priority": d.get("priority"), "next_move": d.get("next_move")}
            for d in recent_decisions[:3]
        ],
        "memory_items": [
            {"type": m.get("type"), "content": m.get("content"), "importance": m.get("importance")}
            for m in memory_items[:3]
        ]
    }


def derive_memory_items(output: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    """Create small durable memory candidates from each run."""
    items = []
    decision = output.get("decision")
    risk = output.get("risk")
    constraint = output.get("constraint")
    what_to_ignore = output.get("what_to_ignore")
    strategic_read = output.get("strategic_read")
    priority = output.get("priority", "medium")

    if decision:
        items.append({"type": "decision_pattern", "content": f"Mode {mode}: {decision}", "importance": 4 if priority in ["high", "critical"] else 3})
    if risk:
        items.append({"type": "recurring_risk", "content": risk, "importance": 4 if priority in ["high", "critical"] else 3})
    if constraint:
        items.append({"type": "constraint", "content": constraint, "importance": 4})
    if what_to_ignore:
        items.append({"type": "focus_filter", "content": what_to_ignore, "importance": 3})
    if strategic_read:
        items.append({"type": "strategic_read", "content": strategic_read, "importance": 3})
    return items[:5]


async def save_memory_items(external_user_id: str, output: Dict[str, Any], mode: str, source_run_id: Optional[str] = None):
    if not SUPABASE_ENABLED:
        return []
    user = await get_or_create_user(external_user_id)
    if not user:
        return []

    saved = []
    for item in derive_memory_items(output, mode):
        try:
            row = await sb_insert("memory_items", {
                "user_id": user["id"],
                "type": item["type"],
                "content": item["content"],
                "importance": item["importance"],
                "source_run_id": source_run_id,
                "metadata": {"source": "v94_auto_memory", "mode": mode}
            })
            saved.append(row)
        except Exception:
            pass
    return saved


def build_execution_loop(output: Dict[str, Any]) -> Dict[str, Any]:
    actions = output.get("actions") or []
    return {
        "current_focus": output.get("what_to_do_now") or output.get("next_move") or "",
        "next_action": actions[0] if actions else output.get("next_move", ""),
        "next_prompt": output.get("follow_up_prompt") or (output.get("auto_execution") or {}).get("next_prompt") or "",
        "save_recommendation": {
            "save_actions": bool(actions),
            "save_decision": bool(output.get("decision")),
            "save_memory": True
        },
        "loop_steps": [
            "Run the engine",
            "Save actions/decision",
            "Execute first action",
            "Run follow-up prompt if context changes"
        ],
        "stop_condition": (output.get("auto_execution") or {}).get("stop_condition") or "Stop when the next concrete action is clear and assigned."
    }

async def save_run_to_db(req, output, latency_ms, status="completed"):
    if not SUPABASE_ENABLED or not req.auto_save:
        return None
    user = await get_or_create_user(req.user_id or "local_user")
    return await sb_insert("runs", {
        "user_id": user["id"],
        "session_id": req.session_id,
        "mode": req.mode,
        "depth": req.depth,
        "input": req.input,
        "context": req.context,
        "output": output,
        "model": MODEL,
        "latency_ms": latency_ms,
        "status": status
    })


async def save_learning_event(external_user_id, event_type, mode=None, metadata=None):
    if not SUPABASE_ENABLED:
        return None
    user = await get_or_create_user(external_user_id)
    return await sb_insert("learning_events", {
        "user_id": user["id"],
        "event_type": event_type,
        "mode": mode,
        "metadata": metadata or {}
    })


async def ai_run(req, memory, loop_mode=False):
    mode = req.mode if req.mode in MODE_GUIDANCE else "execution"
    depth = req.depth if req.depth in DEPTH_GUIDANCE else "standard"
    response = await asyncio.wait_for(
        client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt(mode, depth, loop_mode)},
                {"role": "user", "content": build_user_prompt(req, memory)}
            ],
            temperature=0.25,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"},
        ),
        timeout=TIMEOUT,
    )
    return normalize_output(extract_json(response.choices[0].message.content))


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /\n"


@app.get("/")
async def root():
    return {"ok": True, "service": APP_NAME, "version": "V95.2"}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": APP_NAME,
        "version": "V95.2",
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "supabase_enabled": SUPABASE_ENABLED,
        "timeout_seconds": TIMEOUT,
        "max_tokens": MAX_TOKENS,
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


@app.get("/debug")
async def debug():
    return {
        "ok": True,
        "version": "V95.2",
        "routes": [
            "/", "/health", "/debug", "/schema", "/run", "/run-test", "/auto-loop",
            "/recent-runs", "/memory", "/memory-summary", "/stability-check", "/actions", "/save-action",
            "/decisions", "/save-decision", "/profile", "/robots.txt"
        ],
        "model": MODEL,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "supabase_enabled": SUPABASE_ENABLED,
        "modes": list(MODE_GUIDANCE.keys()),
        "depths": list(DEPTH_GUIDANCE.keys())
    }


@app.get("/schema")
async def schema():
    return {
        "ok": True,
        "version": "V95.2",
        "response_schema": CANONICAL_SCHEMA,
        "modes": MODE_GUIDANCE,
        "depths": list(DEPTH_GUIDANCE.keys())
    }


@app.post("/run")
async def run(req: RunRequest):
    start = time.perf_counter()
    try:
        memory = await load_memory(req.user_id or "local_user")
        output = await ai_run(req, memory, False)
        latency_ms = int((time.perf_counter() - start) * 1000)

        try:
            saved = await save_run_to_db(req, output, latency_ms)
            await save_learning_event(req.user_id or "local_user", "run_created", req.mode, {
                "depth": req.depth,
                "latency_ms": latency_ms,
                "saved": bool(saved)
            })
            if saved and isinstance(saved, dict):
                output["run_id"] = saved.get("id")
                try:
                    memory_saved = await save_memory_items(req.user_id or "local_user", output, req.mode or "execution", saved.get("id"))
                    output["memory_items_saved"] = len(memory_saved)
                except Exception as memory_error:
                    output["memory_item_warning"] = str(memory_error)
        except Exception as save_error:
            output["memory_save_warning"] = str(save_error)

        return validate_output_shape(output)

    except asyncio.TimeoutError:
        out = fallback_response(f"Backend/OpenAI request exceeded {TIMEOUT} seconds.")
        out["status"] = "timeout_fallback"
        return validate_output_shape(out)

    except Exception as exc:
        out = fallback_response(f"Backend error: {str(exc)}")
        out["status"] = "error_fallback"
        return validate_output_shape(out)


@app.post("/auto-loop")
async def auto_loop(req: AutoLoopRequest):
    # V95 stability lock: no autonomous loop yet.
    # Manual execution only until /run, /memory, frontend rendering, and DB saves are proven stable.
    base_req = RunRequest(
        input=req.input,
        context=req.context,
        mode=req.mode,
        depth=req.depth,
        user_id=req.user_id,
        session_id=req.session_id,
        auto_save=True
    )
    memory = await load_memory(req.user_id or "local_user")
    try:
        output = await ai_run(base_req, memory, False)
    except Exception as exc:
        output = fallback_response(f"Manual loop planning failed: {str(exc)}")

    output = validate_output_shape(output)
    output["auto_execution"]["enabled"] = False
    output["manual_execution_only"] = True
    output["execution_loop"]["loop_steps"] = [
        "Review output",
        "Save actions or decision",
        "Execute first action manually",
        "Run follow-up prompt manually after progress"
    ]

    await save_learning_event(req.user_id or "local_user", "manual_loop_planned", req.mode, {"auto_disabled": True})
    return {"ok": True, "version": "V95.2", "auto_enabled": False, "message": "Manual execution loop only in V95.", "final": output}



@app.post("/run-test")
async def run_test():
    req = RunRequest(
        input="Test V95 stability. Give me a decision, next move, actions, risk, priority, and manual execution loop.",
        mode="execution",
        depth="standard",
        user_id="local_user",
        session_id="v95_test",
        auto_save=False
    )
    try:
        memory = await load_memory("local_user")
        output = await ai_run(req, memory, False)
        return {"ok": True, "version": "V95.2", "output": validate_output_shape(output)}
    except Exception as exc:
        return {"ok": False, "version": "V95.2", "output": validate_output_shape(fallback_response(str(exc)))}

@app.get("/memory")
async def memory(user_id: str = Query("local_user")):
    return await load_memory(user_id)




@app.get("/memory-summary")
async def memory_summary(user_id: str = Query("local_user")):
    memory = await load_memory(user_id)
    return {"ok": True, "version": "V95.2", "summary": summarize_memory_for_prompt(memory)}

@app.post("/stability-check")
async def stability_check():
    health_data = await health()
    checks = {
        "backend_live": True,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "supabase_enabled": SUPABASE_ENABLED,
        "model": MODEL,
        "timeout_seconds": TIMEOUT,
        "max_tokens": MAX_TOKENS,
        "manual_execution_only": True,
        "auto_loop_enabled": False,
        "memory_injection": "last_3_items"
    }
    return {"ok": True, "version": "V95.2", "health": health_data, "checks": checks}

@app.get("/recent-runs")
async def recent_runs(user_id: str = Query("local_user"), limit: int = Query(20, ge=1, le=50)):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "runs": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "runs": await sb_get("runs", f"?user_id=eq.{user['id']}&order=created_at.desc&limit={limit}")}


@app.get("/actions")
async def actions(user_id: str = Query("local_user"), status: str = Query("open")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "actions": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "actions": await sb_get("actions", f"?user_id=eq.{user['id']}&status=eq.{status}&order=created_at.desc&limit=50")}


@app.post("/save-action")
async def save_action(req: SaveActionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_insert("actions", {
        "user_id": user["id"],
        "run_id": req.run_id,
        "text": req.text,
        "priority": req.priority,
        "status": req.status,
        "owner": req.owner,
        "metadata": req.metadata or {}
    })
    await save_learning_event(req.user_id or "local_user", "action_saved", None, {"action_id": row.get("id") if isinstance(row, dict) else None})
    return {"ok": True, "action": row}


@app.get("/decisions")
async def decisions(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "decisions": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "decisions": await sb_get("decisions", f"?user_id=eq.{user['id']}&order=created_at.desc&limit=50")}


@app.post("/save-decision")
async def save_decision(req: SaveDecisionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_insert("decisions", {
        "user_id": user["id"],
        "run_id": req.run_id,
        "decision": req.decision,
        "risk": req.risk,
        "priority": req.priority,
        "rationale": req.rationale,
        "next_move": req.next_move,
        "metadata": req.metadata or {}
    })
    await save_learning_event(req.user_id or "local_user", "decision_saved", None, {"decision_id": row.get("id") if isinstance(row, dict) else None})
    return {"ok": True, "decision": row}


@app.get("/profile")
async def get_profile(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "profile": None}
    user = await get_or_create_user(user_id)
    rows = await sb_get("profiles", f"?user_id=eq.{user['id']}&limit=1")
    return {"ok": True, "profile": rows[0] if rows else None}


@app.post("/profile")
async def save_profile(req: ProfileRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_upsert("profiles", {
        "user_id": user["id"],
        "role": req.role,
        "goals": req.goals,
        "experience": req.experience,
        "constraints": req.constraints,
        "resume_context": req.resume_context,
        "preferences": req.preferences or {},
        "updated_at": now_iso()
    }, "user_id")
    await save_learning_event(req.user_id or "local_user", "profile_saved", None, {})
    return {"ok": True, "profile": row}
