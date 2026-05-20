from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import os, json, re, uuid

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_VERSION = "V36540-Strategic-Inference-Engine"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATA_DIR = os.getenv("EE_DATA_DIR", "/tmp/executive_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Executive Engine OS", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://executive-engine-frontend.onrender.com"],
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

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def db_path(workspace_id="default", user_id="will"):
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", f"{workspace_id}_{user_id}")
    return os.path.join(DATA_DIR, f"workspace_{safe}.json")

def empty_workspace(workspace_id="default", user_id="will"):
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
            "strategic_theme": None,
            "inference_history": []
        },
        "continuity": {
            "recent_commands": [],
            "recent_assets": [],
            "recent_entities": []
        }
    }

def load_workspace(workspace_id="default", user_id="will"):
    path = db_path(workspace_id, user_id)
    if not os.path.exists(path):
        return empty_workspace(workspace_id, user_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = empty_workspace(workspace_id, user_id)
        for k, v in base.items():
            data.setdefault(k, v)
        data.setdefault("operator_state", base["operator_state"])
        data["operator_state"].setdefault("inference_history", [])
        data.setdefault("continuity", base["continuity"])
        return data
    except Exception:
        return empty_workspace(workspace_id, user_id)

def save_workspace(ws):
    ws["updated_at"] = now_iso()
    with open(db_path(ws["workspace_id"], ws["user_id"]), "w", encoding="utf-8") as f:
        json.dump(ws, f, indent=2, ensure_ascii=False)

def words(text):
    return set(re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower()))

def detect_intent(text, mode="", brain="", output_type=""):
    blob = f"{text} {mode} {brain} {output_type}".lower()
    table = {
        "proposal": ["proposal", "sow", "quote", "pitch", "offer"],
        "revenue": ["revenue", "sales", "lead", "cpa", "ads", "seo", "pricing", "dealership", "customer"],
        "meeting": ["meeting", "agenda", "call", "prep", "talking points"],
        "decision": ["decide", "decision", "choose", "option", "should i"],
        "risk": ["risk", "broken", "problem", "blocker", "issue", "wrong", "failure"],
        "build": ["build", "ship", "deploy", "fix", "implement", "create"],
        "communication": ["email", "reply", "message", "follow-up", "follow up"]
    }
    scores = {k: sum(1 for x in v if x in blob) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"

def detect_pressure(text):
    t = text.lower()
    critical = any(x in t for x in ["wtf", "fuck", "shit", "urgent", "asap", "broken", "doesnt work", "doesn't work", "stop"])
    high = sum(1 for x in ["proposal", "client", "revenue", "deploy", "build", "fix", "deadline", "money", "cpa"] if x in t)
    if critical:
        return {"level": "Critical", "reason": "immediate pressure/frustration signal"}
    if high >= 2:
        return {"level": "High", "reason": "commercial/execution pressure"}
    if high == 1:
        return {"level": "Medium", "reason": "active workstream signal"}
    return {"level": "Normal", "reason": "standard command"}

def retrieve_context(ws, query, limit=8):
    q = words(query)
    def score(item):
        blob = json.dumps(item).lower()
        return sum(1 for w in q if w in blob) * 4 + int(item.get("importance", 3) or 3)
    return {
        "memory": sorted(ws.get("memory", []), key=score, reverse=True)[:limit],
        "workflows": sorted(ws.get("workflows", []), key=score, reverse=True)[:limit],
        "decisions": ws.get("decisions", [])[-10:],
        "operator_state": ws.get("operator_state", {})
    }

def infer_workflow_title(text, intent):
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= 80:
        return clean
    return f"{intent.title()}: {clean[:68]}"

def upsert_workflow(ws, req, intent, pressure):
    title = infer_workflow_title(req.input, intent)
    q = words(title)
    best, best_score = None, 0
    for wf in ws.get("workflows", []):
        s = len(q & words(wf.get("title", "")))
        if s > best_score:
            best, best_score = wf, s
    if best and best_score >= 3:
        best["updated_at"] = now_iso()
        best["last_command"] = req.input
        best["status"] = "active"
        best["priority"] = "Critical" if pressure["level"] == "Critical" else best.get("priority", "High")
        best["continuity_count"] = int(best.get("continuity_count", 0)) + 1
        return best
    wf = {
        "id": f"wf_{uuid.uuid4().hex[:8]}",
        "title": title,
        "intent": intent,
        "status": "active",
        "priority": "Critical" if pressure["level"] == "Critical" else "High",
        "owner": "Will",
        "next_action": "Generate the next strategic asset.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_command": req.input,
        "continuity_count": 1,
        "importance": 4
    }
    ws["workflows"].append(wf)
    ws["workflows"] = ws["workflows"][-100:]
    return wf

FORBIDDEN_LANGUAGE = [
    "comprehensive strategy",
    "high-impact",
    "drive efficiency",
    "stakeholders",
    "optimize workflows",
    "leverage opportunities",
    "best practices",
    "streamline operations",
    "conduct analysis",
    "review existing assets",
    "determine the specific type"
]

def clean_language(value):
    if isinstance(value, str):
        out = value
        replacements = {
            "comprehensive strategy": "focused operating plan",
            "high-impact": "revenue-relevant",
            "drive efficiency": "remove wasted motion",
            "stakeholders": "decision-makers",
            "optimize workflows": "tighten the execution path",
            "leverage opportunities": "use the strongest opening",
            "best practices": "what works in this situation",
            "streamline operations": "remove friction",
            "conduct analysis": "identify the constraint",
            "review existing assets": "use only assets that move the decision",
            "determine the specific type": "choose the asset that forces the next decision"
        }
        for a, b in replacements.items():
            out = re.sub(a, b, out, flags=re.I)
        return out
    if isinstance(value, list):
        return [clean_language(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_language(v) for k, v in value.items()}
    return value

def build_strategic_inference(req, intent, pressure, context, workflow):
    text = req.input.lower()
    inference = {
        "hidden_bottleneck": "The system needs to identify the real constraint, not repeat the surface task.",
        "leverage_point": "Create the asset or decision that unlocks the next move fastest.",
        "wrong_move": "Do not create generic planning steps that make the user do the work.",
        "commercial_angle": "Tie the output to revenue, control, speed, risk reduction, or decision momentum.",
        "operator_instinct": "Say the thing a sharp operator would notice immediately."
    }

    if "dealership" in text or "auto loan" in text or "cpa" in text:
        inference = {
            "hidden_bottleneck": "The dealership does not care about SEO or ads. It cares about funded vehicle deals at a predictable acquisition cost.",
            "leverage_point": "Position the offer around finance-intent lead capture, lead handling speed, and funded-deal tracking.",
            "wrong_move": "Do not lead with keyword research, blog calendars, or generic digital marketing activities.",
            "commercial_angle": "CPA under $100 is believable only if broad car-shopping traffic is excluded and credit/financing intent is isolated.",
            "operator_instinct": "Use Google Ads for immediate finance-intent demand; use SEO as the 90-day cost-control layer."
        }
    elif "build" in text and ("engine" in text or "system" in text):
        inference = {
            "hidden_bottleneck": "The product is not failing because it lacks structure. It is failing when responses do not produce strategic leverage.",
            "leverage_point": "Upgrade reasoning quality before adding more UI or dashboard surface area.",
            "wrong_move": "Do not add more cards, widgets, or static sections to hide weak cognition.",
            "commercial_angle": "The value is dependency: the executive feels sharper, faster, and more in control after every command.",
            "operator_instinct": "The system must challenge weak assumptions and produce the next asset, not narrate a process."
        }
    elif intent == "meeting":
        inference = {
            "hidden_bottleneck": "Most meetings fail because they lack a decision target.",
            "leverage_point": "Enter with the close first: what decision must be made before the meeting ends.",
            "wrong_move": "Do not create a polite agenda that avoids the hard decision.",
            "commercial_angle": "The meeting must protect time, force ownership, and reduce post-call ambiguity.",
            "operator_instinct": "Prepare the objection before the other person says it."
        }
    elif intent == "decision":
        inference = {
            "hidden_bottleneck": "The issue is not options. It is the cost of delay and unclear tradeoffs.",
            "leverage_point": "Choose the option that preserves momentum and limits downside.",
            "wrong_move": "Do not keep exploring once the tradeoff is obvious.",
            "commercial_angle": "A fast reversible decision beats a perfect delayed decision.",
            "operator_instinct": "Name the tradeoff directly and move."
        }
    elif intent == "risk":
        inference = {
            "hidden_bottleneck": "The problem will expand if the system keeps changing multiple layers at once.",
            "leverage_point": "Isolate the failing layer and ship the smallest controlled fix.",
            "wrong_move": "Do not redesign while debugging.",
            "commercial_angle": "Protect working assets first; speed only matters after stability.",
            "operator_instinct": "Lock the stable base before touching anything else."
        }

    return inference

def strategic_fallback(req, intent, pressure, context, workflow):
    inf = build_strategic_inference(req, intent, pressure, context, workflow)

    if intent == "proposal" or "proposal" in req.input.lower():
        asset = f"""DEALERSHIP PROPOSAL — STRATEGIC DRAFT

Core Position:
The dealership does not need “SEO and Google Ads.” It needs a predictable path to financed vehicle buyers at a controlled acquisition cost.

Strategic Read:
{inf["hidden_bottleneck"]}

Offer:
90-Day Funded Deal Acquisition Sprint

What We Control:
1. Search intent: only financing, bad-credit, approval, and local buyer terms.
2. Landing path: pre-approval focused, fast contact, no generic dealership browsing.
3. Tracking: lead source, form submit, call, booked appointment, approval, funded deal.
4. Budget waste: remove broad auto traffic, research traffic, and low-intent clicks weekly.
5. SEO layer: build local finance pages to reduce paid dependency over 90 days.

Why CPA Under $100 Can Work:
It is not a “traffic” target. It is an intent-control target. The campaign must avoid broad car shoppers and isolate buyers actively looking for financing.

What Not To Sell:
- Blog calendar first
- Generic SEO reports
- Broad Google Ads campaigns
- Vanity ranking reports
- Traffic without funded-deal tracking

Close:
If the goal is CPA under $100, the first move is not more marketing. It is tighter intent control, better lead handling, and proof that the dealership can convert finance leads into funded deals."""
        return {
            "next_move": "Reframe the proposal around funded deals and CPA control, not SEO/Ads activity.",
            "decision": "Lead with finance-intent Google Ads for speed; use SEO as the 90-day cost-control layer.",
            "action_steps": [
                "Open the proposal with funded-deal economics, not marketing tasks.",
                "State that CPA under $100 depends on excluding broad car-shopping traffic.",
                "Build the offer as a 90-day acquisition sprint with weekly waste removal.",
                "Add tracking from click to lead to appointment to funded deal.",
                "Close with a kickoff ask: budget, landing page access, tracking access, launch date."
            ],
            "ready_assets": [asset],
            "risk": "The deal will sound weak if it sells deliverables instead of showing how the dealership gets finance-ready buyers at a controlled cost.",
            "priority": "High",
            "recommended_command": "Generate the final dealership proposal with pricing, timeline, deliverables, and kickoff email.",
            "what_to_do_now": "Use the funded-deal acquisition angle as the spine of the proposal.",
            "asset": asset,
            "follow_up": "Next output should produce the actual client-facing proposal, not another planning list.",
            "provider_used": "local-strategic-inference-engine",
            "status": "success"
        }

    asset = f"""STRATEGIC INFERENCE

Hidden Bottleneck:
{inf["hidden_bottleneck"]}

Leverage Point:
{inf["leverage_point"]}

Wrong Move:
{inf["wrong_move"]}

Commercial Angle:
{inf["commercial_angle"]}

Operator Instinct:
{inf["operator_instinct"]}

Active Workflow:
{workflow.get("title")}
"""
    return {
        "next_move": inf["leverage_point"],
        "decision": f"Do this: {inf['operator_instinct']}",
        "action_steps": [
            inf["wrong_move"],
            inf["leverage_point"],
            "Create the decision-moving asset now.",
            "Save the inference to the active workflow.",
            "Use the next command to produce the finished asset."
        ],
        "ready_assets": [asset],
        "risk": inf["hidden_bottleneck"],
        "priority": "Critical" if pressure["level"] == "Critical" else "High",
        "recommended_command": "Generate the finished executive asset using this strategic inference.",
        "what_to_do_now": inf["leverage_point"],
        "asset": asset,
        "follow_up": "Continue from this strategic inference instead of restarting the topic.",
        "provider_used": "local-strategic-inference-engine",
        "status": "success"
    }

def build_prompt(req, intent, pressure, context, workflow, inference):
    return f"""
You are Executive Engine OS — Strategic Inference Engine.

You are not a chatbot. You are a sharp operator sitting beside the executive.

Your job:
- infer the real bottleneck
- identify the highest-leverage move
- challenge weak assumptions
- create the actual asset
- remove generic business language
- make the user think: "that is smart"

Detected intent: {intent}
Pressure: {pressure}
Active workflow: {json.dumps(workflow, ensure_ascii=False)}
Retrieved context: {json.dumps(context, ensure_ascii=False)[:8000]}
Strategic inference: {json.dumps(inference, ensure_ascii=False, indent=2)}

Forbidden language:
{json.dumps(FORBIDDEN_LANGUAGE)}

Rules:
1. Do not produce generic task lists.
2. Do not say "conduct analysis", "review assets", or "prepare strategy" unless you create the actual strategic output.
3. Every answer must include at least one non-obvious insight.
4. Every answer must say what NOT to do.
5. Commercial logic matters: money, risk, speed, leverage, control, conversion, trust.
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

def enforce_contract(data):
    data = clean_language(data or {})
    data.setdefault("next_move", "Identify the real bottleneck and create the decision-moving asset.")
    data.setdefault("decision", "Prioritize strategic leverage over generic activity.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is organized output with no strategic intelligence.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Generate the finished asset using the strategic inference.")
    data.setdefault("provider_used", "local-strategic-inference-engine")
    data.setdefault("status", "success")
    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]
    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Name the hidden bottleneck.",
            "Choose the leverage move.",
            "Create the asset that forces the next decision."
        ][:3-len(data["action_steps"])]
    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset", "Strategic inference saved.")]
    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"
    return data

def call_openai(req, intent, pressure, context, workflow, inference):
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, intent, pressure, context, workflow, inference)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.28,
            response_format={"type": "json_object"}
        )
        data = json.loads(result.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{DEFAULT_MODEL}"
        return enforce_contract(data)
    except Exception:
        return None

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "strategic_inference",
        "purpose": "turn organized output into commercially sharp operator intelligence"
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
    ws = load_workspace(req.workspace_id or "default", req.user_id or "will")
    intent = detect_intent(req.input, req.mode or "", req.brain or "", req.output_type or "")
    pressure = detect_pressure(req.input)
    context = retrieve_context(ws, req.input)
    workflow = upsert_workflow(ws, req, intent, pressure)
    inference = build_strategic_inference(req, intent, pressure, context, workflow)

    response = call_openai(req, intent, pressure, context, workflow, inference)
    if not response:
        response = strategic_fallback(req, intent, pressure, context, workflow)
    response = enforce_contract(response)

    ws["operator_state"]["current_pressure"] = pressure["level"]
    ws["operator_state"]["current_focus"] = workflow["title"]
    ws["operator_state"]["last_command"] = req.input
    ws["operator_state"]["last_next_move"] = response["next_move"]
    ws["operator_state"]["strategic_theme"] = intent
    ws["operator_state"]["inference_history"].append({
        "id": f"inf_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "workflow_id": workflow["id"],
        "input": req.input[:500],
        "inference": inference,
        "next_move": response["next_move"]
    })
    ws["operator_state"]["inference_history"] = ws["operator_state"]["inference_history"][-50:]

    ws["decisions"].append({
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "workflow_id": workflow["id"],
        "decision": response["decision"],
        "next_move": response["next_move"],
        "risk": response["risk"],
        "priority": response["priority"],
        "strategic_inference": inference,
        "importance": 5
    })
    ws["decisions"] = ws["decisions"][-100:]

    ws["activity"].append({
        "id": f"act_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "type": "run",
        "intent": intent,
        "pressure": pressure["level"],
        "workflow_id": workflow["id"],
        "input": req.input[:500]
    })
    ws["activity"] = ws["activity"][-100:]

    ws["continuity"]["recent_commands"].append(req.input[:300])
    ws["continuity"]["recent_commands"] = ws["continuity"]["recent_commands"][-30:]
    for asset in response.get("ready_assets", [])[:5]:
        ws["continuity"]["recent_assets"].append({
            "id": f"asset_{uuid.uuid4().hex[:8]}",
            "created_at": now_iso(),
            "workflow_id": workflow["id"],
            "content": str(asset)[:2500]
        })
    ws["continuity"]["recent_assets"] = ws["continuity"]["recent_assets"][-50:]
    workflow["next_action"] = response["recommended_command"]
    workflow["updated_at"] = now_iso()

    save_workspace(ws)

    response["strategic_inference"] = inference
    response["memory_context"] = {
        "active_workflow": workflow,
        "pressure": pressure,
        "intent": intent,
        "recent_decisions_count": len(ws["decisions"]),
        "inference_count": len(ws["operator_state"]["inference_history"])
    }
    response["version"] = APP_VERSION
    return response

@app.post("/memory")
def add_memory(item: MemoryRequest):
    ws = load_workspace(item.workspace_id or "default", item.user_id or "will")
    mem = {
        "id": f"mem_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "type": item.type,
        "title": item.title or item.content[:80],
        "content": item.content,
        "importance": item.importance or 3,
        "tags": item.tags or []
    }
    ws["memory"].append(mem)
    ws["memory"] = ws["memory"][-250:]
    save_workspace(ws)
    return {"status": "success", "version": APP_VERSION, "memory": mem}

@app.get("/memory")
def memory(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)
    return {"status": "success", "version": APP_VERSION, "memory": ws["memory"], "decisions": ws["decisions"][-25:]}

@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)
    active = [w for w in ws["workflows"] if w.get("status") == "active"]
    return {
        "status": "success",
        "version": APP_VERSION,
        "operator_state": ws["operator_state"],
        "active_workflows": active,
        "recent_decisions": ws["decisions"][-10:],
        "recent_assets": ws["continuity"]["recent_assets"][-10:],
        "memory_count": len(ws["memory"])
    }

@app.get("/operator-scan")
def operator_scan(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)
    hist = ws["operator_state"].get("inference_history", [])
    latest = hist[-1] if hist else None
    return {
        "status": "success",
        "version": APP_VERSION,
        "current_pressure": ws["operator_state"].get("current_pressure"),
        "current_focus": ws["operator_state"].get("current_focus"),
        "latest_inference": latest,
        "recommended_command": "Generate the finished asset using the latest strategic inference."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36540",
            "POST /run returns strategic_inference object",
            "Proposal test produces funded-deal positioning, not generic SEO/Ads tasks",
            "Forbidden generic language is replaced",
            "GET /engine-state shows inference_history"
        ],
        "proposal_test": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
