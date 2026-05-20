from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import os, json, re, uuid

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_VERSION = "V36560-Executive-Presence-Engine"
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
            "presence_mode": None,
            "last_command": None,
            "last_next_move": None,
            "presence_history": []
        },
        "continuity": {
            "recent_commands": [],
            "recent_assets": []
        }
    }

def load_workspace(workspace_id="default", user_id="will"):
    path = db_path(workspace_id, user_id)
    if not os.path.exists(path):
        return empty_workspace(workspace_id, user_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            ws = json.load(f)
        base = empty_workspace(workspace_id, user_id)
        for k, v in base.items():
            ws.setdefault(k, v)
        ws.setdefault("operator_state", base["operator_state"])
        ws["operator_state"].setdefault("presence_history", [])
        return ws
    except Exception:
        return empty_workspace(workspace_id, user_id)

def save_workspace(ws):
    ws["updated_at"] = now_iso()
    with open(db_path(ws["workspace_id"], ws["user_id"]), "w", encoding="utf-8") as f:
        json.dump(ws, f, indent=2, ensure_ascii=False)

def words(text):
    return set(re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower()))

def detect_intent(text):
    t = text.lower()
    table = {
        "proposal": ["proposal", "pitch", "quote", "offer", "scope"],
        "build": ["build", "deploy", "fix", "engine", "backend", "frontend", "version"],
        "decision": ["decide", "decision", "choose", "should i"],
        "meeting": ["meeting", "agenda", "call", "prep"],
        "revenue": ["sales", "revenue", "cpa", "lead", "dealership", "ads", "seo"],
        "risk": ["risk", "broken", "problem", "stuck", "failure"],
        "strategy": ["strategy", "positioning", "market", "roadmap"]
    }
    scores = {k: sum(1 for x in v if x in t) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"

def detect_pressure(text):
    t = text.lower()
    if any(x in t for x in ["wtf", "fuck", "shit", "urgent", "asap", "broken"]):
        return "Critical"
    score = sum(1 for x in ["proposal", "revenue", "client", "build", "deploy", "risk", "deadline"] if x in t)
    if score >= 2:
        return "High"
    if score == 1:
        return "Medium"
    return "Normal"

def retrieve_context(ws, query):
    q = words(query)
    recent = ws.get("decisions", [])[-8:]
    relevant = []
    for item in recent:
        blob = json.dumps(item).lower()
        overlap = sum(1 for w in q if w in blob)
        if overlap:
            relevant.append(item)
    return relevant[-5:]

FORBIDDEN = [
    "comprehensive strategy",
    "conduct analysis",
    "review existing assets",
    "determine the specific type",
    "high-impact",
    "optimize workflows",
    "stakeholders",
    "best practices",
    "streamline operations",
    "create a targeted asset",
    "operational needs",
    "maintain workflow momentum"
]

def remove_generic_language(text):
    replacements = {
        "comprehensive strategy": "focused operating move",
        "conduct analysis": "name the constraint",
        "review existing assets": "use only what changes the decision",
        "determine the specific type": "choose the asset that forces movement",
        "high-impact": "revenue-relevant",
        "optimize workflows": "tighten execution",
        "stakeholders": "decision-makers",
        "best practices": "what works here",
        "streamline operations": "remove friction",
        "maintain workflow momentum": "force momentum"
    }
    out = text
    for a, b in replacements.items():
        out = re.sub(a, b, out, flags=re.I)
    return out

def determine_presence_mode(intent):
    mapping = {
        "proposal": "commercial",
        "build": "technical",
        "decision": "ruthless",
        "meeting": "political",
        "revenue": "commercial",
        "risk": "containment",
        "strategy": "executive"
    }
    return mapping.get(intent, "operator")

def executive_presence(req, intent, pressure):
    text = req.input.lower()
    mode = determine_presence_mode(intent)

    base = {
        "truth": "The system should force momentum, not generate more operational theater.",
        "constraint": "The main bottleneck is unclear prioritization and weak decision pressure.",
        "leverage": "Force one irreversible next move.",
        "wrong_move": "Do not create another planning loop.",
        "executive_presence": "Cut noise. Make the move. Protect momentum.",
        "psychology": "Executives want certainty, speed, leverage, and control."
    }

    if any(x in text for x in ["dealership", "cpa", "seo", "google ads"]):
        base = {
            "truth": "The dealership does not care about marketing activity. It cares about financed buyers and predictable acquisition cost.",
            "constraint": "The CPA target only works if intent quality and lead handling speed are controlled.",
            "leverage": "Sell financed-deal economics, not campaign tasks.",
            "wrong_move": "Do not lead with SEO deliverables or keyword research.",
            "executive_presence": "If the campaign attracts broad car shoppers, the economics collapse.",
            "psychology": "The client wants confidence that this turns into funded deals, not traffic."
        }

    elif "executive engine" in text or "reasoning" in text:
        base = {
            "truth": "The UI is no longer the bottleneck. Weak cognition is.",
            "constraint": "The system still sounds like organized management software instead of a sharp operator.",
            "leverage": "Compress responses and increase judgment density.",
            "wrong_move": "Do not add more UI to hide weak reasoning.",
            "executive_presence": "If the response does not make the user sharper immediately, it failed.",
            "psychology": "Executives psychologically depend on systems that reduce pressure and create certainty."
        }

    return {
        "mode": mode,
        **base
    }

def build_asset(reasoning, intent):
    if intent == "proposal":
        return f"""EXECUTIVE PROPOSAL POSITIONING

Truth:
{reasoning["truth"]}

Core Commercial Angle:
This is not a marketing proposal.
This is a financed-buyer acquisition system.

The Real Offer:
- controlled CPA
- finance-intent traffic
- appointment generation
- funded-deal tracking
- lower acquisition waste

What To Avoid:
{reasoning["wrong_move"]}

Operator Positioning:
Google Ads creates speed.
SEO reduces dependency over time.
Tracking proves ROI.

Closing Line:
If the dealership wants sub-$100 CPA, the system must control intent, landing-page friction, and lead handling speed from day one."""
    return f"""EXECUTIVE PRESENCE OUTPUT

Truth:
{reasoning["truth"]}

Constraint:
{reasoning["constraint"]}

Leverage:
{reasoning["leverage"]}

Wrong Move:
{reasoning["wrong_move"]}

Executive Presence:
{reasoning["executive_presence"]}

Psychology:
{reasoning["psychology"]}

This response should force clarity and movement, not more operational noise."""

def local_response(req, intent, pressure, reasoning):
    asset = build_asset(reasoning, intent)

    return {
        "next_move": reasoning["leverage"],
        "decision": reasoning["executive_presence"],
        "action_steps": [
            reasoning["wrong_move"],
            "Remove unnecessary work immediately.",
            "Force the next irreversible move.",
            "Create the finished asset now.",
            "Use the next command to finalize execution."
        ],
        "ready_assets": [asset],
        "risk": reasoning["constraint"],
        "priority": "Critical" if pressure == "Critical" else "High",
        "recommended_command": "Generate the finished executive-grade asset using this positioning.",
        "what_to_do_now": reasoning["executive_presence"],
        "asset": asset,
        "follow_up": "Do not reopen planning. Force execution.",
        "provider_used": "local-executive-presence-engine",
        "status": "success"
    }

def build_prompt(req, reasoning, mode, context):
    return f"""
You are Executive Engine OS — Executive Presence Engine.

You are:
- calm
- direct
- commercially sharp
- psychologically aware
- compressive
- authoritative

You are NOT:
- generic
- verbose
- operationally soft
- corporate
- management-consultant style

Current presence mode:
{mode}

Executive reasoning:
{json.dumps(reasoning, ensure_ascii=False, indent=2)}

Recent context:
{json.dumps(context, ensure_ascii=False)[:6000]}

Rules:
1. Compress aggressively.
2. Say the uncomfortable truth if needed.
3. Name wasted motion.
4. Prioritize ruthlessly.
5. Say what NOT to do.
6. Tie everything to leverage, momentum, control, revenue, risk, or speed.
7. Never use these phrases:
{json.dumps(FORBIDDEN)}

Return only valid JSON:
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

def enforce(data):
    data = data or {}

    for key in list(data.keys()):
        if isinstance(data[key], str):
            data[key] = remove_generic_language(data[key])

    data.setdefault("next_move", "Force the next irreversible move.")
    data.setdefault("decision", "Cut wasted motion and move.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is drifting into operational theater.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Generate the final executive asset now.")
    data.setdefault("provider_used", "local-executive-presence-engine")
    data.setdefault("status", "success")

    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]

    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]

    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Remove wasted motion.",
            "Force the next decision.",
            "Create the final asset."
        ][:3-len(data["action_steps"])]

    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset", "Executive presence output saved.")]

    return data

def call_openai(req, reasoning, mode, context):
    if not OPENAI_API_KEY or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, reasoning, mode, context)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.18,
            response_format={"type": "json_object"}
        )

        data = json.loads(result.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{DEFAULT_MODEL}"

        return enforce(data)

    except Exception:
        return None

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "executive_presence",
        "purpose": "authority, compression, leverage, executive psychology"
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

    intent = detect_intent(req.input)
    pressure = detect_pressure(req.input)
    context = retrieve_context(ws, req.input)
    presence = executive_presence(req, intent, pressure)
    mode = presence["mode"]

    response = call_openai(req, presence, mode, context)

    if not response:
        response = local_response(req, intent, pressure, presence)

    response = enforce(response)

    decision_record = {
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "input": req.input[:500],
        "intent": intent,
        "pressure": pressure,
        "presence_mode": mode,
        "decision": response["decision"],
        "next_move": response["next_move"],
        "reasoning": presence
    }

    ws["decisions"].append(decision_record)
    ws["decisions"] = ws["decisions"][-100:]

    ws["operator_state"]["current_pressure"] = pressure
    ws["operator_state"]["current_focus"] = intent
    ws["operator_state"]["presence_mode"] = mode
    ws["operator_state"]["last_command"] = req.input
    ws["operator_state"]["last_next_move"] = response["next_move"]

    ws["operator_state"]["presence_history"].append({
        "created_at": now_iso(),
        "mode": mode,
        "truth": presence["truth"],
        "leverage": presence["leverage"]
    })

    ws["operator_state"]["presence_history"] = ws["operator_state"]["presence_history"][-50:]

    ws["continuity"]["recent_commands"].append(req.input[:300])
    ws["continuity"]["recent_commands"] = ws["continuity"]["recent_commands"][-30:]

    for asset in response.get("ready_assets", [])[:5]:
        ws["continuity"]["recent_assets"].append({
            "id": f"asset_{uuid.uuid4().hex[:8]}",
            "created_at": now_iso(),
            "content": str(asset)[:3000]
        })

    ws["continuity"]["recent_assets"] = ws["continuity"]["recent_assets"][-50:]

    save_workspace(ws)

    response["executive_presence"] = presence
    response["memory_context"] = {
        "presence_mode": mode,
        "pressure": pressure,
        "recent_decisions": len(ws["decisions"]),
        "presence_history": len(ws["operator_state"]["presence_history"])
    }

    response["version"] = APP_VERSION

    return response

@app.get("/engine-state")
def engine_state(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)

    return {
        "status": "success",
        "version": APP_VERSION,
        "operator_state": ws["operator_state"],
        "recent_decisions": ws["decisions"][-10:],
        "recent_assets": ws["continuity"]["recent_assets"][-10:]
    }

@app.get("/operator-scan")
def operator_scan(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)

    latest = ws["operator_state"]["presence_history"][-1] if ws["operator_state"]["presence_history"] else None

    return {
        "status": "success",
        "version": APP_VERSION,
        "presence_mode": ws["operator_state"].get("presence_mode"),
        "pressure": ws["operator_state"].get("current_pressure"),
        "latest_presence": latest,
        "recommended_command": "Generate the final executive-grade output with compressed reasoning."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36560",
            "Responses use compressed executive language",
            "Responses identify wasted motion",
            "Responses include what NOT to do",
            "Responses shift tone based on intent",
            "Presence modes stored in engine state"
        ],
        "proposal_test": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
        "presence_test": "Convert this into a specific executive operating brief with decision, next action, asset, risk, and follow-up command."
    }
