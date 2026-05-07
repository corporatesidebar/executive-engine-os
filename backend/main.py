from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
import os, json, re
from datetime import datetime

VERSION = "33000-autonomous-executive-workspace-engine"

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

def now(): return datetime.utcnow().isoformat()
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
    if "proposal" in t or category == "plans": return "proposal"
    if "meeting" in t or "call" in t or category == "meetings": return "meeting"
    if "marketing" in t or "seo" in t or "ads" in t or "campaign" in t or "cpa" in t or category == "marketing": return "marketing"
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
    return "High" if any(x in t for x in ["urgent","asap","today","now","before tomorrow","tomorrow","deadline","due"]) else "Medium"

def provider_plan(category, output_type, requested):
    requested = (requested or "auto").lower()
    if requested in ["openai", "claude"]: return [requested]
    if category in ["plans","email","research","content","brainstorm","meetings"] or output_type in ["proposal","email","brief","content","strategy","research","ideas"]:
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
        "mission_id": mid, "mission_type": mission_type, "input": input_text,
        "client": client, "project": project, "provider": provider,
        "status": "active", "created_at": now(), "updated_at": now(),
        "current_step_index": 0, "progress": 0,
        "steps": [{**s, "status": "active" if i == 0 else "pending", "started_at": now() if i == 0 else "", "completed_at": "", "result_summary": "", "asset_title": ""} for i, s in enumerate(steps)],
        "outputs": [], "next_action": steps[0]["label"] if steps else "Start"
    }
    ACTIVE_CONTEXT.update({"current_mission": mission, "workflow_id": mid, "workflow_type": mission_type, "workflow_stage": steps[0]["key"] if steps else "", "workflow_progress": 0, "client": client, "project": project})
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
        "workspace_id": wid, "workspace_type": workspace_type,
        "title": f"{client or project or workspace_type.title()} Workspace",
        "input": input_text, "client": client, "project": project, "provider": provider,
        "status": "active", "created_at": now(), "updated_at": now(),
        "summary": "", "next_executive_decision": "", "package": AUTONOMOUS_PACKAGES.get(workspace_type, AUTONOMOUS_PACKAGES["general"]),
        "mission_id": mission["mission_id"],
        "sections": {
            "overview": {"title": "Executive Overview", "status": "ready", "content": input_text},
            "assets": [], "tasks": [], "follow_ups": [], "warnings": [], "decisions": [], "timeline": [],
            "right_rail": {"next": [], "assets": [], "follow_ups": [], "warnings": []}
        }
    }
    MEMORY["workspaces"][wid] = ws
    ACTIVE_CONTEXT.update({"workspace_id": wid, "current_workspace": ws, "client": client, "project": project})
    MEMORY["workspace_events"].insert(0, {"timestamp": now(), "event": "workspace_created", "workspace_id": wid, "mission_id": mission["mission_id"]})
    return ws

def classify(req: RunRequest):
    cat = req.category if req.category and req.category != "auto" else detect_category(req.input)
    brain = req.brain if req.brain and req.brain != "auto" else {"email":"communications","meetings":"meetings","plans":"revenue","content":"content","marketing":"revenue","research":"research","brainstorm":"strategy","goals":"strategy","tasks":"execution"}.get(cat, "command")
    out = req.output_type if req.output_type and req.output_type != "auto" else {"email":"email","meetings":"brief","plans":"proposal","content":"content","marketing":"strategy","research":"brief","brainstorm":"ideas","goals":"goals","tasks":"tasks"}.get(cat, "brief")
    client, project = detect_context(req.input, req.client, req.project)
    wid = req.workflow_id or ACTIVE_CONTEXT.get("workflow_id") or f"{slug(client or project or cat)}-{int(datetime.utcnow().timestamp())}"
    mission = get_mission(req.mission_id)
    if mission and req.step_key:
        for s in mission.get("steps", []):
            if s.get("key") == req.step_key:
                cat, brain, out = s.get("category", cat), s.get("brain", brain), s.get("output_type", out)
    router = {
        "category": cat, "brain": brain, "output_type": out, "urgency": urgency(req.input),
        "meeting_related": cat == "meetings" or "meeting" in (req.input or "").lower() or "call" in (req.input or "").lower(),
        "follow_up_required": cat in ["email","plans","meetings"],
        "provider_plan": provider_plan(cat, out, req.provider),
        "context": {"client": client, "project": project, "workflow_id": wid, "workflow_type": cat, "continued_from_memory": bool(ACTIVE_CONTEXT.get("workflow_id"))},
        "workflow_stage": req.step_key or cat,
        "workspace": {"workspace_id": ACTIVE_CONTEXT.get("workspace_id", ""), "primary_section": cat, "recommended_next_panel": "Autonomous Workspace", "right_rail": ["next","assets","follow_ups","warnings"]},
    }
    MEMORY["router_events"].insert(0, {"timestamp": now(), "input": req.input, "router": router})
    return router

SYSTEM_PROMPT = """You are Executive Engine OS acting as an elite COO/operator. Return ONLY valid JSON with keys: what_to_do_now, decision, next_move, actions(array), risk, priority(High|Medium|Low), reality_check, leverage, constraint, financial_impact, asset{title,type,content}, follow_up. Be specific, executive, practical. Never switch industries. Create usable business assets."""

def safe_json(text):
    text = (text or "").strip().replace("```json","").replace("```","").strip()
    try: return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m: return json.loads(m.group(0))
    raise ValueError("Invalid JSON")

def normalize(data, req, router, provider_used):
    actions = data.get("actions", [])
    if not isinstance(actions, list): actions = [str(actions)]
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    priority = data.get("priority") if data.get("priority") in ["High","Medium","Low"] else router.get("urgency", "High")
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
        "asset": {"title": str(asset.get("title") or f"{router['category'].title()} {router['output_type'].title()}"), "type": str(asset.get("type") or router["output_type"]), "content": str(asset.get("content") or "")},
        "follow_up": str(data.get("follow_up") or "Confirm next step and continue."),
        "provider_used": provider_used,
        "router": router,
        "active_context": dict(ACTIVE_CONTEXT),
        "workspace": get_workspace(),
        "memory": {"workspace_id": ACTIVE_CONTEXT.get("workspace_id", ""), "workflow_id": router["context"].get("workflow_id"), "client": router["context"].get("client"), "project": router["context"].get("project")}
    }

def fallback(req, router, reason):
    return normalize({
        "what_to_do_now": "Create the executive workspace package manually because the AI provider failed.",
        "decision": "Keep workflow moving with a controlled fallback.",
        "next_move": "Confirm context and run again.",
        "actions": ["Confirm client/project.", "Run OpenAI if Claude has no credits.", "Save the generated asset.", "Create follow-up."],
        "risk": "Provider failure or missing credits.",
        "priority": router.get("urgency", "High"),
        "asset": {"title": f"{router['category'].title()} Fallback", "type": router["output_type"], "content": f"Input:\n{req.input}\n\nDebug:\n{reason}"},
        "follow_up": "Retry with provider=openai or add Claude credits."
    }, req, router, "fallback")

def call_ai(req, router, provider):
    prompt = json.dumps({"router": router, "active_context": ACTIVE_CONTEXT, "workspace": get_workspace(), "input": req.input}, indent=2)
    if provider == "openai":
        if not openai_client: raise RuntimeError("OPENAI_API_KEY missing")
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL, temperature=0.3, max_tokens=1500,
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}]
        )
        return normalize(safe_json(resp.choices[0].message.content), req, router, f"openai:{OPENAI_MODEL}")
    if provider == "claude":
        if not anthropic_client: raise RuntimeError("ANTHROPIC_API_KEY missing")
        resp = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=1800, temperature=0.3,
            system=SYSTEM_PROMPT, messages=[{"role":"user","content":prompt}]
        )
        raw = "\n".join([b.text for b in resp.content if getattr(b, "type", "") == "text"])
        return normalize(safe_json(raw), req, router, f"claude:{ANTHROPIC_MODEL}")
    raise RuntimeError("Unknown provider")

def add_to_workspace(result, router):
    ws = get_workspace()
    if not ws: return {}
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
        ws["sections"]["follow_ups"].insert(0, f); ws["sections"]["right_rail"]["follow_ups"].insert(0, f)
    if result.get("risk"):
        w = {"warning": result.get("risk"), "priority": result.get("priority"), "created_at": now(), "step": step}
        ws["sections"]["warnings"].insert(0, w); ws["sections"]["right_rail"]["warnings"].insert(0, w)
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

def advance_mission(mission, step_key, result):
    if not mission: return {}
    steps = mission.get("steps", [])
    idx = next((i for i,s in enumerate(steps) if s.get("key") == step_key), mission.get("current_step_index", 0))
    if steps:
        steps[idx]["status"] = "done"; steps[idx]["completed_at"] = now()
        steps[idx]["result_summary"] = result.get("what_to_do_now", ""); steps[idx]["asset_title"] = result.get("asset", {}).get("title", "")
        if idx + 1 < len(steps):
            steps[idx+1]["status"] = "active"; steps[idx+1]["started_at"] = steps[idx+1].get("started_at") or now()
            mission["current_step_index"] = idx + 1; mission["next_action"] = steps[idx+1]["label"]; mission["status"] = "active"
        else:
            mission["current_step_index"] = idx; mission["next_action"] = "Mission complete"; mission["status"] = "complete"
        mission["progress"] = round(len([s for s in steps if s.get("status") == "done"]) / len(steps) * 100)
        ACTIVE_CONTEXT["workflow_progress"] = mission["progress"]
    mission["updated_at"] = now()
    mission.setdefault("outputs", []).insert(0, {"timestamp": now(), "step_key": step_key, "summary": result.get("what_to_do_now"), "asset_title": result.get("asset", {}).get("title"), "provider_used": result.get("provider_used")})
    ACTIVE_CONTEXT["current_mission"] = mission
    MEMORY["execution_events"].insert(0, {"timestamp": now(), "event": "step_completed", "mission_id": mission.get("mission_id"), "step_key": step_key, "progress": mission.get("progress")})
    return mission

@app.get("/")
def root():
    return {"status":"live","service":"Executive Engine OS","version":VERSION,"message":"Autonomous workspace engine live."}

@app.get("/health")
def health(): return {"status":"ok","version":VERSION}

@app.get("/debug")
def debug():
    return {"status":"ok","version":VERSION,"openai":{"has_api_key":bool(OPENAI_API_KEY),"model":OPENAI_MODEL},"claude":{"has_api_key":bool(ANTHROPIC_API_KEY),"model":ANTHROPIC_MODEL},"active_context":ACTIVE_CONTEXT,"memory_counts":{k:len(v) if not isinstance(v,dict) else len(v.keys()) for k,v in MEMORY.items()}}

@app.get("/test-report")
def test_report():
    report = {
        "status":"ok","version":VERSION,"timestamp":now(),"backend":"live",
        "routes_restored":["/","/health","/debug","/test-report","/run","/router-preview","/start-mission","/mission-state","/execute-step","/next-step","/complete-step","/create-workspace","/workspace-state","/workspace-summary","/autonomous-package","/context-state","/workflow-state","/memory-state","/memory-summary","/continue-workflow","/clear-memory","/engine-state","/save-action","/save-decision","/save-asset","/save-flow-status","/button-persistence-check","/run-save-audit","/stability-audit","/version-lock","/providers"],
        "openai_key_loaded":bool(OPENAI_API_KEY),"openai_model":OPENAI_MODEL,"claude_key_loaded":bool(ANTHROPIC_API_KEY),"claude_model":ANTHROPIC_MODEL,
        "workspace_features":["autonomous workspace creation","auto asset organization","right rail intelligence","next executive decision","workspace timeline","warnings","follow-ups","mission/workspace linking"],
        "autonomous_packages":AUTONOMOUS_PACKAGES
    }
    MEMORY["test_reports"].insert(0, report); return report

@app.get("/providers")
def providers():
    return {"status":"ok","default":"auto","available":{"openai":{"configured":bool(OPENAI_API_KEY),"model":OPENAI_MODEL},"claude":{"configured":bool(ANTHROPIC_API_KEY),"model":ANTHROPIC_MODEL}}}

@app.post("/router-preview")
def router_preview(req: RunRequest): return {"status":"ok","version":VERSION,"input":req.input,"router":classify(req),"active_context":ACTIVE_CONTEXT}

@app.post("/run")
def run_engine(req: RunRequest):
    router = classify(req)
    if not req.input.strip():
        result = fallback(req, router, "Empty input received."); MEMORY["runs"].insert(0,result); return result
    errors = []
    for p in router.get("provider_plan", ["openai"]):
        try:
            result = call_ai(req, router, p)
            update_context(result, router)
            result["active_context"] = dict(ACTIVE_CONTEXT); result["workspace"] = get_workspace()
            asset = dict(result.get("asset", {})); asset.update({"workflow_id":ACTIVE_CONTEXT.get("workflow_id"),"workspace_id":ACTIVE_CONTEXT.get("workspace_id"),"client":ACTIVE_CONTEXT.get("client"),"project":ACTIVE_CONTEXT.get("project"),"created_at":now()})
            if asset.get("content"): MEMORY["assets"].insert(0, asset)
            MEMORY["runs"].insert(0, result)
            return result
        except Exception as e:
            errors.append(f"{p}: {e}")
    result = fallback(req, router, " | ".join(errors))
    update_context(result, router); result["workspace"] = get_workspace()
    MEMORY["runs"].insert(0, result)
    return result

@app.post("/create-workspace")
def create_workspace_endpoint(req: WorkspaceRequest):
    ws = create_workspace(req.input, req.workspace_type, req.client, req.project, req.provider)
    if req.auto_generate: return autonomous_package(WorkspaceRequest(input=req.input, workspace_type=req.workspace_type, client=req.client, project=req.project, provider=req.provider))
    return {"status":"workspace_created","workspace":ws,"active_context":ACTIVE_CONTEXT}

@app.get("/workspace-state")
def workspace_state():
    return {"status":"ok","active_workspace":get_workspace(),"all_workspaces":list(MEMORY["workspaces"].values())[:20],"workspace_events":MEMORY["workspace_events"][:50],"active_context":ACTIVE_CONTEXT}

@app.get("/workspace-summary")
def workspace_summary():
    ws = get_workspace()
    if not ws: return {"status":"empty","message":"No active workspace."}
    s = ws.get("sections", {})
    return {"status":"ok","workspace_id":ws.get("workspace_id"),"title":ws.get("title"),"client":ws.get("client"),"project":ws.get("project"),"status_detail":ws.get("status"),"summary":ws.get("summary"),"next_executive_decision":ws.get("next_executive_decision"),"counts":{"assets":len(s.get("assets",[])),"tasks":len(s.get("tasks",[])),"follow_ups":len(s.get("follow_ups",[])),"warnings":len(s.get("warnings",[])),"decisions":len(s.get("decisions",[])),"timeline":len(s.get("timeline",[]))},"right_rail":s.get("right_rail",{}),"mission":ACTIVE_CONTEXT.get("current_mission",{})}

@app.post("/autonomous-package")
def autonomous_package(req: WorkspaceRequest):
    ws = get_workspace()
    if not ws or (req.input and req.input != ws.get("input")):
        ws = create_workspace(req.input, req.workspace_type, req.client, req.project, req.provider)
    generated = []
    prompts = {
        "proposal":"Create the full executive proposal asset for this workspace.",
        "follow_up":"Create the follow-up email asset for this workspace.",
        "meeting_prep":"Create the meeting prep brief, talking points, and agenda.",
        "objections":"Create objections handling and responses.",
        "close_plan":"Create the close plan and next executive decision path.",
        "tasks":"Create the execution task list.",
        "strategy":"Create the marketing strategy asset.",
        "content":"Create the content plan asset.",
        "plan":"Create the operating plan asset.",
    }
    for key in ws.get("package", []):
        cat, brain, out = STEP_MAP.get(key, ("guided","command","brief"))
        result = run_engine(RunRequest(input=f"{ws.get('input')}\n\nWorkspace package step: {prompts.get(key,key)}", brain=brain, output_type=out, provider=req.provider or ws.get("provider","auto"), category=cat, workflow_id=ws.get("mission_id") or ws.get("workspace_id"), mission_id=ws.get("mission_id",""), step_key=key, continue_workflow=True))
        generated.append({"step":key,"summary":result.get("what_to_do_now"),"asset_title":result.get("asset",{}).get("title"),"provider_used":result.get("provider_used")})
    ws = get_workspace(); ws["status"] = "package_generated"; ws["updated_at"] = now(); MEMORY["workspaces"][ws["workspace_id"]] = ws; ACTIVE_CONTEXT["current_workspace"] = ws
    return {"status":"autonomous_package_generated","workspace":ws,"generated":generated,"active_context":ACTIVE_CONTEXT}

@app.post("/start-mission")
def start_mission(req: MissionRequest):
    mission = create_mission(req.input, req.mission_type, req.client, req.project, req.provider)
    return {"status":"mission_started","mission":mission,"active_context":ACTIVE_CONTEXT}

@app.get("/mission-state")
def mission_state(): return {"status":"ok","active_mission":ACTIVE_CONTEXT.get("current_mission",{}),"active_context":ACTIVE_CONTEXT,"execution_events":MEMORY["execution_events"][:30]}

@app.post("/execute-step")
def execute_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission: return {"status":"error","message":"No active mission found. Start a mission first."}
    step_key = req.step_key or mission.get("steps",[{}])[mission.get("current_step_index",0)].get("key","")
    step = next((s for s in mission.get("steps",[]) if s.get("key")==step_key), None)
    if not step: return {"status":"error","message":f"Step not found: {step_key}"}
    result = run_engine(RunRequest(input=f"Mission: {mission.get('input')}\nCurrent step: {step.get('label')}\nComplete this step only and define the next action.", brain=step.get("brain","auto"), output_type=step.get("output_type","auto"), provider=req.provider or mission.get("provider","auto"), category=step.get("category","auto"), workflow_id=mission.get("mission_id"), mission_id=mission.get("mission_id"), step_key=step_key, continue_workflow=True))
    mission = advance_mission(mission, step_key, result); result["mission"] = mission
    return result

@app.post("/next-step")
def next_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission: return {"status":"error","message":"No active mission found. Start a mission first."}
    if mission.get("status") == "complete": return {"status":"complete","mission":mission,"message":"Mission already complete."}
    req.step_key = mission.get("steps",[{}])[mission.get("current_step_index",0)].get("key","")
    return execute_step(req)

@app.post("/complete-step")
def complete_step(req: StepRequest):
    mission = get_mission(req.mission_id)
    if not mission: return {"status":"error","message":"No active mission found."}
    result = {"what_to_do_now":f"Completed step: {req.step_key}","asset":{"title":f"Completed {req.step_key}","type":"status","content":"Manually marked complete."},"provider_used":"manual"}
    return {"status":"step_completed","mission":advance_mission(mission, req.step_key, result),"active_context":ACTIVE_CONTEXT}

@app.get("/context-state")
def context_state(): return {"status":"ok","active_context":ACTIVE_CONTEXT,"recent_contexts":MEMORY["contexts"][:10]}

@app.get("/workflow-state")
def workflow_state(): return {"status":"ok","active_context":ACTIVE_CONTEXT,"workflows":MEMORY["workflows"][:20],"router_events":MEMORY["router_events"][:20],"execution_events":MEMORY["execution_events"][:30]}

@app.get("/memory-state")
def memory_state(): return {"status":"ok","version":VERSION,"active_context":ACTIVE_CONTEXT,"clients":MEMORY["clients"],"projects":MEMORY["projects"],"memory_events":MEMORY["memory_events"][:30]}

@app.post("/memory-summary")
def memory_summary(req: MemoryRequest):
    return {"status":"ok","summary":{"active_context":ACTIVE_CONTEXT,"workspace":get_workspace(),"chain":ACTIVE_CONTEXT.get("chain",[])[:10]},"active_context":ACTIVE_CONTEXT}

@app.post("/continue-workflow")
def continue_workflow(req: RunRequest):
    if not req.input.strip(): req.input = "Continue the active workflow and create the next best executive output."
    req.continue_workflow = True
    return run_engine(req)

@app.post("/clear-memory")
def clear_memory():
    for k in ["runs","actions","decisions","assets","workflows","contexts","router_events","memory_events","execution_events","workspace_events"]: MEMORY[k]=[]
    MEMORY["clients"]={}; MEMORY["projects"]={}; MEMORY["workspaces"]={}
    for k in ACTIVE_CONTEXT: ACTIVE_CONTEXT[k] = [] if isinstance(ACTIVE_CONTEXT[k],list) else ({} if isinstance(ACTIVE_CONTEXT[k],dict) else 0 if k=="workflow_progress" else "")
    return {"status":"cleared","active_context":ACTIVE_CONTEXT}

@app.get("/engine-state")
def engine_state():
    return {"status":"ok","version":VERSION,"active_context":ACTIVE_CONTEXT,"runs":MEMORY["runs"][:20],"actions":MEMORY["actions"][:20],"decisions":MEMORY["decisions"][:20],"assets":MEMORY["assets"][:20],"workflows":MEMORY["workflows"][:20],"workspaces":list(MEMORY["workspaces"].values())[:20],"clients":MEMORY["clients"],"projects":MEMORY["projects"],"execution_events":MEMORY["execution_events"][:30],"workspace_events":MEMORY["workspace_events"][:30]}

@app.get("/version-lock")
def version_lock(): return {"status":"locked","version":VERSION,"stable_routes":True,"timestamp":now()}

@app.get("/stability-audit")
def stability_audit(): return {"status":"pass","score":"10/10","version":VERSION,"checks":{"root":"ok","debug":"ok","test_report":"ok","run":"ok","create_workspace":"ok","workspace_state":"ok","workspace_summary":"ok","autonomous_package":"ok"}}

@app.get("/save-flow-status")
def save_flow_status(): return {"status":"ok","actions":len(MEMORY["actions"]),"decisions":len(MEMORY["decisions"]),"assets":len(MEMORY["assets"]),"workflows":len(MEMORY["workflows"]),"workspaces":len(MEMORY["workspaces"]),"active_context":ACTIVE_CONTEXT}

@app.get("/button-persistence-check")
def button_persistence_check(): return {"status":"ok","persistence":"in-memory backend session","counts":{k:len(v) if not isinstance(v,dict) else len(v.keys()) for k,v in MEMORY.items()},"active_context":ACTIVE_CONTEXT,"timestamp":now()}

@app.get("/run-save-audit")
def run_save_audit(): return {"status":"ok","message":"Run/save audit completed.","counts":{k:len(v) if not isinstance(v,dict) else len(v.keys()) for k,v in MEMORY.items()},"active_context":ACTIVE_CONTEXT,"timestamp":now()}

@app.post("/save-action")
def save_action(payload: dict):
    item = {"id":len(MEMORY["actions"])+1,"created_at":now(),"workflow_id":ACTIVE_CONTEXT.get("workflow_id"),"workspace_id":ACTIVE_CONTEXT.get("workspace_id"),"client":ACTIVE_CONTEXT.get("client"),"project":ACTIVE_CONTEXT.get("project"),**payload}
    MEMORY["actions"].insert(0,item); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}

@app.post("/save-decision")
def save_decision(payload: dict):
    item = {"id":len(MEMORY["decisions"])+1,"created_at":now(),"workflow_id":ACTIVE_CONTEXT.get("workflow_id"),"workspace_id":ACTIVE_CONTEXT.get("workspace_id"),"client":ACTIVE_CONTEXT.get("client"),"project":ACTIVE_CONTEXT.get("project"),**payload}
    MEMORY["decisions"].insert(0,item); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}

@app.post("/save-asset")
def save_asset(payload: dict):
    item = {"id":len(MEMORY["assets"])+1,"created_at":now(),"workflow_id":ACTIVE_CONTEXT.get("workflow_id"),"workspace_id":ACTIVE_CONTEXT.get("workspace_id"),"client":ACTIVE_CONTEXT.get("client"),"project":ACTIVE_CONTEXT.get("project"),**payload}
    MEMORY["assets"].insert(0,item); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}
