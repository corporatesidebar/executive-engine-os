from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import os
import json
import re
import uuid
import math

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


APP_VERSION = "V36500-Executive-Intelligence-Architecture"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = FastAPI(
    title="Executive Engine OS",
    version=APP_VERSION,
    description="Executive Intelligence Architecture backend for continuity, memory, routing, pressure detection, sequencing, and executive-grade output."
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


# -----------------------------
# Models
# -----------------------------

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


class MemoryItem(BaseModel):
    workspace_id: str = "default"
    user_id: str = "will"
    type: str = "note"
    title: Optional[str] = None
    content: str
    importance: Optional[int] = 3
    tags: Optional[List[str]] = []


class WorkflowItem(BaseModel):
    workspace_id: str = "default"
    user_id: str = "will"
    title: str
    status: str = "active"
    priority: str = "High"
    owner: Optional[str] = "Will"
    next_action: Optional[str] = None
    deadline: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# -----------------------------
# Lightweight persistence
# -----------------------------

DATA_DIR = os.getenv("EE_DATA_DIR", "/tmp/executive_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

def _path(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)
    return os.path.join(DATA_DIR, safe)

def _read_json(name: str, default: Any) -> Any:
    p = _path(name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(name: str, data: Any) -> None:
    p = _path(name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# -----------------------------
# Intelligence primitives
# -----------------------------

INTENT_PATTERNS = {
    "proposal": ["proposal", "quote", "scope", "sow", "offer", "pitch", "deal", "client"],
    "email": ["email", "reply", "send", "message", "follow up", "follow-up", "dm"],
    "meeting": ["meeting", "agenda", "prep", "call", "presentation", "talking points"],
    "decision": ["decide", "decision", "choose", "option", "should i", "yes or no"],
    "strategy": ["strategy", "positioning", "market", "growth", "plan", "roadmap"],
    "execution": ["build", "fix", "ship", "deploy", "implement", "execute", "make", "create"],
    "revenue": ["revenue", "sales", "lead", "pipeline", "conversion", "cpa", "seo", "ads", "pricing"],
    "risk": ["risk", "problem", "blocker", "broken", "issue", "urgent", "sucks", "terrible"],
    "personal_productivity": ["overwhelmed", "confused", "stuck", "too much", "organize", "hair out"],
}

PRESSURE_TERMS = {
    "critical": ["now", "asap", "urgent", "broken", "doesn't work", "doesnt work", "fix this", "fuck", "shit", "terrible", "wtf", "stop", "can't", "cant"],
    "high": ["today", "tonight", "deadline", "client", "money", "revenue", "deploy", "launch", "proposal", "court", "meeting"],
    "medium": ["soon", "next", "plan", "improve", "better", "organize"],
}

EXECUTIVE_VERBS = [
    "decide", "ship", "remove", "prioritize", "sequence", "delegate", "approve",
    "prepare", "close", "protect", "simplify", "escalate", "stabilize"
]

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def score_terms(text: str, terms: List[str]) -> int:
    t = text.lower()
    return sum(1 for term in terms if term in t)

def detect_intent(text: str, mode: Optional[str], output_type: Optional[str], brain: Optional[str]) -> Dict[str, Any]:
    t = text.lower()
    scores = {}
    for intent, terms in INTENT_PATTERNS.items():
        scores[intent] = score_terms(t, terms)

    # Explicit dropdowns should influence but not blindly override.
    for signal in [mode or "", output_type or "", brain or ""]:
        s = signal.lower()
        for intent in scores:
            if intent in s:
                scores[intent] += 2

    primary = max(scores, key=scores.get)
    if scores[primary] == 0:
        primary = "execution"

    secondary = sorted([k for k, v in scores.items() if v > 0 and k != primary], key=lambda k: scores[k], reverse=True)[:3]
    return {
        "primary_intent": primary,
        "secondary_intents": secondary,
        "scores": scores,
        "mode": mode or "execution",
        "brain": brain or "operator",
        "output_type": output_type or "standard",
    }

def detect_pressure(text: str) -> Dict[str, Any]:
    t = text.lower()
    critical = score_terms(t, PRESSURE_TERMS["critical"])
    high = score_terms(t, PRESSURE_TERMS["high"])
    medium = score_terms(t, PRESSURE_TERMS["medium"])

    if critical >= 1 or high >= 3:
        level = "Critical"
        posture = "Stabilize first, reduce friction, produce usable output immediately."
    elif high >= 1:
        level = "High"
        posture = "Move quickly, preserve momentum, make the next decision obvious."
    elif medium >= 1:
        level = "Medium"
        posture = "Clarify sequence, convert ambiguity into a clean next move."
    else:
        level = "Normal"
        posture = "Improve leverage and progress without overcomplicating."

    return {
        "level": level,
        "signals": {"critical": critical, "high": high, "medium": medium},
        "posture": posture
    }

def extract_entities(text: str) -> Dict[str, List[str]]:
    # Lightweight entity extraction without external dependencies.
    urls = re.findall(r"https?://[^\s]+", text)
    money = re.findall(r"\$[\d,]+(?:\.\d+)?[kKmM]?", text)
    percents = re.findall(r"\b\d+(?:\.\d+)?\s?%", text)
    dates = re.findall(r"\b(?:today|tomorrow|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4}-\d{2}-\d{2})\b", text, flags=re.I)
    quoted = re.findall(r'"([^"]+)"', text)
    caps_phrases = re.findall(r"\b[A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,4}\b", text)
    return {
        "urls": urls[:10],
        "money": money[:10],
        "percents": percents[:10],
        "dates": dates[:10],
        "quoted": quoted[:10],
        "proper_phrases": list(dict.fromkeys(caps_phrases))[:15],
    }

def load_workspace(workspace_id: str, user_id: str) -> Dict[str, Any]:
    key = f"workspace_{workspace_id}_{user_id}.json"
    data = _read_json(key, {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "memories": [],
        "workflows": [],
        "decisions": [],
        "activity": [],
        "operational_graph": {"nodes": [], "edges": []}
    })
    return data

def save_workspace(data: Dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    key = f"workspace_{data.get('workspace_id', 'default')}_{data.get('user_id', 'will')}.json"
    _write_json(key, data)

def retrieve_relevant_memory(workspace: Dict[str, Any], text: str, limit: int = 6) -> List[Dict[str, Any]]:
    words = set(re.findall(r"[a-zA-Z0-9]{3,}", text.lower()))
    ranked = []
    for item in workspace.get("memories", []) + workspace.get("workflows", []) + workspace.get("decisions", []):
        hay = json.dumps(item).lower()
        overlap = sum(1 for w in words if w in hay)
        importance = int(item.get("importance", 3)) if isinstance(item, dict) else 3
        score = overlap * 2 + importance
        if score > 0:
            ranked.append((score, item))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in ranked[:limit]]

def update_operational_graph(workspace: Dict[str, Any], analysis: Dict[str, Any], text: str) -> Dict[str, Any]:
    graph = workspace.setdefault("operational_graph", {"nodes": [], "edges": []})
    node_id = f"cmd_{uuid.uuid4().hex[:8]}"
    entities = analysis.get("entities", {})
    node = {
        "id": node_id,
        "type": "command",
        "label": text[:90],
        "intent": analysis["intent"]["primary_intent"],
        "pressure": analysis["pressure"]["level"],
        "created_at": now_iso()
    }
    graph["nodes"].append(node)

    for phrase in entities.get("proper_phrases", [])[:6]:
        ent_id = "entity_" + re.sub(r"[^a-zA-Z0-9]+", "_", phrase.lower()).strip("_")[:40]
        if not any(n.get("id") == ent_id for n in graph["nodes"]):
            graph["nodes"].append({"id": ent_id, "type": "entity", "label": phrase})
        graph["edges"].append({"from": node_id, "to": ent_id, "type": "mentions"})

    graph["nodes"] = graph["nodes"][-150:]
    graph["edges"] = graph["edges"][-300:]
    return graph

def create_or_update_workflow(workspace: Dict[str, Any], text: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    intent = analysis["intent"]["primary_intent"]
    pressure = analysis["pressure"]["level"]
    if intent not in ["execution", "proposal", "meeting", "strategy", "revenue", "risk", "decision"]:
        return None

    title = infer_workflow_title(text, intent)
    existing = None
    for wf in workspace.get("workflows", []):
        if similarity(wf.get("title", ""), title) > 0.45:
            existing = wf
            break

    if existing:
        existing["updated_at"] = now_iso()
        existing["last_input"] = text[:500]
        existing["pressure"] = pressure
        existing["status"] = "active"
        return existing

    wf = {
        "id": f"wf_{uuid.uuid4().hex[:8]}",
        "type": "workflow",
        "title": title,
        "status": "active",
        "priority": "Critical" if pressure == "Critical" else "High",
        "owner": "Will",
        "next_action": "Generate executive-grade output and preserve the next move.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_input": text[:500],
        "intent": intent,
        "pressure": pressure,
        "importance": 4
    }
    workspace.setdefault("workflows", []).append(wf)
    workspace["workflows"] = workspace["workflows"][-75:]
    return wf

def similarity(a: str, b: str) -> float:
    aw = set(re.findall(r"[a-zA-Z0-9]{3,}", a.lower()))
    bw = set(re.findall(r"[a-zA-Z0-9]{3,}", b.lower()))
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(1, len(aw | bw))

def infer_workflow_title(text: str, intent: str) -> str:
    clean = normalize_text(text)
    if len(clean) <= 72:
        return clean
    prefix = {
        "proposal": "Proposal",
        "meeting": "Meeting Prep",
        "strategy": "Strategy",
        "revenue": "Revenue",
        "decision": "Decision",
        "risk": "Risk / Stabilization",
        "execution": "Execution"
    }.get(intent, "Execution")
    return f"{prefix}: {clean[:62].rstrip()}"

def build_analysis(req: RunRequest, workspace: Dict[str, Any]) -> Dict[str, Any]:
    text = normalize_text(req.input)
    intent = detect_intent(text, req.mode, req.output_type, req.brain)
    pressure = detect_pressure(text)
    entities = extract_entities(text)
    relevant_memory = retrieve_relevant_memory(workspace, text)
    return {
        "input": text,
        "intent": intent,
        "pressure": pressure,
        "entities": entities,
        "relevant_memory": relevant_memory,
        "timestamp": now_iso()
    }

def build_system_prompt(analysis: Dict[str, Any]) -> str:
    return f"""
You are Executive Engine OS: a private executive cognition layer for Will Webb.

Your job is not to give generic advice. Your job is to create operational leverage.

Think like a CEO, COO, Chief of Staff, revenue operator, and execution architect.

Core requirements:
- Preserve the required response fields exactly.
- Make a real decision or recommendation.
- Produce specific, usable work.
- Reduce pressure.
- Create momentum.
- Do not over-explain.
- Do not say "you could"; say what to do.
- If the user asks for proposal/email/message/plan, create the actual asset.
- If the user is frustrated, stabilize the situation and give a direct executable path.
- Keep the answer executive-grade, commercially sharp, and non-generic.

Detected:
Primary intent: {analysis["intent"]["primary_intent"]}
Secondary intents: {analysis["intent"]["secondary_intents"]}
Pressure level: {analysis["pressure"]["level"]}
Pressure posture: {analysis["pressure"]["posture"]}

Relevant memory/context:
{json.dumps(analysis.get("relevant_memory", []), ensure_ascii=False, indent=2)[:6000]}

Return ONLY valid JSON with this exact schema:
{{
  "next_move": "single strongest next move",
  "decision": "clear executive recommendation",
  "action_steps": ["3-7 concrete steps"],
  "ready_assets": ["usable assets, scripts, proposal sections, email text, bullets, or implementation outputs"],
  "risk": "real operational/commercial risk",
  "priority": "Critical | High | Medium | Low",
  "recommended_command": "the next command the user should run",
  "what_to_do_now": "one immediate instruction",
  "asset": "best complete asset when useful",
  "follow_up": "what the system should watch or do next",
  "provider_used": "openai:{DEFAULT_MODEL}",
  "status": "success"
}}
"""

def fallback_response(req: RunRequest, analysis: Dict[str, Any], workflow: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    text = analysis["input"]
    intent = analysis["intent"]["primary_intent"]
    pressure = analysis["pressure"]["level"]

    if intent == "proposal" or "proposal" in text.lower():
        asset = build_proposal_asset(text)
        next_move = "Turn the request into a client-ready proposal structure now, then tighten pricing, proof, and next-step language."
        decision = "Use a direct revenue-first proposal: outcome, offer, execution plan, proof, commercial terms, next step."
        steps = [
            "Define the buyer, business problem, and measurable win in the first 3 lines.",
            "State the offer as an execution package, not a list of services.",
            "Include a 30/60/90-day delivery plan with owners, assets, and success metrics.",
            "Attach pricing or a commercial range only after value is clear.",
            "End with one decisive next step: approval, kickoff call, or deposit."
        ]
        ready = [asset]
        recommended = "Turn this into a final client proposal with pricing, timeline, and kickoff email."
    elif intent == "email":
        asset = build_email_asset(text)
        next_move = "Send a clean executive message that removes ambiguity and forces the next decision."
        decision = "Use a short direct note with context, decision, ask, and deadline."
        steps = [
            "Open with the reason for the message.",
            "State the decision or recommendation plainly.",
            "Make one clear ask.",
            "Give a deadline or next meeting point.",
            "Remove defensive language and filler."
        ]
        ready = [asset]
        recommended = "Draft the final version of this message for the exact recipient and situation."
    elif intent == "meeting":
        asset = build_meeting_asset(text)
        next_move = "Convert the meeting into a decision session with a defined outcome."
        decision = "Do not attend with loose notes. Enter with agenda, decision target, risks, and close."
        steps = [
            "Set the meeting objective in one sentence.",
            "Prepare the 3 decisions that must come out of the meeting.",
            "List likely objections and responses.",
            "Prepare the close before the meeting starts.",
            "Capture owners and deadlines before leaving."
        ]
        ready = [asset]
        recommended = "Build my meeting prep with agenda, talking points, risks, and close."
    elif intent in ["risk", "execution"] and pressure in ["Critical", "High"]:
        asset = build_stabilization_asset(text)
        next_move = "Stabilize the system: preserve the working base, isolate the broken layer, and ship one controlled fix."
        decision = "Stop broad redesign. Fix only the failing intelligence/output layer and protect layout/navigation."
        steps = [
            "Lock the current working UI and do not modify layout or navigation.",
            "Identify whether the failure is input capture, routing, response generation, or rendering.",
            "Patch the smallest backend/output layer responsible for the weak result.",
            "Run one known test command and compare output quality against the required contract.",
            "Promote only if the output is materially more useful and the UI remains unchanged."
        ]
        ready = [asset]
        recommended = "Run a controlled backend-only intelligence fix and test it against the proposal command."
    else:
        asset = build_execution_asset(text, intent)
        next_move = "Convert the input into one executable outcome and preserve it as an active workflow."
        decision = "Treat this as an execution workflow, not a chat response."
        steps = [
            "Clarify the win condition in one sentence.",
            "Choose the highest-leverage next move.",
            "Create the working asset immediately.",
            "Sequence the next 3 actions by dependency.",
            "Save the decision and keep the workflow active."
        ]
        ready = [asset]
        recommended = "Convert this into a full execution brief with decision, asset, risks, and next command."

    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": steps[:7],
        "ready_assets": ready,
        "risk": infer_risk(intent, pressure),
        "priority": "Critical" if pressure == "Critical" else "High" if pressure == "High" else "Medium",
        "recommended_command": recommended,
        "what_to_do_now": steps[0],
        "asset": asset,
        "follow_up": "Keep this workflow active and use the next command to deepen the asset instead of restarting context.",
        "provider_used": "local-intelligence-fallback",
        "status": "success",
        "router": {
            "intent": analysis["intent"],
            "pressure": analysis["pressure"],
            "workflow_id": workflow.get("id") if workflow else None
        },
        "active_context": {
            "workflow": workflow,
            "relevant_memory": analysis.get("relevant_memory", [])[:4]
        }
    }

def infer_risk(intent: str, pressure: str) -> str:
    if pressure == "Critical":
        return "The real risk is uncontrolled changes creating more confusion, weaker output, or lost momentum."
    if intent == "proposal":
        return "The real risk is sounding like a vendor instead of a revenue/operator partner with a clear business outcome."
    if intent == "email":
        return "The real risk is sending a message that creates more back-and-forth instead of forcing the next decision."
    if intent == "meeting":
        return "The real risk is entering the meeting without a decision target and leaving with vague follow-ups."
    return "The real risk is turning this into more planning instead of one concrete shipped outcome."

def build_proposal_asset(text: str) -> str:
    return f"""CLIENT-READY PROPOSAL STRUCTURE

Executive Outcome:
We will build a practical growth/execution system that turns the current objective into measurable business movement, with clear ownership, faster decisions, and fewer stalled actions.

Business Problem:
The current gap is not effort. The gap is execution clarity, sequencing, and a system that converts opportunities into visible progress.

Recommended Engagement:
1. Diagnose the revenue / operational bottleneck.
2. Build the execution plan around the highest-leverage win.
3. Create the required assets: offer, messaging, workflow, follow-up, reporting, and accountability structure.
4. Run weekly optimization against real numbers.
5. Tighten the system until it produces repeatable output.

30-Day Focus:
- Clarify offer and buyer pain.
- Build priority execution plan.
- Create first revenue/ops assets.
- Launch controlled test.
- Track conversion, friction, and next actions.

60-Day Focus:
- Improve what works.
- Remove low-yield activity.
- Strengthen follow-up and decision flow.
- Package repeatable process.

90-Day Focus:
- Scale the winning workflow.
- Create operating rhythm.
- Convert lessons into a durable system.

Next Step:
Approve the initial execution sprint and schedule kickoff."""

def build_email_asset(text: str) -> str:
    return """Subject: Next Step

Hi,

Here is the clean path forward.

The priority is to remove ambiguity and move this into execution. My recommendation is that we align on the outcome, confirm the next action, and assign ownership now so this does not turn into another open loop.

What I need from you:
1. Confirm the desired outcome.
2. Confirm who owns the next step.
3. Confirm the deadline.

Once confirmed, I’ll move this forward with the required asset, plan, or execution sequence.

Best,
Will"""

def build_meeting_asset(text: str) -> str:
    return """MEETING PREP

Objective:
Leave the meeting with a clear decision, owner, and next action.

Agenda:
1. Current situation.
2. Business objective.
3. Primary constraint.
4. Recommended decision.
5. Risks and tradeoffs.
6. Owners and deadlines.

Talking Points:
- The goal is not more discussion; the goal is a decision.
- We need the simplest path that creates measurable progress.
- Anything that does not move the outcome forward gets removed or deferred.

Close:
Before we end, we need one owner, one deadline, and one measurable next step."""

def build_stabilization_asset(text: str) -> str:
    return """CONTROLLED STABILIZATION PLAN

Decision:
Do not redesign. Do not expand scope. Fix the intelligence/output failure only.

Locked:
- Layout
- Navigation
- Sidebars
- API contract
- Deployment structure

Fix:
- Improve intent detection.
- Add pressure detection.
- Add workflow continuity.
- Improve response specificity.
- Generate actual assets instead of advice.
- Preserve next recommended command.

Validation Test:
Input: Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.

Pass Criteria:
- Output must be a proposal, not unrelated content.
- Output must include a clear decision.
- Output must include usable proposal sections.
- Output must include concrete next actions.
- Output must not change UI layout."""

def build_execution_asset(text: str, intent: str) -> str:
    return f"""EXECUTION BRIEF

Input:
{text}

Operating Decision:
Treat this as an active executive workflow. The goal is to create a usable outcome now, not another planning loop.

Win Condition:
A clear decision, a specific next move, and one usable asset are produced immediately.

Execution Sequence:
1. Lock the objective.
2. Identify the highest-leverage next move.
3. Create the asset.
4. Identify the risk.
5. Save the next command.
6. Continue from context next time instead of restarting."""

def parse_model_json(raw: str) -> Dict[str, Any]:
    if not raw:
        raise ValueError("empty model response")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start:end+1]
    return json.loads(cleaned)

def call_openai(req: RunRequest, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not OPENAI_API_KEY or OpenAI is None:
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)
    system = build_system_prompt(analysis)
    user = f"""
User command:
{analysis["input"]}

Additional request metadata:
mode={req.mode}
brain={req.brain}
output_type={req.output_type}
depth={req.depth}
"""
    try:
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.35,
            response_format={"type": "json_object"}
        )
        content = result.choices[0].message.content
        data = parse_model_json(content)
        data["provider_used"] = f"openai:{DEFAULT_MODEL}"
        data["status"] = "success"
        return enforce_contract(data)
    except Exception as e:
        return None

def enforce_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    required = {
        "next_move": "",
        "decision": "",
        "action_steps": [],
        "ready_assets": [],
        "risk": "",
        "priority": "High",
        "recommended_command": "",
        "provider_used": "",
        "status": "success"
    }
    for k, v in required.items():
        data.setdefault(k, v)

    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]

    data["action_steps"] = [str(x) for x in data.get("action_steps", [])][:7]
    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Confirm the desired outcome.",
            "Create the required asset.",
            "Execute the next step and preserve context."
        ][:3-len(data["action_steps"])]

    data["ready_assets"] = [str(x) for x in data.get("ready_assets", [])]
    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset", "No asset generated.")]

    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"

    return data


# -----------------------------
# API Routes
# -----------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Executive Engine OS",
        "version": APP_VERSION,
        "architecture": [
            "continuity",
            "memory",
            "operational_graphing",
            "workflow_persistence",
            "pressure_detection",
            "intelligent_routing",
            "contextual_reasoning",
            "operational_sequencing",
            "executive_communication_generation",
            "proactive_execution_support"
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

@app.get("/providers")
def providers():
    return {
        "status": "ok",
        "providers": {
            "openai": {
                "available": bool(OPENAI_API_KEY and OpenAI is not None),
                "model": DEFAULT_MODEL
            },
            "local_intelligence_fallback": {
                "available": True,
                "model": "deterministic-executive-engine"
            }
        }
    }

@app.post("/run")
def run(req: RunRequest):
    workspace = load_workspace(req.workspace_id or "default", req.user_id or "will")
    analysis = build_analysis(req, workspace)
    workflow = create_or_update_workflow(workspace, req.input, analysis)
    update_operational_graph(workspace, analysis, req.input)

    workspace.setdefault("activity", []).append({
        "id": f"act_{uuid.uuid4().hex[:8]}",
        "type": "run",
        "input": req.input[:1000],
        "intent": analysis["intent"]["primary_intent"],
        "pressure": analysis["pressure"]["level"],
        "created_at": now_iso()
    })
    workspace["activity"] = workspace["activity"][-100:]

    model_data = call_openai(req, analysis)
    response = model_data if model_data else fallback_response(req, analysis, workflow)
    response = enforce_contract(response)

    response.setdefault("router", {
        "intent": analysis["intent"],
        "pressure": analysis["pressure"],
        "workflow_id": workflow.get("id") if workflow else None
    })
    response.setdefault("active_context", {
        "workflow": workflow,
        "relevant_memory": analysis.get("relevant_memory", [])[:4],
        "operational_graph_summary": {
            "nodes": len(workspace.get("operational_graph", {}).get("nodes", [])),
            "edges": len(workspace.get("operational_graph", {}).get("edges", []))
        }
    })
    response.setdefault("workspace", {
        "workspace_id": workspace.get("workspace_id"),
        "active_workflows": len([w for w in workspace.get("workflows", []) if w.get("status") == "active"]),
        "memory_count": len(workspace.get("memories", []))
    })

    # Persist output decision for continuity.
    workspace.setdefault("decisions", []).append({
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "type": "decision",
        "input": req.input[:500],
        "decision": response.get("decision", ""),
        "next_move": response.get("next_move", ""),
        "priority": response.get("priority", "High"),
        "created_at": now_iso(),
        "importance": 4
    })
    workspace["decisions"] = workspace["decisions"][-75:]
    save_workspace(workspace)

    return response

@app.post("/memory")
def save_memory(item: MemoryItem):
    workspace = load_workspace(item.workspace_id, item.user_id)
    memory = {
        "id": f"mem_{uuid.uuid4().hex[:8]}",
        "type": item.type,
        "title": item.title or item.content[:80],
        "content": item.content,
        "importance": item.importance or 3,
        "tags": item.tags or [],
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    workspace.setdefault("memories", []).append(memory)
    workspace["memories"] = workspace["memories"][-200:]
    save_workspace(workspace)
    return {"status": "success", "memory": memory}

@app.get("/memory")
def list_memory(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    return {
        "status": "success",
        "workspace_id": workspace_id,
        "memories": workspace.get("memories", []),
        "decisions": workspace.get("decisions", [])[-20:]
    }

@app.post("/workflow")
def save_workflow(item: WorkflowItem):
    workspace = load_workspace(item.workspace_id, item.user_id)
    wf = {
        "id": f"wf_{uuid.uuid4().hex[:8]}",
        "type": "workflow",
        "title": item.title,
        "status": item.status,
        "priority": item.priority,
        "owner": item.owner,
        "next_action": item.next_action,
        "deadline": item.deadline,
        "context": item.context or {},
        "importance": 4,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    workspace.setdefault("workflows", []).append(wf)
    save_workspace(workspace)
    return {"status": "success", "workflow": wf}

@app.get("/workflow")
def list_workflows(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    return {
        "status": "success",
        "workspace_id": workspace_id,
        "workflows": workspace.get("workflows", [])
    }

@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    active = [w for w in workspace.get("workflows", []) if w.get("status") == "active"]
    recent_decisions = workspace.get("decisions", [])[-10:]
    activity = workspace.get("activity", [])[-15:]
    return {
        "status": "success",
        "version": APP_VERSION,
        "workspace_id": workspace_id,
        "active_workflows": active,
        "recent_decisions": recent_decisions,
        "recent_activity": activity,
        "memory_count": len(workspace.get("memories", [])),
        "operational_graph": {
            "nodes": len(workspace.get("operational_graph", {}).get("nodes", [])),
            "edges": len(workspace.get("operational_graph", {}).get("edges", []))
        }
    }

@app.get("/operator-scan")
def operator_scan(workspace_id: str = "default", user_id: str = "will"):
    workspace = load_workspace(workspace_id, user_id)
    active = [w for w in workspace.get("workflows", []) if w.get("status") == "active"]
    critical = [w for w in active if w.get("priority") == "Critical" or w.get("pressure") == "Critical"]
    high = [w for w in active if w.get("priority") == "High" or w.get("pressure") == "High"]

    next_focus = critical[0] if critical else high[0] if high else active[0] if active else None
    return {
        "status": "success",
        "next_move": next_focus.get("next_action") if next_focus else "Create the first active workflow through /run.",
        "pressure": "Critical" if critical else "High" if high else "Normal",
        "active_workflows": len(active),
        "focus_workflow": next_focus,
        "recommended_command": "Continue the highest-pressure workflow and generate the next asset."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            {
                "name": "Health",
                "method": "GET",
                "path": "/health",
                "expected": "status ok"
            },
            {
                "name": "Run Proposal Intelligence",
                "method": "POST",
                "path": "/run",
                "body": {
                    "input": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
                    "mode": "execution",
                    "brain": "revenue",
                    "output_type": "proposal",
                    "depth": "standard"
                },
                "expected_fields": [
                    "next_move",
                    "decision",
                    "action_steps",
                    "ready_assets",
                    "risk",
                    "priority",
                    "recommended_command",
                    "provider_used",
                    "status"
                ]
            },
            {
                "name": "Engine State",
                "method": "GET",
                "path": "/engine-state",
                "expected": "active workflows, decisions, memory count"
            }
        ],
        "copy_tools": {
            "curl_run": "curl -X POST https://executive-engine-os.onrender.com/run -H 'Content-Type: application/json' -d '{\"input\":\"Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.\",\"mode\":\"execution\",\"brain\":\"revenue\",\"output_type\":\"proposal\",\"depth\":\"standard\"}'"
        }
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
