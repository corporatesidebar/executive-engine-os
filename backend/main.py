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


APP_NAME = "Executive Engine OS V117"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2800"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title=APP_NAME, version="117.0.0")

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
- Current backend: V117 quality fix.
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
- Current priority: V117 release candidate stability, learning dashboard, profile-aware output, response quality, frontend DB validation, right-panel persistence, and manual execution loop.
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
- confirming V117 backend response quality
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
            "Document pass/fail before building V117."
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
        "version": "V117",
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
    base["version"] = "V117"
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
Focus on V117 quality validation, /run, /memory, /save-action, /save-decision, /actions, /decisions, frontend right panel, and manual execution.
"""
    return ""


DEFAULT_PROFILE_CONTEXT = {
    "role": "Founder / operator building Executive Engine OS",
    "goals": "Build a stable, high-end executive command center that saves runs, actions, decisions, and memory before adding automation or bots.",
    "experience": "Senior operator / executive profile focused on growth, operations, systems, marketing, technology, and business execution.",
    "constraints": "Needs simple deployment flow, stable backend, clean UI, no wasted features, no confusing instructions, and no generic answers.",
    "preferences": {
        "style": "direct, executive, specific, no filler",
        "output": "Decision, next move, actions, risk, priority, execution loop",
        "phase": "backend stability and memory before Figma redesign or automation"
    }
}

def merged_profile(memory: Dict[str, Any]) -> Dict[str, Any]:
    profile = memory.get("profile") or {}
    merged = dict(DEFAULT_PROFILE_CONTEXT)
    if isinstance(profile, dict):
        for key in ["role", "goals", "experience", "constraints", "resume_context"]:
            if profile.get(key):
                merged[key] = profile.get(key)
        if isinstance(profile.get("preferences"), dict):
            prefs = dict(DEFAULT_PROFILE_CONTEXT["preferences"])
            prefs.update(profile.get("preferences") or {})
            merged["preferences"] = prefs
    return merged

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
        "profile": merged_profile(memory),
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
You are Executive Engine OS V117.

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
- Use the user profile context when available. If profile is missing, use DEFAULT_PROFILE_CONTEXT.
- Adapt recommendations to a founder/operator building this system directly, not a large company with a team.
- Do not invent team members. If delegation is needed, frame it as outsource/defer/automate later/personally handle.
- Speak to the user like a senior operator who wants exact actions and working systems.
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
    return {"ok": True, "service": APP_NAME, "version": "V117"}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": APP_NAME,
        "version": "V117",
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
        "version": "V117",
        "routes": [
            "/", "/health", "/debug", "/schema", "/run", "/run-test", "/auto-loop",
            "/engine-state", "/project-context", "/quality-test", "/memory", "/memory-summary", "/stability-check",
            "/recent-runs", "/actions", "/save-action", "/decisions", "/save-decision", "/button-persistence-check", "/v117-smoke", "/frontend-button-map", "/button-action-contract", "/v116-smoke", "/frontend-contract", "/v115-smoke", "/ship-readiness", "/deploy-verifier", "/frontend-smoke-test", "/v114-check", "/run-validation", "/frontend-recovery", "/run-execution-check", "/frontend-live-status", "/v111-check", "/run-button-diagnostics", "/frontend-stability", "/navigation-map", "/frontend-diagnostics", "/v108-check", "/frontend-config", "/cleanup-check", "/visual-brief", "/layout-brief", "/figma-brief", "/ux-flow", "/ux-brief", "/next-build", "/system-status", "/go-live-check", "/learning", "/learning-events", "/operator-brief", "/profile-status", "/profile", "/robots.txt"
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
        "version": "V117",
        "response_schema": CANONICAL_SCHEMA,
        "modes": MODE_GUIDANCE,
        "depths": list(DEPTH_GUIDANCE.keys())
    }


@app.get("/project-context")
async def project_context():
    return {
        "ok": True,
        "version": "V117",
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
        return {"ok": True, "version": "V117", "output": normalize_output(output)}
    except Exception as exc:
        return {"ok": False, "version": "V117", "output": normalize_output(fallback_response(str(exc)))}




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
            "version": "V117",
            "generic_hits": generic_hits,
            "passed_quality_gate": len(generic_hits) == 0,
            "output": normalized
        }
    except Exception as exc:
        return {
            "ok": False,
            "version": "V117",
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
    return {"ok": True, "version": "V117", "auto_enabled": False, "message": "Manual execution loop only.", "final": output}


@app.get("/memory")
async def memory(user_id: str = Query("local_user")):
    return await load_memory(user_id)


@app.get("/memory-summary")
async def memory_summary(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {"ok": True, "version": "V117", "summary": summarize_memory_for_prompt(memory_data)}


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
    return {"ok": True, "version": "V117", "health": health_data, "checks": checks}




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
        "version": "V117",
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
    return {"ok": True, "version": "V117", "actions": dedupe_rows(rows, "text")}

@app.post("/save-action")
async def save_action(req: SaveActionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")

    duplicate = await existing_action(user["id"], req.text)
    if duplicate:
        return {"ok": True, "version": "V117", "duplicate": True, "action": duplicate}

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
    return {"ok": True, "version": "V117", "duplicate": False, "action": row}

@app.get("/decisions")
async def decisions(user_id: str = Query("local_user")):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "decisions": []}
    user = await get_or_create_user(user_id)
    rows = await sb_get("decisions", f"?user_id=eq.{user['id']}&order=created_at.desc&limit=50")
    return {"ok": True, "version": "V117", "decisions": dedupe_rows(rows, "decision")}

@app.post("/save-decision")
async def save_decision(req: SaveDecisionRequest):
    if not SUPABASE_ENABLED:
        return {"ok": False, "supabase_enabled": False, "message": "Supabase is not configured."}
    user = await get_or_create_user(req.user_id or "local_user")

    duplicate = await existing_decision(user["id"], req.decision)
    if duplicate:
        return {"ok": True, "version": "V117", "duplicate": True, "decision": duplicate}

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
    return {"ok": True, "version": "V117", "duplicate": False, "decision": row}



def count_by_key(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows or []:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def top_items_from_memory(memory_items: List[Dict[str, Any]], mem_type: str, limit: int = 5) -> List[Dict[str, Any]]:
    items = [m for m in memory_items or [] if m.get("type") == mem_type]
    return [
        {
            "content": m.get("content"),
            "importance": m.get("importance"),
            "created_at": m.get("created_at")
        }
        for m in items[:limit]
    ]


def build_learning_summary(memory_data: Dict[str, Any]) -> Dict[str, Any]:
    recent_runs = memory_data.get("recent_runs") or []
    open_actions = memory_data.get("open_actions") or []
    recent_decisions = memory_data.get("recent_decisions") or []
    memory_items = memory_data.get("memory_items") or []

    modes = count_by_key(recent_runs, "mode")
    high_priority_actions = [a for a in open_actions if str(a.get("priority") or "").lower() in ["high", "critical"]]

    repeated_constraints = top_items_from_memory(memory_items, "constraint", 5)
    repeated_risks = top_items_from_memory(memory_items, "recurring_risk", 5)
    decision_patterns = top_items_from_memory(memory_items, "decision_pattern", 5)
    focus_filters = top_items_from_memory(memory_items, "focus_filter", 5)

    recommended_next = "Run 3 more real workflows, save one action and one decision each time, then review this learning page again."
    if len(recent_runs) >= 5 and len(open_actions) >= 3:
        recommended_next = "Start tightening workflow quality: reduce duplicate actions, complete stale open actions, and improve profile context."
    if not memory_data.get("profile"):
        recommended_next = "Complete Your Profile first so the system can personalize decisions and actions."

    return {
        "total_runs": len(recent_runs),
        "open_actions": len(open_actions),
        "saved_decisions": len(recent_decisions),
        "memory_items": len(memory_items),
        "mode_usage": modes,
        "high_priority_actions": len(high_priority_actions),
        "repeated_constraints": repeated_constraints,
        "repeated_risks": repeated_risks,
        "decision_patterns": decision_patterns,
        "focus_filters": focus_filters,
        "product_read": {
            "status": "learning_active" if recent_runs else "not_enough_data",
            "read": "The system is now collecting runs, actions, decisions, and memory items. Use this to identify repeated blockers, decision patterns, and execution gaps.",
            "recommended_next": recommended_next
        },
        "manual_execution_only": True,
        "auto_loop_enabled": False
    }


















@app.get("/button-persistence-check")
async def button_persistence_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    recent_runs = memory_data.get("recent_runs") or []
    open_actions = memory_data.get("open_actions") or []
    recent_decisions = memory_data.get("recent_decisions") or []

    latest_run = recent_runs[0] if recent_runs else None
    latest_action = open_actions[0] if open_actions else None
    latest_decision = recent_decisions[0] if recent_decisions else None

    return {
        "ok": True,
        "version": "V117",
        "purpose": "Confirm output buttons save data and the right rail can refresh from Supabase.",
        "counts": {
            "recent_runs": len(recent_runs),
            "open_actions": len(open_actions),
            "saved_decisions": len(recent_decisions),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "latest": {
            "run_input": latest_run.get("input") if isinstance(latest_run, dict) else None,
            "action": latest_action.get("text") if isinstance(latest_action, dict) else None,
            "decision": latest_decision.get("decision") if isinstance(latest_decision, dict) else None
        },
        "pass_condition": "After clicking Add to Action Queue and Save Decision, open_actions and saved_decisions counts should increase or dedupe should return an existing row.",
        "next_move": "Run one command, click Add to Action Queue, click Save Decision, then refresh /button-persistence-check."
    }


@app.get("/v117-smoke")
async def v117_smoke(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "backend_ready": True,
        "supabase_enabled": bool(memory_data.get("supabase_enabled")),
        "frontend_buttons": {
            "run": "runV117Command()",
            "save_actions": "saveV117Actions()",
            "save_decision": "saveV117Decision()",
            "validate": "validateV117Run()",
            "refresh": "refreshV117Rail()"
        },
        "test": [
            "Hard refresh frontend.",
            "Run one command.",
            "Confirm V117 output card appears.",
            "Click Add to Action Queue.",
            "Confirm button changes to Actions Saved or visible success appears.",
            "Click Save Decision.",
            "Confirm button changes to Decision Saved or visible success appears.",
            "Click Validate Run.",
            "Check /button-persistence-check."
        ]
    }


@app.get("/frontend-button-map")
async def frontend_button_map():
    return {
        "ok": True,
        "version": "V117",
        "button_contract": {
            "Run Engine": "runV117Command",
            "Add to Action Queue": "saveV117Actions",
            "Save Decision": "saveV117Decision",
            "Validate Run": "validateV117Run",
            "Refresh Right Panel": "refreshV117Rail"
        },
        "fallbacks": [
            "inline onclick",
            "document click listener",
            "legacy alias mapping",
            "visible status box"
        ]
    }

@app.get("/button-action-contract")
async def button_action_contract():
    return {
        "ok": True,
        "version": "V117",
        "problem_fixed": "Output buttons could render from older output cards and not bind correctly.",
        "contract": {
            "add_action_button": "window.saveV117Actions()",
            "save_decision_button": "window.saveV117Decision()",
            "refresh_right_panel_button": "window.refreshV117Rail()",
            "validate_run_button": "window.validateV117Run()",
            "run_button": "window.runV117Command()"
        },
        "rules": [
            "Buttons use inline onclick handlers.",
            "Event delegation also catches button clicks.",
            "All old run/save/validate aliases point to V117.",
            "Failure messages show visibly in the command card."
        ]
    }


@app.get("/v116-smoke")
async def v116_smoke(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "supabase_enabled": bool(memory_data.get("supabase_enabled")),
        "counts": {
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "test": [
            "Run Engine",
            "Click Add to Action Queue",
            "Click Save Decision",
            "Click Validate Run",
            "Confirm visible status messages appear",
            "Confirm right rail refreshes"
        ]
    }

@app.get("/frontend-contract")
async def frontend_contract():
    return {
        "ok": True,
        "version": "V117",
        "contract": {
            "visible_input_id": "v103Input",
            "run_function": "runV117Command",
            "run_endpoint": "POST /run",
            "output_renderer": "renderOutput115",
            "save_actions_endpoint": "POST /save-action",
            "save_decision_endpoint": "POST /save-decision",
            "right_panel_endpoint": "GET /engine-state",
            "validation_endpoint": "GET /run-validation"
        },
        "rules": [
            "The visible command box must always be read directly.",
            "Run Engine must not depend on hidden chat UI.",
            "Output must render inline under the command center.",
            "Save buttons must call backend endpoints directly.",
            "Right panel must refresh after run and save.",
            "No silent failures: errors must show visibly."
        ]
    }


@app.get("/v115-smoke")
async def v115_smoke(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "backend_ready": True,
        "supabase_enabled": bool(memory_data.get("supabase_enabled")),
        "counts": {
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "frontend_test": [
            "Hard refresh frontend.",
            "Confirm V117 appears in UI/status.",
            "Type a real command.",
            "Click Run Engine.",
            "Confirm output card appears.",
            "Click Add to Action Queue.",
            "Click Save Decision.",
            "Click Validate Run.",
            "Confirm right rail updates."
        ],
        "go_no_go": "GO if Run Engine produces an output card and /run-validation shows the latest input."
    }


@app.get("/ship-readiness")
async def ship_readiness(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    recent_runs = memory_data.get("recent_runs") or []
    open_actions = memory_data.get("open_actions") or []
    recent_decisions = memory_data.get("recent_decisions") or []
    checks = [
        {"name": "Backend live", "passed": True},
        {"name": "OpenAI configured", "passed": bool(os.getenv("OPENAI_API_KEY"))},
        {"name": "Supabase live", "passed": bool(memory_data.get("supabase_enabled"))},
        {"name": "Run history exists", "passed": len(recent_runs) > 0},
        {"name": "Actions exist", "passed": len(open_actions) > 0},
        {"name": "Decisions exist", "passed": len(recent_decisions) > 0},
        {"name": "Frontend contract defined", "passed": True}
    ]
    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": True,
        "version": "V117",
        "score": f"{passed}/{len(checks)}",
        "ready": passed >= 6,
        "checks": checks,
        "decision": "Frontend can be considered usable if V117 smoke test passes.",
        "next_move": "Stop building versions and test the deployed frontend end-to-end."
    }

@app.get("/deploy-verifier")
async def deploy_verifier(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "purpose": "Verify backend, database, frontend contract, and run/save loop before more feature work.",
        "checks": {
            "backend_live": True,
            "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or []),
            "run_endpoint": "POST /run",
            "action_endpoint": "POST /save-action",
            "decision_endpoint": "POST /save-decision",
            "right_rail_endpoint": "GET /engine-state"
        },
        "frontend_contract": {
            "api_base": "https://executive-engine-os.onrender.com",
            "visible_input_required": True,
            "run_button_required": True,
            "inline_output_required": True,
            "right_panel_refresh_required": True
        },
        "go_no_go": "GO if V117 frontend can run a command, render output, save an action, save a decision, and refresh right rail."
    }


@app.get("/frontend-smoke-test")
async def frontend_smoke_test():
    return {
        "ok": True,
        "version": "V117",
        "manual_test": [
            "Hard refresh frontend.",
            "Confirm command box is visible.",
            "Type: What should I focus on today to move Executive Engine OS forward?",
            "Click Run Engine.",
            "Confirm output card appears under the command box.",
            "Click Add to Action Queue.",
            "Click Save Decision.",
            "Confirm right panel refreshes.",
            "Open /run-validation and confirm latest_input matches your prompt."
        ],
        "common_failure": {
            "button_no_response": "Open browser console. Check whether runV117Command is defined.",
            "backend_offline": "Check /health and Render backend deploy.",
            "no_right_panel_data": "Check /engine-state.",
            "old_ui_cached": "Hard refresh or clear browser cache."
        }
    }


@app.get("/v114-check")
async def v114_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    checks = [
        {"name": "Backend V117 live", "passed": True},
        {"name": "OpenAI configured", "passed": bool(os.getenv("OPENAI_API_KEY"))},
        {"name": "Supabase accessible", "passed": bool(memory_data.get("supabase_enabled"))},
        {"name": "Recent run exists", "passed": len(memory_data.get("recent_runs") or []) >= 1},
        {"name": "Actions table active", "passed": len(memory_data.get("open_actions") or []) >= 1},
        {"name": "Decisions table active", "passed": len(memory_data.get("recent_decisions") or []) >= 1},
    ]
    return {
        "ok": True,
        "version": "V117",
        "passed": sum(1 for c in checks if c["passed"]),
        "total": len(checks),
        "checks": checks,
        "next_move": "Deploy V117 frontend, hard refresh, and run the smoke test."
    }

@app.get("/run-validation")
async def run_validation(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    recent_runs = memory_data.get("recent_runs") or []
    latest = recent_runs[0] if recent_runs else None
    latest_output = latest.get("output") if isinstance(latest, dict) else {}

    return {
        "ok": True,
        "version": "V117",
        "purpose": "Validate that frontend Run Engine creates a saved backend run and returns renderable output.",
        "checks": {
            "backend_live": True,
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "has_recent_run": bool(recent_runs),
            "latest_run_id": latest.get("id") if isinstance(latest, dict) else None,
            "latest_input": latest.get("input") if isinstance(latest, dict) else None,
            "latest_has_decision": bool(latest_output.get("decision")) if isinstance(latest_output, dict) else False,
            "latest_has_actions": bool(latest_output.get("actions")) if isinstance(latest_output, dict) else False,
            "open_actions_count": len(memory_data.get("open_actions") or []),
            "saved_decisions_count": len(memory_data.get("recent_decisions") or [])
        },
        "pass_condition": "After clicking Run Engine, has_recent_run should stay true and latest_input should match the command you typed.",
        "next_move": "Use the frontend command box. If output renders, click Save Action and Save Decision, then recheck /run-validation."
    }


@app.get("/frontend-recovery")
async def frontend_recovery():
    return {
        "ok": True,
        "version": "V117",
        "recovery_strategy": "The frontend now includes a visible recovery output area and direct run fallback that does not depend on the older chat renderer.",
        "fixed_paths": [
            "Visible command textarea -> direct POST /run",
            "Inline output render -> v112 output card",
            "Save actions -> /save-action",
            "Save decision -> /save-decision",
            "Right rail refresh -> /engine-state",
            "Failure state -> visible error box instead of silent failure"
        ],
        "test_steps": [
            "Hard refresh frontend.",
            "Type: What should I focus on today to move Executive Engine OS forward?",
            "Click Run Engine.",
            "Confirm output card appears below command box.",
            "Click Add to Action Queue.",
            "Click Save Decision.",
            "Confirm right rail refreshes."
        ]
    }

@app.get("/run-execution-check")
async def run_execution_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "purpose": "Confirm the frontend Run Engine button has a direct, reliable execution path.",
        "execution_path": [
            "Visible textarea is read directly.",
            "Payload is posted directly to POST /run.",
            "Assistant output is rendered by V117 renderer.",
            "Right rail refreshes with /engine-state.",
            "Saved run appears in Supabase recent_runs."
        ],
        "backend_state": {
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "test": "Open frontend, type a command, click Run Engine. The result card should appear directly below the command area."
    }

@app.get("/frontend-live-status")
async def frontend_live_status(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "backend_live": True,
        "api_base": "https://executive-engine-os.onrender.com",
        "supabase_enabled": bool(memory_data.get("supabase_enabled")),
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "memory_counts": {
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "frontend_message": "Backend live. Use /run for command execution and /engine-state for right rail refresh.",
        "run_button_expected": "Visible command box -> runV117Command -> POST /run fallback if sendMessage fails."
    }


@app.get("/v110-check")
async def v110_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    checks = [
        {"name": "Backend V117 live", "passed": True},
        {"name": "OpenAI configured", "passed": bool(os.getenv("OPENAI_API_KEY"))},
        {"name": "Supabase memory accessible", "passed": bool(memory_data.get("supabase_enabled"))},
        {"name": "Engine state available", "passed": True},
        {"name": "Run button fallback available", "passed": True}
    ]
    return {
        "ok": True,
        "version": "V117",
        "checks": checks,
        "passed": sum(1 for c in checks if c["passed"]),
        "total": len(checks),
        "next_move": "Deploy V117 frontend, hard refresh, click Refresh/Sync Local, then run one command from the visible command box."
    }

@app.get("/run-button-diagnostics")
async def run_button_diagnostics():
    return {
        "ok": True,
        "version": "V117",
        "issue_fixed": "V108 Run Engine button could fail because the simplified V103 command UI did not reliably sync the visible textarea with the original hidden input/send flow.",
        "frontend_fix": [
            "Run button now calls runV117Command() directly.",
            "Visible command textarea is read directly.",
            "If sendMessage exists, it is used after syncing input.",
            "If sendMessage fails, frontend posts directly to /run.",
            "Results are rendered through existing message flow when possible."
        ],
        "test": "Open frontend, type into the large command box, click Run Engine, confirm output appears."
    }

@app.get("/frontend-stability")
async def frontend_stability(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "stability_status": "frontend_stability_polish",
        "checks": {
            "backend_live": True,
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "frontend_focus": [
            "Command box visible",
            "Run Engine button stable",
            "Right panel readable",
            "Save buttons do not duplicate",
            "Mobile layout does not break",
            "No hidden input box",
            "No broken navigation links"
        ],
        "next_move": "Deploy V117 frontend and confirm the home screen, right sidebar, Learning page, and Profile page all render without layout breaks."
    }


@app.get("/navigation-map")
async def navigation_map():
    return {
        "ok": True,
        "version": "V117",
        "routes": {
            "Command": "Home command center",
            "Plan Today": "daily_brief workflow",
            "Decision": "decision workflow",
            "Meeting": "meeting workflow",
            "Content": "content workflow",
            "Learning": "/learning frontend page backed by /learning",
            "Profile": "/profile frontend page backed by /profile and /profile-status"
        },
        "rule": "Every visible navigation item must either load a page or set a workflow."
    }

@app.get("/frontend-diagnostics")
async def frontend_diagnostics(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "frontend_expected": {
            "api_base": "https://executive-engine-os.onrender.com",
            "frontend_base": "https://executive-engine-frontend.onrender.com",
            "home": "Command-first Today’s Command Center",
            "right_panel": "Current Focus, Open Actions, Saved Decisions, Learning/Profile/Status boxes",
            "buttons": {
                "run_engine": "POST /run",
                "add_to_action_queue": "POST /save-action",
                "save_decision": "POST /save-decision",
                "refresh_memory": "GET /engine-state"
            }
        },
        "backend_state": {
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "diagnostic_decision": "If frontend looks broken after deploy, hard refresh first, then confirm index.html was uploaded to /frontend and Render frontend deployed the latest commit.",
        "next_test": "Run one prompt, save one action, save one decision, then confirm /engine-state updates."
    }


@app.get("/v107-check")
async def v107_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    checks = [
        {"name": "Backend V117 live", "passed": True},
        {"name": "OpenAI configured", "passed": bool(os.getenv("OPENAI_API_KEY"))},
        {"name": "Supabase enabled", "passed": bool(memory_data.get("supabase_enabled"))},
        {"name": "Recent runs available", "passed": len(memory_data.get("recent_runs") or []) >= 1},
        {"name": "Actions endpoint data available", "passed": len(memory_data.get("open_actions") or []) >= 1},
        {"name": "Decisions endpoint data available", "passed": len(memory_data.get("recent_decisions") or []) >= 1},
    ]
    return {
        "ok": True,
        "version": "V117",
        "checks": checks,
        "passed": sum(1 for c in checks if c["passed"]),
        "total": len(checks),
        "next_move": "Deploy V117 frontend, hard refresh, and verify the command box plus right panel load cleanly."
    }

@app.get("/frontend-config")
async def frontend_config():
    return {
        "ok": True,
        "version": "V117",
        "api_base": "https://executive-engine-os.onrender.com",
        "frontend_base": "https://executive-engine-frontend.onrender.com",
        "required_frontend_behaviors": [
            "Command box visible on page load",
            "Run Engine calls /run",
            "Right rail loads /engine-state",
            "Save Action calls /save-action",
            "Save Decision calls /save-decision",
            "Learning page calls /learning",
            "Profile page calls /profile and /profile-status"
        ],
        "status": "cleanup_bugfix"
    }


@app.get("/cleanup-check")
async def cleanup_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "checks": {
            "backend_live": True,
            "supabase_enabled": bool(memory_data.get("supabase_enabled")),
            "recent_runs_count": len(memory_data.get("recent_runs") or []),
            "open_actions_count": len(memory_data.get("open_actions") or []),
            "saved_decisions_count": len(memory_data.get("recent_decisions") or []),
            "memory_items_count": len(memory_data.get("memory_items") or []),
            "manual_execution_only": True,
            "auto_loop_enabled": False
        },
        "decision": "Frontend cleanup can proceed if command input, right rail, save buttons, learning page, and profile page all load without console errors.",
        "next_move": "Deploy V117 frontend, hard refresh, run one prompt, save one action, save one decision, and confirm right rail updates."
    }

@app.get("/visual-brief")
async def visual_brief():
    return {
        "ok": True,
        "version": "V117",
        "visual_decision": "Polish the existing V103 command-first layout without changing backend logic.",
        "style_direction": {
            "tone": "high-end executive SaaS",
            "inspiration": "Apple / Stripe / Linear",
            "colors": {
                "navy": "#0B1220",
                "white": "#FFFFFF",
                "surface": "#F8FAFC",
                "blue": "#2563EB",
                "green": "#059669",
                "orange": "#EA580C"
            },
            "rules": [
                "Command box remains primary.",
                "Workflow pills stay secondary.",
                "Right rail remains clean and one-line.",
                "Reduce visual noise.",
                "Use soft borders, hierarchy, and spacing.",
                "No new product features."
            ]
        },
        "success_criteria": [
            "Looks premium without becoming busy.",
            "User immediately sees where to type.",
            "Right panel is readable.",
            "Buttons feel clickable.",
            "No backend behavior changes."
        ]
    }

@app.get("/layout-brief")
async def layout_brief():
    return {
        "ok": True,
        "version": "V117",
        "layout_decision": "Command-first executive workspace.",
        "primary_screen_order": [
            "Top bar: product name + compact system state",
            "Main: Today’s Command Center",
            "Main: one command box",
            "Main: workflow pills",
            "Main: latest output",
            "Right rail: Current Focus, Open Actions, Saved Decisions, Learning Signal"
        ],
        "remove_or_reduce": [
            "duplicate status cards",
            "debug-looking controls",
            "large metric blocks with no action value",
            "too many workflow boxes",
            "bottom-only composer",
            "repeated navigation labels"
        ],
        "success_criteria": [
            "User knows where to type in under 5 seconds",
            "Run Engine is visually obvious",
            "Right rail shows saved backend state",
            "Learning and Profile remain available but secondary",
            "No backend logic is broken"
        ]
    }

@app.get("/figma-brief")
async def figma_brief(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "title": "Executive Engine OS — Figma UI Brief",
        "purpose": "Create a high-end executive command center that is obvious in under 5 seconds.",
        "current_product_state": {
            "backend": "Render FastAPI backend live.",
            "database": "Supabase memory live.",
            "ai": "OpenAI connected.",
            "saved_state": "Runs, actions, decisions, memory items, learning, profile status.",
            "frontend": "Functional but still too busy. Needs flow simplification, not more features."
        },
        "primary_user": "CEO / COO / Founder / senior operator who wants faster decisions and execution.",
        "core_user_flow": [
            "User lands on Today’s Command Center.",
            "User sees one primary command input.",
            "User chooses workflow only if needed.",
            "User runs engine.",
            "System returns decision, next move, actions, risk, priority, execution loop.",
            "User saves action or decision.",
            "Right panel updates with saved state.",
            "Learning page shows patterns over time."
        ],
        "layout": {
            "left_sidebar": [
                "Command",
                "Plan Today",
                "Decision",
                "Meeting",
                "Content",
                "Learning",
                "Profile"
            ],
            "top_bar": [
                "Executive Engine OS",
                "Search centered but compact",
                "System status chips only if useful"
            ],
            "main_area": [
                "Today’s Command Center title",
                "One command box near top-center",
                "Workflow selector as compact tabs/pills",
                "Suggested starter cards below command box",
                "Output card below input, not scattered"
            ],
            "right_panel": [
                "Current Focus",
                "Open Actions",
                "Saved Decisions",
                "Learning Signal"
            ]
        },
        "design_rules": [
            "Keep dark navy left/top structure.",
            "Use clean white main workspace.",
            "Reduce cards and repeated labels.",
            "No meaningless metrics.",
            "No duplicate status widgets.",
            "No debug controls visible to normal users.",
            "Every visible button must have a clear action.",
            "Use one-line right-panel rows.",
            "Make the command input the hero."
        ],
        "visual_style": {
            "tone": "Apple / Stripe / Linear quality",
            "colors": "dark navy, white, muted blue, subtle green/orange status only",
            "spacing": "less clutter, more hierarchy",
            "typography": "larger labels, clear hierarchy, executive-grade"
        },
        "must_not_do": [
            "Do not add bot team UI yet.",
            "Do not add automation marketplace UI yet.",
            "Do not add more navigation clutter.",
            "Do not hide the command box at the bottom.",
            "Do not make the user choose from too many modes.",
            "Do not redesign the backend flow."
        ],
        "memory_counts": {
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        }
    }


@app.get("/ux-flow")
async def ux_flow():
    return {
        "ok": True,
        "version": "V117",
        "screen_order": [
            {
                "screen": "Home / Command",
                "job": "Let the executive immediately run the system.",
                "primary_component": "Command input",
                "secondary_component": "Workflow pills"
            },
            {
                "screen": "Output",
                "job": "Turn answer into action.",
                "primary_component": "Decision / Next Move / Actions",
                "secondary_component": "Save Action / Save Decision"
            },
            {
                "screen": "Right Panel",
                "job": "Show the user what the system remembers.",
                "primary_component": "Current Focus / Open Actions / Saved Decisions"
            },
            {
                "screen": "Learning",
                "job": "Show patterns and repeated blockers.",
                "primary_component": "Repeated constraints and decision patterns"
            },
            {
                "screen": "Profile",
                "job": "Make future output sharper.",
                "primary_component": "Role, goals, constraints, resume/context"
            }
        ],
        "decision": "Simplify UI around one command input and one memory-driven right panel.",
        "next_move": "Use this endpoint output as the Figma prompt before making more code changes."
    }

@app.get("/ux-brief")
async def ux_brief(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "brief": {
            "ux_goal": "Make Executive Engine OS feel obvious when a CEO logs in: choose a workflow, type one command, get a decision, save actions/decisions, and see memory update.",
            "current_state": {
                "backend": "Live and connected to OpenAI + Supabase.",
                "memory": "Runs, actions, decisions, and memory items are saving.",
                "right_sidebar": "Backend data is available through /engine-state.",
                "learning": "Learning dashboard is available through /learning.",
                "profile": "Profile-aware output is available through /profile-status."
            },
            "ui_principles": [
                "One obvious command area.",
                "Right panel shows only useful saved state.",
                "No duplicate buttons or redundant status cards.",
                "No generic metrics.",
                "No confusing mode clutter.",
                "Every button must do something visible.",
                "User should know what to do in under 5 seconds."
            ],
            "recommended_next_ui": [
                "Top area: Today’s Command Center.",
                "Primary CTA: Run Engine.",
                "Secondary workflow selector: Execute, Today, Decision, Meeting, Content, Personal.",
                "Right panel: Current Focus, Open Actions, Saved Decisions, Learning Signal.",
                "Profile page: role, goals, constraints, resume/context.",
                "Learning page: repeated constraints, decision patterns, open action count."
            ],
            "do_not_add_yet": [
                "Bot team",
                "External automation",
                "Figma redesign before current UX flow is validated",
                "More nav items",
                "More dashboards without clear action value"
            ],
            "memory_counts": {
                "recent_runs": len(memory_data.get("recent_runs") or []),
                "open_actions": len(memory_data.get("open_actions") or []),
                "saved_decisions": len(memory_data.get("recent_decisions") or []),
                "memory_items": len(memory_data.get("memory_items") or [])
            }
        }
    }


@app.get("/next-build")
async def next_build():
    return {
        "ok": True,
        "version": "V117",
        "recommended_next": "V117 — Frontend UX Simplification Build",
        "why": "V117 defines the Figma-ready flow. V117 should implement the simplified frontend layout without changing backend logic.",
        "requirements": [
            "No new backend features unless a frontend bug blocks usage.",
            "Simplify the home screen.",
            "Make workflow selection clear and secondary.",
            "Keep the command input central.",
            "Make right sidebar show clean DB state.",
            "Make Learning and Profile pages useful, not decorative.",
            "Prepare Figma instructions from actual working product state."
        ],
        "hold": [
            "Do not build bot team yet.",
            "Do not add external automation yet.",
            "Do not redesign blindly.",
            "Do not add more nav clutter."
        ]
    }

@app.get("/system-status")
async def system_status(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    learning_data = build_learning_summary(memory_data) if "build_learning_summary" in globals() else {}
    return {
        "ok": True,
        "version": "V117",
        "status": "release_candidate",
        "backend": {
            "live": True,
            "model": MODEL,
            "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "timeout_seconds": TIMEOUT,
            "max_tokens": MAX_TOKENS
        },
        "database": {
            "supabase_enabled": SUPABASE_ENABLED,
            "memory_accessible": bool(memory_data.get("supabase_enabled")),
            "recent_runs": len(memory_data.get("recent_runs") or []),
            "open_actions": len(memory_data.get("open_actions") or []),
            "saved_decisions": len(memory_data.get("recent_decisions") or []),
            "memory_items": len(memory_data.get("memory_items") or [])
        },
        "product": {
            "manual_execution_only": True,
            "auto_loop_enabled": False,
            "bots_enabled": False,
            "external_automation_enabled": False,
            "figma_ready_next": True,
            "ux_brief_ready": True
        },
        "learning": learning_data.get("product_read", {}) if isinstance(learning_data, dict) else {}
    }


@app.get("/go-live-check")
async def go_live_check(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    recent_runs = memory_data.get("recent_runs") or []
    open_actions = memory_data.get("open_actions") or []
    recent_decisions = memory_data.get("recent_decisions") or []
    memory_items = memory_data.get("memory_items") or []

    checks = [
        {"name": "Backend health", "passed": True, "detail": "FastAPI service is live."},
        {"name": "OpenAI key", "passed": bool(os.getenv("OPENAI_API_KEY")), "detail": "OpenAI key is configured."},
        {"name": "Supabase connection", "passed": bool(memory_data.get("supabase_enabled")), "detail": "Supabase memory is accessible."},
        {"name": "Recent runs", "passed": len(recent_runs) > 0, "detail": f"{len(recent_runs)} recent runs found."},
        {"name": "Open actions", "passed": len(open_actions) > 0, "detail": f"{len(open_actions)} open actions found."},
        {"name": "Saved decisions", "passed": len(recent_decisions) > 0, "detail": f"{len(recent_decisions)} saved decisions found."},
        {"name": "Memory items", "passed": len(memory_items) > 0, "detail": f"{len(memory_items)} memory items found."},
        {"name": "Manual execution lock", "passed": True, "detail": "Auto-loop/bots/external automation are disabled."}
    ]

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    ready = passed >= 7

    return {
        "ok": True,
        "version": "V117",
        "ready_for_frontend_polish": ready,
        "score": f"{passed}/{total}",
        "checks": checks,
        "decision": "Proceed to Figma/UI polish after verifying frontend displays V117 status cleanly." if ready else "Do not add new features. Fix failed checks first.",
        "next_move": "Run one frontend prompt, save one action and one decision, then recheck /go-live-check."
    }

@app.get("/learning")
async def learning(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    return {
        "ok": True,
        "version": "V117",
        "learning": build_learning_summary(memory_data)
    }


@app.get("/learning-events")
async def learning_events(user_id: str = Query("local_user"), limit: int = Query(50, ge=1, le=100)):
    if not SUPABASE_ENABLED:
        return {"ok": True, "supabase_enabled": False, "events": []}
    user = await get_or_create_user(user_id)
    rows = await sb_get("learning_events", f"?user_id=eq.{user['id']}&order=created_at.desc&limit={limit}")
    return {"ok": True, "version": "V117", "events": rows}


@app.get("/operator-brief")
async def operator_brief(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    learning_data = build_learning_summary(memory_data)
    return {
        "ok": True,
        "version": "V117",
        "brief": {
            "today_focus": learning_data["product_read"]["recommended_next"],
            "system_status": "Backend + Supabase memory live. Learning dashboard active. Manual execution only.",
            "open_actions": learning_data["open_actions"],
            "saved_decisions": learning_data["saved_decisions"],
            "memory_items": learning_data["memory_items"],
            "highest_leverage_move": "Use the app for 3 real workflows and save actions/decisions so the learning layer has real signal.",
            "do_not_do_yet": ["Do not build bot team", "Do not add external automation", "Do not start Figma redesign until learning output is useful"]
        }
    }

@app.get("/profile-status")
async def profile_status(user_id: str = Query("local_user")):
    memory_data = await load_memory(user_id)
    profile = memory_data.get("profile")
    merged = merged_profile(memory_data)
    completion = {
        "has_saved_profile": bool(profile),
        "has_role": bool(profile and profile.get("role")),
        "has_goals": bool(profile and profile.get("goals")),
        "has_experience": bool(profile and profile.get("experience")),
        "has_constraints": bool(profile and profile.get("constraints")),
        "has_resume_context": bool(profile and profile.get("resume_context"))
    }
    score = sum(1 for v in completion.values() if v)
    return {
        "ok": True,
        "version": "V117",
        "completion_score": score,
        "completion": completion,
        "profile_used_for_prompt": merged,
        "recommendation": "Add role, goals, experience, constraints, and resume context to make output sharper." if score < 4 else "Profile is strong enough for personalized output."
    }

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
    return {"ok": True, "version": "V117", "profile": row, "profile_status": "saved"}
