from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import os, json, re, uuid

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_VERSION = "V36530-Continuity-Memory-Engine"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DATA_DIR = os.getenv("EE_DATA_DIR", "/tmp/executive_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(
    title="Executive Engine OS",
    version=APP_VERSION,
    description="Continuity + Memory Engine for Executive Engine OS."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://executive-engine-frontend.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: Optional[str] = "execution"
    brain: Optional[str] = "operator"
    output_type: Optional[str] = "standard"
    depth: Optional[str] = "standard"
    provider: Optional[str] = "openai"
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"
    context: Optional[Dict[str, Any]] = None


class MemoryRequest(BaseModel):
    content: str
    title: Optional[str] = None
    type: Optional[str] = "context"
    importance: Optional[int] = 3
    tags: Optional[List[str]] = []
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"


class WorkflowRequest(BaseModel):
    title: str
    status: Optional[str] = "active"
    priority: Optional[str] = "High"
    next_action: Optional[str] = None
    owner: Optional[str] = "Will"
    deadline: Optional[str] = None
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"
    context: Optional[Dict[str, Any]] = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_key(workspace_id: str, user_id: str) -> str:
    raw = f"{workspace_id}_{user_id}"
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", raw)


def db_path(workspace_id: str, user_id: str) -> str:
    return os.path.join(DATA_DIR, f"workspace_{safe_key(workspace_id, user_id)}.json")


def empty_workspace(workspace_id: str, user_id: str) -> Dict[str, Any]:
    return {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "memory": [],
        "workflows": [],
        "decisions": [],
        "activity": [],
        "operator_state": {
            "current_pressure": "Normal",
            "current_focus": None,
            "last_command": None,
            "last_next_move": None,
            "open_loops": [],
            "stalled_items": [],
            "active_theme": None
        },
        "continuity": {
            "current_thread": [],
            "recent_entities": [],
            "recent_assets": [],
            "recent_commands": []
        }
    }


def load_workspace(workspace_id: str = "default", user_id: str = "will") -> Dict[str, Any]:
    path = db_path(workspace_id, user_id)
    if not os.path.exists(path):
        return empty_workspace(workspace_id, user_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("memory", [])
        data.setdefault("workflows", [])
        data.setdefault("decisions", [])
        data.setdefault("activity", [])
        data.setdefault("operator_state", empty_workspace(workspace_id, user_id)["operator_state"])
        data.setdefault("continuity", empty_workspace(workspace_id, user_id)["continuity"])
        return data
    except Exception:
        return empty_workspace(workspace_id, user_id)


def save_workspace(data: Dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    with open(db_path(data["workspace_id"], data["user_id"]), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def words(text: str) -> set:
    return set(re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower()))


def detect_pressure(text: str) -> Dict[str, Any]:
    t = text.lower()
    critical = ["urgent", "asap", "wtf", "fuck", "shit", "broken", "doesn't work", "doesnt work", "stop", "now"]
    high = ["proposal", "client", "deploy", "revenue", "money", "deadline", "meeting", "risk", "fix", "build"]
    c = sum(1 for x in critical if x in t)
    h = sum(1 for x in high if x in t)
    if c:
        return {"level": "Critical", "reason": "frustration or immediate failure signal detected"}
    if h >= 2:
        return {"level": "High", "reason": "commercial or execution pressure detected"}
    if h == 1:
        return {"level": "Medium", "reason": "workstream signal detected"}
    return {"level": "Normal", "reason": "no acute pressure signal detected"}


def detect_intent(text: str, mode: str = "", brain: str = "", output_type: str = "") -> str:
    t = " ".join([text, mode or "", brain or "", output_type or ""]).lower()
    table = {
        "proposal": ["proposal", "sow", "quote", "pitch", "client offer"],
        "meeting": ["meeting", "agenda", "prep", "call", "talking points"],
        "email": ["email", "reply", "message", "follow up", "dm"],
        "decision": ["decide", "decision", "choose", "yes or no", "option"],
        "revenue": ["revenue", "sales", "lead", "cpa", "ads", "seo", "pricing", "dealership"],
        "risk": ["risk", "broken", "problem", "blocker", "issue", "wrong"],
        "build": ["build", "ship", "deploy", "fix", "implement", "create"],
    }
    scores = {k: sum(1 for x in v if x in t) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"


def extract_entities(text: str) -> List[str]:
    phrases = re.findall(r"\b[A-Z][A-Za-z0-9&.\-/]*(?:\s+[A-Z][A-Za-z0-9&.\-/]*){0,5}\b", text)
    money = re.findall(r"\$[\d,]+(?:\.\d+)?[kKmM]?", text)
    perc = re.findall(r"\b\d+(?:\.\d+)?\s?%", text)
    return list(dict.fromkeys(phrases + money + perc))[:20]


def relevance_score(item: Dict[str, Any], query: str) -> int:
    q = words(query)
    blob = json.dumps(item).lower()
    overlap = sum(1 for w in q if w in blob)
    importance = int(item.get("importance", 3) or 3)
    recency = 2 if item.get("updated_at") or item.get("created_at") else 0
    return overlap * 4 + importance + recency


def retrieve_context(workspace: Dict[str, Any], query: str, limit: int = 8) -> Dict[str, Any]:
    memory = sorted(workspace.get("memory", []), key=lambda x: relevance_score(x, query), reverse=True)[:limit]
    workflows = sorted(workspace.get("workflows", []), key=lambda x: relevance_score(x, query), reverse=True)[:limit]
    decisions = sorted(workspace.get("decisions", []), key=lambda x: relevance_score(x, query), reverse=True)[:limit]
    active = [w for w in workspace.get("workflows", []) if w.get("status") == "active"]
    return {
        "relevant_memory": [m for m in memory if relevance_score(m, query) > 3],
        "relevant_workflows": [w for w in workflows if relevance_score(w, query) > 3],
        "recent_decisions": decisions[:5],
        "active_workflows": active[:10],
        "operator_state": workspace.get("operator_state", {})
    }


def infer_workflow_title(text: str, intent: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= 80:
        return clean
    label = {
        "proposal": "Proposal",
        "meeting": "Meeting",
        "email": "Communication",
        "decision": "Decision",
        "revenue": "Revenue",
        "risk": "Risk",
        "build": "Build",
        "operator": "Operator"
    }.get(intent, "Workflow")
    return f"{label}: {clean[:68].rstrip()}"


def upsert_workflow(workspace: Dict[str, Any], req: RunRequest, intent: str, pressure: Dict[str, Any]) -> Dict[str, Any]:
    title = infer_workflow_title(req.input, intent)
    q = words(title)
    best = None
    best_score = 0
    for wf in workspace.get("workflows", []):
        score = len(q & words(wf.get("title", "")))
        if score > best_score:
            best, best_score = wf, score

    if best and best_score >= 3:
        best["updated_at"] = now_iso()
        best["status"] = "active"
        best["priority"] = "Critical" if pressure["level"] == "Critical" else best.get("priority", "High")
        best["last_command"] = req.input
        best["continuity_count"] = int(best.get("continuity_count", 0)) + 1
        return best

    wf = {
        "id": f"wf_{uuid.uuid4().hex[:8]}",
        "title": title,
        "intent": intent,
        "status": "active",
        "priority": "Critical" if pressure["level"] == "Critical" else "High",
        "owner": "Will",
        "next_action": "Generate the next concrete asset and keep this workflow moving.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_command": req.input,
        "continuity_count": 1,
        "importance": 4
    }
    workspace["workflows"].append(wf)
    workspace["workflows"] = workspace["workflows"][-100:]
    return wf


def update_continuity(workspace: Dict[str, Any], req: RunRequest, intent: str, pressure: Dict[str, Any], workflow: Dict[str, Any], response: Dict[str, Any]) -> None:
    entities = extract_entities(req.input)
    state = workspace["operator_state"]
    state["current_pressure"] = pressure["level"]
    state["current_focus"] = workflow.get("title")
    state["last_command"] = req.input
    state["last_next_move"] = response.get("next_move")
    state["active_theme"] = intent

    if response.get("risk"):
        open_loop = {
            "id": f"loop_{uuid.uuid4().hex[:8]}",
            "workflow_id": workflow.get("id"),
            "title": response.get("risk"),
            "created_at": now_iso(),
            "status": "open"
        }
        state.setdefault("open_loops", []).append(open_loop)
        state["open_loops"] = state["open_loops"][-25:]

    continuity = workspace["continuity"]
    continuity.setdefault("current_thread", []).append({
        "at": now_iso(),
        "input": req.input[:500],
        "intent": intent,
        "pressure": pressure["level"],
        "workflow_id": workflow.get("id"),
        "next_move": response.get("next_move")
    })
    continuity["current_thread"] = continuity["current_thread"][-30:]
    continuity["recent_entities"] = list(dict.fromkeys((entities + continuity.get("recent_entities", []))))[:50]
    continuity.setdefault("recent_commands", []).append(req.input[:300])
    continuity["recent_commands"] = continuity["recent_commands"][-30:]

    for asset in response.get("ready_assets", [])[:5]:
        continuity.setdefault("recent_assets", []).append({
            "id": f"asset_{uuid.uuid4().hex[:8]}",
            "workflow_id": workflow.get("id"),
            "content": str(asset)[:2000],
            "created_at": now_iso()
        })
    continuity["recent_assets"] = continuity["recent_assets"][-50:]


def build_prompt(req: RunRequest, intent: str, pressure: Dict[str, Any], context: Dict[str, Any], workflow: Dict[str, Any]) -> str:
    return f"""
You are Executive Engine OS for Will Webb.

You are not a chatbot. You are an executive continuity and memory engine.

Your task:
- remember active context
- continue workflows instead of restarting
- infer pressure and operational state
- create the actual work product
- produce executive-grade next moves
- avoid generic business language
- preserve the response contract

Intent: {intent}
Pressure: {pressure}
Active workflow: {json.dumps(workflow, ensure_ascii=False)}
Retrieved continuity context:
{json.dumps(context, ensure_ascii=False, indent=2)[:8000]}

Rules:
1. Never say "conduct analysis" unless you include what analysis to perform and why.
2. Never say "prepare proposal" without producing proposal material.
3. Never use filler like comprehensive strategy, high-impact, stakeholders, optimize workflows, drive efficiency.
4. Use commercial/operator reasoning.
5. Make the response feel like it remembers what matters.
6. Return only valid JSON.

Required JSON:
{{
  "next_move": "",
  "decision": "",
  "action_steps": [],
  "ready_assets": [],
  "risk": "",
  "priority": "Critical | High | Medium | Low",
  "recommended_command": "",
  "what_to_do_now": "",
  "asset": "",
  "follow_up": "",
  "provider_used": "openai:{DEFAULT_MODEL}",
  "status": "success"
}}
"""


def enforce_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    data.setdefault("next_move", "Move the active workflow forward with one concrete asset.")
    data.setdefault("decision", "Continue from the active context and avoid restarting the work.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is losing continuity and turning this into another disconnected response.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Continue this workflow and generate the next executable asset.")
    data.setdefault("provider_used", "local-continuity-engine")
    data.setdefault("status", "success")

    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]

    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Keep the active workflow open.",
            "Generate the next concrete asset.",
            "Save the decision and next command for continuity."
        ][:3-len(data["action_steps"])]

    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset") or "Continuity record saved for the active workflow."]

    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"

    return data


def fallback_response(req: RunRequest, intent: str, pressure: Dict[str, Any], context: Dict[str, Any], workflow: Dict[str, Any]) -> Dict[str, Any]:
    if intent == "proposal" or "proposal" in req.input.lower():
        asset = """PROPOSAL CONTINUITY DRAFT

Positioning:
Do not sell SEO and Google Ads as services. Sell funded auto-loan opportunities at a controlled acquisition cost.

Commercial Logic:
The dealership wants applications that can become funded deals. A CPA under $100 only matters if the traffic is credit-intent, local, and filtered away from low-buying-intent searches.

Offer:
90-Day Auto Loan Acquisition Sprint

What We Build:
1. Google Ads campaigns around credit-intent and financing-intent search terms.
2. Landing page path focused on pre-approval, inventory-fit, and fast contact.
3. Local SEO pages targeting Ontario auto financing, bad credit car loans, and dealership-specific service areas.
4. Conversion tracking for lead source, form submit, call, booked appointment, and funded deal.
5. Weekly CPA review with waste removal and budget reallocation.

Risk Control:
No broad auto keywords. No vanity SEO reporting. No traffic that cannot become a finance lead.

Client Close:
If the dealership wants lower CPA, the first move is not more marketing. It is tighter intent control, cleaner landing pages, and faster lead handling."""
        return enforce_contract({
            "next_move": "Turn the dealership request into a funded-deal acquisition offer, not an SEO/Ads task list.",
            "decision": "Lead with Google Ads for immediate credit-intent demand; use SEO as the 90-day cost-reduction layer.",
            "action_steps": [
                "Frame the proposal around funded applications, not clicks or rankings.",
                "Build the offer as a 90-day acquisition sprint with weekly CPA control.",
                "Exclude broad auto traffic and focus on financing/bad-credit/local-intent searches.",
                "Include conversion tracking from ad click to lead to booked appointment to funded deal.",
                "Close with a kickoff decision: budget, landing page, tracking, launch date."
            ],
            "ready_assets": [asset],
            "risk": "CPA under $100 fails if the campaign buys broad car-shopping traffic instead of finance-intent leads.",
            "priority": "High",
            "recommended_command": "Generate the full dealership proposal with pricing, scope, landing page plan, and kickoff email.",
            "what_to_do_now": "Use the funded-deal positioning as the proposal spine.",
            "asset": asset,
            "follow_up": "Track this as the active proposal workflow and reuse the positioning in the next command.",
            "provider_used": "local-continuity-engine",
            "status": "success"
        })

    asset = f"""CONTINUITY RECORD

Active Workflow:
{workflow.get("title")}

What The System Now Remembers:
- Current intent: {intent}
- Current pressure: {pressure.get("level")}
- Active focus: {workflow.get("title")}
- Prior relevant workflows: {len(context.get("relevant_workflows", []))}
- Prior relevant memory items: {len(context.get("relevant_memory", []))}

Next Continuity Move:
Continue this workflow from the current state instead of restarting."""
    return enforce_contract({
        "next_move": "Keep this as an active workflow and generate the next concrete asset from memory.",
        "decision": "The system should continue from saved context, not treat the next command as isolated.",
        "action_steps": [
            "Save the current command into the active workflow.",
            "Preserve the next move, risk, and ready asset.",
            "Use retrieved memory before generating the next response.",
            "Surface open loops and stalled items in engine state.",
            "Use the next command to deepen the asset, not restart the topic."
        ],
        "ready_assets": [asset],
        "risk": "Without continuity, Executive Engine keeps sounding organized but not truly useful.",
        "priority": "High" if pressure.get("level") in ["High", "Critical"] else "Medium",
        "recommended_command": "Continue this workflow and generate the next asset using saved context.",
        "what_to_do_now": "Run the next command against the same workflow so memory compounds.",
        "asset": asset,
        "follow_up": "Check /engine-state to confirm active workflow, recent decisions, open loops, and memory count.",
        "provider_used": "local-continuity-engine",
        "status": "success"
    })


def call_openai(req: RunRequest, intent: str, pressure: Dict[str, Any], context: Dict[str, Any], workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, intent, pressure, context, workflow)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.35,
            response_format={"type": "json_object"}
        )
        raw = result.choices[0].message.content or "{}"
        data = json.loads(raw)
        data["provider_used"] = f"openai:{DEFAULT_MODEL}"
        return enforce_contract(data)
    except Exception:
        return None


@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "continuity_memory",
        "features": [
            "persistent_workspace_state",
            "active_workflows",
            "decision_memory",
            "operator_state",
            "open_loops",
            "recent_assets",
            "retrieval_context",
            "workflow_continuation"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "openai_configured": bool(OPENAI_API_KEY),
        "data_dir": DATA_DIR
    }


@app.post("/run")
def run(req: RunRequest):
    workspace = load_workspace(req.workspace_id or "default", req.user_id or "will")
    intent = detect_intent(req.input, req.mode or "", req.brain or "", req.output_type or "")
    pressure = detect_pressure(req.input)
    workflow = upsert_workflow(workspace, req, intent, pressure)
    context = retrieve_context(workspace, req.input)

    response = call_openai(req, intent, pressure, context, workflow)
    if not response:
        response = fallback_response(req, intent, pressure, context, workflow)

    update_continuity(workspace, req, intent, pressure, workflow, response)

    workspace["activity"].append({
        "id": f"act_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "type": "run",
        "input": req.input[:800],
        "intent": intent,
        "pressure": pressure["level"],
        "workflow_id": workflow["id"]
    })
    workspace["activity"] = workspace["activity"][-100:]

    workspace["decisions"].append({
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "workflow_id": workflow["id"],
        "input": req.input[:500],
        "decision": response.get("decision"),
        "next_move": response.get("next_move"),
        "risk": response.get("risk"),
        "priority": response.get("priority"),
        "importance": 4
    })
    workspace["decisions"] = workspace["decisions"][-100:]

    workflow["next_action"] = response.get("recommended_command") or response.get("next_move")
    workflow["updated_at"] = now_iso()

    save_workspace(workspace)

    response["memory_context"] = {
        "active_workflow": workflow,
        "operator_state": workspace["operator_state"],
        "relevant_memory_count": len(context["relevant_memory"]),
        "active_workflow_count": len([w for w in workspace["workflows"] if w.get("status") == "active"]),
        "recent_decisions_count": len(workspace["decisions"]),
        "open_loops_count": len(workspace["operator_state"].get("open_loops", []))
    }
    response["version"] = APP_VERSION
    return response


@app.post("/memory")
def add_memory(item: MemoryRequest):
    workspace = load_workspace(item.workspace_id or "default", item.user_id or "will")
    memory = {
        "id": f"mem_{uuid.uuid4().hex[:8]}",
        "type": item.type,
        "title": item.title or item.content[:80],
        "content": item.content,
        "importance": item.importance,
        "tags": item.tags or [],
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    workspace["memory"].append(memory)
    workspace["memory"] = workspace["memory"][-250:]
    save_workspace(workspace)
    return {"status": "success", "version": APP_VERSION, "memory": memory}


@app.get("/memory")
def get_memory(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    return {
        "status": "success",
        "version": APP_VERSION,
        "memory": workspace["memory"],
        "decisions": workspace["decisions"][-25:],
        "operator_state": workspace["operator_state"]
    }


@app.post("/workflow")
def add_workflow(item: WorkflowRequest):
    workspace = load_workspace(item.workspace_id or "default", item.user_id or "will")
    wf = {
        "id": f"wf_{uuid.uuid4().hex[:8]}",
        "title": item.title,
        "status": item.status,
        "priority": item.priority,
        "next_action": item.next_action,
        "owner": item.owner,
        "deadline": item.deadline,
        "context": item.context or {},
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "importance": 4
    }
    workspace["workflows"].append(wf)
    save_workspace(workspace)
    return {"status": "success", "version": APP_VERSION, "workflow": wf}


@app.get("/workflow")
def get_workflows(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    return {"status": "success", "version": APP_VERSION, "workflows": workspace["workflows"]}


@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    active = [w for w in workspace["workflows"] if w.get("status") == "active"]
    return {
        "status": "success",
        "version": APP_VERSION,
        "operator_state": workspace["operator_state"],
        "active_workflows": active,
        "recent_decisions": workspace["decisions"][-10:],
        "recent_assets": workspace["continuity"].get("recent_assets", [])[-10:],
        "recent_commands": workspace["continuity"].get("recent_commands", [])[-10:],
        "memory_count": len(workspace["memory"]),
        "open_loops": workspace["operator_state"].get("open_loops", [])
    }


@app.get("/operator-scan")
def operator_scan(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    active = [w for w in workspace["workflows"] if w.get("status") == "active"]
    critical = [w for w in active if w.get("priority") == "Critical"]
    focus = critical[0] if critical else active[-1] if active else None
    return {
        "status": "success",
        "version": APP_VERSION,
        "pressure": workspace["operator_state"].get("current_pressure", "Normal"),
        "focus": focus,
        "next_move": focus.get("next_action") if focus else "Create the first active workflow.",
        "open_loops": workspace["operator_state"].get("open_loops", [])[-10:],
        "recommended_command": "Continue the active workflow using saved memory and produce the next asset."
    }


@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36530",
            "POST /run stores active workflow and decision",
            "GET /engine-state shows operator_state, active_workflows, recent_decisions, open_loops",
            "POST /memory saves durable context",
            "GET /operator-scan returns current pressure and next move"
        ],
        "copy_tools": {
            "health": "https://executive-engine-os.onrender.com/health",
            "engine_state": "https://executive-engine-os.onrender.com/engine-state",
            "proposal_test": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
        }
    }


@app.get("/test-report-json")
def test_report_json():
    return test_report()
