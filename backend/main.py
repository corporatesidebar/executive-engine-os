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


APP_NAME = "Executive Engine OS V97"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2800"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title=APP_NAME, version="97.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_CONTEXT = """
Executive Engine OS real project context:
- Product: AI executive command center for CEOs/COOs/founders.
- Backend live on Render: https://executive-engine-os.onrender.com
- Frontend live on Render: https://executive-engine-frontend.onrender.com
- Current backend: V97 quality fix.
- Previous confirmed backend: V96.2 technical loop working.
- OpenAI connected.
- Supabase connected.
- RLS enabled and safe.
- /health works.
- /debug works.
- /schema works.
- /run works and returns structured JSON.
- /memory works and returns recent_runs and memory_items.
- Runs save to Supabase.
- Auto memory extraction works.
- Manual execution loop works.
- Manual execution only.
- Auto-loop disabled.
- No bot team yet.
- No external automation yet.
- No Gmail/Calendar/CRM/Figma/Canva write integration yet.
- Frontend renders structured output and right sidebar memory/status.
- UI is usable but not final.
- Figma redesign comes later, after backend/output quality is stable.
- Current priority: response quality, frontend DB validation, right-panel persistence, and manual execution loop.
- Architecture: Frontend -> Render Backend -> OpenAI + Supabase.
- Operating loop: Memory -> Decision -> Action -> Memory -> Repeat.

Current execution stage:
1. Stop building new features.
2. Validate backend-memory loop with real inputs.
3. Confirm /run saves new recent_runs.
4. Confirm /memory shows the newest run.
5. Confirm /save-action creates open_actions.
6. Confirm /save-decision creates recent_decisions.
7. Confirm frontend right panel reads backend memory, not only local storage.
8. Only after this: profile-aware output, then frontend polish, then Figma.

Forbidden generic advice:
- Do not tell the user to review market trends.
- Do not tell the user to review user feedback unless the specific feedback source exists.
- Do not say product roadmap unless referring to the actual Executive Engine build sequence.
- Do not invent a product development team, marketing team, or team members.
- Do not recommend meetings unless the user asks for meeting prep.
- Do not recommend customer research, market share, churn, retention, or feature adoption unless the user asks about customers.
- Do not recommend new features before validation of the existing execution loop.
- Do not recommend automation, agents, or bots yet.
- Do not recommend Figma redesign yet.

When asked "What should I focus on today to move Executive Engine OS forward?":
The correct answer must be about:
- confirming V97 backend response quality
- testing /run from frontend
- checking /memory for a new recent_run
- using Save Action and Save Decision buttons
- verifying /actions and /decisions endpoints
- confirming right sidebar displays saved backend state
- documenting pass/fail results
"""



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


CANONICAL_SCHEMA: Dict[str, Any] = {
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fallback_response(reason: str = "Backend fallback") -> Dict[str, Any]:
    return {
        "executive_summary": "The full AI response was not completed, so use this fallback to keep execution moving.",
        "what_to_do_now": "Verify the live Executive Engine OS loop: run one frontend command, confirm /memory creates a new recent_run, then test Save Action and Save Decision.",
        "decision": "Do not build new features until the backend-memory-frontend loop is verified end to end.",
        "why_this_matters": "Execution velocity matters. Waiting for a perfect answer creates drag and prevents momentum.",
        "next_move": "Run the frontend prompt again, then check /memory, /actions, and /decisions to confirm Supabase persistence.",
        "actions": [
            "Run a real frontend command through /run.",
            "Open /memory and confirm a new recent_run appears at the top.",
            "Click Save Action in the frontend and confirm /actions returns it.",
            "Click Save Decision in the frontend and confirm /decisions returns it.",
            "Document pass/fail before building V97."
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
        "execution_loop": {
            "current_focus": "Restore a stable backend response.",
            "next_action": "Check the failed route/import error and redeploy a clean backend file.",
            "next_prompt": "Fix the backend deploy error and return a stable /health response.",
            "save_recommendation": {"save_memory": False, "save_actions": False, "save_decision": False},
            "loop_steps": ["Fix backend file", "Deploy", "Test /health", "Test /run"],
            "stop_condition": "Stop when /health and /run both work."
        },
        "reality_check": "The current response is a fallback, not a full strategic answer.",
        "leverage": "Momentum and clarity are the leverage points.",
        "constraint": reason,
        "financial_impact": "Slow execution creates opportunity cost; the immediate goal is to reduce that drag.",
        "manual_execution_only": True,
        "version": "V97",
        "project_context_applied": True
    }


def extract_json(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty model response")
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
    raise ValueError("No valid JSON object found")


def ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


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
            "Execute first action manually",
            "Run follow-up prompt manually if context changes"
        ],
        "stop_condition": (output.get("auto_execution") or {}).get("stop_condition") or "Stop when the next concrete action is clear and assigned."
    }


def normalize_output(data: Any, reason: str = "") -> Dict[str, Any]:
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
    base["manual_execution_only"] = True
    base["version"] = "V97"
    base["project_context_applied"] = True
    return base



GENERIC_MEMORY_BLOCKLIST = [
    "market trends",
    "user feedback",
    "product roadmap",
    "product development team",
    "marketing team",
    "market demands",
    "feature adoption",
    "customer loyalty",
    "user satisfaction scores",
    "churn",
    "market share",
    "requested features",
    "pain points"
]

def is_generic_prior_context(value: Any) -> bool:
    text = json.dumps(value, default=str).lower()
    return any(term in text for term in GENERIC_MEMORY_BLOCKLIST)

def project_directive_for_input(user_input: str) -> str:
    text = (user_input or "").lower()
    if "executive engine" in text or "os forward" in text or "move executive" in text:
        return """
PROJECT-SPECIFIC DIRECTIVE:
The user is asking what to do next for Executive Engine OS.
Do not answer with generic product/customer/market advice.
Answer with backend/frontend/Supabase execution validation steps.
Focus on V97 quality validation, /run, /memory, /save-action, /save-decision, /actions, /decisions, frontend right panel, and manual execution.
"""
    return ""

def summarize_memory_for_prompt(memory: Dict[str, Any]) -> Dict[str, Any]:
    if not memory or not memory.get("supabase_enabled"):
        return {"project_context": PROJECT_CONTEXT, "status": "no_db_memory"}

    profile = memory.get("profile") or {}
    recent_runs = [r for r in (memory.get("recent_runs") or []) if not is_generic_prior_context(r)]
    recent_decisions = [d for d in (memory.get("recent_decisions") or []) if not is_generic_prior_context(d)]
    open_actions = memory.get("open_actions") or []
    memory_items = [m for m in (memory.get("memory_items") or []) if not is_generic_prior_context(m)]

    return {
        "project_context": PROJECT_CONTEXT,
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
    items = []
    for mem_type, key, importance in [
        ("decision_pattern", "decision", 4),
        ("recurring_risk", "risk", 4),
        ("constraint", "constraint", 4),
        ("focus_filter", "what_to_ignore", 3),
        ("strategic_read", "strategic_read", 3),
    ]:
        value = output.get(key)
        if value:
            items.append({"type": mem_type, "content": value, "importance": importance})
    return items[:5]


def build_system_prompt(mode: str, depth: str, loop_mode: bool = False) -> str:
    return f"""
You are Executive Engine OS V97.

PROJECT CONTEXT:
{PROJECT_CONTEXT}

ROLE:
Act like an elite CEO, COO, President, Chief of Staff, strategist, and operator for this specific product.
Turn messy input into decisive executive execution using the real Executive Engine OS project context.

OUTPUT:
Return ONLY valid JSON.
No markdown.
No prose outside JSON.
Use this exact schema:
{json.dumps(CANONICAL_SCHEMA)}

QUALITY:
- Make answers specific to Executive Engine OS, Render backend, Supabase memory, frontend behavior, and manual execution.
- Treat old generic memory as contamination if it talks about market trends, user feedback, product roadmap, feature requests, marketing team, retention, churn, or customers.
- If the input asks what to focus on today for Executive Engine OS, the answer must be a validation plan for the live system, not business/product strategy.
- Use exact endpoint names and exact checks.
- The first action must be something the user can do immediately in the browser or Render/Supabase.
- Avoid generic SaaS/product advice unless the user specifically provides that context.
- Give exact next steps, endpoints, files, deploy checks, and success criteria.
- Be specific, direct, and execution-focused.
- Do not give generic, shallow, obvious, or motivational advice.
- Every field must add distinct useful context.
- Each action must be executable today.
- Include reasoning, tradeoffs, risk, sequence, delegation, timeline, and success metric.
- Manual execution only. Do not claim automation is running.
- Do not claim DB, Gmail, Calendar, Canva, Figma, CRM, or external app access unless explicitly provided.
- Make follow_up_prompt a copy/paste prompt the user can run next.

MODE:
{MODE_GUIDANCE.get(mode, MODE_GUIDANCE["execution"])}

DEPTH:
{DEPTH_GUIDANCE.get(depth, DEPTH_GUIDANCE["standard"])}
"""


def build_user_prompt(req: RunRequest, memory: Optional[Dict[str, Any]] = None) -> str:
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

{project_directive_for_input(req.input)}
"""


def supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


async def sb_get(table: str, query: str = "") -> Any:
    if not SUPABASE_ENABLED:
        return []
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}{query}", headers=supabase_headers())
        r.raise_for_status()
        return r.json()


async def sb_insert(table: str, payload: Dict[str, Any]) -> Any:
    if not SUPABASE_ENABLED:
        return None
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=supabase_headers(), json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data


async def sb_upsert(table: str, payload: Dict[str, Any], conflict: str) -> Any:
    if not SUPABASE_ENABLED:
        return None
    headers = supabase_headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict}", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) and data else data


async def get_or_create_user(external_user_id: str) -> Optional[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return None
    existing = await sb_get("users", f"?external_user_id=eq.{external_user_id}&limit=1")
    if existing:
        return existing[0]
    return await sb_insert("users", {"external_user_id": external_user_id})


async def load_memory(external_user_id: str) -> Dict[str, Any]:
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


async def save_run_to_db(req: RunRequest, output: Dict[str, Any], latency_ms: int, status: str = "completed") -> Optional[Dict[str, Any]]:
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


async def save_learning_event(external_user_id: str, event_type: str, mode: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    if not SUPABASE_ENABLED:
        return None
    user = await get_or_create_user(external_user_id)
    return await sb_insert("learning_events", {
        "user_id": user["id"],
        "event_type": event_type,
        "mode": mode,
        "metadata": metadata or {}
    })


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
                "metadata": {"source": "v96_2_auto_memory", "mode": mode}
            })
            saved.append(row)
        except Exception:
            pass
    return saved


async def ai_run(req: RunRequest, memory: Dict[str, Any], loop_mode: bool = False) -> Dict[str, Any]:
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
    return {"ok": True, "service": APP_NAME, "version": "V97"}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": APP_NAME,
        "version": "V97",
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
        "version": "V97",
        "routes": [
            "/", "/health", "/debug", "/schema", "/run", "/run-test", "/auto-loop",
            "/engine-state", "/project-context", "/quality-test", "/memory", "/memory-summary", "/stability-check",
            "/recent-runs", "/actions", "/save-action", "/decisions", "/save-decision", "/profile", "/robots.txt"
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
        "version": "V97",
        "response_schema": CANONICAL_SCHEMA,
        "modes": MODE_GUIDANCE,
        "depths": list(DEPTH_GUIDANCE.keys())
    }


@app.get("/project-context")
async def project_context():
    return {
        "ok": True,
        "version": "V97",
        "project_context": PROJECT_CONTEXT,
        "manual_execution_only": True,
        "auto_loop_enabled": False
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
                "saved": bool(saved),
                "project_context_applied": True
            })
            if saved and isinstance(saved, dict):
                output["run_id"] = saved.get("id")
                memory_saved = await save_memory_items(req.user_id or "local_user", output, req.mode or "execution", saved.get("id"))
                output["memory_items_saved"] = len(memory_saved)
        except Exception as save_error:
            output["memory_save_warning"] = str(save_error)

        return normalize_output(output)

    except asyncio.TimeoutError:
        out = fallback_response(f"Backend/OpenAI request exceeded {TIMEOUT} seconds.")
        out["status"] = "timeout_fallback"
        return normalize_output(out)

    except Exception as exc:
        out = fallback_response(f"Backend error: {str(exc)}")
        out["status"] = "error_fallback"
        return normalize_output(out)


@app.post("/run-test")
async def run_test():
    req = RunRequest(
        input="What should I focus on today to move Executive Engine OS forward?",
        mode="execution",
        depth="standard",
        user_id="local_user",
        session_id="v96_2_test",
        auto_save=False
    )
    try:
        memory = await load_memory("local_user")
        output = await ai_run(req, memory, False)
        return {"ok": True, "version": "V97", "output": normalize_output(output)}
    except Exception as exc:
        return {"ok": False, "version": "V97", "output": normalize_output(fallback_response(str(exc)))}




@app.post("/quality-test")
@app.get("/quality-test")
async def quality_test():
    req = RunRequest(
        input="What should I focus on today to move Executive Engine OS forward?",
        mode="execution",
        depth="standard",
        user_id="local_user",
        session_id="v96_3_quality_test",
        auto_save=False
    )
    try:
        memory = await load_memory("local_user")
        output = await ai_run(req, memory, False)
        normalized = normalize_output(output)
        text = json.dumps(normalized).lower()
        generic_hits = [term for term in GENERIC_MEMORY_BLOCKLIST if term in text]
        return {
            "ok": True,
            "version": "V97",
            "generic_hits": generic_hits,
            "passed_quality_gate": len(generic_hits) == 0,
            "output": normalized
        }
    except Exception as exc:
        return {
            "ok": False,
            "version": "V97",
            "error": str(exc),
            "output": normalize_output(fallback_response(str(exc)))
        }

@app.post("/auto-loop")
async def auto_loop(req: AutoLoopRequest):
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

    output = normalize_output(output)
    output["auto_execution"]["enabled"] = False
    output["manual_execution_only"] = True
    output["execution_loop"]["loop_steps"] = [
        "Review output",
        "Save actions or decision",
        "Execute first action manually",
        "Run follow-up prompt manually after progress"
    ]

    await save_learning_event(req.user_id or "local_user", "manual_loop_planned", req.mode, {"auto_disabled": True})
    return {"ok": True, "version": "V97", "auto_enabled": False, "message": "Manual execution loop only.", "final": output}


@app.get("/memory")
async def memory(user_id: str = Query("local_user")):
    return await load_memory(user_id)


@app.get("/memory-summary")
async def memory_summary(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {"ok": True, "version": "V97", "summary": summarize_memory_for_prompt(memory_data)}


@app.post("/stability-check")
@app.get("/stability-check")
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
        "memory_injection": "last_3_items",
        "project_context_applied": True
    }
    return {"ok": True, "version": "V97", "health": health_data, "checks": checks}




@app.get("/engine-state")
async def engine_state(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    recent_runs = memory_data.get("recent_runs") or []
    open_actions = dedupe_rows(memory_data.get("open_actions") or [], "text")
    recent_decisions = dedupe_rows(memory_data.get("recent_decisions") or [], "decision")
    memory_items = memory_data.get("memory_items") or []

    latest = recent_runs[0] if recent_runs else None
    latest_output = latest.get("output") if isinstance(latest, dict) else {}

    return {
        "ok": True,
        "version": "V97",
        "supabase_enabled": memory_data.get("supabase_enabled", False),
        "today_focus": {
            "title": latest_output.get("what_to_do_now") if isinstance(latest_output, dict) else "No focus yet",
            "next_move": latest_output.get("next_move") if isinstance(latest_output, dict) else "Run the engine to create one."
        },
        "your_engine": [
            {"id": r.get("id"), "title": str(r.get("input") or "Saved run")[:80], "mode": r.get("mode"), "created_at": r.get("created_at")}
            for r in recent_runs[:10]
        ],
        "open_actions": [
            {"id": a.get("id"), "text": a.get("text"), "priority": a.get("priority"), "status": a.get("status")}
            for a in open_actions[:10]
        ],
        "recent_decisions": [
            {"id": d.get("id"), "decision": d.get("decision"), "priority": d.get("priority"), "created_at": d.get("created_at")}
            for d in recent_decisions[:10]
        ],
        "memory_items": [
            {"type": m.get("type"), "content": m.get("content"), "importance": m.get("importance")}
            for m in memory_items[:5]
        ],
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }
@app.get("/recent-runs")
async def recent_runs(user_id: str = Query("local_user"), limit: int = Query(20, ge=1, le=50)):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "runs": []}
    user = await get_or_create_user(user_id)
    return {"ok": True, "runs": await sb_get("runs", f"?user_id=eq.{user['id']}&order=created_at.desc&limit={limit}")}



def normalize_dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


async def existing_action(user_id: str, text: str) -> Optional[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return None
    try:
        rows = await sb_get("actions", f"?user_id=eq.{user_id}&status=eq.open&order=created_at.desc&limit=50")
        target = normalize_dedupe_text(text)
        for row in rows:
            if normalize_dedupe_text(row.get("text")) == target:
                return row
    except Exception:
        return None
    return None


async def existing_decision(user_id: str, decision: str) -> Optional[Dict[str, Any]]:
    if not SUPABASE_ENABLED:
        return None
    try:
        rows = await sb_get("decisions", f"?user_id=eq.{user_id}&order=created_at.desc&limit=50")
        target = normalize_dedupe_text(decision)
        for row in rows:
            if normalize_dedupe_text(row.get("decision")) == target:
                return row
    except Exception:
        return None
    return None


def dedupe_rows(rows: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    seen = set()
    clean = []
    for row in rows:
        marker = normalize_dedupe_text(row.get(key))
        if not marker or marker in seen:
            continue
        seen.add(marker)
        clean.append(row)
    return clean

@app.get("/actions")
async def actions(user_id: str = Query("local_user"), status: str = Query("open")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "actions": []}
    user = await get_or_create_user(user_id)
    rows = await sb_get("actions", f"?user_id=eq.{user['id']}&status=eq.{status}&order=created_at.desc&limit=50")
    return {"ok": True, "version": "V97", "actions": dedupe_rows(rows, "text")}

@app.post("/save-action")
async def save_action(req: SaveActionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")

    duplicate = await existing_action(user["id"], req.text)
    if duplicate:
        return {"ok": True, "version": "V97", "duplicate": True, "action": duplicate}

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
    return {"ok": True, "version": "V97", "duplicate": False, "action": row}

@app.get("/decisions")
async def decisions(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "decisions": []}
    user = await get_or_create_user(user_id)
    rows = await sb_get("decisions", f"?user_id=eq.{user['id']}&order=created_at.desc&limit=50")
    return {"ok": True, "version": "V97", "decisions": dedupe_rows(rows, "decision")}

@app.post("/save-decision")
async def save_decision(req: SaveDecisionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")

    duplicate = await existing_decision(user["id"], req.decision)
    if duplicate:
        return {"ok": True, "version": "V97", "duplicate": True, "decision": duplicate}

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
    return {"ok": True, "version": "V97", "duplicate": False, "decision": row}

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
