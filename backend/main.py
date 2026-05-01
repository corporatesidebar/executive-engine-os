
import os, json, re, time, asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

APP_NAME = "Executive Engine OS V92 Backend"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2800"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title=APP_NAME, version="92.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")], allow_methods=["*"], allow_headers=["*"], allow_credentials=False)

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
    metadata: Optional[Dict[str, Any]] = None

class SaveDecisionRequest(BaseModel):
    user_id: Optional[str] = "local_user"
    run_id: Optional[str] = None
    decision: str
    risk: Optional[str] = None
    priority: Optional[str] = "medium"
    rationale: Optional[str] = None
    next_move: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProfileRequest(BaseModel):
    user_id: Optional[str] = "local_user"
    role: Optional[str] = None
    goals: Optional[str] = None
    experience: Optional[str] = None
    constraints: Optional[str] = None
    resume_context: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

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
    "auto_execution": {"enabled": False, "next_prompt": "", "suggested_loop": [], "stop_condition": ""},
    "reality_check": "",
    "leverage": "",
    "constraint": "",
    "financial_impact": "",
}

MODE_GUIDANCE = {
    "execution": "Turn a messy business issue, blocker, task, or vague situation into a direct execution plan.",
    "daily_brief": "Build an operating plan for the day: main focus, priority sequence, follow-ups, risks, and what to ignore.",
    "decision": "Make a clear recommendation with tradeoffs, risk, opportunity, missing information, and next move.",
    "meeting": "Prepare meeting objective, agenda, talking points, hard questions, stakeholder read, risks, and follow-up.",
    "personal": "Clarify messy personal, admin, communication, or life context with practical next moves.",
    "content": "Create content, scripts, social posts, Figma prompts, Canva briefs, landing page ideas, and marketing angles.",
    "learning": "Analyze patterns, bottlenecks, decision habits, and workflow recommendations.",
}

DEPTH_GUIDANCE = {
    "quick": "Concise but useful. Actions: 3-4.",
    "standard": "Strong executive brief. Actions: 4-6. Each field adds useful context.",
    "deep": "Strategic operator brief. Actions: 6-8. Include sequence, hidden constraints, and tradeoffs.",
    "board_level": "Executive memo style. Actions: 6-10. Include risk, financial impact, delegation, timeline, and metrics.",
}

def now_iso(): return datetime.now(timezone.utc).isoformat()

def fallback_response(reason="Backend fallback"):
    return {
        "executive_summary": "The full AI response was not completed, so use this fallback to keep execution moving.",
        "what_to_do_now": "Clarify the desired outcome, identify the biggest constraint, and execute the first concrete action immediately.",
        "decision": "Move forward with the clearest low-regret next step instead of waiting for perfect information.",
        "why_this_matters": "Execution velocity matters. Waiting for a perfect answer creates drag and prevents momentum.",
        "next_move": "Write the desired outcome in one sentence, list the top constraint, and take a 15-minute action that moves the situation forward.",
        "actions": ["Write the desired outcome in one clear sentence.", "Identify the one constraint blocking progress.", "Choose the first action that can be completed in 15 minutes.", "Execute it now, then reassess with better context.", "Retry the engine if a deeper strategic answer is still needed."],
        "priority": "high",
        "risk": "The main risk is staying stuck because the input, backend, or decision context is incomplete.",
        "opportunity": "You can still create forward motion by reducing the situation to outcome, constraint, and first move.",
        "what_to_ignore": "Ignore perfect formatting, overthinking, and low-value details that do not change the immediate move.",
        "questions_to_answer": ["What outcome do you want?", "What is blocking progress?", "What decision needs to be made now?"],
        "delegation": "If another person owns the blocker, assign them one clear deliverable and a deadline.",
        "timeline": "Immediate: define outcome and constraint. Next 15 minutes: take first action. Today: reassess and create the next step.",
        "success_metric": "A concrete action is completed and the next decision is clearer.",
        "strategic_read": "When uncertain, the operator move is to create clarity through action rather than wait for more information.",
        "follow_up_prompt": "Now turn this into a complete execution plan with owner, timeline, and success metric.",
        "auto_execution": {"enabled": False, "next_prompt": "Turn this fallback into a full execution plan.", "suggested_loop": ["Clarify outcome", "Identify constraint", "Execute first action"], "stop_condition": "Stop when the next physical or digital action is clear."},
        "reality_check": "The current response is a fallback, not a full strategic answer.",
        "leverage": "Momentum and clarity are the leverage points.",
        "constraint": reason,
        "financial_impact": "Slow execution creates opportunity cost; the immediate goal is to reduce that drag.",
    }

def extract_json(text):
    if not text: raise ValueError("Empty model response")
    try: return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m: return json.loads(m.group(0))
    raise ValueError("No valid JSON object found")

def ensure_list(value):
    if isinstance(value, list): return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip(): return [value.strip()]
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
    base["priority"] = priority if priority in {"low","medium","high","critical"} else "medium"
    auto = base.get("auto_execution") if isinstance(base.get("auto_execution"), dict) else {}
    base["auto_execution"] = {
        "enabled": bool(auto.get("enabled", False)),
        "next_prompt": str(auto.get("next_prompt") or base.get("follow_up_prompt") or ""),
        "suggested_loop": ensure_list(auto.get("suggested_loop")) or base["actions"][:3],
        "stop_condition": str(auto.get("stop_condition") or "Stop when the next move is clear enough to execute.")
    }
    for k, v in {
        "what_to_do_now": base.get("executive_summary",""),
        "next_move": base["actions"][0] if base["actions"] else "",
        "reality_check": base.get("why_this_matters",""),
        "leverage": base.get("opportunity",""),
        "constraint": base.get("risk",""),
        "financial_impact": "The financial impact depends on execution speed, decision quality, and whether the next move removes a real constraint."
    }.items():
        if not base.get(k): base[k] = v
    return base

def build_system_prompt(mode, depth, loop_mode=False):
    loop = "AUTO-EXECUTION LOOP: Provide the next internal prompt, suggested internal loop steps, and stop condition. Do not claim external actions were completed." if loop_mode else "AUTO-EXECUTION: Provide a useful next_prompt for the next run. Do not claim external actions were completed."
    return f"""
You are Executive Engine OS V92.
Act like an elite CEO, COO, President, Chief of Staff, strategist, and operator.
Turn messy input into decisive executive execution.
Return ONLY valid JSON. No markdown. No text outside JSON.

Schema:
{json.dumps(CANONICAL_SCHEMA)}

Quality:
- Be specific, direct, and execution-focused.
- Do not give generic, shallow, obvious, or motivational advice.
- Every field must add distinct useful context.
- Each action must be executable today.
- Include reasoning, tradeoffs, risk, sequence, delegation, timeline, and success metric.
- If context is weak, still produce a useful answer and ask sharp questions.
- Do not claim DB, Gmail, Calendar, Canva, Figma, CRM, or external app access unless explicitly provided.
- Make follow_up_prompt a copy/paste prompt the user can run next.

Mode guidance: {MODE_GUIDANCE.get(mode, MODE_GUIDANCE["execution"])}
Depth guidance: {DEPTH_GUIDANCE.get(depth, DEPTH_GUIDANCE["standard"])}
{loop}
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
{json.dumps(memory or {}, indent=2)}

CONTEXT:
{req.context or "No additional context provided."}

USER INPUT:
{req.input}
"""

def sb_headers():
    return {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

async def sb_get(table, query=""):
    if not SUPABASE_ENABLED: return []
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}{query}", headers=sb_headers())
        r.raise_for_status()
        return r.json()

async def sb_insert(table, payload):
    if not SUPABASE_ENABLED: return None
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data

async def sb_upsert(table, payload, conflict):
    if not SUPABASE_ENABLED: return None
    h = sb_headers(); h["Prefer"] = "resolution=merge-duplicates,return=representation"
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict}", headers=h, json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data

async def get_or_create_user(external_user_id):
    if not SUPABASE_ENABLED: return None
    existing = await sb_get("users", f"?external_user_id=eq.{external_user_id}&limit=1")
    if existing: return existing[0]
    return await sb_insert("users", {"external_user_id": external_user_id})

async def load_memory(external_user_id):
    if not SUPABASE_ENABLED: return {"supabase_enabled": False}
    try:
        user = await get_or_create_user(external_user_id)
        user_id = user["id"]
        return {
            "supabase_enabled": True,
            "user": user,
            "profile": (await sb_get("profiles", f"?user_id=eq.{user_id}&limit=1"))[:1],
            "recent_runs": await sb_get("runs", f"?user_id=eq.{user_id}&order=created_at.desc&limit=5"),
            "recent_decisions": await sb_get("decisions", f"?user_id=eq.{user_id}&order=created_at.desc&limit=5"),
            "open_actions": await sb_get("actions", f"?user_id=eq.{user_id}&status=eq.open&order=created_at.desc&limit=10"),
            "memory_items": await sb_get("memory_items", f"?user_id=eq.{user_id}&order=importance.desc,created_at.desc&limit=10")
        }
    except Exception as exc:
        return {"supabase_enabled": False, "memory_error": str(exc)}

async def save_run_to_db(req, output, latency_ms, status="completed"):
    if not SUPABASE_ENABLED or not req.auto_save: return None
    user = await get_or_create_user(req.user_id or "local_user")
    return await sb_insert("runs", {"user_id": user["id"], "session_id": req.session_id, "mode": req.mode, "depth": req.depth, "input": req.input, "context": req.context, "output": output, "model": MODEL, "latency_ms": latency_ms, "status": status})

async def save_learning_event(external_user_id, event_type, mode=None, metadata=None):
    if not SUPABASE_ENABLED: return None
    user = await get_or_create_user(external_user_id)
    return await sb_insert("learning_events", {"user_id": user["id"], "event_type": event_type, "mode": mode, "metadata": metadata or {}})

async def ai_run(req, memory, loop_mode=False):
    mode = req.mode if req.mode in MODE_GUIDANCE else "execution"
    depth = req.depth if req.depth in DEPTH_GUIDANCE else "standard"
    response = await asyncio.wait_for(client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": build_system_prompt(mode, depth, loop_mode)}, {"role": "user", "content": build_user_prompt(req, memory)}],
        temperature=0.25,
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
    ), timeout=TIMEOUT)
    return normalize_output(extract_json(response.choices[0].message.content))

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots(): return "User-agent: *\nDisallow: /\n"

@app.get("/")
async def root(): return {"ok": True, "service": APP_NAME, "version": "V92"}

@app.get("/health")
async def health():
    return {"ok": True, "service": APP_NAME, "version": "V92", "model": MODEL, "openai_key_set": bool(os.getenv("OPENAI_API_KEY")), "supabase_enabled": SUPABASE_ENABLED, "timeout_seconds": TIMEOUT, "max_tokens": MAX_TOKENS}

@app.get("/debug")
async def debug():
    return {"ok": True, "version": "V92", "routes": ["/", "/health", "/debug", "/schema", "/run", "/auto-loop", "/recent-runs", "/memory", "/actions", "/save-action", "/decisions", "/save-decision", "/profile", "/robots.txt"], "model": MODEL, "openai_key_set": bool(os.getenv("OPENAI_API_KEY")), "supabase_enabled": SUPABASE_ENABLED, "modes": list(MODE_GUIDANCE.keys()), "depths": list(DEPTH_GUIDANCE.keys())}

@app.get("/schema")
async def schema():
    return {"ok": True, "version": "V92", "response_schema": CANONICAL_SCHEMA, "modes": MODE_GUIDANCE, "depths": list(DEPTH_GUIDANCE.keys())}

@app.post("/run")
async def run(req: RunRequest):
    start = time.perf_counter()
    try:
        memory = await load_memory(req.user_id or "local_user")
        output = await ai_run(req, memory, False)
        latency_ms = int((time.perf_counter() - start) * 1000)
        try:
            saved = await save_run_to_db(req, output, latency_ms)
            await save_learning_event(req.user_id or "local_user", "run_created", req.mode, {"depth": req.depth, "latency_ms": latency_ms, "saved": bool(saved)})
            if saved and isinstance(saved, dict): output["run_id"] = saved.get("id")
        except Exception as save_error:
            output["memory_save_warning"] = str(save_error)
        return output
    except asyncio.TimeoutError:
        out = fallback_response(f"Backend/OpenAI request exceeded {TIMEOUT} seconds."); out["status"] = "timeout_fallback"; return out
    except Exception as exc:
        out = fallback_response(f"Backend error: {str(exc)}"); out["status"] = "error_fallback"; return out

@app.post("/auto-loop")
async def auto_loop(req: AutoLoopRequest):
    steps, current_input = [], req.input
    memory = await load_memory(req.user_id or "local_user")
    for i in range(max(1, min(req.max_steps or 3, 5))):
        loop_req = RunRequest(input=current_input, context=req.context, mode=req.mode, depth=req.depth, user_id=req.user_id, session_id=req.session_id, auto_save=True)
        try: output = await ai_run(loop_req, memory, True)
        except Exception as exc: output = fallback_response(f"Auto-loop step {i+1} failed: {str(exc)}")
        steps.append({"step": i + 1, "input": current_input, "output": output})
        next_prompt = output.get("auto_execution", {}).get("next_prompt") or output.get("follow_up_prompt")
        if not next_prompt: break
        current_input = next_prompt
    await save_learning_event(req.user_id or "local_user", "auto_loop_created", req.mode, {"steps": len(steps)})
    return {"ok": True, "version": "V92", "steps": steps, "final": steps[-1]["output"] if steps else None}

@app.get("/memory")
async def memory(user_id: str = Query("local_user")): return await load_memory(user_id)

@app.get("/recent-runs")
async def recent_runs(user_id: str = Query("local_user"), limit: int = Query(20, ge=1, le=50)):
    if not SUPABASE_ENABLED: return {"ok": True, "supabase_enabled": False, "runs": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "runs": await sb_get("runs", f"?user_id=eq.{user['id']}&order=created_at.desc&limit={limit}")}

@app.get("/actions")
async def actions(user_id: str = Query("local_user"), status: str = Query("open")):
    if not SUPABASE_ENABLED: return {"ok": True, "supabase_enabled": False, "actions": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "actions": await sb_get("actions", f"?user_id=eq.{user['id']}&status=eq.{status}&order=created_at.desc&limit=50")}

@app.post("/save-action")
async def save_action(req: SaveActionRequest):
    if not SUPABASE_ENABLED: return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_insert("actions", {"user_id": user["id"], "run_id": req.run_id, "text": req.text, "priority": req.priority, "status": req.status, "owner": req.owner, "metadata": req.metadata or {}})
    await save_learning_event(req.user_id or "local_user", "action_saved", None, {"action_id": row.get("id") if isinstance(row, dict) else None})
    return {"ok": True, "action": row}

@app.get("/decisions")
async def decisions(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED: return {"ok": True, "supabase_enabled": False, "decisions": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "decisions": await sb_get("decisions", f"?user_id=eq.{user['id']}&order=created_at.desc&limit=50")}

@app.post("/save-decision")
async def save_decision(req: SaveDecisionRequest):
    if not SUPABASE_ENABLED: return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_insert("decisions", {"user_id": user["id"], "run_id": req.run_id, "decision": req.decision, "risk": req.risk, "priority": req.priority, "rationale": req.rationale, "next_move": req.next_move, "metadata": req.metadata or {}})
    await save_learning_event(req.user_id or "local_user", "decision_saved", None, {"decision_id": row.get("id") if isinstance(row, dict) else None})
    return {"ok": True, "decision": row}

@app.get("/profile")
async def get_profile(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED: return {"ok": True, "supabase_enabled": False, "profile": None}
    user = await get_or_create_user(user_id)
    rows = await sb_get("profiles", f"?user_id=eq.{user['id']}&limit=1")
    return {"ok": True, "profile": rows[0] if rows else None}

@app.post("/profile")
async def save_profile(req: ProfileRequest):
    if not SUPABASE_ENABLED: return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")
    row = await sb_upsert("profiles", {"user_id": user["id"], "role": req.role, "goals": req.goals, "experience": req.experience, "constraints": req.constraints, "resume_context": req.resume_context, "preferences": req.preferences or {}, "updated_at": now_iso()}, "user_id")
    await save_learning_event(req.user_id or "local_user", "profile_saved", None, {})
    return {"ok": True, "profile": row}
