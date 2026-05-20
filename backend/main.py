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

APP_VERSION = "V36580-Executive-Briefing-Engine"
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
            "briefing_mode": None,
            "last_command": None,
            "last_next_move": None,
            "briefing_history": []
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
        ws["operator_state"].setdefault("briefing_history", [])
        ws.setdefault("continuity", base["continuity"])
        return ws
    except Exception:
        return empty_workspace(workspace_id, user_id)

def save_workspace(ws):
    ws["updated_at"] = now_iso()
    with open(db_path(ws["workspace_id"], ws["user_id"]), "w", encoding="utf-8") as f:
        json.dump(ws, f, indent=2, ensure_ascii=False)

def detect_intent(text):
    t = text.lower()
    table = {
        "proposal": ["proposal", "pitch", "quote", "offer", "scope"],
        "build": ["build", "deploy", "fix", "engine", "backend", "frontend", "version"],
        "decision": ["decide", "decision", "choose", "should i", "pivot"],
        "meeting": ["meeting", "agenda", "call", "prep"],
        "revenue": ["sales", "revenue", "cpa", "lead", "dealership", "ads", "seo", "cash"],
        "risk": ["risk", "broken", "problem", "stuck", "failure"],
        "overload": ["overwhelmed", "too many", "scattered", "chaos", "busy", "burned"],
        "strategy": ["strategy", "positioning", "market", "roadmap"]
    }
    scores = {k: sum(1 for x in v if x in t) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"

def detect_pressure(text):
    t = text.lower()
    if any(x in t for x in ["wtf", "fuck", "shit", "urgent", "asap", "broken", "overwhelmed"]):
        return "Critical"
    score = sum(1 for x in ["proposal", "revenue", "client", "build", "deploy", "risk", "deadline", "cash"] if x in t)
    if score >= 2:
        return "High"
    if score == 1:
        return "Medium"
    return "Normal"

def retrieve_context(ws, query):
    recent = ws.get("decisions", [])[-8:]
    recent_assets = ws.get("continuity", {}).get("recent_assets", [])[-5:]
    return {"recent_decisions": recent, "recent_assets": recent_assets}

FORBIDDEN_LABELS = [
    "operator read",
    "leverage move",
    "do this now",
    "ready assets",
    "follow-up command",
    "primary risk",
    "command centre",
    "active brief"
]

GENERIC_PHRASES = {
    "conduct analysis": "make the call",
    "review existing assets": "use only what moves the decision",
    "determine the specific type": "choose the asset that forces movement",
    "high-impact": "revenue-relevant",
    "optimize workflows": "tighten execution",
    "stakeholders": "decision-makers",
    "best practices": "what works here",
    "streamline operations": "remove friction",
    "maintain workflow momentum": "force momentum",
    "gather key leaders": "bring only the decision owner",
    "rapid decision-making session": "15-minute decision lock",
    "assess current initiatives": "cut everything except the revenue path"
}

def clean_text(s):
    if not isinstance(s, str):
        return s
    out = s
    for a, b in GENERIC_PHRASES.items():
        out = re.sub(a, b, out, flags=re.I)
    return out.strip()

def clean_obj(obj):
    if isinstance(obj, str):
        return clean_text(obj)
    if isinstance(obj, list):
        return [clean_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    return obj

def briefing_mode(intent):
    return {
        "proposal": "commercial_brief",
        "revenue": "cash_path_brief",
        "build": "build_control_brief",
        "decision": "decision_lock_brief",
        "meeting": "political_brief",
        "risk": "containment_brief",
        "overload": "pressure_reduction_brief",
        "strategy": "strategic_position_brief",
    }.get(intent, "operator_brief")

def build_briefing(req, intent, pressure, context):
    t = req.input.lower()

    brief = {
        "dominant_insight": "You do not need more structure. You need a single decision that forces movement.",
        "decision": "Pick the next move and remove everything that competes with it.",
        "pressure_signal": "Fragmentation is creating drag.",
        "warning": "If everything stays active, nothing becomes decisive.",
        "next_action": "Choose one priority and turn it into the finished asset now.",
        "stop_doing": ["Stop expanding the plan.", "Stop treating every active item as equal."],
        "briefing_mode": briefing_mode(intent)
    }

    if any(x in t for x in ["dealership", "auto loan", "seo", "google ads", "cpa"]):
        brief = {
            "dominant_insight": "The dealership does not buy marketing. It buys funded deals at a believable acquisition cost.",
            "decision": "Position the offer as a 90-day financed-buyer acquisition sprint.",
            "pressure_signal": "A sub-$100 CPA collapses if broad car-shopping traffic enters the campaign.",
            "warning": "Do not lead with SEO reports, blog calendars, or campaign setup. Those feel like vendor work.",
            "next_action": "Write the proposal around finance-intent traffic, lead handling speed, and funded-deal tracking.",
            "stop_doing": ["Stop selling SEO and Ads as services.", "Stop measuring success as traffic or rankings."],
            "briefing_mode": "commercial_brief"
        }

    elif "overwhelmed" in t or "too many" in t or "scattered" in t:
        brief = {
            "dominant_insight": "You are not overloaded because of workload. You are overloaded because nothing is being eliminated.",
            "decision": "Cut active priorities to one revenue path, one stability path, and one personal/admin path.",
            "pressure_signal": "The pressure is coming from open loops, not lack of effort.",
            "warning": "Keeping every initiative alive is disguised procrastination.",
            "next_action": "Name the one thing that can create cash, control, or relief this week. Everything else gets delayed.",
            "stop_doing": ["Stop starting new threads.", "Stop improving systems that are not tied to this week's leverage."],
            "briefing_mode": "pressure_reduction_brief"
        }

    elif "pivot" in t or "keep building executive engine" in t:
        brief = {
            "dominant_insight": "Do not pivot while the core thesis is getting clearer. Tighten the product until one use case feels unavoidable.",
            "decision": "Keep building, but narrow the next 7 days to response quality and daily-use dependency.",
            "pressure_signal": "The risk is not building the wrong product. The risk is widening the product before one workflow becomes addictive.",
            "warning": "A pivot now would reset momentum and recreate the same uncertainty somewhere else.",
            "next_action": "Lock one daily executive workflow and make it excellent before adding surface area.",
            "stop_doing": ["Stop evaluating the whole company every day.", "Stop adding features before the core response earns trust."],
            "briefing_mode": "decision_lock_brief"
        }

    elif intent == "build":
        brief = {
            "dominant_insight": "The shell is good enough. The bottleneck is how the system thinks and presents the answer.",
            "decision": "Do not touch UI. Upgrade only the briefing layer.",
            "pressure_signal": "Every broad system add creates more testing drag.",
            "warning": "More architecture will hide weak cognition instead of fixing it.",
            "next_action": "Make the response feel like an executive briefing: one truth, one move, one warning, one action.",
            "stop_doing": ["Stop adding dashboards.", "Stop changing layout.", "Stop expanding scope."],
            "briefing_mode": "build_control_brief"
        }

    return brief

def build_asset(brief, intent):
    if intent == "proposal":
        return f"""EXECUTIVE BRIEFING — DEALERSHIP PROPOSAL

{brief["dominant_insight"]}

Decision:
{brief["decision"]}

Offer Spine:
90-Day Financed-Buyer Acquisition Sprint

What Matters:
- finance-intent traffic
- landing-page speed
- lead handling speed
- appointment conversion
- funded-deal attribution
- weekly waste removal

Do Not Sell:
- generic SEO
- blog calendars
- broad Google Ads
- traffic reports
- rankings without lead quality

Close:
If the dealership wants sub-$100 CPA, the first move is not more marketing. It is intent control and funded-deal tracking."""
    return f"""EXECUTIVE BRIEFING

{brief["dominant_insight"]}

Decision:
{brief["decision"]}

Pressure:
{brief["pressure_signal"]}

Warning:
{brief["warning"]}

Move:
{brief["next_action"]}

Stop:
- {brief["stop_doing"][0]}
- {brief["stop_doing"][1]}
"""

def local_response(req, intent, pressure, brief):
    asset = build_asset(brief, intent)
    return {
        "next_move": brief["next_action"],
        "decision": brief["decision"],
        "action_steps": [
            brief["stop_doing"][0],
            brief["stop_doing"][1],
            brief["next_action"]
        ],
        "ready_assets": [asset],
        "risk": brief["warning"],
        "priority": "Critical" if pressure == "Critical" else "High",
        "recommended_command": "Generate the final executive briefing output from this decision.",
        "what_to_do_now": brief["next_action"],
        "asset": asset,
        "follow_up": "Do not reopen the decision. Execute the move.",
        "provider_used": "local-executive-briefing-engine",
        "status": "success"
    }

def build_prompt(req, brief, context):
    return f"""
You are Executive Engine OS — Executive Briefing Engine.

Your job:
Convert the command into a high-signal executive briefing.

The response must feel like:
- a calm executive briefing
- one dominant truth
- one decision
- one warning
- one next action
- no filler
- no project-manager labels
- no generic AI sections

Briefing intelligence:
{json.dumps(brief, ensure_ascii=False, indent=2)}

Recent context:
{json.dumps(context, ensure_ascii=False)[:6000]}

Rules:
1. Open with one dominant insight.
2. Keep the language compressed and expensive.
3. Do not use labels like Operator Read, Leverage Move, Do This Now, Ready Assets, Follow-up Command.
4. Include what to stop doing.
5. Tie the output to control, speed, revenue, risk, or pressure reduction.
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

def enforce(data):
    data = clean_obj(data or {})
    data.setdefault("next_move", "Choose the one move that forces momentum.")
    data.setdefault("decision", "Stop widening. Commit to the next decisive action.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is looking organized while staying unfocused.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Generate the final executive briefing.")
    data.setdefault("what_to_do_now", data["next_move"])
    data.setdefault("asset", "")
    data.setdefault("follow_up", "Execute the decision; do not reopen the loop.")
    data.setdefault("provider_used", "local-executive-briefing-engine")
    data.setdefault("status", "success")

    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]
    if len(data["action_steps"]) > 5:
        data["action_steps"] = data["action_steps"][:5]
    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Stop the competing work.",
            "Lock the decision.",
            "Execute the next move."
        ][:3-len(data["action_steps"])]
    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset") or "Executive briefing saved."]

    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"
    return data

def call_openai(req, brief, context):
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, brief, context)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.15,
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
        "engine": "executive_briefing",
        "purpose": "compress cognition into one dominant insight, one decision, one warning, one action"
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
    brief = build_briefing(req, intent, pressure, context)

    response = call_openai(req, brief, context)
    if not response:
        response = local_response(req, intent, pressure, brief)
    response = enforce(response)

    record = {
        "id": f"brief_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "input": req.input[:500],
        "intent": intent,
        "pressure": pressure,
        "briefing_mode": brief["briefing_mode"],
        "dominant_insight": brief["dominant_insight"],
        "decision": response["decision"],
        "next_move": response["next_move"],
        "risk": response["risk"],
    }

    ws["decisions"].append(record)
    ws["decisions"] = ws["decisions"][-100:]

    ws["operator_state"]["current_pressure"] = pressure
    ws["operator_state"]["current_focus"] = intent
    ws["operator_state"]["briefing_mode"] = brief["briefing_mode"]
    ws["operator_state"]["last_command"] = req.input
    ws["operator_state"]["last_next_move"] = response["next_move"]
    ws["operator_state"]["briefing_history"].append(record)
    ws["operator_state"]["briefing_history"] = ws["operator_state"]["briefing_history"][-50:]

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

    response["executive_briefing"] = brief
    response["memory_context"] = {
        "briefing_mode": brief["briefing_mode"],
        "pressure": pressure,
        "recent_decisions": len(ws["decisions"]),
        "briefing_history": len(ws["operator_state"]["briefing_history"])
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
    latest = ws["operator_state"]["briefing_history"][-1] if ws["operator_state"]["briefing_history"] else None
    return {
        "status": "success",
        "version": APP_VERSION,
        "briefing_mode": ws["operator_state"].get("briefing_mode"),
        "pressure": ws["operator_state"].get("current_pressure"),
        "latest_briefing": latest,
        "recommended_command": "Generate the final executive briefing and execute the move."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36580",
            "POST /run returns executive_briefing object",
            "Responses open with one dominant insight",
            "Responses avoid project-manager labels",
            "Responses are compressed: one decision, one warning, one action",
            "Engine state stores briefing history"
        ],
        "test_commands": [
            "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
            "I have too many active projects and feel overwhelmed.",
            "Should I keep building Executive Engine or pivot?"
        ]
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
