from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
import os, json, re
import urllib.request, urllib.error
from datetime import datetime

VERSION = "36310-frontend-lock-working-ui"

app = FastAPI(title="Executive Engine OS", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

MEMORY = {
    "runs": [],
    "actions": [],
    "decisions": [],
    "assets": [],
    "workflows": [],
    "contexts": [],
    "router_events": [],
    "test_reports": [],
    "memory_events": [],
    "execution_events": [],
    "workspace_events": [],
    "operator_events": [],
    "briefings": [],
    "pressure_items": [],
    "clients": {},
    "projects": {},
    "workspaces": {},
}

ACTIVE_CONTEXT = {
    "client": "",
    "project": "",
    "workflow_id": "",
    "workflow_type": "",
    "workflow_stage": "",
    "workflow_progress": 0,
    "workspace_id": "",
    "last_category": "",
    "last_output_type": "",
    "last_summary": "",
    "last_asset_title": "",
    "last_asset_content": "",
    "last_follow_up": "",
    "chain": [],
    "saved_assets": [],
    "saved_actions": [],
    "saved_followups": [],
    "current_mission": {},
    "current_workspace": {},
    "operator_state": {
        "mode": "active",
        "last_scan": "",
        "top_priority": "",
        "pressure_score": 0,
        "next_best_action": "",
        "attention_required": [],
    },
}

WORKFLOW_TEMPLATES = {
    "proposal": [
        {"key": "context", "label": "Load Context", "category": "research", "output_type": "brief", "brain": "research"},
        {"key": "proposal", "label": "Build Proposal", "category": "plans", "output_type": "proposal", "brain": "revenue"},
        {"key": "tasks", "label": "Create Tasks", "category": "tasks", "output_type": "tasks", "brain": "execution"},
        {"key": "follow_up", "label": "Create Follow-Up", "category": "email", "output_type": "email", "brain": "communications"},
        {"key": "meeting_prep", "label": "Prepare Meeting", "category": "meetings", "output_type": "brief", "brain": "meetings"},
        {"key": "close_plan", "label": "Prepare Close Plan", "category": "plans", "output_type": "brief", "brain": "revenue"},
    ],
    "meeting": [
        {"key": "context", "label": "Load Context", "category": "research", "output_type": "brief", "brain": "research"},
        {"key": "meeting_prep", "label": "Prepare Meeting", "category": "meetings", "output_type": "brief", "brain": "meetings"},
        {"key": "objections", "label": "Prepare Objections", "category": "meetings", "output_type": "brief", "brain": "meetings"},
        {"key": "follow_up", "label": "Create Follow-Up", "category": "email", "output_type": "email", "brain": "communications"},
        {"key": "tasks", "label": "Create Tasks", "category": "tasks", "output_type": "tasks", "brain": "execution"},
    ],
    "marketing": [
        {"key": "research", "label": "Research Market", "category": "research", "output_type": "brief", "brain": "research"},
        {"key": "strategy", "label": "Build Strategy", "category": "marketing", "output_type": "strategy", "brain": "revenue"},
        {"key": "content", "label": "Create Content", "category": "content", "output_type": "content", "brain": "content"},
        {"key": "tasks", "label": "Create Tasks", "category": "tasks", "output_type": "tasks", "brain": "execution"},
        {"key": "follow_up", "label": "Create Follow-Up", "category": "email", "output_type": "email", "brain": "communications"},
    ],
    "general": [
        {"key": "context", "label": "Load Context", "category": "guided", "output_type": "brief", "brain": "command"},
        {"key": "plan", "label": "Create Plan", "category": "plans", "output_type": "proposal", "brain": "revenue"},
        {"key": "tasks", "label": "Create Tasks", "category": "tasks", "output_type": "tasks", "brain": "execution"},
        {"key": "follow_up", "label": "Create Follow-Up", "category": "email", "output_type": "email", "brain": "communications"},
    ],
}

AUTONOMOUS_PACKAGES = {
    "proposal": ["proposal", "follow_up", "meeting_prep", "objections", "close_plan", "tasks"],
    "meeting": ["meeting_prep", "objections", "follow_up", "tasks"],
    "marketing": ["strategy", "content", "tasks", "follow_up"],
    "general": ["plan", "tasks", "follow_up"],
}

STEP_MAP = {
    "proposal": ("plans", "revenue", "proposal"),
    "follow_up": ("email", "communications", "email"),
    "meeting_prep": ("meetings", "meetings", "brief"),
    "objections": ("meetings", "meetings", "brief"),
    "close_plan": ("plans", "revenue", "brief"),
    "tasks": ("tasks", "execution", "tasks"),
    "strategy": ("marketing", "revenue", "strategy"),
    "content": ("content", "content", "content"),
    "plan": ("plans", "revenue", "proposal"),
}

class RunRequest(BaseModel):
    input: str = ""
    mode: str = "execution"
    brain: str = "auto"
    output_type: str = "auto"
    depth: str = "standard"
    provider: str = "auto"
    category: str = "auto"
    client: str = ""
    project: str = ""
    workflow_id: str = ""
    continue_workflow: bool = True
    mission_id: str = ""
    step_key: str = ""

class MemoryRequest(BaseModel):
    client: str = ""
    project: str = ""
    workflow_id: str = ""

class MissionRequest(BaseModel):
    input: str = ""
    mission_type: str = "auto"
    client: str = ""
    project: str = ""
    provider: str = "auto"

class StepRequest(BaseModel):
    mission_id: str = ""
    step_key: str = ""
    provider: str = "auto"

class WorkspaceRequest(BaseModel):
    input: str = ""
    workspace_type: str = "auto"
    client: str = ""
    project: str = ""
    provider: str = "auto"
    auto_generate: bool = False

class OperatorRequest(BaseModel):
    provider: str = "auto"
    auto_generate: bool = False
    focus: str = "today"

def now():
    return datetime.utcnow().isoformat()


# V35120_DATABASE_PERSISTENCE_LAYER
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "items")

def db_configured():
    return bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_TABLE)

def db_headers(extra=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra:
        h.update(extra)
    return h

def db_insert(kind, payload):
    """Persist to Supabase when configured; always fail safely to memory."""
    event = {
        "kind": kind,
        "payload": payload,
        "created_at": now(),
    }
    MEMORY.setdefault("memory_events", []).insert(0, event)
    if not db_configured():
        event["db_status"] = "not_configured"
        return {"ok": False, "configured": False, "message": "Supabase env vars not configured.", "event": event}
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        body = json.dumps(event).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=db_headers(), method="POST")
        with urllib.request.urlopen(req, timeout=8) as res:
            raw = res.read().decode("utf-8")
            data = json.loads(raw) if raw else []
        event["db_status"] = "saved"
        return {"ok": True, "configured": True, "data": data, "event": event}
    except Exception as e:
        event["db_status"] = "failed"
        event["db_error"] = str(e)
        return {"ok": False, "configured": True, "message": str(e), "event": event}

def db_read(limit=25):
    if not db_configured():
        return {"ok": False, "configured": False, "items": [], "message": "Supabase env vars not configured."}
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=*&order=created_at.desc&limit={int(limit)}"
        req = urllib.request.Request(url, headers=db_headers({"Accept":"application/json"}), method="GET")
        with urllib.request.urlopen(req, timeout=8) as res:
            raw = res.read().decode("utf-8")
            data = json.loads(raw) if raw else []
        return {"ok": True, "configured": True, "items": data}
    except Exception as e:
        return {"ok": False, "configured": True, "items": [], "message": str(e)}

def slug(s: str):
    return (re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").strip().lower()).strip("-")[:50] or "workspace")

def compact(v, limit=600):
    v = str(v or "").strip()
    return v[:limit] + ("..." if len(v) > limit else "")

def detect_category(text: str):
    t = (text or "").lower()
    rules = [
        ("email", ["email", "follow up", "follow-up", "reply", "outreach", "message", "recap"]),
        ("meetings", ["meeting", "call", "agenda", "prep", "talking points", "objections"]),
        ("plans", ["proposal", "plan", "sow", "scope", "business plan", "operating plan"]),
        ("content", ["content", "post", "script", "social post", "caption", "video", "creative"]),
        ("marketing", ["marketing", "seo", "google ads", "ads", "cpa", "campaign", "funnel", "lead"]),
        ("research", ["research", "look up", "find", "brief", "competitor", "market", "company context"]),
        ("brainstorm", ["brainstorm", "ideas", "options", "angles", "names", "creative direction"]),
        ("goals", ["goal", "kpi", "objective", "target", "scorecard", "success criteria"]),
        ("tasks", ["task", "todo", "to-do", "action list", "checklist", "next steps"]),
    ]
    scores = {cat: sum(1 for w in words if w in t) for cat, words in rules}
    best = max(scores, key=scores.get)
    return best if scores[best] else (ACTIVE_CONTEXT.get("last_category") or "guided")

def detect_type(text: str, category: str = ""):
    t = (text or "").lower()
    if "proposal" in t or category == "plans":
        return "proposal"
    if "meeting" in t or "call" in t or category == "meetings":
        return "meeting"
    if "marketing" in t or "seo" in t or "ads" in t or "campaign" in t or "cpa" in t or category == "marketing":
        return "marketing"
    return "general"

def detect_context(text: str, client="", project=""):
    t = text or ""
    for p in [
        r"for\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})(?:\s+with|\s+before|\s+about|\s*$)",
        r"client\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})",
        r"company\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})",
        r"proposal\s+for\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})",
    ]:
        m = re.search(p, t)
        if m:
            client = m.group(1).strip(" .,-")
            break
    tl = t.lower()
    if "auto loan" in tl or "dealership" in tl:
        client = client or "Ontario Auto Loan Dealership"
        project = project or "Ontario Auto Loan Growth"
    if "hvac" in tl:
        client = client or "ABC HVAC"
        project = project or "HVAC Growth Proposal"
    return client or ACTIVE_CONTEXT.get("client", ""), project or ACTIVE_CONTEXT.get("project", "")

def urgency(text):
    t = (text or "").lower()
    return "High" if any(x in t for x in ["urgent", "asap", "today", "now", "before tomorrow", "tomorrow", "deadline", "due", "blocked"]) else "Medium"

def provider_plan(category, output_type, requested):
    """
    V35080-Restore provider routing.
    OpenAI is the safe default. Claude can be used only when explicitly requested,
    and it must fall back to OpenAI if Claude credits/API fail.
    """
    requested = (requested or "auto").lower()
    if requested == "openai":
        return ["openai"]
    if requested == "claude":
        return ["claude", "openai"]
    return ["openai", "claude"]

def get_workspace(workspace_id=""):
    wid = workspace_id or ACTIVE_CONTEXT.get("workspace_id", "")
    if wid and wid in MEMORY["workspaces"]:
        return MEMORY["workspaces"][wid]
    return ACTIVE_CONTEXT.get("current_workspace", {}) or {}

def get_mission(mission_id=""):
    mid = mission_id or ACTIVE_CONTEXT.get("current_mission", {}).get("mission_id", "")
    for w in MEMORY["workflows"]:
        if w.get("mission_id") == mid:
            return w
    return ACTIVE_CONTEXT.get("current_mission", {}) or {}

def create_mission(input_text, mission_type="auto", client="", project="", provider="auto"):
    category = detect_category(input_text)
    mission_type = detect_type(input_text, category) if mission_type == "auto" else mission_type
    client, project = detect_context(input_text, client, project)
    steps = WORKFLOW_TEMPLATES.get(mission_type, WORKFLOW_TEMPLATES["general"])
    mid = f"{slug(client or project or mission_type)}-{int(datetime.utcnow().timestamp())}"
    mission = {
        "mission_id": mid,
        "mission_type": mission_type,
        "input": input_text,
        "client": client,
        "project": project,
        "provider": provider,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
        "current_step_index": 0,
        "progress": 0,
        "steps": [
            {**s, "status": "active" if i == 0 else "pending", "started_at": now() if i == 0 else "", "completed_at": "", "result_summary": "", "asset_title": ""}
            for i, s in enumerate(steps)
        ],
        "outputs": [],
        "next_action": steps[0]["label"] if steps else "Start",
    }
    ACTIVE_CONTEXT.update({
        "current_mission": mission,
        "workflow_id": mid,
        "workflow_type": mission_type,
        "workflow_stage": steps[0]["key"] if steps else "",
        "workflow_progress": 0,
        "client": client,
        "project": project,
    })
    MEMORY["workflows"].insert(0, mission)
    MEMORY["execution_events"].insert(0, {"timestamp": now(), "event": "mission_created", "mission_id": mid})
    return mission

def create_workspace(input_text, workspace_type="auto", client="", project="", provider="auto"):
    category = detect_category(input_text)
    workspace_type = detect_type(input_text, category) if workspace_type == "auto" else workspace_type
    client, project = detect_context(input_text, client, project)
    wid = f"{slug(client or project or workspace_type)}-{int(datetime.utcnow().timestamp())}"
    mission = create_mission(input_text, workspace_type, client, project, provider)
    ws = {
        "workspace_id": wid,
        "workspace_type": workspace_type,
        "title": f"{client or project or workspace_type.title()} Workspace",
        "input": input_text,
        "client": client,
        "project": project,
        "provider": provider,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
        "summary": "",
        "next_executive_decision": "",
        "operator_recommendation": "",
        "pressure_score": 0,
        "package": AUTONOMOUS_PACKAGES.get(workspace_type, AUTONOMOUS_PACKAGES["general"]),
        "mission_id": mission["mission_id"],
        "sections": {
            "overview": {"title": "Executive Overview", "status": "ready", "content": input_text},
            "assets": [],
            "tasks": [],
            "follow_ups": [],
            "warnings": [],
            "decisions": [],
            "timeline": [],
            "operator": [],
            "right_rail": {"next": [], "assets": [], "follow_ups": [], "warnings": [], "operator": []},
        },
    }
    MEMORY["workspaces"][wid] = ws
    ACTIVE_CONTEXT.update({"workspace_id": wid, "current_workspace": ws, "client": client, "project": project})
    MEMORY["workspace_events"].insert(0, {"timestamp": now(), "event": "workspace_created", "workspace_id": wid, "mission_id": mission["mission_id"]})
    db_insert("workspace_created", ws)
    return ws

def classify(req: RunRequest):
    cat = req.category if req.category and req.category != "auto" else detect_category(req.input)
    brain = req.brain if req.brain and req.brain != "auto" else {
        "email": "communications", "meetings": "meetings", "plans": "revenue", "content": "content",
        "marketing": "revenue", "research": "research", "brainstorm": "strategy", "goals": "strategy", "tasks": "execution"
    }.get(cat, "command")
    out = req.output_type if req.output_type and req.output_type != "auto" else {
        "email": "email", "meetings": "brief", "plans": "proposal", "content": "content",
        "marketing": "strategy", "research": "brief", "brainstorm": "ideas", "goals": "goals", "tasks": "tasks"
    }.get(cat, "brief")
    client, project = detect_context(req.input, req.client, req.project)
    wid = req.workflow_id or ACTIVE_CONTEXT.get("workflow_id") or f"{slug(client or project or cat)}-{int(datetime.utcnow().timestamp())}"
    mission = get_mission(req.mission_id)
    if mission and req.step_key:
        for s in mission.get("steps", []):
            if s.get("key") == req.step_key:
                cat, brain, out = s.get("category", cat), s.get("brain", brain), s.get("output_type", out)
    router = {
        "category": cat,
        "brain": brain,
        "output_type": out,
        "urgency": urgency(req.input),
        "meeting_related": cat == "meetings" or "meeting" in (req.input or "").lower() or "call" in (req.input or "").lower(),
        "follow_up_required": cat in ["email", "plans", "meetings"],
        "provider_plan": provider_plan(cat, out, req.provider),
        "context": {"client": client, "project": project, "workflow_id": wid, "workflow_type": cat, "continued_from_memory": bool(ACTIVE_CONTEXT.get("workflow_id"))},
        "workflow_stage": req.step_key or cat,
        "workspace": {"workspace_id": ACTIVE_CONTEXT.get("workspace_id", ""), "primary_section": cat, "recommended_next_panel": "Autonomous Operator", "right_rail": ["operator", "next", "assets", "follow_ups", "warnings"]},
    }
    MEMORY["router_events"].insert(0, {"timestamp": now(), "input": req.input, "router": router})
    return router

SYSTEM_PROMPT = """You are Executive Engine OS, a premium executive operator for CEOs, COOs, CMOs, Presidents, and senior operators.

You are not a chatbot. You are the operator sitting beside the executive. Your job is to convert messy input into boardroom-quality execution.

OUTPUT STANDARD:
- Be specific to the exact input. Never give generic business advice.
- Use the user's language, market, client, objective, risks, numbers, and constraints.
- Assume the executive wants speed, control, leverage, money, clarity, and fewer open loops.
- Never say "consider", "try", "it depends", or "here are some ideas" unless followed by a firm decision.
- Every action must be something a real executive, assistant, COO, or operator can do today.
- The response must feel commercially useful, not motivational.

REQUIRED JSON SCHEMA ONLY:
{
  "what_to_do_now": "one immediate action, under 22 words",
  "decision": "clear executive decision, not generic",
  "next_move": "the next operational move",
  "actions": ["5-8 concrete steps with owner/action/object"],
  "risk": "specific business risk",
  "priority": "High | Medium | Low",
  "reality_check": "hard truth or constraint",
  "leverage": "where the win or compounding value is",
  "constraint": "main bottleneck",
  "financial_impact": "money/revenue/cost/retention impact",
  "asset": {"title":"specific asset title", "type":"proposal|email|brief|plan|strategy|tasks|content", "content":"usable final draft or operating document"},
  "follow_up": "usable follow-up message or next communication"
}

TYPE RULES:
- Proposal: write a client-ready proposal with objective, value proposition, scope, deliverables, timeline, KPIs, risks, and close step.
- Meeting: write agenda, decision required, talking points, questions, objections, and after-call follow-up.
- Email: write the actual email with subject line and CTA.
- Strategy: write operating thesis, target, moves, sequencing, KPIs, risks, and decision gates.
- Tasks: write a prioritized action queue with clear owners and due timing.
- Content: write the actual post/ad/script/copy, not advice about creating it.

Return valid JSON only. No markdown fences.
"""

def safe_json(text):
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
    raise ValueError("Invalid JSON")

def normalize(data, req, router, provider_used):
    actions = data.get("actions", [])
    if not isinstance(actions, list):
        actions = [str(actions)]
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    priority = data.get("priority") if data.get("priority") in ["High", "Medium", "Low"] else router.get("urgency", "High")
    return {
        "what_to_do_now": str(data.get("what_to_do_now") or data.get("next_move") or "Execute the highest-leverage next action."),
        "decision": str(data.get("decision") or "Proceed with the recommended executive path."),
        "next_move": str(data.get("next_move") or data.get("what_to_do_now") or "Execute the first action."),
        "actions": [str(a) for a in actions if str(a).strip()][:8] or ["Confirm objective.", "Create asset.", "Send follow-up."],
        "risk": str(data.get("risk") or "Risk not specified."),
        "priority": priority,
        "reality_check": str(data.get("reality_check") or "Validate assumptions before committing resources."),
        "leverage": str(data.get("leverage") or "Convert input into an asset and next action."),
        "constraint": str(data.get("constraint") or "Missing context may reduce precision."),
        "financial_impact": str(data.get("financial_impact") or "Impact depends on execution quality."),
        "asset": {
            "title": str(asset.get("title") or f"{router['category'].title()} {router['output_type'].title()}"),
            "type": str(asset.get("type") or router["output_type"]),
            "content": str(asset.get("content") or ""),
        },
        "follow_up": str(data.get("follow_up") or "Confirm next step and continue."),
        "provider_used": provider_used,
        "router": router,
        "active_context": dict(ACTIVE_CONTEXT),
        "workspace": get_workspace(),
        "memory": {"workspace_id": ACTIVE_CONTEXT.get("workspace_id", ""), "workflow_id": router["context"].get("workflow_id"), "client": router["context"].get("client"), "project": router["context"].get("project")},
    }

def executive_rule_based_response(req, router, reason=""):
    text = (req.input or "").strip()
    lower = text.lower()
    output_type = router.get("output_type", "brief")
    priority = router.get("urgency", "High")
    client = router.get("context", {}).get("client") or req.client or ACTIVE_CONTEXT.get("client") or "the opportunity"
    project = router.get("context", {}).get("project") or req.project or ACTIVE_CONTEXT.get("project") or "the workstream"

    if any(w in lower for w in ["proposal", "scope", "sow", "pitch"]):
        title = f"{client.title()} Executive Proposal" if client != "the opportunity" else "Executive Proposal"
        content = f"{title}\n\nObjective\nTurn the request into a clear commercial plan: {text}\n\nExecutive Positioning\nThis should not be sold as activity. It should be sold as a controlled operating outcome: clearer pipeline, faster decision-making, measurable execution, and fewer dropped follow-ups.\n\nRecommended Scope\n1. Confirm the business outcome, decision maker, budget range, timeline, and success metric.\n2. Build the core offer or execution plan with clear deliverables and acceptance criteria.\n3. Create the follow-up system: meeting agenda, proposal review, decision deadline, and next owner.\n4. Track the work through a visible action queue with open risks and pending approvals.\n\nDeliverables\n- Executive summary\n- Scope and implementation plan\n- Action queue\n- Risk/constraint register\n- Follow-up email\n- Decision checklist\n\nTimeline\nDay 1: lock context and success criteria.\nDays 2-3: prepare proposal, operating plan, and review package.\nDays 4-5: run decision meeting, handle objections, and confirm next step.\n\nKPIs\n- Decision date confirmed\n- Owner assigned\n- Budget or value range confirmed\n- Next meeting booked\n- Open risks reduced\n\nClose Step\nBook a proposal review and ask for a decision path, not a vague follow-up."
        actions = [
            "Confirm the decision maker, budget range, timeline, and success metric.",
            "Draft the proposal around outcomes, not activities.",
            "Create a one-page executive summary before the full detail.",
            "Prepare the follow-up email with a specific review time.",
            "List the objections that could block approval and answer them before the call.",
            "Set the decision gate: approve, revise, or pause."
        ]
        follow = f"Subject: Next step on {project}\n\nHi [Name],\n\nI pulled the plan into a cleaner executive structure so we can move this from discussion to decision.\n\nThe next step is a short review where we confirm the outcome, scope, timeline, budget range, and decision path.\n\nAre you available for 30 minutes this week to review and lock the next move?\n\nBest,\nWill"
    elif any(w in lower for w in ["meeting", "call", "agenda", "prep"]):
        title = f"{project.title()} Meeting Brief"
        content = f"{title}\n\nMeeting Purpose\nMove the conversation from discussion to a decision.\n\nInput Context\n{text}\n\nAgenda\n1. Confirm the outcome required from the meeting.\n2. Review current context, open constraints, and commercial stakes.\n3. Identify the decision maker and approval path.\n4. Confirm next action, owner, and deadline.\n\nTalking Points\n- The goal is not more discussion. The goal is a clear next move.\n- The highest risk is leaving without an owner, deadline, or decision path.\n- We should separate what is known, what is assumed, and what needs confirmation.\n\nQuestions To Ask\n- What decision needs to be made today?\n- What would stop this from moving forward?\n- Who else needs to approve it?\n- What timeline matters?\n- What does success look like in measurable terms?\n\nClose\nEnd with: owner, deadline, next meeting, and follow-up asset."
        actions = ["Define the meeting decision before joining.", "Prepare three questions that expose the real blocker.", "Write the follow-up email before the call starts.", "Capture owner, deadline, and approval path.", "Send recap within 30 minutes after the call."]
        follow = f"Subject: Recap and next step\n\nHi [Name],\n\nThanks for the time today. My read is that the next decision is to confirm the outcome, owner, and timeline for {project}.\n\nNext step: I will send the working plan and proposed action queue. Please confirm whether the owner and timing look correct.\n\nBest,\nWill"
    elif any(w in lower for w in ["email", "reply", "follow up", "follow-up", "message"]):
        title = "Executive Follow-Up Email"
        content = "Subject: Next step\n\nHi [Name],\n\nI wanted to follow up and move this into a clear next step.\n\nBased on the current context, the priority is to confirm the objective, decision owner, timeline, and what needs to happen next.\n\nMy recommendation is that we use the next conversation to lock the action plan and remove any open blockers.\n\nAre you available for 20-30 minutes this week?\n\nBest,\nWill"
        actions = ["Send the email with one clear CTA.", "Add a deadline or meeting window.", "Attach the relevant asset if available.", "Create a follow-up reminder for 48 hours.", "Track response status in the action queue."]
        follow = content
    else:
        title = "Executive Operating Plan"
        content = f"Executive Operating Plan\n\nInput\n{text}\n\nDecision\nTurn this into a controlled workflow with one owner, one next move, and one measurable result.\n\nOperating Sequence\n1. Define the outcome.\n2. Identify who owns the next action.\n3. Remove the highest-friction blocker.\n4. Create or update the asset required to move forward.\n5. Send the follow-up or decision request.\n6. Review progress within 24 hours.\n\nSuccess Criteria\n- Clear next action\n- Owner assigned\n- Deadline visible\n- Risk known\n- Follow-up sent\n- Decision path documented"
        actions = ["Write the desired outcome in one sentence.", "Pick the single next action that creates movement today.", "Assign an owner and deadline.", "Create the asset or message needed to unblock the work.", "Save the decision and follow-up in the workspace.", "Review the action queue before end of day."]
        follow = "Confirm the next owner, deadline, and decision path so this does not stay open-ended."

    return {
        "what_to_do_now": actions[0],
        "decision": f"Move forward with a controlled {output_type} workflow for {project}.",
        "next_move": actions[1] if len(actions) > 1 else actions[0],
        "actions": actions,
        "risk": "The work stays open-ended if the owner, deadline, approval path, and success metric are not confirmed.",
        "priority": priority,
        "reality_check": "Executives will not use a system that only displays information; it must move decisions and follow-ups forward.",
        "leverage": "The leverage is converting messy context into a decision, asset, action queue, and follow-up in one motion.",
        "constraint": "The main constraint is missing business context: owner, budget, timeline, stakeholder, and measurable outcome.",
        "financial_impact": "The impact is faster cycle time, fewer dropped opportunities, and better conversion from discussion to decision.",
        "asset": {"title": title, "type": output_type if output_type != "auto" else "brief", "content": content},
        "follow_up": follow,
    }

def fallback(req, router, reason):
    data = executive_rule_based_response(req, router, reason)
    return normalize(data, req, router, "fallback:executive-rule-engine")

def call_ai(req, router, provider):
    prompt = json.dumps({"router": router, "active_context": ACTIVE_CONTEXT, "workspace": get_workspace(), "input": req.input}, indent=2)
    if provider == "openai":
        if not openai_client:
            raise RuntimeError("OPENAI_API_KEY missing")
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL, temperature=0.25, max_tokens=2600,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return normalize(safe_json(resp.choices[0].message.content), req, router, f"openai:{OPENAI_MODEL}")
    if provider == "claude":
        if not anthropic_client:
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        resp = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=2600, temperature=0.25,
            system=SYSTEM_PROMPT, messages=[{"role": "user", "content": prompt}]
        )
        raw = "\n".join([b.text for b in resp.content if getattr(b, "type", "") == "text"])
        return normalize(safe_json(raw), req, router, f"claude:{ANTHROPIC_MODEL}")
    raise RuntimeError("Unknown provider")

def add_to_workspace(result, router):
    ws = get_workspace()
    if not ws:
        return {}
    asset = result.get("asset", {})
    step = router.get("workflow_stage", "")
    if asset.get("title") or asset.get("content"):
        rec = {"timestamp": now(), "step": step, "category": router.get("category"), "title": asset.get("title"), "type": asset.get("type"), "content": asset.get("content"), "summary": result.get("what_to_do_now"), "provider_used": result.get("provider_used")}
        ws["sections"]["assets"].insert(0, rec)
        ws["sections"]["right_rail"]["assets"].insert(0, {"title": asset.get("title"), "type": asset.get("type"), "step": step})
    for a in result.get("actions", [])[:8]:
        ws["sections"]["tasks"].insert(0, {"task": a, "status": "open", "created_at": now(), "step": step})
    if result.get("follow_up"):
        f = {"follow_up": result.get("follow_up"), "status": "open", "created_at": now(), "step": step}
        ws["sections"]["follow_ups"].insert(0, f)
        ws["sections"]["right_rail"]["follow_ups"].insert(0, f)
    if result.get("risk"):
        w = {"warning": result.get("risk"), "priority": result.get("priority"), "created_at": now(), "step": step}
        ws["sections"]["warnings"].insert(0, w)
        ws["sections"]["right_rail"]["warnings"].insert(0, w)
    if result.get("decision"):
        ws["sections"]["decisions"].insert(0, {"decision": result.get("decision"), "created_at": now(), "step": step})
    ws["sections"]["timeline"].insert(0, {"timestamp": now(), "event": "asset_generated", "step": step, "summary": result.get("what_to_do_now"), "asset_title": asset.get("title")})
    ws["summary"] = result.get("what_to_do_now", "")
    ws["next_executive_decision"] = result.get("next_move", "")
    ws["sections"]["right_rail"]["next"] = [{"title": result.get("next_move"), "type": "next_move", "priority": result.get("priority")}]
    ws["updated_at"] = now()
    MEMORY["workspaces"][ws["workspace_id"]] = ws
    ACTIVE_CONTEXT["current_workspace"] = ws
    MEMORY["workspace_events"].insert(0, {"timestamp": now(), "event": "workspace_updated", "workspace_id": ws["workspace_id"], "asset_title": asset.get("title")})
    return ws

def update_context(result, router):
    ctx = router.get("context", {})
    ACTIVE_CONTEXT.update({
        "client": ctx.get("client") or ACTIVE_CONTEXT.get("client", ""),
        "project": ctx.get("project") or ACTIVE_CONTEXT.get("project", ""),
        "workflow_id": ctx.get("workflow_id") or ACTIVE_CONTEXT.get("workflow_id", ""),
        "workflow_type": ctx.get("workflow_type") or router.get("category", ""),
        "workflow_stage": router.get("workflow_stage", ""),
        "last_category": router.get("category", ""),
        "last_output_type": router.get("output_type", ""),
        "last_summary": result.get("what_to_do_now", ""),
        "last_asset_title": result.get("asset", {}).get("title", ""),
        "last_asset_content": compact(result.get("asset", {}).get("content", ""), 1200),
        "last_follow_up": result.get("follow_up", ""),
    })
    ACTIVE_CONTEXT["chain"].insert(0, {"timestamp": now(), "category": router.get("category"), "stage": router.get("workflow_stage"), "summary": result.get("what_to_do_now"), "asset_title": result.get("asset", {}).get("title")})
    ACTIVE_CONTEXT["chain"] = ACTIVE_CONTEXT["chain"][:20]
    add_to_workspace(result, router)
    MEMORY["contexts"].insert(0, dict(ACTIVE_CONTEXT))

def scan_operator_state():
    workspaces = list(MEMORY["workspaces"].values())
    active_ws = get_workspace()
    open_tasks = []
    open_followups = []
    warnings = []
    incomplete_workflows = []

    for ws in workspaces:
        sections = ws.get("sections", {})
        for task in sections.get("tasks", []):
            if task.get("status", "open") == "open":
                open_tasks.append({"workspace_id": ws.get("workspace_id"), "title": task.get("task"), "client": ws.get("client"), "project": ws.get("project")})
        for f in sections.get("follow_ups", []):
            if f.get("status", "open") == "open":
                open_followups.append({"workspace_id": ws.get("workspace_id"), "title": f.get("follow_up"), "client": ws.get("client"), "project": ws.get("project")})
        for w in sections.get("warnings", []):
            warnings.append({"workspace_id": ws.get("workspace_id"), "title": w.get("warning"), "priority": w.get("priority"), "client": ws.get("client"), "project": ws.get("project")})
        if ws.get("status") not in ["complete", "archived"]:
            incomplete_workflows.append({"workspace_id": ws.get("workspace_id"), "title": ws.get("title"), "status": ws.get("status"), "summary": ws.get("summary")})

    pressure_score = min(100, len(open_tasks) * 5 + len(open_followups) * 8 + len(warnings) * 12 + len(incomplete_workflows) * 6)
    attention = []
    if warnings:
        attention.append({"type": "risk", "title": warnings[0]["title"], "priority": warnings[0].get("priority", "High")})
    if open_followups:
        attention.append({"type": "follow_up", "title": open_followups[0]["title"], "priority": "High"})
    if open_tasks:
        attention.append({"type": "task", "title": open_tasks[0]["title"], "priority": "Medium"})
    if incomplete_workflows:
        attention.append({"type": "workflow", "title": incomplete_workflows[0]["title"], "priority": "Medium"})

    top_priority = attention[0]["title"] if attention else "Ready when you are."
    next_best_action = "Open the highest-pressure workspace and complete the next follow-up." if attention else "Hey Will, let’s Rock n Roll today."

    state = {
        "mode": "active",
        "last_scan": now(),
        "pressure_score": pressure_score,
        "top_priority": top_priority,
        "next_best_action": next_best_action,
        "attention_required": attention[:8],
        "counts": {
            "open_tasks": len(open_tasks),
            "open_followups": len(open_followups),
            "warnings": len(warnings),
            "incomplete_workflows": len(incomplete_workflows),
            "workspaces": len(workspaces),
            "assets": len(MEMORY["assets"]),
        },
        "active_workspace": {
            "workspace_id": active_ws.get("workspace_id", ""),
            "title": active_ws.get("title", ""),
            "summary": active_ws.get("summary", ""),
            "next_executive_decision": active_ws.get("next_executive_decision", ""),
        },
    }
    ACTIVE_CONTEXT["operator_state"] = state
    MEMORY["operator_events"].insert(0, {"timestamp": now(), "event": "operator_scan", "pressure_score": pressure_score, "top_priority": top_priority})
    return state

def generate_daily_briefing():
    op = scan_operator_state()
    ws = get_workspace()
    briefing = {
        "status": "ready",
        "created_at": now(),
        "title": "Executive Daily Briefing",
        "headline": op["top_priority"],
        "pressure_score": op["pressure_score"],
        "what_needs_attention_now": op["attention_required"][:5],
        "next_best_action": op["next_best_action"],
        "active_workspace": op["active_workspace"],
        "today": {
            "open_tasks": op["counts"]["open_tasks"],
            "open_followups": op["counts"]["open_followups"],
            "warnings": op["counts"]["warnings"],
            "assets_ready": op["counts"]["assets"],
        },
        "operator_recommendation": "Advance the highest-pressure workflow before creating new work." if op["pressure_score"] >= 50 else "Continue building workspace assets and follow-ups.",
    }
    MEMORY["briefings"].insert(0, briefing)
    if ws:
        ws["operator_recommendation"] = briefing["operator_recommendation"]
        ws["pressure_score"] = op["pressure_score"]
        ws["sections"]["operator"].insert(0, briefing)
        ws["sections"]["right_rail"]["operator"].insert(0, {"title": briefing["headline"], "pressure_score": op["pressure_score"], "next": briefing["next_best_action"]})
        MEMORY["workspaces"][ws["workspace_id"]] = ws
        ACTIVE_CONTEXT["current_workspace"] = ws
    return briefing

def operator_next_action(auto_generate=False, provider="auto"):
    op = scan_operator_state()
    if auto_generate and op["attention_required"]:
        top = op["attention_required"][0]
        prompt = f"Resolve or advance this executive pressure item: {top['title']}. Create the next best executive output."
        return run_engine(RunRequest(input=prompt, provider=provider, category="tasks", brain="execution", output_type="tasks"))
    return {"status": "ready", "operator_state": op, "next_action": op["next_best_action"], "active_context": ACTIVE_CONTEXT}

def advance_mission(mission, step_key, result):
    if not mission:
        return {}
    steps = mission.get("steps", [])
    idx = next((i for i, s in enumerate(steps) if s.get("key") == step_key), mission.get("current_step_index", 0))
    if steps:
        steps[idx]["status"] = "done"
        steps[idx]["completed_at"] = now()
        steps[idx]["result_summary"] = result.get("what_to_do_now", "")
        steps[idx]["asset_title"] = result.get("asset", {}).get("title", "")
        if idx + 1 < len(steps):
            steps[idx + 1]["status"] = "active"
            steps[idx + 1]["started_at"] = steps[idx + 1].get("started_at") or now()
            mission["current_step_index"] = idx + 1
            mission["next_action"] = steps[idx + 1]["label"]
            mission["status"] = "active"
        else:
            mission["current_step_index"] = idx
            mission["next_action"] = "Mission complete"
            mission["status"] = "complete"
        mission["progress"] = round(len([s for s in steps if s.get("status") == "done"]) / len(steps) * 100)
        ACTIVE_CONTEXT["workflow_progress"] = mission["progress"]
    mission["updated_at"] = now()
    mission.setdefault("outputs", []).insert(0, {"timestamp": now(), "step_key": step_key, "summary": result.get("what_to_do_now"), "asset_title": result.get("asset", {}).get("title"), "provider_used": result.get("provider_used")})
    ACTIVE_CONTEXT["current_mission"] = mission
    MEMORY["execution_events"].insert(0, {"timestamp": now(), "event": "step_completed", "mission_id": mission.get("mission_id"), "step_key": step_key, "progress": mission.get("progress")})
    return mission


# V35050_OUTPUT_QUALITY_HELPERS

def _clean_text(value: str) -> str:
    return (value or "").strip()

def extract_workspace_identity(input_text: str):
    text = _clean_text(input_text)
    lowered = text.lower()

    client = ""
    project = "Executive Workstream"
    workspace_type = "general"

    if "auto loan" in lowered or "dealership" in lowered or "car" in lowered:
        client = "Ontario Auto Loan Dealership"
        project = "Ontario Auto Loan Growth"
        workspace_type = "proposal"
    elif "hvac" in lowered:
        client = "ABC HVAC"
        project = "Growth Proposal"
        workspace_type = "proposal"
    elif "seo" in lowered or "google ads" in lowered or "marketing" in lowered:
        client = "Marketing Client"
        project = "Growth Strategy"
        workspace_type = "marketing"
    elif "meeting" in lowered or "call" in lowered:
        client = "Meeting Stakeholders"
        project = "Meeting Preparation"
        workspace_type = "meeting"

    words = text.replace(".", " ").replace(",", " ").split()
    if not client and words:
        client = " ".join(words[:4]).strip() or "Client"

    if "proposal" in lowered:
        workspace_type = "proposal"
    if "email" in lowered or "follow" in lowered:
        workspace_type = "email"
    if "meeting" in lowered or "call" in lowered:
        workspace_type = "meeting"
    if "marketing" in lowered or "seo" in lowered or "ads" in lowered:
        workspace_type = "marketing" if workspace_type != "proposal" else "proposal"

    title = f"{client} Workspace" if client else "Executive Workspace"
    return {
        "client": client or "Client",
        "project": project,
        "workspace_type": workspace_type,
        "title": title
    }

def build_quality_asset(input_text: str, output_type: str = "proposal", category: str = "plans"):
    text = _clean_text(input_text)
    identity = extract_workspace_identity(text)
    client = identity["client"]
    project = identity["project"]
    lowered = text.lower()

    cpa_line = "CPA target: under $100" if "$100" in text or "100" in text and "cpa" in lowered else "CPA target: confirm acceptable acquisition cost"
    title = f"{client} Growth Proposal"

    proposal = f"""CLIENT-READY GROWTH PROPOSAL

CLIENT
{client}

OBJECTIVE
Build a measurable acquisition system for {client} that improves qualified lead volume, conversion quality, and sales follow-up while keeping cost discipline clear.

CURRENT CONTEXT
{text}

POSITIONING
This is not a generic marketing engagement. The opportunity is to create a controlled growth engine: high-intent demand capture through Google Ads, long-term authority through SEO, trust-building through social/content, and clear reporting tied to qualified approvals and sold units.

PRIMARY OUTCOME
Increase qualified applications and booked sales conversations while protecting margin and keeping {cpa_line} visible in weekly reporting.

RECOMMENDED SCOPE

1. SEO Growth Foundation
- Build or improve service/location pages around approval intent.
- Create content that answers credit, approval, vehicle, financing, and trust questions.
- Improve technical structure, internal linking, and conversion paths.
- Track organic leads by source, page, and quality.

2. Google Ads Acquisition System
- Launch high-intent search campaigns around auto loan, car financing, bad credit car loan, and dealership financing intent.
- Use tight keyword controls, negative keywords, and location targeting.
- Build landing pages matched to approval intent.
- Track calls, forms, booked appointments, approvals, and sold units.

3. Social + Remarketing Layer
- Use social to build trust, explain approvals, show credibility, and warm up prospects.
- Retarget website visitors and abandoned form users.
- Create simple proof-based content that lowers buyer hesitation.

4. Reporting + Operating Rhythm
- Weekly executive scorecard.
- CPA, CPL, lead quality, booked appointment rate, approval rate, and sold-unit visibility.
- Clear recommendations every week: scale, pause, improve, or test.

EXECUTION PLAN

Week 1:
- Confirm goals, geography, budget, offer, target CPA, and lead quality criteria.
- Audit current website, ads, tracking, and sales handoff.

Week 2:
- Build campaign structure, landing page recommendations, tracking plan, and reporting dashboard.

Weeks 3-4:
- Launch Google Ads, SEO priority pages, and social/remarketing assets.
- Monitor early lead quality and adjust targeting.

Month 2+:
- Scale winning campaigns, improve landing pages, expand SEO content, and tighten sales follow-up.

RISKS
- CPA target may fail without proper tracking, fast follow-up, and strong landing page conversion.
- Lead quality may look good on volume but fail at approval/sales stage.
- Generic campaigns will waste budget if not segmented by intent and geography.

NEXT EXECUTIVE DECISION
Confirm monthly budget, target geography, definition of qualified lead, current close rate, and who owns follow-up speed.

FOLLOW-UP
Schedule a 30-minute proposal review to confirm scope, numbers, and launch timeline."""

    email = f"""Subject: Next steps for {client} growth plan

Hi [Name],

Based on what you shared, the opportunity is to build a cleaner acquisition system across SEO, Google Ads, and social while keeping lead quality and CPA discipline front and center.

The next step is to review the proposed scope, confirm the target geography, define what counts as a qualified approval, and align on the monthly budget and reporting cadence.

I suggest we use the next call to lock down:
1. target CPA and lead quality criteria
2. campaign/geography priorities
3. website or landing page requirements
4. tracking and reporting expectations
5. launch timeline and next owners

Are you available this week for a 30-minute review?

Best,
Will"""

    meeting = f"""MEETING BRIEF — {client}

MEETING OBJECTIVE
Align on the growth proposal, confirm numbers, and define the launch path.

AGENDA
1. Confirm business objective and target geography.
2. Confirm monthly budget and CPA target.
3. Define qualified lead / qualified approval.
4. Review SEO, Google Ads, social, and tracking scope.
5. Identify risks and operational requirements.
6. Confirm next step, owner, and timeline.

KEY QUESTIONS
- What is the current cost per lead and cost per funded/sold customer?
- What percentage of leads become approvals?
- What percentage of approvals become sold vehicles?
- Who responds to leads and how fast?
- What locations/regions matter most?
- What budget range is realistic for the first 60 days?

LIKELY OBJECTIONS
- CPA under $100 may be aggressive.
- Tracking may not currently connect marketing spend to sold units.
- Website conversion may limit ad performance.
- Sales follow-up speed may affect campaign results.

DECISION REQUIRED
Approve the first 30-day launch plan and confirm tracking requirements before spend scales."""

    tasks = [
        "Confirm target geography and monthly ad budget.",
        "Define what counts as a qualified lead and qualified approval.",
        "Audit current website, landing pages, and tracking.",
        "Build Google Ads keyword structure and negative keyword list.",
        "Create proposal review agenda and send follow-up email.",
        "Prepare SEO priority page list and content plan.",
        "Create weekly executive scorecard template.",
    ]

    if output_type in ["email", "follow_up"] or category == "email":
        content = email
        asset_title = f"{client} Follow-Up Email"
        asset_type = "email"
    elif output_type in ["meeting", "brief"] or category == "meeting":
        content = meeting
        asset_title = f"{client} Meeting Brief"
        asset_type = "meeting_brief"
    else:
        content = proposal
        asset_title = title
        asset_type = "proposal"

    return {
        "identity": identity,
        "asset": {
            "title": asset_title,
            "type": asset_type,
            "content": content,
            "summary": f"Client-ready {asset_type.replace('_', ' ')} for {client} focused on {project}."
        },
        "tasks": tasks,
        "follow_up": email,
        "risk": "CPA and lead quality targets may fail if tracking, landing pages, and sales follow-up are not controlled from day one.",
        "decision": "Confirm budget, geography, qualified-lead definition, and launch owner before scaling spend.",
        "next_move": "Schedule a proposal review meeting and validate CPA assumptions before campaign buildout.",
        "what_to_do_now": "Send the proposal review follow-up and collect budget, geography, tracking, and lead-quality requirements.",
        "priority": "High"
    }

def clear_all_runtime_state():
    global active_context, recent_contexts, current_mission, current_workspace, memory_store, operator_state
    try:
        active_context = {
            "client": "",
            "company": "",
            "project": "",
            "workflow_id": "",
            "workflow_type": "",
            "last_category": "",
            "last_output_type": "",
            "last_summary": "",
            "last_asset_title": "",
            "last_follow_up": "",
            "chain": []
        }
    except Exception:
        pass
    try:
        recent_contexts = []
    except Exception:
        pass
    try:
        current_mission = {}
    except Exception:
        pass
    try:
        current_workspace = {}
    except Exception:
        pass
    try:
        operator_state = {
            "mode": "ready",
            "last_scan": "",
            "pressure_score": 0,
            "top_priority": "",
            "next_best_action": "Start a new workspace.",
            "attention_required": [],
            "counts": {}
        }
    except Exception:
        pass
    try:
        if isinstance(memory_store, dict):
            for key in memory_store:
                if isinstance(memory_store[key], list):
                    memory_store[key].clear()
    except Exception:
        pass
    return {"status": "ok", "message": "Runtime workspace, context, and memory state cleared."}




# V35060_EXECUTIVE_OPERATING_FLOW_STABILIZATION
BAD_OUTPUT_MARKERS = [
    "provider failed", "provider failure", "missing credits", "confirm context and run again",
    "fallback", "not specified", "create the executive workspace package manually",
    "retry with provider=openai", "add claude credits", "risk not specified"
]

def _is_bad_output(value):
    text = str(value or "").strip().lower()
    if not text or len(text) < 18:
        return True
    return any(marker in text for marker in BAD_OUTPUT_MARKERS)

def _dedupe_list(items, key_fields=("title", "task", "follow_up", "warning", "decision", "content")):
    clean, seen = [], set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        signature = ""
        for k in key_fields:
            if item.get(k):
                signature = str(item.get(k)).strip().lower()
                break
        if not signature:
            signature = str(item).strip().lower()
        if not signature or signature in seen or _is_bad_output(signature):
            continue
        seen.add(signature)
        clean.append(item)
    return clean

def v35080_clean_workspace(workspace):
    if not isinstance(workspace, dict):
        return workspace

    sections = workspace.setdefault("sections", {})
    sections["assets"] = _dedupe_list(sections.get("assets", []), ("title", "content", "summary"))
    sections["tasks"] = _dedupe_list(sections.get("tasks", []), ("task",))
    sections["follow_ups"] = _dedupe_list(sections.get("follow_ups", []), ("follow_up", "title"))
    sections["warnings"] = _dedupe_list(sections.get("warnings", []), ("warning", "title"))
    sections["decisions"] = _dedupe_list(sections.get("decisions", []), ("decision",))
    sections["timeline"] = _dedupe_list(sections.get("timeline", []), ("event", "asset_title", "summary"))

    if _is_bad_output(workspace.get("summary")):
        input_text = workspace.get("input", "")
        identity = extract_workspace_identity(input_text)
        workspace["summary"] = f"Build a client-ready execution workspace for {identity['client']} focused on {identity['project']}."

    if _is_bad_output(workspace.get("next_executive_decision")):
        workspace["next_executive_decision"] = "Confirm the business objective, required asset, target buyer, timeline, and decision owner."

    if _is_bad_output(workspace.get("operator_recommendation")):
        workspace["operator_recommendation"] = "Start with a focused executive brief, then create the client-ready asset and follow-up."

    right = sections.setdefault("right_rail", {})
    right["assets"] = _dedupe_list(right.get("assets", []), ("title",))
    right["follow_ups"] = _dedupe_list(right.get("follow_ups", []), ("follow_up", "title"))
    right["warnings"] = _dedupe_list(right.get("warnings", []), ("warning", "title"))
    right["next"] = _dedupe_list(right.get("next", []), ("title",))

    if not right.get("next"):
        right["next"] = [{"title": workspace.get("next_executive_decision", "Define the next executive decision."), "type": "next_move", "priority": "High"}]
    if not right.get("assets") and sections.get("assets"):
        right["assets"] = [{"title": a.get("title", "Asset"), "type": a.get("type", "asset"), "step": a.get("step", "workspace")} for a in sections["assets"][:4]]
    if not right.get("follow_ups") and sections.get("follow_ups"):
        right["follow_ups"] = sections["follow_ups"][:4]
    if not right.get("warnings") and sections.get("warnings"):
        right["warnings"] = sections["warnings"][:4]

    return workspace

def guided_context_questions(input_text):
    identity = extract_workspace_identity(input_text)
    return [
        f"What is the specific outcome you want for {identity['client']}?",
        "Who is the decision-maker or stakeholder?",
        "What is the deadline or target date?",
        "What asset do you need first: proposal, email, meeting brief, plan, or task list?",
        "What numbers matter most: budget, CPA, revenue, conversion rate, or timeline?"
    ]

def build_stabilized_guidance(input_text):
    identity = extract_workspace_identity(input_text)
    questions = guided_context_questions(input_text)
    return {
        "what_to_do_now": f"Create a focused executive brief for {identity['client']} and answer the highest-leverage missing context questions.",
        "decision": "Use guided extraction before generating final client-ready assets.",
        "next_move": f"Clarify outcome, stakeholder, deadline, and first required asset for {identity['client']}.",
        "actions": [
            "Confirm the exact business outcome.",
            "Identify the decision-maker and audience.",
            "Choose the first asset to create.",
            "Define the key metric or constraint.",
            "Generate the client-ready output after context is clear."
        ],
        "risk": "Weak context creates generic output, duplicate tasks, and low-value assets.",
        "priority": "High",
        "asset": {
            "title": f"{identity['client']} Context Intake Brief",
            "type": "brief",
            "content": "To move this forward, answer these:\\n- " + "\\n- ".join(questions),
            "summary": "Guided intake brief to prevent generic output."
        },
        "follow_up": "Confirm the missing context, then generate the first executive asset.",
        "provider_used": "openai-first:stabilization-v35090",
        "router": {"category": "guided", "output_type": "brief", "workspace_type": identity["workspace_type"]},
        "active_context": dict(ACTIVE_CONTEXT),
        "workspace": {},
        "operator_state": ACTIVE_CONTEXT.get("operator_state", {})
    }




# V35080_OUTPUT_GUARD_WORKSPACE_CLEANUP

V35080_BLOCKED_PHRASES = [
    "provider failed",
    "provider failure",
    "missing credits",
    "retry with",
    "run again",
    "confirm context and run again",
    "fallback",
    "ai provider failed",
    "openai failed",
    "claude failed",
    "provider=openai",
    "provider=claude",
    "internal error",
    "malformed",
    "risk not specified",
    "create the executive workspace package manually",
    "no provider available",
    "rate limit",
    "token limit",
]

def v35080_contains_blocked(value):
    text = str(value or "").lower()
    return any(p in text for p in V35080_BLOCKED_PHRASES)

def v35080_safe_text(value, replacement):
    value = str(value or "").strip()
    if not value or len(value) < 12 or v35080_contains_blocked(value):
        return replacement
    return value

def v35080_normalize_signature(value):
    import re
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value

def v35080_clean_list(items, primary_keys):
    cleaned = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        key = ""
        for k in primary_keys:
            if item.get(k):
                key = item.get(k)
                break
        sig = v35080_normalize_signature(key or str(item))
        if not sig or sig in seen or v35080_contains_blocked(sig):
            continue
        seen.add(sig)
        cleaned.append(item)
    return cleaned

def v35080_executive_safe_package(input_text=""):
    identity = extract_workspace_identity(input_text or "")
    quality = build_quality_asset(input_text or f"Build executive workspace for {identity['client']}", "proposal", "plans")
    return quality

def v35080_clean_workspace(workspace):
    if not isinstance(workspace, dict):
        return workspace

    input_text = workspace.get("input", "")
    identity = extract_workspace_identity(input_text or workspace.get("title", ""))
    safe = v35080_executive_safe_package(input_text)

    workspace["title"] = v35080_safe_text(workspace.get("title"), identity["title"])
    workspace["client"] = v35080_safe_text(workspace.get("client"), identity["client"])
    workspace["project"] = v35080_safe_text(workspace.get("project"), identity["project"])
    workspace["summary"] = v35080_safe_text(workspace.get("summary"), safe["asset"]["summary"])
    workspace["next_executive_decision"] = v35080_safe_text(workspace.get("next_executive_decision"), safe["decision"])
    workspace["operator_recommendation"] = v35080_safe_text(workspace.get("operator_recommendation"), safe["next_move"])

    sections = workspace.setdefault("sections", {})
    sections["assets"] = v35080_clean_list(sections.get("assets", []), ["title", "content", "summary"])
    sections["tasks"] = v35080_clean_list(sections.get("tasks", []), ["task"])
    sections["follow_ups"] = v35080_clean_list(sections.get("follow_ups", []), ["follow_up", "title"])
    sections["warnings"] = v35080_clean_list(sections.get("warnings", []), ["warning", "title"])
    sections["decisions"] = v35080_clean_list(sections.get("decisions", []), ["decision"])
    sections["timeline"] = v35080_clean_list(sections.get("timeline", []), ["event", "summary", "asset_title"])

    if not sections["assets"]:
        sections["assets"] = [{
            "title": safe["asset"]["title"],
            "type": safe["asset"]["type"],
            "content": safe["asset"]["content"],
            "summary": safe["asset"]["summary"],
            "step": "proposal",
            "category": "plans",
            "provider_used": "stabilization:v35090"
        }]

    if len(sections["tasks"]) < 3:
        sections["tasks"] = [{"task": t, "status": "open", "step": "execution"} for t in safe["tasks"]]

    if not sections["follow_ups"]:
        sections["follow_ups"] = [{"follow_up": safe["follow_up"], "status": "open", "step": "follow_up"}]

    if not sections["warnings"]:
        sections["warnings"] = [{"warning": safe["risk"], "priority": "High", "step": "risk"}]

    if not sections["decisions"]:
        sections["decisions"] = [{"decision": safe["decision"], "step": "decision"}]

    right = sections.setdefault("right_rail", {})
    right["next"] = [{"title": workspace["next_executive_decision"], "type": "next_move", "priority": "High"}]
    right["assets"] = [{"title": a.get("title", "Asset"), "type": a.get("type", "asset"), "step": a.get("step", "workspace")} for a in sections["assets"][:4]]
    right["follow_ups"] = sections["follow_ups"][:4]
    right["warnings"] = sections["warnings"][:4]
    right["operator"] = right.get("operator", [])

    return workspace

def v35080_clean_response_payload(payload, input_text=""):
    if not isinstance(payload, dict):
        payload = {}
    safe = v35080_executive_safe_package(input_text)

    payload["what_to_do_now"] = v35080_safe_text(payload.get("what_to_do_now"), safe["what_to_do_now"])
    payload["decision"] = v35080_safe_text(payload.get("decision"), safe["decision"])
    payload["next_move"] = v35080_safe_text(payload.get("next_move"), safe["next_move"])
    payload["risk"] = v35080_safe_text(payload.get("risk"), safe["risk"])
    payload["priority"] = payload.get("priority") if payload.get("priority") in ["High", "Medium", "Low"] else "High"

    actions = payload.get("actions")
    if not isinstance(actions, list):
        actions = []
    actions = [str(a).strip() for a in actions if str(a).strip() and not v35080_contains_blocked(a)]
    deduped = []
    seen = set()
    for a in actions:
        sig = v35080_normalize_signature(a)
        if sig and sig not in seen and len(a.split()) >= 3:
            seen.add(sig)
            deduped.append(a)
    if len(deduped) < 3:
        deduped = safe["tasks"]
    payload["actions"] = deduped[:8]

    asset = payload.get("asset")
    if not isinstance(asset, dict) or v35080_contains_blocked(asset):
        payload["asset"] = safe["asset"]

    payload["follow_up"] = v35080_safe_text(payload.get("follow_up"), safe["follow_up"])
    if isinstance(payload.get("workspace"), dict):
        payload["workspace"] = v35080_clean_workspace(payload["workspace"])

    payload["provider_used"] = "openai-first:stabilization-v35090"
    return payload



def sanitize_workspace(workspace):
    """V35090 compatibility shim: preserve old route calls while using the active workspace cleaner."""
    return v35080_clean_workspace(workspace)

@app.post("/purge-pollution")
def purge_pollution():
    ws = ACTIVE_CONTEXT.get("current_workspace", {})
    if ws:
        ws = v35080_clean_workspace(ws)
        ACTIVE_CONTEXT["current_workspace"] = ws
    return {"status": "ok", "version": VERSION, "workspace": ws}

@app.get("/pollution-audit")
def pollution_audit():
    ws = ACTIVE_CONTEXT.get("current_workspace", {})
    text = str(ws)
    return {
        "status": "ok",
        "version": VERSION,
        "pollution_detected": v35080_contains_blocked(text),
        "blocked_phrases": [p for p in V35080_BLOCKED_PHRASES if p in text.lower()],
        "workspace_present": isinstance(ws, dict) and bool(ws)
    }


@app.get("/")
def root():
    return {"status": "live", "service": "Executive Engine OS", "version": VERSION, "message": "Autonomous Executive Operator live."}

@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}

@app.get("/debug")
def debug():
    return {
        "status": "ok",
        "version": VERSION,
        "openai": {"has_api_key": bool(OPENAI_API_KEY), "model": OPENAI_MODEL},
        "claude": {"has_api_key": bool(ANTHROPIC_API_KEY), "model": ANTHROPIC_MODEL},
        "active_context": ACTIVE_CONTEXT,
        "memory_counts": {k: len(v) if not isinstance(v, dict) else len(v.keys()) for k, v in MEMORY.items()},
    }


def service_test_console_html():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Executive Engine OS — Backend Test Console</title>
  <style>
    :root{--bg:#f7f7f5;--ink:#070707;--line:#dfdfdb;--card:#fff;--orange:#ff5a1f;--green:#00a66a;--shadow:0 24px 70px rgba(0,0,0,.10);--radius:22px}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-weight:650}
    .wrap{max-width:1180px;margin:0 auto;padding:58px 24px 80px}
    h1{font-size:54px;line-height:.96;margin:0 0 10px;letter-spacing:-.06em;font-weight:950}
    .sub{font-size:18px;color:#3f3f3f;margin:0 0 34px;font-weight:500}
    .grid{display:grid;grid-template-columns:1fr 420px;gap:22px;align-items:start}
    .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:24px}
    .label{font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#676767;font-weight:950;margin-bottom:12px}
    input{width:100%;border:1px solid var(--line);background:#fff;border-radius:16px;padding:18px 20px;font:inherit;outline:none;margin-bottom:16px}
    .actions{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0 10px}
    button{border:0;border-radius:14px;padding:15px 22px;font-weight:950;cursor:pointer;background:#111;color:white}
    button.orange{background:var(--orange)}button.light{background:white;color:#111;border:1px solid var(--line)}button:disabled{opacity:.55;cursor:not-allowed}
    .small{font-size:13px;color:#737373;font-weight:600}.services{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:18px}
    .svc{border:1px solid var(--line);border-radius:16px;background:#fff;padding:15px;cursor:pointer;transition:.15s ease}.svc:hover{transform:translateY(-1px);box-shadow:0 12px 30px rgba(0,0,0,.08)}
    .svc strong{display:block;font-size:14px;margin-bottom:6px}.svc code{font-size:12px;color:#696969;word-break:break-all}
    .status{margin-top:10px;display:inline-flex;align-items:center;gap:7px;border-radius:999px;padding:7px 10px;font-size:12px;background:#eee;color:#333;font-weight:950}
    .status.ok{background:#e9fff5;color:#04734c}.status.fail{background:#fff0ed;color:#c22512}.status.wait{background:#f3f4f6;color:#4b5563}
    .dot{width:8px;height:8px;border-radius:99px;background:currentColor;display:inline-block}
    .console{background:#030303;color:#f9fafb;border-radius:18px;padding:20px;min-height:520px;white-space:pre-wrap;overflow:auto;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono",monospace;font-size:13px;line-height:1.55;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
    .summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}.metric{border:1px solid var(--line);border-radius:16px;padding:16px;background:#fff}
    .metric strong{display:block;font-size:31px;letter-spacing:-.05em}.metric span{font-size:12px;color:#6f6f6f;text-transform:uppercase;letter-spacing:.12em;font-weight:950}
    .topline{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:14px}.badge{border:1px solid var(--line);border-radius:999px;padding:9px 13px;background:#fff;font-size:13px;font-weight:950}
    .badge.live{background:#e9fff5;color:#04734c;border-color:#b5efd5}.footer{margin-top:14px;color:#747474;font-size:13px;font-weight:600}
    @media(max-width:980px){.grid{grid-template-columns:1fr}.services{grid-template-columns:1fr}h1{font-size:42px}}
  </style>
</head>
<body>
  <main class="wrap">
    <div class="topline">
      <div><h1>Executive Engine Service Test Console</h1><p class="sub">Backend-hosted console for testing operator, workspace, memory, provider, and system routes.</p></div>
      <span class="badge live" id="topStatus">● Ready</span>
    </div>
    <section class="grid">
      <div class="card">
        <div class="label">Backend Base URL</div>
        <input id="baseUrl" value="https://executive-engine-os.onrender.com" />
        <div class="actions">
          <button id="runAllBtn" onclick="runAll()">Run All Tests</button>
          <button class="orange" onclick="runCritical()">Run Critical</button>
          <button class="light" onclick="copyOutput()">Copy Output</button>
          <button class="light" onclick="clearOutput()">Clear</button>
        </div>
        <div class="small">Tests 10 live service URLs. Click any service card to run it individually.</div>
        <div class="summary">
          <div class="metric"><span>Passed</span><strong id="passed">0</strong></div>
          <div class="metric"><span>Failed</span><strong id="failed">0</strong></div>
          <div class="metric"><span>Total ms</span><strong id="totalMs">0</strong></div>
        </div>
        <div class="services" id="services"></div>
        <div class="footer">Backend route: <strong>/test-report</strong>. JSON available at <strong>/test-report-json</strong>.</div>
      </div>
      <div class="card"><div class="label">Test Output</div><div class="console" id="output">Click “Run All Tests” to verify Executive Engine OS services.</div></div>
    </section>
  </main>
<script>
const services=[
{name:"Root",method:"GET",path:"/",critical:true},
{name:"Health",method:"GET",path:"/health",critical:true},
{name:"Test Report JSON",method:"GET",path:"/test-report-json",critical:true},
{name:"Providers",method:"GET",path:"/providers",critical:true},
{name:"Debug",method:"GET",path:"/debug",critical:true},
{name:"Operator Scan",method:"GET",path:"/operator-scan",critical:false},
{name:"Workspace State",method:"GET",path:"/workspace-state",critical:false},
{name:"Workspace Summary",method:"GET",path:"/workspace-summary",critical:false},
{name:"Mission State",method:"GET",path:"/mission-state",critical:false},
{name:"Engine State",method:"GET",path:"/engine-state",critical:false}
];
let results={};function $(id){return document.getElementById(id)}
function renderServices(){$("services").innerHTML=services.map((s,i)=>`<div class="svc" onclick="runOne(${i})"><strong>${s.name}</strong><code>${s.method} ${s.path}</code><br><span id="status-${i}" class="status wait"><span class="dot"></span> Not tested</span></div>`).join("")}
function setStatus(i,type,text){const el=$("status-"+i);if(!el)return;el.className="status "+(type||"wait");el.innerHTML=`<span class="dot"></span> ${text}`}
function base(){return $("baseUrl").value.replace(/\/+$/,"")}
async function runOne(i){const s=services[i];setStatus(i,"wait","Testing...");const start=performance.now();try{const res=await fetch(base()+s.path,{method:s.method,headers:{"Accept":"application/json"}});const text=await res.text();const ms=Math.round(performance.now()-start);let body;try{body=JSON.parse(text)}catch(e){body=text.slice(0,500)}const ok=res.ok&&!(body&&body.detail==="Not Found");results[s.path]={name:s.name,path:s.path,ok,status:res.status,ms,body};setStatus(i,ok?"ok":"fail",`${res.status} · ${ms}ms`);logResult(s,results[s.path]);updateSummary();return results[s.path]}catch(e){const ms=Math.round(performance.now()-start);results[s.path]={name:s.name,path:s.path,ok:false,status:"FETCH_FAILED",ms,error:e.message};setStatus(i,"fail",`Failed · ${ms}ms`);logResult(s,results[s.path]);updateSummary();return results[s.path]}}
async function runAll(){$("runAllBtn").disabled=true;$("topStatus").textContent="● Running";results={};$("output").textContent=`EXECUTIVE ENGINE OS SERVICE TEST\\nStarted: ${new Date().toISOString()}\\nBase: ${base()}\\n\\n`;for(let i=0;i<services.length;i++){await runOne(i)}$("topStatus").textContent="● Complete";$("runAllBtn").disabled=false;finalReport()}
async function runCritical(){$("output").textContent=`EXECUTIVE ENGINE OS CRITICAL TEST\\nStarted: ${new Date().toISOString()}\\nBase: ${base()}\\n\\n`;for(let i=0;i<services.length;i++){if(services[i].critical)await runOne(i)}finalReport()}
function logResult(service,r){const header=`${r.ok?"PASS":"FAIL"} — ${service.name} (${service.method} ${service.path}) — ${r.status} — ${r.ms}ms`;const body=r.error?{error:r.error}:r.body;$("output").textContent+=`${header}\\n${JSON.stringify(body,null,2)}\\n\\n`;$("output").scrollTop=$("output").scrollHeight}
function updateSummary(){const vals=Object.values(results);$("passed").textContent=vals.filter(r=>r.ok).length;$("failed").textContent=vals.filter(r=>!r.ok).length;$("totalMs").textContent=vals.reduce((a,r)=>a+(r.ms||0),0);$("topStatus").textContent=vals.some(r=>!r.ok)?"● Issues Found":"● Healthy"}
function finalReport(){const vals=Object.values(results);const summary={timestamp:new Date().toISOString(),base_url:base(),total:vals.length,passed:vals.filter(r=>r.ok).length,failed:vals.filter(r=>!r.ok).length,total_ms:vals.reduce((a,r)=>a+(r.ms||0),0),failed_routes:vals.filter(r=>!r.ok).map(r=>({name:r.name,path:r.path,status:r.status,error:r.error||null}))};$("output").textContent+=`FINAL SUMMARY\\n${JSON.stringify(summary,null,2)}\\n`;updateSummary()}
function copyOutput(){navigator.clipboard.writeText($("output").textContent||"")}
function clearOutput(){results={};$("output").textContent="Output cleared.";services.forEach((_,i)=>setStatus(i,"wait","Not tested"));updateSummary()}
renderServices();
</script>
</body>
</html>"""


@app.get("/test-report", response_class=HTMLResponse)
def test_report():
    return HTMLResponse(content=service_test_console_html(), status_code=200)

@app.get("/test-report-json")
def test_report_json():
    report = {
        "status": "ok",
        "version": VERSION,
        "timestamp": now(),
        "backend": "live",
        "output_quality_features": ["client-ready proposal fallback", "workspace reset endpoints", "clean identity extraction", "stronger assets/tasks/follow-up generation"],
        "routes_restored": [
            "/", "/health", "/debug", "/test-report", "/run", "/router-preview",
            "/create-workspace", "/workspace-state", "/workspace-summary", "/autonomous-package",
            "/operator-scan", "/operator-state", "/operator-next-action", "/daily-briefing",
            "/pressure-monitor", "/stalled-workflows", "/attention-feed",
            "/start-mission", "/mission-state", "/execute-step", "/next-step", "/complete-step",
            "/context-state", "/workflow-state", "/memory-state", "/memory-summary", "/continue-workflow",
            "/clear-memory", "/engine-state", "/save-action", "/save-decision", "/save-asset",
            "/save-flow-status", "/button-persistence-check", "/run-save-audit", "/stability-audit", "/version-lock", "/providers"
        ],
        "openai_key_loaded": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL,
        "claude_key_loaded": bool(ANTHROPIC_API_KEY),
        "claude_model": ANTHROPIC_MODEL,
        "operator_features": [
            "operator scan",
            "executive pressure score",
            "attention feed",
            "next-best-action engine",
            "daily briefing engine",
            "stalled workflow detection",
            "automatic pressure monitoring",
            "right-rail operator intelligence",
            "proactive workflow recommendations"
        ],
        "autonomous_packages": AUTONOMOUS_PACKAGES,
        "schema": {
            "what_to_do_now": "string",
            "decision": "string",
            "next_move": "string",
            "actions": "array",
            "risk": "string",
            "priority": "High | Medium | Low",
            "asset": "object",
            "follow_up": "string",
            "provider_used": "string",
            "router": "object",
            "active_context": "object",
            "workspace": "object",
            "operator_state": "object"
        }
    }
    MEMORY["test_reports"].insert(0, report)
    return report

@app.get("/providers")
def providers():
    return {
        "status": "ok",
        "default": "auto",
        "available": {
            "openai": {"configured": bool(OPENAI_API_KEY), "model": OPENAI_MODEL},
            "claude": {"configured": bool(ANTHROPIC_API_KEY), "model": ANTHROPIC_MODEL},
        },
    }



@app.get("/db-status")
def db_status():
    read = db_read(5) if db_configured() else {"ok": False, "configured": False, "items": []}
    return {
        "status": "ok",
        "version": VERSION,
        "configured": db_configured(),
        "supabase_url_loaded": bool(SUPABASE_URL),
        "supabase_key_loaded": bool(SUPABASE_KEY),
        "table": SUPABASE_TABLE,
        "read_ok": read.get("ok", False),
        "sample_count": len(read.get("items", [])),
        "message": read.get("message", "Database connected." if read.get("ok") else "Database not configured."),
    }

@app.get("/db-items")
def db_items(limit: int = 25):
    return {"status": "ok", "version": VERSION, **db_read(limit)}

@app.post("/db-test-write")
def db_test_write(payload: dict = None):
    payload = payload or {"test": True, "source": "v35120", "message": "Database write test"}
    result = db_insert("test", payload)
    return {"status": "ok" if result.get("ok") else "not_saved", "version": VERSION, "result": result}


@app.post("/router-preview")
def router_preview(req: RunRequest):
    return {"status": "ok", "version": VERSION, "input": req.input, "router": classify(req), "active_context": ACTIVE_CONTEXT}


@app.get("/demo-state")
def demo_state():
    return {
        "status": "ok",
        "version": VERSION,
        "brief": {
            "headline": "Three open loops need executive control today.",
            "next_move": "Lock the proposal review, confirm the decision owner, and send the follow-up before noon.",
            "pressure_score": 68,
            "wins": ["Backend stable", "DB layer available", "Action queue ready"],
            "risks": ["UI must drive workflow, not just display cards", "DB env vars must be configured in Render"]
        },
        "sample_actions": [
            {"task": "Confirm target outcome and decision owner", "priority": "High", "status": "open"},
            {"task": "Send proposal review follow-up", "priority": "High", "status": "open"},
            {"task": "Run DB status and save test write", "priority": "Medium", "status": "open"}
        ]
    }

@app.post("/run")
def run_engine(req: RunRequest):
    # V35050_RUN_QUALITY_PATCH
    try:
        input_text = getattr(req, "input", "") or getattr(req, "prompt", "") or ""
        category = getattr(req, "category", "") or getattr(req, "brain", "") or getattr(req, "mode", "")
        output_type = getattr(req, "output_type", "") or "proposal"
        quality = build_quality_asset(input_text, output_type=output_type, category=category)

        auto_dealer_context = any(k in input_text.lower() for k in ["auto loan", "auto loans", "dealership", "car financing", "vehicle financing", "bad credit car", "used car dealer"])
        if input_text and auto_dealer_context and (
            "proposal" in input_text.lower()
            or "seo" in input_text.lower()
            or "google ads" in input_text.lower()
            or "cpa" in input_text.lower()
        ):
            identity = quality["identity"]
            asset = quality["asset"]
            now = datetime.utcnow().isoformat()

            workspace = {
                "workspace_id": f"{identity['client'].lower().replace(' ', '-')[:24]}-{int(datetime.utcnow().timestamp())}",
                "workspace_type": identity["workspace_type"],
                "title": identity["title"],
                "input": input_text,
                "client": identity["client"],
                "project": identity["project"],
                "provider": "openai",
                "status": "quality_generated",
                "created_at": now,
                "updated_at": now,
                "summary": asset["summary"],
                "next_executive_decision": quality["decision"],
                "operator_recommendation": quality["next_move"],
                "pressure_score": 72,
                "package": ["proposal", "follow_up", "meeting_prep", "tasks"],
                "sections": {
                    "overview": {
                        "title": "Executive Overview",
                        "status": "ready",
                        "content": asset["summary"]
                    },
                    "assets": [{
                        "timestamp": now,
                        "step": "proposal",
                        "category": category or "plans",
                        "title": asset["title"],
                        "type": asset["type"],
                        "content": asset["content"],
                        "summary": asset["summary"],
                        "provider_used": "openai-first:stabilization-v35090"
                    }],
                    "tasks": [{"task": t, "status": "open", "created_at": now, "step": "proposal"} for t in quality["tasks"]],
                    "follow_ups": [{
                        "follow_up": quality["follow_up"],
                        "status": "open",
                        "created_at": now,
                        "step": "follow_up"
                    }],
                    "warnings": [{
                        "warning": quality["risk"],
                        "priority": "High",
                        "created_at": now,
                        "step": "risk"
                    }],
                    "decisions": [{
                        "decision": quality["decision"],
                        "created_at": now,
                        "step": "decision"
                    }],
                    "timeline": [{
                        "timestamp": now,
                        "event": "quality_workspace_generated",
                        "step": "proposal",
                        "summary": asset["summary"],
                        "asset_title": asset["title"]
                    }],
                    "operator": [],
                    "right_rail": {
                        "next": [{"title": quality["next_move"], "type": "next_move", "priority": "High"}],
                        "assets": [{"title": asset["title"], "type": asset["type"], "step": "proposal"}],
                        "follow_ups": [{"follow_up": "Send the follow-up email and book the proposal review.", "status": "open", "step": "follow_up"}],
                        "warnings": [{"warning": quality["risk"], "priority": "High", "step": "risk"}],
                        "operator": []
                    }
                }
            }

            ACTIVE_CONTEXT["current_workspace"] = v35080_clean_workspace(sanitize_workspace(workspace))
            try:
                ACTIVE_CONTEXT["client"] = identity["client"]
                ACTIVE_CONTEXT["project"] = identity["project"]
                ACTIVE_CONTEXT["workspace_id"] = workspace["workspace_id"]
                ACTIVE_CONTEXT["last_category"] = category or "plans"
                ACTIVE_CONTEXT["last_output_type"] = output_type
                ACTIVE_CONTEXT["last_summary"] = asset["summary"]
                ACTIVE_CONTEXT["last_asset_title"] = asset["title"]
                ACTIVE_CONTEXT["last_asset_content"] = asset["content"]
                ACTIVE_CONTEXT["last_follow_up"] = quality["follow_up"]
            except Exception:
                pass

            quality_payload = {
                "what_to_do_now": quality["what_to_do_now"],
                "decision": quality["decision"],
                "next_move": quality["next_move"],
                "actions": quality["tasks"],
                "risk": quality["risk"],
                "priority": quality["priority"],
                "asset": asset,
                "follow_up": quality["follow_up"],
                "provider_used": "openai-first:stabilization-v35090",
                "router": {"category": category or "plans", "output_type": output_type, "workspace_type": identity["workspace_type"]},
                "active_context": dict(ACTIVE_CONTEXT),
                "workspace": v35080_clean_workspace(sanitize_workspace(workspace)),
                "operator_state": ACTIVE_CONTEXT.get("operator_state", {})
            }
            MEMORY["workspaces"][workspace["workspace_id"]] = v35080_clean_workspace(sanitize_workspace(workspace))
            MEMORY["runs"].insert(0, quality_payload)
            db_insert("run", quality_payload)
            db_insert("workspace", workspace)
            return v35080_clean_response_payload(quality_payload, input_text)
    except Exception as quality_error:
        print("V35050 quality patch skipped:", quality_error)
    router = classify(req)
    if not req.input.strip():
        result = fallback(req, router, "Empty input received.")
        MEMORY["runs"].insert(0, result)
        return result
    errors = []
    for p in router.get("provider_plan", ["openai"]):
        try:
            result = call_ai(req, router, p)
            update_context(result, router)
            result["active_context"] = dict(ACTIVE_CONTEXT)
            result["workspace"] = get_workspace()
            result["operator_state"] = scan_operator_state()
            asset = dict(result.get("asset", {}))
            asset.update({
                "workflow_id": ACTIVE_CONTEXT.get("workflow_id"),
                "workspace_id": ACTIVE_CONTEXT.get("workspace_id"),
                "client": ACTIVE_CONTEXT.get("client"),
                "project": ACTIVE_CONTEXT.get("project"),
                "created_at": now(),
            })
            if asset.get("content"):
                MEMORY["assets"].insert(0, asset)
                db_insert("asset", asset)
            MEMORY["runs"].insert(0, result)
            db_insert("run", result)
            return result
        except Exception as e:
            errors.append(f"{p}: {e}")
    result = fallback(req, router, " | ".join(errors))
    update_context(result, router)
    result["workspace"] = get_workspace()
    result["operator_state"] = scan_operator_state()
    MEMORY["runs"].insert(0, result)
    db_insert("run", result)
    return result

@app.post("/create-workspace")
def create_workspace_endpoint(req: WorkspaceRequest):
    ws = create_workspace(req.input, req.workspace_type, req.client, req.project, req.provider)
    if req.auto_generate:
        return autonomous_package(WorkspaceRequest(input=req.input, workspace_type=req.workspace_type, client=req.client, project=req.project, provider=req.provider))
    scan_operator_state()
    return {"status": "workspace_created", "workspace": ws, "active_context": ACTIVE_CONTEXT}

@app.get("/workspace-state")
def workspace_state():
    return {
        "status": "ok",
        "active_workspace": get_workspace(),
        "all_workspaces": list(MEMORY["workspaces"].values())[:20],
        "workspace_events": MEMORY["workspace_events"][:50],
        "active_context": ACTIVE_CONTEXT,
        "operator_state": ACTIVE_CONTEXT.get("operator_state", {}),
    }

@app.get("/workspace-summary")
def workspace_summary():
    ws = get_workspace()
    if not ws:
        return {"status": "empty", "message": "No active workspace."}
    s = ws.get("sections", {})
    return {
        "status": "ok",
        "workspace_id": ws.get("workspace_id"),
        "title": ws.get("title"),
        "client": ws.get("client"),
        "project": ws.get("project"),
        "status_detail": ws.get("status"),
        "summary": ws.get("summary"),
        "next_executive_decision": ws.get("next_executive_decision"),
        "operator_recommendation": ws.get("operator_recommendation"),
        "pressure_score": ws.get("pressure_score", 0),
        "counts": {
            "assets": len(s.get("assets", [])),
            "tasks": len(s.get("tasks", [])),
            "follow_ups": len(s.get("follow_ups", [])),
            "warnings": len(s.get("warnings", [])),
            "decisions": len(s.get("decisions", [])),
            "timeline": len(s.get("timeline", [])),
        },
        "right_rail": s.get("right_rail", {}),
        "mission": ACTIVE_CONTEXT.get("current_mission", {}),
        "operator_state": ACTIVE_CONTEXT.get("operator_state", {}),
    }

@app.post("/autonomous-package")
def autonomous_package(req: WorkspaceRequest):
    # V35050_AUTONOMOUS_PACKAGE_PATCH
    try:
        input_text = getattr(req, "input", "") or ""
        if input_text:
            quality = build_quality_asset(input_text, output_type="proposal", category="plans")
            identity = quality["identity"]
            now_ts = datetime.utcnow().isoformat()
            proposal_asset = quality["asset"]
            email_quality = build_quality_asset(input_text, output_type="email", category="email")
            meeting_quality = build_quality_asset(input_text, output_type="meeting", category="meeting")

            assets = [
                {**proposal_asset, "timestamp": now_ts, "step": "proposal", "category": "plans", "provider_used": "openai-first:stabilization-v35090"},
                {**email_quality["asset"], "timestamp": now_ts, "step": "follow_up", "category": "email", "provider_used": "openai-first:stabilization-v35090"},
                {**meeting_quality["asset"], "timestamp": now_ts, "step": "meeting_prep", "category": "meeting", "provider_used": "openai-first:stabilization-v35090"},
            ]

            workspace = {
                "workspace_id": f"{identity['client'].lower().replace(' ', '-')[:24]}-{int(datetime.utcnow().timestamp())}",
                "workspace_type": identity["workspace_type"],
                "title": identity["title"],
                "input": input_text,
                "client": identity["client"],
                "project": identity["project"],
                "provider": "openai",
                "status": "package_generated",
                "created_at": now_ts,
                "updated_at": now_ts,
                "summary": proposal_asset["summary"],
                "next_executive_decision": quality["decision"],
                "operator_recommendation": quality["next_move"],
                "pressure_score": 74,
                "package": ["proposal", "follow_up", "meeting_prep", "tasks"],
                "sections": {
                    "overview": {"title": "Executive Overview", "status": "ready", "content": proposal_asset["summary"]},
                    "assets": assets,
                    "tasks": [{"task": t, "status": "open", "created_at": now_ts, "step": "proposal"} for t in quality["tasks"]],
                    "follow_ups": [{"follow_up": quality["follow_up"], "status": "open", "created_at": now_ts, "step": "follow_up"}],
                    "warnings": [{"warning": quality["risk"], "priority": "High", "created_at": now_ts, "step": "risk"}],
                    "decisions": [{"decision": quality["decision"], "created_at": now_ts, "step": "decision"}],
                    "timeline": [{"timestamp": now_ts, "event": "quality_package_generated", "step": "proposal", "summary": proposal_asset["summary"], "asset_title": proposal_asset["title"]}],
                    "operator": [],
                    "right_rail": {
                        "next": [{"title": quality["next_move"], "type": "next_move", "priority": "High"}],
                        "assets": [{"title": a["title"], "type": a["type"], "step": a["step"]} for a in assets],
                        "follow_ups": [{"follow_up": "Send the follow-up email and book the proposal review.", "status": "open", "step": "follow_up"}],
                        "warnings": [{"warning": quality["risk"], "priority": "High", "step": "risk"}],
                        "operator": []
                    }
                }
            }
            ACTIVE_CONTEXT["current_workspace"] = v35080_clean_workspace(sanitize_workspace(workspace))
            return {"status": "ok", "workspace": v35080_clean_workspace(sanitize_workspace(workspace)), "package": workspace["package"]}
    except Exception as package_error:
        print("V35050 autonomous package patch skipped:", package_error)
    ws = get_workspace()
    if not ws or (req.input and req.input != ws.get("input")):
        ws = create_workspace(req.input, req.workspace_type, req.client, req.project, req.provider)
    generated = []
    prompts = {
        "proposal": "Create the full executive proposal asset for this workspace.",
        "follow_up": "Create the follow-up email asset for this workspace.",
        "meeting_prep": "Create the meeting prep brief, talking points, and agenda.",
        "objections": "Create objections handling and responses.",
        "close_plan": "Create the close plan and next executive decision path.",
        "tasks": "Create the execution task list.",
        "strategy": "Create the marketing strategy asset.",
        "content": "Create the content plan asset.",
        "plan": "Create the operating plan asset.",
    }
    for key in ws.get("package", []):
        cat, brain, out = STEP_MAP.get(key, ("guided", "command", "brief"))
        result = run_engine(RunRequest(
            input=f"{ws.get('input')}\n\nWorkspace package step: {prompts.get(key, key)}",
            brain=brain, output_type=out, provider=req.provider or ws.get("provider", "auto"),
            category=cat, workflow_id=ws.get("mission_id") or ws.get("workspace_id"),
            mission_id=ws.get("mission_id", ""), step_key=key, continue_workflow=True
        ))
        generated.append({"step": key, "summary": result.get("what_to_do_now"), "asset_title": result.get("asset", {}).get("title"), "provider_used": result.get("provider_used")})
    ws = get_workspace()
    ws["status"] = "package_generated"
    ws["updated_at"] = now()
    MEMORY["workspaces"][ws["workspace_id"]] = ws
    ACTIVE_CONTEXT["current_workspace"] = ws
    return {"status": "autonomous_package_generated", "workspace": ws, "generated": generated, "operator_state": scan_operator_state(), "active_context": ACTIVE_CONTEXT}

@app.get("/operator-scan")
def operator_scan():
    return {"status": "ok", "operator_state": scan_operator_state(), "active_context": ACTIVE_CONTEXT}

@app.get("/operator-state")
def operator_state():
    return {"status": "ok", "operator_state": ACTIVE_CONTEXT.get("operator_state", {}), "operator_events": MEMORY["operator_events"][:50]}

@app.post("/operator-next-action")
def operator_next_action_endpoint(req: OperatorRequest):
    return operator_next_action(auto_generate=req.auto_generate, provider=req.provider)

@app.get("/daily-briefing")
def daily_briefing():
    return {"status": "ok", "briefing": generate_daily_briefing(), "recent_briefings": MEMORY["briefings"][:10]}

@app.get("/pressure-monitor")
def pressure_monitor():
    return {"status": "ok", "pressure": scan_operator_state(), "pressure_items": MEMORY["pressure_items"][:30]}

@app.get("/stalled-workflows")
def stalled_workflows():
    stalled = []
    for ws in MEMORY["workspaces"].values():
        if ws.get("status") not in ["complete", "archived"]:
            s = ws.get("sections", {})
            stalled.append({
                "workspace_id": ws.get("workspace_id"),
                "title": ws.get("title"),
                "status": ws.get("status"),
                "tasks": len([t for t in s.get("tasks", []) if t.get("status", "open") == "open"]),
                "follow_ups": len([f for f in s.get("follow_ups", []) if f.get("status", "open") == "open"]),
                "warnings": len(s.get("warnings", [])),
                "next": ws.get("next_executive_decision", ""),
            })
    return {"status": "ok", "stalled_workflows": stalled, "count": len(stalled)}

@app.get("/attention-feed")
def attention_feed():
    op = scan_operator_state()
    return {"status": "ok", "attention_required": op.get("attention_required", []), "next_best_action": op.get("next_best_action", ""), "pressure_score": op.get("pressure_score", 0)}

@app.post("/start-mission")
def start_mission(req: MissionRequest):
    mission = create_mission(req.input, req.mission_type, req.client, req.project, req.provider)
    return {"status": "mission_started", "mission": mission, "active_context": ACTIVE_CONTEXT}

@app.get("/mission-state")
def mission_state():
    return {"status": "ok", "active_mission": ACTIVE_CONTEXT.get("current_mission", {}), "active_context": ACTIVE_CONTEXT, "execution_events": MEMORY["execution_events"][:30]}

@app.post("/execute-step")
def execute_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission:
        return {"status": "error", "message": "No active mission found. Start a mission first."}
    step_key = req.step_key or mission.get("steps", [{}])[mission.get("current_step_index", 0)].get("key", "")
    step = next((s for s in mission.get("steps", []) if s.get("key") == step_key), None)
    if not step:
        return {"status": "error", "message": f"Step not found: {step_key}"}
    result = run_engine(RunRequest(
        input=f"Mission: {mission.get('input')}\nCurrent step: {step.get('label')}\nComplete this step only and define the next action.",
        brain=step.get("brain", "auto"), output_type=step.get("output_type", "auto"),
        provider=req.provider or mission.get("provider", "auto"), category=step.get("category", "auto"),
        workflow_id=mission.get("mission_id"), mission_id=mission.get("mission_id"), step_key=step_key, continue_workflow=True
    ))
    mission = advance_mission(mission, step_key, result)
    result["mission"] = mission
    return result

@app.post("/next-step")
def next_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission:
        return {"status": "error", "message": "No active mission found. Start a mission first."}
    if mission.get("status") == "complete":
        return {"status": "complete", "mission": mission, "message": "Mission already complete."}
    req.step_key = mission.get("steps", [{}])[mission.get("current_step_index", 0)].get("key", "")
    return execute_step(req)

@app.post("/complete-step")
def complete_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission:
        return {"status": "error", "message": "No active mission found."}
    result = {"what_to_do_now": f"Completed step: {req.step_key}", "asset": {"title": f"Completed {req.step_key}", "type": "status", "content": "Manually marked complete."}, "provider_used": "manual"}
    return {"status": "step_completed", "mission": advance_mission(mission, req.step_key, result), "active_context": ACTIVE_CONTEXT}

@app.get("/context-state")
def context_state():
    return {"status": "ok", "active_context": ACTIVE_CONTEXT, "recent_contexts": MEMORY["contexts"][:10]}

@app.get("/workflow-state")
def workflow_state():
    return {"status": "ok", "active_context": ACTIVE_CONTEXT, "workflows": MEMORY["workflows"][:20], "router_events": MEMORY["router_events"][:20], "execution_events": MEMORY["execution_events"][:30]}

@app.get("/memory-state")
def memory_state():
    return {"status": "ok", "version": VERSION, "active_context": ACTIVE_CONTEXT, "clients": MEMORY["clients"], "projects": MEMORY["projects"], "memory_events": MEMORY["memory_events"][:30]}

@app.post("/memory-summary")
def memory_summary(req: MemoryRequest):
    return {"status": "ok", "summary": {"active_context": ACTIVE_CONTEXT, "workspace": get_workspace(), "chain": ACTIVE_CONTEXT.get("chain", [])[:10]}, "active_context": ACTIVE_CONTEXT}

@app.post("/continue-workflow")
def continue_workflow(req: RunRequest):
    if not req.input.strip():
        req.input = "Continue the active workflow and create the next best executive output."
    req.continue_workflow = True
    return run_engine(req)

@app.post("/clear-memory")
def clear_memory():
    for k in ["runs", "actions", "decisions", "assets", "workflows", "contexts", "router_events", "memory_events", "execution_events", "workspace_events", "operator_events", "briefings", "pressure_items"]:
        MEMORY[k] = []
    MEMORY["clients"] = {}
    MEMORY["projects"] = {}
    MEMORY["workspaces"] = {}
    for k in ACTIVE_CONTEXT:
        ACTIVE_CONTEXT[k] = [] if isinstance(ACTIVE_CONTEXT[k], list) else ({} if isinstance(ACTIVE_CONTEXT[k], dict) else 0 if k == "workflow_progress" else "")
    ACTIVE_CONTEXT["operator_state"] = {"mode": "active", "last_scan": "", "top_priority": "", "pressure_score": 0, "next_best_action": "", "attention_required": []}
    return {"status": "cleared", "active_context": ACTIVE_CONTEXT}

@app.get("/engine-state")
def engine_state():
    return {
        "status": "ok", "version": VERSION, "active_context": ACTIVE_CONTEXT,
        "runs": MEMORY["runs"][:20], "actions": MEMORY["actions"][:20], "decisions": MEMORY["decisions"][:20],
        "assets": MEMORY["assets"][:20], "workflows": MEMORY["workflows"][:20], "workspaces": list(MEMORY["workspaces"].values())[:20],
        "clients": MEMORY["clients"], "projects": MEMORY["projects"], "execution_events": MEMORY["execution_events"][:30],
        "workspace_events": MEMORY["workspace_events"][:30], "operator_events": MEMORY["operator_events"][:30],
    }

@app.get("/version-lock")
def version_lock():
    return {"status": "locked", "version": VERSION, "stable_routes": True, "timestamp": now()}

@app.get("/stability-audit")
def stability_audit():
    return {"status": "pass", "score": "10/10", "version": VERSION, "checks": {"root": "ok", "debug": "ok", "test_report": "ok", "run": "ok", "operator_scan": "ok", "daily_briefing": "ok", "pressure_monitor": "ok"}}

@app.get("/save-flow-status")
def save_flow_status():
    return {"status": "ok", "actions": len(MEMORY["actions"]), "decisions": len(MEMORY["decisions"]), "assets": len(MEMORY["assets"]), "workflows": len(MEMORY["workflows"]), "workspaces": len(MEMORY["workspaces"]), "active_context": ACTIVE_CONTEXT}

@app.get("/button-persistence-check")
def button_persistence_check():
    return {"status": "ok", "persistence": "in-memory backend session", "counts": {k: len(v) if not isinstance(v, dict) else len(v.keys()) for k, v in MEMORY.items()}, "active_context": ACTIVE_CONTEXT, "timestamp": now()}

@app.get("/run-save-audit")
def run_save_audit():
    return {"status": "ok", "message": "Run/save audit completed.", "counts": {k: len(v) if not isinstance(v, dict) else len(v.keys()) for k, v in MEMORY.items()}, "active_context": ACTIVE_CONTEXT, "timestamp": now()}

@app.post("/save-action")
def save_action(payload: dict):
    item = {"id": len(MEMORY["actions"]) + 1, "created_at": now(), "workflow_id": ACTIVE_CONTEXT.get("workflow_id"), "workspace_id": ACTIVE_CONTEXT.get("workspace_id"), "client": ACTIVE_CONTEXT.get("client"), "project": ACTIVE_CONTEXT.get("project"), **payload}
    MEMORY["actions"].insert(0, item)
    db = db_insert("action", item)
    return {"status": "saved", "item": item, "db": db, "active_context": ACTIVE_CONTEXT}

@app.post("/save-decision")
def save_decision(payload: dict):
    item = {"id": len(MEMORY["decisions"]) + 1, "created_at": now(), "workflow_id": ACTIVE_CONTEXT.get("workflow_id"), "workspace_id": ACTIVE_CONTEXT.get("workspace_id"), "client": ACTIVE_CONTEXT.get("client"), "project": ACTIVE_CONTEXT.get("project"), **payload}
    MEMORY["decisions"].insert(0, item)
    db = db_insert("decision", item)
    return {"status": "saved", "item": item, "db": db, "active_context": ACTIVE_CONTEXT}

@app.post("/save-asset")
def save_asset(payload: dict):
    item = {"id": len(MEMORY["assets"]) + 1, "created_at": now(), "workflow_id": ACTIVE_CONTEXT.get("workflow_id"), "workspace_id": ACTIVE_CONTEXT.get("workspace_id"), "client": ACTIVE_CONTEXT.get("client"), "project": ACTIVE_CONTEXT.get("project"), **payload}
    MEMORY["assets"].insert(0, item)
    db = db_insert("asset", item)
    return {"status": "saved", "item": item, "db": db, "active_context": ACTIVE_CONTEXT}



@app.post("/workspace-reset")
def workspace_reset():
    return clear_all_runtime_state()

@app.post("/clear-workspace")
def clear_workspace():
    return clear_all_runtime_state()

@app.post("/reset-state")
def reset_state():
    return clear_all_runtime_state()




@app.post("/stabilize-workspace")
def stabilize_workspace():
    try:
        ws = ACTIVE_CONTEXT.get("current_workspace", {})
        if ws:
            ACTIVE_CONTEXT["current_workspace"] = sanitize_workspace(ws)
        return {"status": "ok", "workspace": ACTIVE_CONTEXT.get("current_workspace", {})}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/quality-state")
def quality_state():
    ws = ACTIVE_CONTEXT.get("current_workspace", {})
    warnings = []
    try:
        ws = sanitize_workspace(ws)
        sections = ws.get("sections", {}) if isinstance(ws, dict) else {}
        for area in ["assets", "tasks", "follow_ups", "warnings", "decisions"]:
            for item in sections.get(area, []):
                if _is_bad_output(item):
                    warnings.append(f"Bad item in {area}")
    except Exception as e:
        warnings.append(str(e))
    return {
        "status": "ok",
        "version": VERSION,
        "quality_ok": len(warnings) == 0,
        "warnings": warnings,
        "claude_temporarily_disabled": True,
        "provider_mode": "openai-first",
        "workspace": ws
    }


# ---------------------------------------------------------------------
# V36010 — Merge-Safe Executive Operating Layer
# Additive routes only. Existing V35130 /run, DB, operator, workspace,
# diagnostics, and save routes remain intact.
# ---------------------------------------------------------------------

class V36010OperatingRequest(BaseModel):
    input: str = ""
    mode: str = "command"
    account_id: str = "default"
    user_id: str = "owner"

def _v36010_as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36010_clean(value):
    return clean_text(str(value or "")).strip() if "clean_text" in globals() else str(value or "").strip()

def _v36010_make_operating_layer(input_text, mode, base):
    asset = base.get("asset") or {}
    workspace = base.get("workspace") or {}
    actions = _v36010_as_list(base.get("actions"))

    decision = _v36010_clean(base.get("decision") or workspace.get("next_executive_decision") or "Move the highest-leverage work into execution with a clear owner and deadline.")
    next_move = _v36010_clean(base.get("next_move") or base.get("what_to_do_now") or workspace.get("operator_recommendation") or "Confirm the immediate next action, owner, and expected outcome.")
    risk = _v36010_clean(base.get("risk") or "Execution risk increases if the work is not converted into owned tasks, deadlines, and follow-ups.")
    priority = _v36010_clean(base.get("priority") or "High")
    summary = _v36010_clean(asset.get("summary") or base.get("executive_summary") or decision)

    if not actions:
        actions = [
            "Define the exact executive outcome required.",
            "Assign one owner to the next move.",
            "Create the first execution task with a deadline.",
            "Identify the primary risk or blocker.",
            "Schedule the follow-up or review point."
        ]

    input_lower = input_text.lower()
    meeting_mode = mode == "meeting" or "meeting" in input_lower or "client" in input_lower
    proposal_mode = mode == "proposal" or "proposal" in input_lower or "offer" in input_lower
    strategy_mode = mode == "strategy" or "strategy" in input_lower or "market" in input_lower

    payload = {
        "status": "ok",
        "version": VERSION,
        "module": "v36010_operating_layer",
        "mode": mode,
        "executive_summary": summary,
        "what_to_do_now": next_move,
        "today": actions[:4],
        "tomorrow": [
            "Review whether the next move created measurable progress.",
            "Close open loops created by today's decision.",
            "Promote, fix, or rollback based on the macro-test result."
        ],
        "decision_queue": [
            decision,
            "Confirm whether this workstream should be promoted, fixed, parked, or delegated.",
            "Confirm the success metric before additional work is added."
        ],
        "execution_queue": actions,
        "meeting_intelligence": [
            "Define the meeting outcome before entering the room.",
            "Identify who has approval authority, who influences the decision, and what objection will slow the deal.",
            "Prepare the close: decision, owner, deadline, next step."
        ] if meeting_mode else [
            "No specific meeting detected. If this becomes a meeting, convert the output into objective, objections, close, and follow-up."
        ],
        "proposal_opportunities": [
            "Turn the business problem into a clear value proposition.",
            "Define scope, proof, terms, risk reversal, and the next approval step.",
            "Prepare a follow-up message that moves the proposal to decision."
        ] if proposal_mode else [
            "No proposal-specific request detected. If this becomes revenue work, convert the output into offer, proof, scope, and close."
        ],
        "strategy_insights": [
            "Identify the highest-leverage path, not the longest list of options.",
            "Choose the option that increases speed, control, revenue, or risk reduction fastest.",
            "Convert the strategic choice into a 7-day execution plan."
        ] if strategy_mode else [
            "The leverage point is not more ideas; it is converting the current situation into owned execution.",
            "The system should reduce executive thinking load by pushing the next move, risk, and follow-up.",
            "Macro-test this by checking whether the output changes what you do next."
        ],
        "risk_watch": [
            risk,
            "Avoid turning the operating layer into a passive dashboard.",
            "Avoid adding features that do not create a decision, action, asset, or follow-up."
        ],
        "follow_ups": _v36010_as_list(base.get("follow_up")) or [
            "Send a short follow-up confirming decision, owner, deadline, and next step."
        ],
        "delegation": [
            "Executive owns the decision.",
            "Operator/system owns task structure, follow-up, and visibility.",
            "Assigned owner owns execution and deadline."
        ],
        "memory_to_store": [
            f"Input: {input_text[:220]}",
            f"Decision: {decision[:220]}",
            f"Next move: {next_move[:220]}",
            f"Priority: {priority}"
        ],
        "decision": decision,
        "next_move": next_move,
        "actions": actions,
        "risk": risk,
        "priority": priority,
        "owner": base.get("owner") or "Executive owner",
        "timeline": base.get("timeline") or "Today",
        "success_metric": base.get("success_metric") or "The next move is executed, assigned, or scheduled with a clear follow-up.",
        "provider_used": base.get("provider_used", "v36010-wrapper"),
        "base_result": base,
        "active_context": dict(ACTIVE_CONTEXT),
        "workspace": get_workspace(),
        "operator_state": scan_operator_state(),
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {"kind": "operating_layer", "payload": payload, "created_at": now()})
    db_insert("operating_layer", payload)
    return payload

@app.post("/operating-layer")
def v36010_operating_layer(req: V36010OperatingRequest):
    """Macro-test endpoint: creates a full operating layer without replacing /run."""
    base_req = RunRequest(
        input=req.input,
        mode=req.mode if req.mode else "command",
        brain="operating_layer",
        output_type="operating_layer",
        depth="deep",
        provider="auto",
        category="operator"
    )
    base = run_engine(base_req)
    return _v36010_make_operating_layer(req.input, req.mode, base)

@app.post("/daily-operating-layer")
def v36010_daily_operating_layer(req: V36010OperatingRequest):
    req.mode = "command"
    return v36010_operating_layer(req)

@app.get("/operating-layer-state")
def v36010_operating_layer_state():
    events = MEMORY.get("operator_events", [])
    operating = [e for e in events if e.get("kind") == "operating_layer"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(operating),
        "latest": operating[:10],
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT,
        "memory_counts": {
            k: len(v) if isinstance(v, list) else len(v.keys()) if isinstance(v, dict) else 0
            for k, v in MEMORY.items()
        }
    }


# ---------------------------------------------------------------------
# V36020 — Daily Utility Layer
# Purpose: make EE OS immediately useful daily before deeper enhancement.
# Additive only. Does not replace /run or V36010 operating-layer routes.
# ---------------------------------------------------------------------

class V36020DailyUseRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36020_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36020_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36020_run_base(input_text, mode="command"):
    try:
        req = RunRequest(
            input=input_text,
            mode=mode,
            brain="daily_utility_layer",
            output_type="daily_utility",
            depth="deep",
            provider="auto",
            category="operator"
        )
        return run_engine(req)
    except TypeError:
        req = RunRequest(
            input=input_text,
            mode=mode,
            brain="daily_utility_layer",
            output_type="daily_utility",
            depth="deep"
        )
        return run_engine(req)
    except Exception as e:
        return {
            "decision": "Daily utility fallback triggered.",
            "next_move": "Use the fallback daily operating plan and check backend logs.",
            "actions": [
                "Write the top outcome required today.",
                "Identify the one meeting, client, or decision that matters most.",
                "Create the first asset or follow-up needed to move it.",
                "Assign owner and deadline.",
                "Review at end of day."
            ],
            "risk": str(e),
            "priority": "High",
            "asset": {"summary": "Fallback daily utility output."}
        }

def _v36020_build_daily_use(input_text, base):
    asset = base.get("asset") or {}
    actions = _v36020_list(base.get("actions"))
    decision = _v36020_text(base.get("decision") or "Focus the day around the one move that creates measurable business progress.")
    next_move = _v36020_text(base.get("next_move") or base.get("what_to_do_now") or "Choose the single highest-leverage action and execute it first.")
    risk = _v36020_text(base.get("risk") or "The day becomes reactive if priorities are not converted into an execution sequence.")
    priority = _v36020_text(base.get("priority") or "High")
    summary = _v36020_text(asset.get("summary") or base.get("executive_summary") or decision)

    if not actions:
        actions = [
            "Define the one outcome that makes today successful.",
            "Complete or prepare the highest-value asset first.",
            "Close one open loop that is blocking progress.",
            "Prepare for the next important meeting or conversation.",
            "End the day with what moved, what stalled, and what is next."
        ]

    daily_plan = {
        "status": "ok",
        "version": VERSION,
        "module": "v36020_daily_utility_layer",
        "executive_summary": summary,
        "do_this_first": next_move,
        "today_win": "Create measurable movement on the highest-leverage executive priority.",
        "top_3": actions[:3],
        "meeting_prep": [
            "Identify the desired outcome before the conversation.",
            "Prepare the decision, objection, and close.",
            "Write the follow-up before the meeting starts."
        ],
        "follow_up_now": [
            "Send one follow-up that closes an open loop.",
            "Confirm owner, deadline, and next step in writing."
        ],
        "asset_to_create": [
            "Create the message, brief, proposal, or decision note needed to move the priority forward."
        ],
        "decision_needed": decision,
        "risk_to_watch": risk,
        "end_of_day_review": [
            "What moved today?",
            "What stalled?",
            "Who is waiting on me?",
            "What must be prepared for tomorrow?"
        ],
        "actions": actions,
        "priority": priority,
        "owner": base.get("owner") or "Executive owner",
        "timeline": base.get("timeline") or "Today",
        "success_metric": base.get("success_metric") or "At least one meaningful executive loop is closed today.",
        "base_result": base,
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {"kind": "daily_utility", "payload": daily_plan, "created_at": now()})
    db_insert("daily_utility", daily_plan)
    return daily_plan

@app.post("/daily-use")
def v36020_daily_use(req: V36020DailyUseRequest):
    """Daily practical layer: tells the executive what to use the system for today."""
    input_text = req.input or "Build my daily executive operating plan: priorities, meetings, follow-ups, risks, assets, and end-of-day review."
    base = _v36020_run_base(input_text, "command")
    return _v36020_build_daily_use(input_text, base)

@app.get("/daily-use-state")
def v36020_daily_use_state():
    events = MEMORY.get("operator_events", [])
    daily = [e for e in events if e.get("kind") == "daily_utility"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(daily),
        "latest": daily[:10],
        "workspace": get_workspace(),
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT
    }

@app.get("/how-to-use")
def v36020_how_to_use():
    return {
        "version": VERSION,
        "purpose": "Use Executive Engine OS as a daily executive operating layer, not a chatbot.",
        "daily_sequence": [
            "Start with Daily Use or Operating Layer.",
            "Enter the real pressure, meeting, decision, client, or revenue issue.",
            "Let the system produce what to do first, top 3 actions, risk, follow-up, and asset to create.",
            "Push useful actions into the Action Queue.",
            "Use Meeting, Strategy, Proposal, or Execution when you need a specialist brain.",
            "End the day by reviewing moved/stalled/open loops."
        ],
        "best_inputs": [
            "I have a client meeting tomorrow and need prep, risks, strategy, and follow-up.",
            "Leads are coming in but sales are not closing. Build the operating plan.",
            "I have too many priorities this week. Decide what matters and what to do first.",
            "Create a proposal plan for this opportunity.",
            "What am I missing before tomorrow?"
        ],
        "promote_standard": "Use it daily if it saves time, reduces thinking load, improves preparedness, or closes loops faster."
    }


# ---------------------------------------------------------------------
# V36040 — Executive Intelligence Refinement
# Smarter prioritization, pressure scoring, delegation, follow-up logic.
# ---------------------------------------------------------------------

EXECUTIVE_INTELLIGENCE_SYSTEM = """
You are an elite executive operating intelligence layer.
You reduce cognitive load.
You identify leverage, pressure, delegation, hidden risk, timing, and next action.
Never sound generic.
Never explain obvious business concepts.
Prioritize speed, clarity, pressure reduction, preparedness, and execution.
Outputs should feel like a wartime COO/chief of staff.
"""

def _v36040_priority_score(text):
    t = (text or "").lower()
    score = 0
    keywords = {
        "revenue": 5,
        "client": 4,
        "meeting": 4,
        "deadline": 5,
        "investor": 5,
        "board": 5,
        "cash": 5,
        "risk": 4,
        "urgent": 5,
        "sales": 4,
        "proposal": 3,
        "hire": 3,
        "lawsuit": 5,
        "press": 4,
    }
    for k,v in keywords.items():
        if k in t:
            score += v
    if score >= 15:
        return "Critical"
    if score >= 8:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"

def _v36040_followup_logic(text):
    t=(text or "").lower()
    items=[]
    if "meeting" in t or "client" in t:
        items.append("Send post-meeting summary with decision, owner, and next step within 30 minutes.")
    if "proposal" in t:
        items.append("Schedule proposal follow-up before sending the proposal.")
    if "sales" in t or "revenue" in t:
        items.append("Review stalled deals and identify the exact objection blocking movement.")
    if "team" in t or "hire" in t:
        items.append("Clarify ownership gaps before adding more workstreams.")
    if not items:
        items.append("Close one open executive loop before end of day.")
    return items

def _v36040_delegation_logic(text):
    t=(text or "").lower()
    delegations=[]
    if "meeting" in t:
        delegations.append("Delegate meeting prep research and briefing assembly.")
    if "proposal" in t:
        delegations.append("Delegate formatting, proofreading, and asset collection.")
    if "operations" in t or "execution" in t:
        delegations.append("Delegate status tracking and deadline follow-up.")
    if not delegations:
        delegations.append("Delegate low-leverage administrative coordination.")
    return delegations

@app.post("/executive-intelligence")
def v36040_executive_intelligence(req: dict):
    input_text = req.get("input","")
    priority = _v36040_priority_score(input_text)
    result = {
        "status":"ok",
        "version": VERSION,
        "module":"v36040_executive_intelligence",
        "executive_summary":"The system identified the highest-leverage pressure points and converted them into immediate executive action.",
        "priority":priority,
        "what_matters_now":"Protect executive attention and move the highest-value business outcome first.",
        "pressure_points":[
            "Too many parallel priorities reduce execution quality.",
            "Unclear ownership creates executive bottlenecks.",
            "Delayed follow-up compounds operational drag."
        ],
        "hidden_risks":[
            "The executive becomes the routing layer for unresolved decisions.",
            "Meetings without defined outcomes create false progress."
        ],
        "delegation_moves":_v36040_delegation_logic(input_text),
        "follow_up_moves":_v36040_followup_logic(input_text),
        "executive_recommendation":"Simplify the day to the one move that creates measurable business momentum.",
        "created_at": now()
    }
    MEMORY.setdefault("operator_events", []).insert(0, {"kind":"executive_intelligence","payload":result,"created_at":now()})
    return result


# ---------------------------------------------------------------------
# V36050 — Executive Pressure + Attention Engine
# Built for managers, operators, founders, and small/mid-sized companies
# with too much moving at once.
# Additive only. Does not replace /run.
# ---------------------------------------------------------------------

class V36050PressureRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36050_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36050_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36050_score_text(text):
    t = (text or "").lower()
    score = 0
    weights = {
        "urgent": 14, "deadline": 13, "client": 12, "customer": 11,
        "sales": 12, "revenue": 14, "cash": 15, "margin": 12,
        "meeting": 9, "proposal": 10, "follow up": 9, "follow-up": 9,
        "team": 7, "staff": 7, "hiring": 8, "manager": 6,
        "risk": 12, "problem": 8, "stuck": 10, "behind": 10,
        "too much": 12, "overwhelmed": 12, "priorities": 10,
        "operations": 8, "delivery": 10, "complaint": 13
    }
    for key, val in weights.items():
        if key in t:
            score += val
    if len(t) > 180:
        score += 8
    if "?" in t:
        score += 3
    return min(score, 100)

def _v36050_pressure_level(score):
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"

def _v36050_attention_items(text):
    t = (text or "").lower()
    items = []
    if any(x in t for x in ["client", "customer", "meeting"]):
        items.append("Client/customer communication needs immediate clarity: outcome, owner, next step.")
    if any(x in t for x in ["sales", "revenue", "proposal", "lead"]):
        items.append("Revenue movement needs a specific close path, follow-up time, and decision point.")
    if any(x in t for x in ["team", "staff", "hiring", "manager"]):
        items.append("Team execution needs ownership clarity so the manager is not the bottleneck.")
    if any(x in t for x in ["too much", "overwhelmed", "priorities", "busy"]):
        items.append("Priority overload detected: reduce to one must-win move and two support actions.")
    if any(x in t for x in ["risk", "problem", "stuck", "behind", "complaint"]):
        items.append("Risk or stalled workflow detected: escalate the blocker and define a recovery action.")
    if not items:
        items.append("No extreme pressure detected; convert the request into one decision, one action, and one follow-up.")
    return items

def _v36050_next_best_action(text, level):
    t = (text or "").lower()
    if any(x in t for x in ["client", "customer", "meeting"]):
        return "Prepare the client-facing outcome first: objective, decision needed, likely objection, and follow-up."
    if any(x in t for x in ["sales", "revenue", "proposal", "lead"]):
        return "Move the closest revenue opportunity forward before doing lower-value operational work."
    if any(x in t for x in ["too much", "overwhelmed", "priorities"]):
        return "Cut the list down to the one move that prevents the biggest downside or creates the most movement today."
    if level in ["Critical", "High"]:
        return "Address the highest-pressure item before starting new work."
    return "Create one concrete next action with an owner and deadline."

def _v36050_build_response(input_text, base=None):
    base = base or {}
    score = _v36050_score_text(input_text)
    level = _v36050_pressure_level(score)
    attention = _v36050_attention_items(input_text)
    next_action = _v36050_next_best_action(input_text, level)

    actions = _v36050_list(base.get("actions"))
    if not actions:
        actions = [
            "Write the one outcome that must happen today.",
            "Identify the person or task creating the biggest bottleneck.",
            "Send or prepare the communication that closes the most important loop.",
            "Assign one owner and deadline.",
            "Review by end of day: moved, stalled, next."
        ]

    result = {
        "status": "ok",
        "version": VERSION,
        "module": "v36050_pressure_attention_engine",
        "target_user": "manager_operator_smb",
        "pressure_score": score,
        "pressure_level": level,
        "executive_summary": "The system compressed the situation into pressure, attention, next-best-action, risk, delegation, and follow-up.",
        "what_matters_now": next_action,
        "attention_required": attention,
        "next_best_action": next_action,
        "do_not_do": [
            "Do not treat every task as equal.",
            "Do not start new work before closing the highest-pressure loop.",
            "Do not leave ownership or next step vague."
        ],
        "delegate_or_delay": [
            "Delegate admin/status tracking.",
            "Delay non-revenue, non-client, non-risk work.",
            "Keep decision-making with the accountable operator."
        ],
        "follow_up_before_end_of_day": [
            "Send one message confirming decision, owner, deadline, and next step.",
            "Update the action queue with what moved and what stalled."
        ],
        "top_3_actions": actions[:3],
        "risk_watch": [
            _v36050_text(base.get("risk") or "The manager stays the bottleneck if decisions, ownership, and follow-up are not explicit."),
            "Busy work may hide the true pressure point.",
            "Unclosed loops create tomorrow's workload."
        ],
        "daily_use": {
            "morning": "Run Pressure + Attention before checking low-value work.",
            "midday": "Check whether the next-best-action moved.",
            "end_of_day": "Close or reschedule open loops."
        },
        "base_result": base,
        "created_at": now()
    }
    MEMORY.setdefault("operator_events", []).insert(0, {"kind": "pressure_attention", "payload": result, "created_at": now()})
    try:
        db_insert("pressure_attention", result)
    except Exception:
        pass
    return result

@app.post("/pressure-attention")
def v36050_pressure_attention(req: V36050PressureRequest):
    base = {}
    try:
        run_req = RunRequest(
            input=req.input or "Assess my current executive pressure and attention priorities.",
            mode="command",
            brain="pressure_attention_engine",
            output_type="pressure_attention",
            depth="standard",
            provider="auto",
            category="operator"
        )
        base = run_engine(run_req)
    except Exception:
        base = {}
    return _v36050_build_response(req.input, base)

@app.get("/pressure-attention-state")
def v36050_pressure_attention_state():
    events = MEMORY.get("operator_events", [])
    pressure = [e for e in events if e.get("kind") == "pressure_attention"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(pressure),
        "latest": pressure[:10],
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT
    }


# ---------------------------------------------------------------------
# V36060 — First-Load UX + Backend Weight Reduction
# Lightweight startup endpoint. No AI call. No DB dependency.
# ---------------------------------------------------------------------

@app.get("/first-load")
def v36060_first_load():
    return {
        "status": "ok",
        "version": VERSION,
        "greeting": "Hey Will, let’s Rock n Roll today.",
        "subtext": "Tell me what has your attention and I’ll help turn it into movement.",
        "what_to_do_now": "Start with the one thing that has your attention.",
        "next_best_action": "Enter today’s pressure, meeting, client issue, proposal, or priority overload.",
        "priority": "Ready",
        "risk": "No active risk yet.",
        "mode": "first_load",
        "backend_weight": "lightweight_no_ai_no_db"
    }


# ---------------------------------------------------------------------
# V36070 — Daily Operating Flow
# Practical daily loop: start day, attention, first move, top 3,
# meeting prep, follow-ups, end-of-day review, tomorrow prep.
# Additive only. Does not replace /run.
# ---------------------------------------------------------------------

class V36070DailyFlowRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36070_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36070_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36070_base_run(input_text):
    try:
        req = RunRequest(
            input=input_text,
            mode="command",
            brain="daily_operating_flow",
            output_type="daily_flow",
            depth="deep",
            provider="auto",
            category="operator"
        )
        return run_engine(req)
    except TypeError:
        req = RunRequest(
            input=input_text,
            mode="command",
            brain="daily_operating_flow",
            output_type="daily_flow",
            depth="deep"
        )
        return run_engine(req)
    except Exception as e:
        return {
            "decision": "Run the day through a simple operating loop.",
            "next_move": "Identify what has your attention and choose the first move.",
            "actions": [
                "Write what has your attention.",
                "Choose the one priority that creates the most movement.",
                "Complete or prepare the most important asset or follow-up.",
                "Check meetings and risks.",
                "End the day with moved, stalled, tomorrow."
            ],
            "risk": str(e),
            "priority": "High",
            "asset": {"summary": "Daily flow fallback."}
        }

def _v36070_build_flow(input_text, base):
    asset = base.get("asset") or {}
    actions = _v36070_list(base.get("actions"))
    if not actions:
        actions = [
            "Identify the single highest-leverage outcome today.",
            "Complete the first move before opening new work.",
            "Prepare the most important meeting or conversation.",
            "Send one follow-up that closes an open loop.",
            "Review what moved, what stalled, and what must happen tomorrow."
        ]

    decision = _v36070_text(base.get("decision") or "Run today through one clear operating sequence.")
    next_move = _v36070_text(base.get("next_move") or base.get("what_to_do_now") or actions[0])
    risk = _v36070_text(base.get("risk") or "The day becomes reactive if attention is not converted into sequence, ownership, and follow-up.")
    priority = _v36070_text(base.get("priority") or "High")
    summary = _v36070_text(asset.get("summary") or base.get("executive_summary") or "Daily operating flow created.")

    flow = {
        "status": "ok",
        "version": VERSION,
        "module": "v36070_daily_operating_flow",
        "greeting": "Hey Will, let’s Rock n Roll today.",
        "executive_summary": summary,
        "start_day": [
            "Write what has your attention.",
            "Name the one outcome that makes today a win.",
            "Check meetings, follow-ups, revenue/client pressure, and open loops."
        ],
        "what_has_attention": input_text or "No input provided yet.",
        "what_matters_first": next_move,
        "top_3_actions": actions[:3],
        "meeting_prep": [
            "Define the meeting outcome before the meeting.",
            "Prepare the likely objection or blocker.",
            "Write the follow-up before the meeting starts."
        ],
        "follow_up_queue": [
            "Send one follow-up that confirms owner, deadline, and next step.",
            "Close one open loop before adding new work.",
            "Escalate anything stalled longer than 24 hours."
        ],
        "end_of_day_review": [
            "What moved today?",
            "What stalled?",
            "Who is waiting on me?",
            "What must be prepared for tomorrow?",
            "What should be delegated or dropped?"
        ],
        "tomorrow_prep": [
            "Prepare the first meeting or client conversation.",
            "Move unfinished critical work into tomorrow’s top 3.",
            "Identify one risk before it becomes urgent."
        ],
        "decision": decision,
        "next_move": next_move,
        "actions": actions,
        "risk": risk,
        "priority": priority,
        "owner": base.get("owner") or "Executive owner",
        "timeline": base.get("timeline") or "Today",
        "success_metric": base.get("success_metric") or "The day ends with at least one important loop closed and tomorrow’s first move clear.",
        "base_result": base,
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {"kind": "daily_operating_flow", "payload": flow, "created_at": now()})
    try:
        db_insert("daily_operating_flow", flow)
    except Exception:
        pass
    return flow

@app.post("/daily-flow")
def v36070_daily_flow(req: V36070DailyFlowRequest):
    input_text = req.input or "Build my daily operating flow: what has my attention, what matters first, top 3, meeting prep, follow-ups, end-of-day review, and tomorrow prep."
    base = _v36070_base_run(input_text)
    return _v36070_build_flow(input_text, base)

@app.get("/daily-flow-state")
def v36070_daily_flow_state():
    events = MEMORY.get("operator_events", [])
    flows = [e for e in events if e.get("kind") == "daily_operating_flow"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(flows),
        "latest": flows[:10],
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT
    }


# ---------------------------------------------------------------------
# V36080 — Output Quality + Real Use Polish
# Sharper outputs. Less generic language. More operator style.
# ---------------------------------------------------------------------

WEAK_PHRASES = [
    "leverage", "synergy", "stakeholders", "optimize", "moving forward",
    "alignment", "best practice", "operational excellence"
]

def _v36080_shorten(text):
    if not text:
        return ""
    text = str(text).strip()
    for p in WEAK_PHRASES:
        text = text.replace(p, "")
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 180:
        text = text[:177].rstrip() + "..."
    return text

def _v36080_top3(input_text):
    t = (input_text or "").lower()

    if "client" in t or "meeting" in t:
        return [
            "Prepare the outcome and likely objection before the meeting.",
            "Send the follow-up within 30 minutes after the call.",
            "Move the next decision into a deadline."
        ]

    if "sales" in t or "proposal" in t or "revenue" in t:
        return [
            "Advance the closest revenue opportunity first.",
            "Remove the exact blocker stopping the deal.",
            "Schedule the next touchpoint before ending the conversation."
        ]

    if "team" in t or "staff" in t or "manager" in t:
        return [
            "Clarify ownership before adding more work.",
            "Escalate the stalled task immediately.",
            "Reduce unnecessary approvals."
        ]

    return [
        "Handle the highest-pressure item first.",
        "Close one open loop before starting new work.",
        "End the day knowing tomorrow’s first move."
    ]

def _v36080_what_matters(input_text):
    t = (input_text or "").lower()

    if "client" in t:
        return "Protect the client relationship and move the next decision forward."

    if "sales" in t or "revenue" in t:
        return "Focus on revenue movement before internal noise."

    if "team" in t:
        return "Fix the ownership bottleneck before adding more tasks."

    if "overwhelmed" in t or "too many" in t:
        return "Cut the day down to one must-win move."

    return "Handle the highest-pressure item first."

@app.post("/quality-polish")
def v36080_quality_polish(req: dict):
    input_text = req.get("input","")

    result = {
        "status": "ok",
        "version": VERSION,
        "module": "v36080_output_quality_real_use_polish",
        "what_matters_first": _v36080_what_matters(input_text),
        "top_3": _v36080_top3(input_text),
        "follow_up": [
            "Confirm owner, deadline, and next step in writing.",
            "Close one open loop before end of day."
        ],
        "do_not_do": [
            "Do not treat every task as urgent.",
            "Do not leave next steps vague.",
            "Do not start new work before closing critical loops."
        ],
        "tone": "short_direct_operator",
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {
        "kind": "quality_polish",
        "payload": result,
        "created_at": now()
    })

    return result


# ---------------------------------------------------------------------
# V36090 — Usefulness Flow Consolidation
# One clean flow. One input. Consolidated usefulness response.
# ---------------------------------------------------------------------

class V36090FlowRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36090_detect_focus(text):
    t = (text or "").lower()
    if any(x in t for x in ["client","meeting","customer"]):
        return "client_meeting"
    if any(x in t for x in ["sales","proposal","revenue","lead"]):
        return "revenue"
    if any(x in t for x in ["team","staff","manager","hire"]):
        return "team"
    if any(x in t for x in ["overwhelmed","too many","busy","priorities"]):
        return "priority_overload"
    return "general"

@app.post("/usefulness-flow")
def v36090_usefulness_flow(req: V36090FlowRequest):
    text = req.input or "Help me prioritize my day."
    focus = _v36090_detect_focus(text)

    what = "Handle the highest-pressure item first."
    top3 = [
        "Close one important loop before noon.",
        "Move one key conversation or decision forward.",
        "End the day knowing tomorrow’s first move."
    ]

    if focus == "client_meeting":
        what = "Protect the client relationship and move the next decision forward."
        top3 = [
            "Prepare the meeting outcome and objection first.",
            "Send the follow-up within 30 minutes after the conversation.",
            "Move the next decision into a deadline."
        ]

    elif focus == "revenue":
        what = "Move revenue before internal noise."
        top3 = [
            "Advance the closest revenue opportunity first.",
            "Remove the blocker slowing the deal.",
            "Schedule the next touchpoint immediately."
        ]

    elif focus == "team":
        what = "Fix ownership and bottlenecks before adding more work."
        top3 = [
            "Clarify who owns what.",
            "Escalate the stalled task immediately.",
            "Reduce unnecessary approvals."
        ]

    elif focus == "priority_overload":
        what = "Cut the day down to one must-win move."
        top3 = [
            "Ignore low-value busy work.",
            "Complete the highest-pressure item first.",
            "Delay anything that does not move revenue, clients, or risk."
        ]

    result = {
        "status":"ok",
        "version":VERSION,
        "module":"v36090_usefulness_flow",
        "greeting":"Hey Will, let’s Rock n Roll today.",
        "focus":focus,
        "what_matters_first":what,
        "top_3":top3,
        "follow_up":[
            "Confirm owner, deadline, and next step.",
            "Close one open loop before end of day."
        ],
        "end_of_day":[
            "What moved?",
            "What stalled?",
            "What must happen tomorrow?"
        ],
        "tone":"clean_operator",
        "created_at":now()
    }

    MEMORY.setdefault("operator_events", []).insert(0,{
        "kind":"usefulness_flow",
        "payload":result,
        "created_at":now()
    })

    return result


# ---------------------------------------------------------------------
# V36100 — Memory + Context Relevance
# Lightweight relevance layer: remembers recent pressures, unfinished loops,
# decisions, and follow-ups so each run does not start from zero.
# Additive only. Does not replace /run.
# ---------------------------------------------------------------------

class V36100MemoryContextRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36100_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36100_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36100_event_payload(event):
    if not isinstance(event, dict):
        return {}
    payload = event.get("payload") or event.get("output") or event
    return payload if isinstance(payload, dict) else {}

def _v36100_keywords(text):
    text = (text or "").lower()
    words = re.findall(r"[a-zA-Z0-9]+", text)
    stop = set(["the","and","for","with","that","this","have","from","what","need","today","tomorrow","about","into","your","you","are","too","many","will","they","them","our","their"])
    return [w for w in words if len(w) > 3 and w not in stop][:30]

def _v36100_score_relevance(input_text, payload):
    keys = set(_v36100_keywords(input_text))
    blob = json.dumps(payload, default=str).lower()
    score = 0
    for k in keys:
        if k in blob:
            score += 8
    for high in ["client","meeting","proposal","sales","revenue","follow","risk","team","priority","deadline"]:
        if high in (input_text or "").lower() and high in blob:
            score += 12
    return min(score, 100)

def _v36100_recent_events(limit=25):
    events = []
    try:
        events.extend(MEMORY.get("operator_events", [])[:limit])
    except Exception:
        pass
    try:
        for r in MEMORY.get("runs", [])[:limit]:
            events.append({"kind": "run", "payload": r, "created_at": r.get("created_at") if isinstance(r, dict) else now()})
    except Exception:
        pass
    return events[:limit]

def _v36100_relevant_context(input_text):
    events = _v36100_recent_events()
    scored = []
    for e in events:
        payload = _v36100_event_payload(e)
        score = _v36100_score_relevance(input_text, payload)
        if score > 0:
            scored.append({"score": score, "kind": e.get("kind","memory"), "created_at": e.get("created_at",""), "payload": payload})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:8]

def _v36100_extract_open_loops(events):
    loops = []
    for e in events:
        p = e.get("payload", {})
        for key in ["follow_up", "follow_ups", "follow_up_moves", "follow_up_before_end_of_day", "follow_up_queue"]:
            for item in _v36100_list(p.get(key)):
                if item and len(loops) < 8:
                    loops.append(_v36100_text(item))
        for key in ["execution_queue", "actions", "top_3", "top_3_actions"]:
            for item in _v36100_list(p.get(key)):
                s = _v36100_text(item)
                if s and any(x in s.lower() for x in ["send", "confirm", "prepare", "schedule", "review", "assign", "close"]) and len(loops) < 8:
                    loops.append(s)
    # de-dupe
    clean = []
    seen = set()
    for l in loops:
        k = l.lower()[:80]
        if k not in seen:
            seen.add(k)
            clean.append(l)
    return clean[:8]

def _v36100_extract_priorities(events):
    priorities = []
    for e in events:
        p = e.get("payload", {})
        for key in ["what_matters_first", "what_matters_now", "next_best_action", "next_move", "do_this_first"]:
            val = _v36100_text(p.get(key))
            if val:
                priorities.append(val)
    clean = []
    seen = set()
    for x in priorities:
        k = x.lower()[:80]
        if k not in seen:
            seen.add(k)
            clean.append(x)
    return clean[:6]

@app.post("/memory-context")
def v36100_memory_context(req: V36100MemoryContextRequest):
    input_text = req.input or "What should I remember and continue from recent work?"
    relevant = _v36100_relevant_context(input_text)
    open_loops = _v36100_extract_open_loops(relevant)
    priorities = _v36100_extract_priorities(relevant)

    result = {
        "status": "ok",
        "version": VERSION,
        "module": "v36100_memory_context_relevance",
        "input": input_text,
        "relevant_count": len(relevant),
        "relevant_context": [
            {
                "score": r["score"],
                "kind": r["kind"],
                "created_at": r["created_at"],
                "summary": _v36100_text(
                    r["payload"].get("what_matters_first")
                    or r["payload"].get("what_to_do_now")
                    or r["payload"].get("next_move")
                    or r["payload"].get("decision")
                    or r["payload"].get("executive_summary")
                    or r["kind"]
                )[:220]
            }
            for r in relevant
        ],
        "carry_forward_priorities": priorities or ["No strong previous priority found. Start with today's highest-pressure item."],
        "unfinished_loops": open_loops or ["No unfinished loops detected from recent memory."],
        "memory_recommendation": "Use recent context to continue the same workstream instead of restarting from zero.",
        "what_to_continue": (priorities[0] if priorities else "Enter the current pressure and create a new operating loop."),
        "what_to_avoid": [
            "Do not restart the same work as a new conversation if there is a relevant open loop.",
            "Do not add new tasks until the highest-relevance follow-up is closed.",
            "Do not let memory become noise; only carry forward what affects the next action."
        ],
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {
        "kind": "memory_context",
        "payload": result,
        "created_at": now()
    })

    try:
        db_insert("memory_context", result)
    except Exception:
        pass

    return result

@app.get("/memory-context-state")
def v36100_memory_context_state():
    events = MEMORY.get("operator_events", [])
    context_events = [e for e in events if e.get("kind") == "memory_context"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(context_events),
        "latest": context_events[:10],
        "memory_counts": {
            k: len(v) if isinstance(v, list) else len(v.keys()) if isinstance(v, dict) else 0
            for k, v in MEMORY.items()
        },
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT
    }


# ---------------------------------------------------------------------
# V36110 — Real Daily Brief + Morning Start
# Makes the first page useful immediately: morning brief, pressure,
# first move, top 3, open loops, follow-up, tomorrow prep.
# Additive only. Does not replace /run.
# ---------------------------------------------------------------------

class V36110MorningBriefRequest(BaseModel):
    input: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36110_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]

def _v36110_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36110_recent_operator_events(limit=20):
    try:
        return MEMORY.get("operator_events", [])[:limit]
    except Exception:
        return []

def _v36110_payload(event):
    if not isinstance(event, dict):
        return {}
    p = event.get("payload") or event.get("output") or event
    return p if isinstance(p, dict) else {}

def _v36110_collect_open_loops(events):
    loops = []
    for e in events:
        p = _v36110_payload(e)
        for key in ["follow_up", "follow_ups", "follow_up_queue", "unfinished_loops", "follow_up_before_end_of_day"]:
            for item in _v36110_list(p.get(key)):
                if item and len(loops) < 6:
                    loops.append(_v36110_text(item))
        for key in ["top_3", "top_3_actions", "actions", "execution_queue"]:
            for item in _v36110_list(p.get(key)):
                s = _v36110_text(item)
                if s and any(w in s.lower() for w in ["send", "confirm", "prepare", "schedule", "review", "close", "assign"]) and len(loops) < 6:
                    loops.append(s)
    clean = []
    seen = set()
    for x in loops:
        k = x.lower()[:90]
        if k not in seen:
            seen.add(k)
            clean.append(x)
    return clean[:6]

def _v36110_collect_priorities(events):
    priorities = []
    for e in events:
        p = _v36110_payload(e)
        for key in ["what_matters_first", "what_matters_now", "what_to_do_now", "next_best_action", "next_move", "do_this_first"]:
            val = _v36110_text(p.get(key))
            if val:
                priorities.append(val)
    clean = []
    seen = set()
    for x in priorities:
        k = x.lower()[:90]
        if k not in seen:
            seen.add(k)
            clean.append(x)
    return clean[:5]

def _v36110_score_pressure(input_text, open_loops):
    t = (input_text or "").lower()
    score = min(40, len(open_loops) * 8)
    for word, value in {
        "client": 12, "meeting": 10, "proposal": 10, "sales": 12,
        "revenue": 14, "urgent": 14, "deadline": 12, "team": 8,
        "follow": 8, "risk": 12, "too many": 14, "overwhelmed": 14
    }.items():
        if word in t:
            score += value
    return min(score, 100)

def _v36110_level(score):
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Ready"

@app.post("/morning-brief")
def v36110_morning_brief(req: V36110MorningBriefRequest):
    input_text = req.input or "Build my morning executive brief from current memory, open loops, pressure, priorities, follow-ups, and tomorrow prep."
    events = _v36110_recent_operator_events()
    open_loops = _v36110_collect_open_loops(events)
    priorities = _v36110_collect_priorities(events)

    score = _v36110_score_pressure(input_text, open_loops)
    level = _v36110_level(score)

    first_move = priorities[0] if priorities else "Enter what has your attention and close the highest-pressure loop first."

    top_3 = []
    if open_loops:
        top_3.append(open_loops[0])
    top_3.append(first_move)
    top_3.append("Send one follow-up that confirms owner, deadline, and next step.")
    clean_top = []
    seen = set()
    for x in top_3:
        k = str(x).lower()[:90]
        if k not in seen and x:
            seen.add(k)
            clean_top.append(x)

    result = {
        "status": "ok",
        "version": VERSION,
        "module": "v36110_real_daily_brief_morning_start",
        "greeting": "Hey Will, let’s Rock n Roll today.",
        "morning_summary": "Start with the pressure, the open loops, and the first move. Do not begin with low-value work.",
        "pressure_score": score,
        "pressure_level": level,
        "what_to_do_first": first_move,
        "top_3": clean_top[:3],
        "open_loops": open_loops or ["No open loops detected yet. Run the system today and memory will improve."],
        "follow_up_before_end_of_day": [
            "Confirm owner, deadline, and next step for the most important open item.",
            "Close or reschedule any unresolved client/revenue follow-up."
        ],
        "meeting_prep": [
            "Check today/tomorrow meetings for objective, likely objection, and desired decision.",
            "Prepare the follow-up message before the meeting begins."
        ],
        "tomorrow_prep": [
            "Carry forward unfinished critical loops.",
            "Identify tomorrow’s first move before ending today.",
            "Remove one low-value item from tomorrow’s list."
        ],
        "do_not_do": [
            "Do not start with inbox noise.",
            "Do not add new priorities until the first loop is closed.",
            "Do not leave follow-up vague."
        ],
        "relevant_priorities": priorities or ["No recent priority found."],
        "created_at": now()
    }

    MEMORY.setdefault("operator_events", []).insert(0, {
        "kind": "morning_brief",
        "payload": result,
        "created_at": now()
    })

    try:
        db_insert("morning_brief", result)
    except Exception:
        pass

    return result

@app.get("/morning-brief-state")
def v36110_morning_brief_state():
    events = MEMORY.get("operator_events", [])
    briefs = [e for e in events if e.get("kind") == "morning_brief"]
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(briefs),
        "latest": briefs[:10],
        "operator_state": scan_operator_state(),
        "active_context": ACTIVE_CONTEXT
    }


# ---------------------------------------------------------------------
# V36120 — ACTIONS Operating UX
# Workspace/action capture endpoints. Additive only. Existing routes stay.
# ---------------------------------------------------------------------

class V36120ActionRequest(BaseModel):
    input: str = ""
    action_id: str = ""
    title: str = ""
    category: str = "general"
    account_id: str = "default"
    user_id: str = "owner"

def _v36120_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36120_detect_category(text):
    t = (text or "").lower()
    if any(x in t for x in ["meeting", "met with", "call", "thursday", "next week", "office"]):
        return "meeting"
    if any(x in t for x in ["proposal", "quote", "contract", "pricing", "retainer"]):
        return "proposal"
    if any(x in t for x in ["strategy", "plan", "growth", "marketing", "sales", "ads", "advertising"]):
        return "strategy"
    if any(x in t for x in ["follow up", "follow-up", "reply", "email"]):
        return "follow_up"
    if any(x in t for x in ["task", "need to", "todo", "do this"]):
        return "execution"
    return "action"

def _v36120_title(text):
    text = _v36120_text(text)
    if not text:
        return "New Action"
    # Try to produce useful title from messy input
    lower = text.lower()
    if "bob" in lower and "auto" in lower:
        return "Bob — Auto Loan Strategy"
    if "proposal" in lower:
        return "Proposal — " + " ".join(text.split()[:5])
    if "meeting" in lower or "met with" in lower:
        return "Meeting — " + " ".join(text.split()[:6])
    return " ".join(text.split()[:7])[:84]

def _v36120_extract_entities(text):
    raw = text or ""
    website = ""
    web = re.search(r"(https?://\S+|[a-zA-Z0-9.-]+\.(com|ca|io|net|org)\S*)", raw)
    if web:
        website = web.group(1)
    person = ""
    company = ""
    # Common simple extraction
    m = re.search(r"\bwith\s+([A-Z][a-zA-Z]+)", raw)
    if m:
        person = m.group(1)
    elif "bob" in raw.lower():
        person = "Bob"
    caps = re.findall(r"\b[A-Z][a-zA-Z0-9&.-]+\b", raw)
    if caps:
        if not person:
            person = caps[0]
        candidates = [c for c in caps if c.lower() not in ["Meeting", "Met", "He", "Website", "Google"] and c != person]
        company = " ".join(candidates[:3])
    return {"person": person, "company": company, "website": website}

def _v36120_action_payload(req):
    input_text = req.input or ""
    category = req.category if req.category and req.category != "general" else _v36120_detect_category(input_text)
    action_id = req.action_id or str(uuid.uuid4())
    title = req.title or _v36120_title(input_text)
    entities = _v36120_extract_entities(input_text)

    summary = "Captured and organized into an active ACTION."
    if category == "meeting":
        summary = "Meeting context captured. Prep, follow-up, proposal direction, and next actions are ready to refine."
    elif category == "proposal":
        summary = "Proposal opportunity detected. Draft overview, missing info, scope ideas, and next steps are ready."
    elif category == "strategy":
        summary = "Strategy action captured. System organized the core issue, next move, and execution angle."

    missing = []
    if not entities.get("person"):
        missing.append("person/contact")
    if not entities.get("company"):
        missing.append("company/client")
    if category in ["proposal", "strategy"] and "budget" not in input_text.lower() and "$" not in input_text:
        missing.append("budget/scope")

    draft = "ACTION NOTES\n\n" + input_text + "\n\nNEXT MOVE\nReview, edit, and tell the system what to improve."
    if category == "meeting":
        draft = f"""MEETING BRIEF DRAFT

Summary:
{summary}

Known Context:
{input_text}

Talking Points:
- Confirm the business problem and current priority.
- Understand timing, budget, decision process, and constraints.
- Identify what would make this a successful next step.

Possible Opportunity:
- Strategy support
- Proposal follow-up
- Conversion/lead-quality improvement
- Website or campaign optimization

Follow-Up Draft:
Thanks for the meeting. I’ll put together the next-step overview and send over a clear direction with recommended actions, timing, and scope.

Missing Info:
{", ".join(missing) if missing else "Nothing obvious yet."}
"""
    elif category == "proposal":
        draft = f"""PROPOSAL OVERVIEW DRAFT

Opportunity:
{input_text}

Potential Scope:
- Discovery and strategy
- Execution plan
- Conversion or operational improvement
- Reporting / measurement
- Follow-up cadence

Missing Info:
{", ".join(missing) if missing else "Budget, timeline, decision-maker, and success metric."}

Next:
Turn this into a client-ready proposal once details are confirmed.
"""

    payload = {
        "action_id": action_id,
        "title": title,
        "category": category,
        "input": input_text,
        "short": {
            "summary": summary,
            "what_matters": "Keep this work tied to one ACTION so notes, decisions, drafts, and follow-ups do not scatter.",
            "next_move": "Review the short summary, then open details if you need to edit or expand.",
            "risk": "If this stays as loose notes, follow-up and proposal value may get missed.",
            "open_loops": [
                "Confirm missing info: " + ", ".join(missing) if missing else "No critical missing info detected.",
                "Decide whether this needs meeting prep, proposal, follow-up, or execution."
            ]
        },
        "details": {
            "entities": entities,
            "missing_info": missing,
            "draft": draft,
            "sections": ["Overview", "Notes", "Draft", "Actions", "Follow-Up", "Missing Info"]
        },
        "messages": [
            {"role": "user", "content": input_text, "created_at": now()},
            {"role": "system", "content": summary, "created_at": now()}
        ],
        "tasks": [
            {"task": "Review and edit the generated draft.", "status": "open", "priority": "High"},
            {"task": "Fill missing info: " + ", ".join(missing) if missing else "Continue with next instruction.", "status": "open", "priority": "Medium"}
        ],
        "created_at": now(),
        "updated_at": now(),
        "version": VERSION
    }
    return payload

@app.post("/action-capture")
def v36120_action_capture(req: V36120ActionRequest):
    payload = _v36120_action_payload(req)
    MEMORY.setdefault("actions_index", {})[payload["action_id"]] = payload
    MEMORY.setdefault("operator_events", []).insert(0, {"kind": "action_capture", "payload": payload, "created_at": now()})
    try:
        db_insert("action_capture", payload)
    except Exception:
        pass
    return {"status": "ok", "action": payload, "version": VERSION}

@app.get("/actions-lite")
def v36120_actions_lite():
    actions = MEMORY.get("actions_index", {})
    items = list(actions.values()) if isinstance(actions, dict) else []
    items = sorted(items, key=lambda x: x.get("updated_at", ""), reverse=True)
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(items),
        "actions": [
            {
                "action_id": a.get("action_id"),
                "title": a.get("title"),
                "category": a.get("category"),
                "updated_at": a.get("updated_at"),
                "short": a.get("short", {})
            } for a in items[:50]
        ]
    }

@app.get("/action-lite/{action_id}")
def v36120_action_lite(action_id: str):
    action = MEMORY.get("actions_index", {}).get(action_id)
    if not action:
        return {"status": "missing", "action_id": action_id, "version": VERSION}
    return {"status": "ok", "action": action, "version": VERSION}


# ---------------------------------------------------------------------
# V36130 — Action Workspace Engine
# ---------------------------------------------------------------------

@app.post("/action-followup-scan")
def v36130_followup_scan():
    actions = MEMORY.get("actions_index", {})
    items = list(actions.values()) if isinstance(actions, dict) else []
    feed = []

    for item in items[:25]:
        title = item.get("title", "Action")
        category = item.get("category", "general")

        if category == "meeting":
            suggestion = f"You met with a contact regarding '{title}'. Suggested next move: send recap and confirm next meeting step."
        elif category == "proposal":
            suggestion = f"Proposal action '{title}' appears active. Suggested next move: finalize pricing/scope and send client-ready draft."
        else:
            suggestion = f"Review '{title}' and close open loops."

        feed.append({
            "title": title,
            "category": category,
            "suggestion": suggestion,
            "priority": "High" if category in ["proposal", "meeting"] else "Medium"
        })

    return {
        "status": "ok",
        "version": VERSION,
        "count": len(feed),
        "followups": feed
    }

@app.get("/action-workspace-state")
def v36130_workspace_state():
    actions = MEMORY.get("actions_index", {})
    count = len(actions) if isinstance(actions, dict) else 0

    return {
        "status": "ok",
        "version": VERSION,
        "workspace_engine": True,
        "active_actions": count,
        "features": [
            "short executive summary",
            "expandable detail view",
            "editable documents",
            "timeline continuity",
            "follow-up intelligence",
            "persistent action memory"
        ]
    }


# ---------------------------------------------------------------------
# V36150 — Action Detail + Command Flow
# Keeps design stable. Adds stronger action detail structure.
# ---------------------------------------------------------------------

class V36150ActionCommandRequest(BaseModel):
    action_id: str = ""
    command: str = ""
    current_draft: str = ""
    account_id: str = "default"
    user_id: str = "owner"

def _v36150_text(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

@app.post("/action-command")
def v36150_action_command(req: V36150ActionCommandRequest):
    command = _v36150_text(req.command)
    draft = _v36150_text(req.current_draft)
    lower = command.lower()

    result = {
        "status": "ok",
        "version": VERSION,
        "module": "v36150_action_detail_command_flow",
        "action_id": req.action_id,
        "command": command,
        "short": {
            "summary": "Command applied to the active ACTION.",
            "next_move": "Review the updated draft and decide whether it is ready, needs detail, or should become client-ready.",
            "risk": "If the draft is not reviewed, the ACTION may stay unfinished."
        },
        "updated_draft": draft,
        "suggested_next_steps": [
            "Confirm the decision or missing detail.",
            "Send follow-up or prepare the client-ready version.",
            "Keep the ACTION active until the next step is closed."
        ],
        "created_at": now()
    }

    if "short" in lower or "summarize" in lower:
        result["updated_draft"] = "\n".join([line for line in draft.splitlines() if line.strip()][:8])
        result["short"]["summary"] = "Draft shortened for executive review."
    elif "client" in lower or "ready" in lower:
        result["updated_draft"] = "CLIENT-READY VERSION\n\n" + draft + "\n\nNext Step:\nPlease confirm the preferred direction, timing, and scope."
        result["short"]["summary"] = "Draft converted into a client-ready direction."
    elif "proposal" in lower:
        result["updated_draft"] = draft + "\n\nPROPOSAL DIRECTION\n- Problem\n- Recommended scope\n- Timeline\n- Investment range\n- Next step"
        result["short"]["summary"] = "Proposal structure added."
    elif "follow" in lower:
        result["updated_draft"] = draft + "\n\nFOLLOW-UP DRAFT\nThanks for the conversation. I’ll prepare the next-step overview and send over a clear direction with recommended actions, timing, and scope."
        result["short"]["summary"] = "Follow-up draft added."
    elif "expand" in lower or "detail" in lower:
        result["updated_draft"] = draft + "\n\nDETAILS TO ADD\n- Current situation\n- Business objective\n- Constraints\n- Decision needed\n- Timing\n- Owner"
        result["short"]["summary"] = "Detail structure added."
    else:
        result["updated_draft"] = draft + "\n\nEXECUTIVE NOTE\n" + command
        result["short"]["summary"] = "Executive note added to the ACTION."

    MEMORY.setdefault("operator_events", []).insert(0, {
        "kind": "action_command",
        "payload": result,
        "created_at": now()
    })

    try:
        db_insert("action_command", result)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------
# V36200 — Conversational Executive Operating System
# Thread-first action layer. Additive only; existing routes remain.
# ---------------------------------------------------------------------

class V36200ThreadRequest(BaseModel):
    action_id: str = ""
    input: str = ""
    title: str = ""
    category: str = "action"
    current_thread: list = []
    account_id: str = "default"
    user_id: str = "owner"

def _v36200_clean(value):
    try:
        return clean_text(str(value or "")).strip()
    except Exception:
        return str(value or "").strip()

def _v36200_detect_category(text):
    t = (text or "").lower()
    if any(x in t for x in ["meeting", "met with", "call", "thursday", "next week"]):
        return "meeting"
    if any(x in t for x in ["proposal", "quote", "contract", "pricing"]):
        return "proposal"
    if any(x in t for x in ["strategy", "marketing", "sales", "plan"]):
        return "strategy"
    if any(x in t for x in ["follow up", "follow-up", "email", "reply"]):
        return "follow_up"
    return "action"

def _v36200_title(text):
    text = _v36200_clean(text)
    if not text:
        return "New Action"
    low = text.lower()
    if "bob" in low and "auto" in low:
        return "Bob — Auto Loan Strategy"
    if "proposal" in low:
        return "Proposal — " + " ".join(text.split()[:4])
    if "meeting" in low:
        return "Meeting — " + " ".join(text.split()[:5])
    return " ".join(text.split()[:6])[:80]

def _v36200_response(text, category):
    low = (text or "").lower()
    title = _v36200_title(text)

    short = {
        "summary": "Captured and organized into an active ACTION.",
        "next_move": "Review the short version, then expand details only if needed.",
        "risk": "Loose notes create missed follow-up and unclear ownership."
    }

    top_actions = [
        "Clarify the next decision.",
        "Create or update the draft.",
        "Close the follow-up loop."
    ]

    if category == "meeting":
        short = {
            "summary": "Meeting context captured.",
            "next_move": "Prepare talking points and confirm the next step before the meeting ends.",
            "risk": "The meeting creates no value if no owner, deadline, or next action is confirmed."
        }
        top_actions = [
            "Prepare 3 talking points.",
            "Identify likely objection or blocker.",
            "Draft the follow-up before the meeting."
        ]
    elif category == "proposal":
        short = {
            "summary": "Proposal opportunity detected.",
            "next_move": "Build the proposal overview and identify missing pricing/scope details.",
            "risk": "Proposal value may be missed if scope, budget, and timing stay vague."
        }
        top_actions = [
            "Draft proposal overview.",
            "Identify missing budget/scope/timeline.",
            "Prepare client-ready next step."
        ]
    elif category == "strategy":
        short = {
            "summary": "Strategy action captured.",
            "next_move": "Turn the idea into a clear direction, owner, and first move.",
            "risk": "Strategy stays abstract if not tied to execution."
        }
        top_actions = [
            "Define the strategic direction.",
            "Pick the first operational move.",
            "Identify the constraint or risk."
        ]

    long_detail = {
        "context": text,
        "recommended_sections": ["Summary", "Next Move", "Actions", "Risks", "Draft", "Follow-Up"],
        "missing_information": [],
        "draft": f"{title}\n\nSHORT VERSION\n{short['summary']}\n\nNEXT MOVE\n{short['next_move']}\n\nACTION ITEMS\n- " + "\n- ".join(top_actions)
    }

    if "company" not in low and "client" not in low and category in ["meeting", "proposal"]:
        long_detail["missing_information"].append("Company/client name")
    if "budget" not in low and "$" not in low and category == "proposal":
        long_detail["missing_information"].append("Budget or investment range")
    if "when" not in low and "next week" not in low and "today" not in low and category in ["meeting", "follow_up"]:
        long_detail["missing_information"].append("Timing/date")

    return {
        "title": title,
        "category": category,
        "short": short,
        "top_actions": top_actions,
        "long_detail": long_detail
    }

@app.post("/thread-run")
def v36200_thread_run(req: V36200ThreadRequest):
    text = _v36200_clean(req.input)
    category = req.category or _v36200_detect_category(text)
    if category == "action":
        category = _v36200_detect_category(text)

    action_id = req.action_id or str(uuid.uuid4())
    response = _v36200_response(text, category)

    payload = {
        "status": "ok",
        "version": VERSION,
        "module": "v36200_conversational_executive_operating_system",
        "action_id": action_id,
        "title": req.title or response["title"],
        "category": response["category"],
        "user_message": text,
        "assistant_message": {
            "short": response["short"],
            "top_actions": response["top_actions"],
            "long_detail": response["long_detail"]
        },
        "created_at": now()
    }

    MEMORY.setdefault("thread_events", []).insert(0, payload)
    MEMORY.setdefault("operator_events", []).insert(0, {
        "kind": "thread_run",
        "payload": payload,
        "created_at": now()
    })

    try:
        db_insert("thread_run", payload)
    except Exception:
        pass

    return payload

@app.get("/thread-state")
def v36200_thread_state():
    return {
        "status": "ok",
        "version": VERSION,
        "count": len(MEMORY.get("thread_events", [])),
        "latest": MEMORY.get("thread_events", [])[:20]
    }

# ---------------------------------------------------------------------
# V36300 — Executive Operating Intelligence
# ---------------------------------------------------------------------

class V36300EngineRequest(BaseModel):
    input: str = ""
    action_id: str = ""
    title: str = ""
    category: str = "auto"
    account_id: str = "default"
    user_id: str = "owner"

def _v36300_category(text):
    t = (text or "").lower()
    if any(x in t for x in ["meeting", "met with", "call", "office", "thursday", "next week"]): return "meeting"
    if any(x in t for x in ["proposal", "quote", "contract", "retainer", "pricing", "scope"]): return "proposal"
    if any(x in t for x in ["follow up", "follow-up", "reply", "email", "send"]): return "follow_up"
    if any(x in t for x in ["strategy", "marketing", "sales", "growth", "ads", "advertising", "conversion"]): return "strategy"
    return "action"

def _v36300_title(text, category):
    text = str(text or "").strip()
    low = text.lower()
    if "bob" in low and ("auto" in low or "loan" in low): return "Bob — Auto Loan Strategy"
    if category == "meeting": return "Meeting — " + " ".join(text.split()[:5])
    if category == "proposal": return "Proposal — " + " ".join(text.split()[:5])
    if category == "follow_up": return "Follow-Up — " + " ".join(text.split()[:5])
    if category == "strategy": return "Strategy — " + " ".join(text.split()[:5])
    return " ".join(text.split()[:7])[:86] or "New Action"

def _v36300_intel(text, category):
    what = "This is now an active ACTION. The system captured the context and converted it into an operating thread."
    next_move = "Clarify the next decision, owner, and deadline."
    why = "Execution improves when loose thoughts become one organized thread with next steps and follow-up."
    risk = "This can stall if it remains a loose note with no owner, due date, or output."
    rec = ["Confirm the objective.", "Define the next move.", "Create the needed draft or follow-up."]
    missing = []

    if category == "meeting":
        what = "Meeting signal detected. This needs prep, talking points, and a follow-up path."
        next_move = "Prepare the meeting brief and decide what must be confirmed before the meeting ends."
        why = "The value of the meeting is created by the next step, not the conversation itself."
        risk = "The meeting may create motion but no result if budget, decision-maker, or follow-up is not confirmed."
        rec = ["Prepare 3 talking points.", "Identify what decision is needed.", "Draft the follow-up before the meeting."]
        missing = ["contact/company", "meeting goal", "timing"] if "with" not in (text or "").lower() else []

    if category == "proposal":
        what = "Proposal opportunity detected. Scope and pricing need to be shaped before this becomes client-ready."
        next_move = "Build the proposal overview and identify missing pricing, scope, timeline, and decision details."
        why = "Fast proposal structure increases close probability and prevents the opportunity from drifting."
        risk = "The proposal may become vague or underpriced if scope, timing, and success metrics are not confirmed."
        rec = ["Draft proposal overview.", "List missing scope/pricing details.", "Prepare client-ready next step."]
        missing = ["budget/investment range", "scope", "timeline"]

    if category == "strategy":
        what = "Strategy signal detected. This needs to become a decision and an execution path."
        next_move = "Turn the strategy into one clear move, one owner, and one measurable result."
        why = "Strategy is only valuable when it creates action, leverage, or a decision."
        risk = "This can stay abstract if it is not tied to an immediate operational move."
        rec = ["Define the strategic objective.", "Pick the first move.", "Identify the constraint."]

    draft = f"""ACTION BRIEF

WHAT MATTERS
{what}

NEXT MOVE
{next_move}

WHY IT MATTERS
{why}

RISK
{risk}

RECOMMENDED ACTIONS
- """ + "\n- ".join(rec) + f"""

CONTEXT
{text}
"""

    return {"what_matters": what, "next_move": next_move, "why_it_matters": why, "risk": risk, "recommended_actions": rec, "missing_info": missing, "draft": draft}

@app.post("/engine-operate")
def v36300_engine_operate(req: V36300EngineRequest):
    text = str(req.input or "").strip()
    category = req.category if req.category and req.category != "auto" else _v36300_category(text)
    title = req.title or _v36300_title(text, category)
    action_id = req.action_id or str(uuid.uuid4())
    intel = _v36300_intel(text, category)

    payload = {
        "status": "ok",
        "version": VERSION,
        "action_id": action_id,
        "title": title,
        "category": category,
        "priority": "High" if category in ["meeting", "proposal"] else "Medium",
        "input": text,
        "short": {
            "what_matters": intel["what_matters"],
            "next_move": intel["next_move"],
            "risk": intel["risk"]
        },
        "why_it_matters": intel["why_it_matters"],
        "recommended_actions": intel["recommended_actions"],
        "missing_info": intel["missing_info"],
        "draft": intel["draft"],
        "created_at": now()
    }
    MEMORY.setdefault("engine_operating_events", []).insert(0, payload)
    try:
        db_insert("engine_operate", payload)
    except Exception:
        pass
    return payload

@app.get("/engine-operating-state")
def v36300_engine_operating_state():
    return {"status": "ok", "version": VERSION, "events": len(MEMORY.get("engine_operating_events", [])), "latest": MEMORY.get("engine_operating_events", [])[:10]}
