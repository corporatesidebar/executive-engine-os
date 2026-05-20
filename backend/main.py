from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import os, json, re, uuid

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_VERSION = "V36590-Executive-Pressure-Engine"
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
            "pressure_source": None,
            "current_focus": None,
            "last_command": None,
            "last_next_move": None,
            "pressure_history": []
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
        ws["operator_state"].setdefault("pressure_history", [])
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
        "overload": ["overwhelmed", "too much", "too many", "stressed", "burned", "scattered", "chaos"],
        "avoidance": ["later", "not sure", "maybe", "thinking", "research", "should i", "what if"],
        "decision": ["decide", "decision", "choose", "pivot", "keep building"],
        "revenue": ["revenue", "sales", "cash", "client", "dealership", "proposal", "cpa", "ads", "seo"],
        "build": ["build", "deploy", "backend", "frontend", "version", "engine"],
        "risk": ["risk", "broken", "problem", "stuck", "failure", "doesn't work", "doesnt work"],
        "meeting": ["meeting", "call", "agenda", "prep"],
    }
    scores = {k: sum(1 for x in v if x in t) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"

def pressure_level(text):
    t = text.lower()
    if any(x in t for x in ["wtf", "fuck", "shit", "overwhelmed", "urgent", "asap", "broken", "can't", "cant"]):
        return "Critical"
    score = sum(1 for x in ["too many", "client", "revenue", "deadline", "risk", "deploy", "cash", "proposal"] if x in t)
    if score >= 2:
        return "High"
    if score == 1:
        return "Medium"
    return "Normal"

GENERIC = {
    "conduct analysis": "make the call",
    "review existing assets": "use only what moves the decision",
    "determine the specific type": "choose the asset that forces movement",
    "high-impact": "revenue-relevant",
    "optimize workflows": "tighten execution",
    "stakeholders": "decision-makers",
    "best practices": "what works here",
    "streamline operations": "remove friction",
    "maintain workflow momentum": "force momentum",
    "assess current initiatives": "cut everything except the leverage path",
    "gather key leaders": "bring only the decision owner"
}

def clean_text(s):
    if not isinstance(s, str):
        return s
    out = s
    for a, b in GENERIC.items():
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

def retrieve_context(ws):
    return {
        "recent_decisions": ws.get("decisions", [])[-8:],
        "recent_assets": ws.get("continuity", {}).get("recent_assets", [])[-5:],
        "operator_state": ws.get("operator_state", {})
    }

def pressure_diagnosis(req, intent, level, context):
    t = req.input.lower()

    diagnosis = {
        "pressure_source": "unresolved decision",
        "dominant_truth": "The pressure is not the amount of work. It is the number of open decisions.",
        "hidden_pattern": "You are keeping options alive to avoid committing too early.",
        "stabilizer": "Close one loop. Do not open another.",
        "decision": "Choose one move and make the others inactive.",
        "warning": "Open loops will keep feeling like workload until they are killed, delegated, or delayed.",
        "next_action": "Pick the one decision that would reduce the most pressure today.",
        "stop": ["Stop reopening decisions.", "Stop treating every open idea as active."]
    }

    if "overwhelmed" in t or "too many" in t or "scattered" in t:
        diagnosis = {
            "pressure_source": "focus fragmentation",
            "dominant_truth": "You are not overloaded because of workload. You are overloaded because nothing is being eliminated.",
            "hidden_pattern": "Every open option is taxing your brain like a real obligation.",
            "stabilizer": "Cut the active list before doing more work.",
            "decision": "Keep one revenue path, one stability path, one personal/admin path. Everything else is delayed.",
            "warning": "If you keep all directions alive, the system will organize chaos instead of reducing it.",
            "next_action": "Write the three active priorities. Kill or delay everything outside them.",
            "stop": ["Stop starting new workstreams.", "Stop improving systems that do not reduce pressure this week."]
        }

    elif "pivot" in t or "keep building executive engine" in t:
        diagnosis = {
            "pressure_source": "strategic doubt",
            "dominant_truth": "You do not need a pivot. You need proof that one workflow is valuable enough to repeat daily.",
            "hidden_pattern": "The urge to pivot is coming from response-quality frustration, not a broken thesis.",
            "stabilizer": "Narrow the product until one daily executive use case becomes unavoidable.",
            "decision": "Keep building Executive Engine for 7 more days, but only test daily-use dependency.",
            "warning": "A pivot now resets momentum and recreates the same uncertainty in a new wrapper.",
            "next_action": "Choose one daily executive workflow and make it excellent before adding anything else.",
            "stop": ["Stop judging the whole product every day.", "Stop adding features before one workflow earns trust."]
        }

    elif any(x in t for x in ["dealership", "proposal", "cpa", "seo", "ads"]):
        diagnosis = {
            "pressure_source": "commercial proof",
            "dominant_truth": "The dealership does not need marketing confidence. It needs confidence that spend turns into funded deals.",
            "hidden_pattern": "Marketing deliverables feel safe to sell, but the buyer is judging economic credibility.",
            "stabilizer": "Anchor the proposal to financed-buyer economics.",
            "decision": "Sell a 90-day funded-deal acquisition sprint, not SEO and Ads.",
            "warning": "If the proposal leads with deliverables, it sounds like every agency.",
            "next_action": "Write the offer around intent control, lead handling speed, and funded-deal tracking.",
            "stop": ["Stop selling generic SEO.", "Stop talking about traffic before funded-deal attribution."]
        }

    elif intent == "build":
        diagnosis = {
            "pressure_source": "build-loop fatigue",
            "dominant_truth": "The pressure is coming from repeated build cycles without a locked pass/fail standard.",
            "hidden_pattern": "More versions feel like progress, but they also create testing drag.",
            "stabilizer": "Define one pass/fail test and stop shipping until it passes.",
            "decision": "Lock the shell. Improve only the response psychology layer.",
            "warning": "If every build opens a new concern, the product will never stabilize.",
            "next_action": "Run three test commands and promote only if pressure drops when reading the answer.",
            "stop": ["Stop adding new architecture.", "Stop changing anything that already works."]
        }

    return diagnosis

def build_asset(dx):
    return f"""EXECUTIVE PRESSURE BRIEF

{dx["dominant_truth"]}

Pressure Source:
{dx["pressure_source"]}

Hidden Pattern:
{dx["hidden_pattern"]}

Decision:
{dx["decision"]}

Stabilizer:
{dx["stabilizer"]}

Warning:
{dx["warning"]}

Move:
{dx["next_action"]}

Stop:
- {dx["stop"][0]}
- {dx["stop"][1]}
"""

def local_response(req, intent, level, dx):
    asset = build_asset(dx)
    return {
        "next_move": dx["next_action"],
        "decision": dx["decision"],
        "action_steps": [
            dx["stop"][0],
            dx["stop"][1],
            dx["next_action"]
        ],
        "ready_assets": [asset],
        "risk": dx["warning"],
        "priority": "Critical" if level == "Critical" else "High",
        "recommended_command": "Generate the next pressure-reducing action from this brief.",
        "what_to_do_now": dx["next_action"],
        "asset": asset,
        "follow_up": "Do not open another loop. Close or kill one first.",
        "provider_used": "local-executive-pressure-engine",
        "status": "success"
    }

def build_prompt(req, dx, context):
    return f"""
You are Executive Engine OS — Executive Pressure Engine.

Your job:
Detect the true pressure source behind the command and reduce executive pressure.

Do not act like a task manager.
Do not give generic productivity advice.
Do not create more work unless it closes a loop.

Pressure diagnosis:
{json.dumps(dx, ensure_ascii=False, indent=2)}

Recent context:
{json.dumps(context, ensure_ascii=False)[:6000]}

Response rules:
1. Open with the psychological truth behind the pressure.
2. Name the pressure source.
3. Identify the hidden pattern.
4. Force a stabilizing decision.
5. Say what to stop doing.
6. Keep the response short, calm, and decisive.
7. Tie the answer to control, relief, momentum, revenue, or risk reduction.

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
    data = clean_obj(data or {})
    data.setdefault("next_move", "Close one loop before opening another.")
    data.setdefault("decision", "Reduce pressure by eliminating options, not adding tasks.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is organizing pressure instead of reducing it.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Generate the next pressure-reducing action.")
    data.setdefault("what_to_do_now", data["next_move"])
    data.setdefault("asset", "")
    data.setdefault("follow_up", "Close or kill one open loop.")
    data.setdefault("provider_used", "local-executive-pressure-engine")
    data.setdefault("status", "success")

    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]
    if len(data["action_steps"]) > 5:
        data["action_steps"] = data["action_steps"][:5]
    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Stop one competing priority.",
            "Lock the stabilizing decision.",
            "Execute the next pressure-reducing move."
        ][:3-len(data["action_steps"])]
    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset") or "Pressure brief saved."]
    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"
    return data

def call_openai(req, dx, context):
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, dx, context)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.12,
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
        "engine": "executive_pressure",
        "purpose": "detect pressure source, reduce overload, force stabilizing decisions"
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
    level = pressure_level(req.input)
    context = retrieve_context(ws)
    dx = pressure_diagnosis(req, intent, level, context)

    response = call_openai(req, dx, context)
    if not response:
        response = local_response(req, intent, level, dx)
    response = enforce(response)

    record = {
        "id": f"pressure_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "input": req.input[:500],
        "intent": intent,
        "pressure_level": level,
        "pressure_source": dx["pressure_source"],
        "dominant_truth": dx["dominant_truth"],
        "decision": response["decision"],
        "next_move": response["next_move"],
        "risk": response["risk"]
    }

    ws["decisions"].append(record)
    ws["decisions"] = ws["decisions"][-100:]

    ws["operator_state"]["current_pressure"] = level
    ws["operator_state"]["pressure_source"] = dx["pressure_source"]
    ws["operator_state"]["current_focus"] = intent
    ws["operator_state"]["last_command"] = req.input
    ws["operator_state"]["last_next_move"] = response["next_move"]
    ws["operator_state"]["pressure_history"].append(record)
    ws["operator_state"]["pressure_history"] = ws["operator_state"]["pressure_history"][-50:]

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

    response["executive_pressure"] = dx
    response["memory_context"] = {
        "pressure_level": level,
        "pressure_source": dx["pressure_source"],
        "recent_decisions": len(ws["decisions"]),
        "pressure_history": len(ws["operator_state"]["pressure_history"])
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
    latest = ws["operator_state"]["pressure_history"][-1] if ws["operator_state"]["pressure_history"] else None
    return {
        "status": "success",
        "version": APP_VERSION,
        "pressure": ws["operator_state"].get("current_pressure"),
        "pressure_source": ws["operator_state"].get("pressure_source"),
        "latest_pressure_read": latest,
        "recommended_command": "Generate the next pressure-reducing action and close one loop."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36590",
            "POST /run returns executive_pressure object",
            "Overload prompts identify focus fragmentation",
            "Pivot prompts identify strategic doubt",
            "Proposal prompts identify commercial proof pressure",
            "Build prompts identify build-loop fatigue",
            "Engine state stores pressure history"
        ],
        "test_commands": [
            "I have too many active projects and feel overwhelmed.",
            "Should I keep building Executive Engine or pivot?",
            "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
            "Build V36590 — Executive Pressure Engine"
        ]
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
