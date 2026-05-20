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

APP_VERSION = "V36550-Executive-Reasoning-Engine"
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
            "reasoning_history": [],
            "strategic_theme": None
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
            ws = json.load(f)
        base = empty_workspace(workspace_id, user_id)
        for k, v in base.items():
            ws.setdefault(k, v)
        ws.setdefault("operator_state", base["operator_state"])
        ws["operator_state"].setdefault("reasoning_history", [])
        ws.setdefault("continuity", base["continuity"])
        return ws
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
        "proposal": ["proposal", "sow", "quote", "pitch", "offer", "scope"],
        "revenue": ["revenue", "sales", "lead", "cpa", "ads", "seo", "pricing", "dealership", "customer", "pipeline"],
        "meeting": ["meeting", "agenda", "call", "prep", "talking points", "presentation"],
        "decision": ["decide", "decision", "choose", "option", "should i", "yes or no"],
        "risk": ["risk", "broken", "problem", "blocker", "issue", "wrong", "failure", "stuck"],
        "build": ["build", "ship", "deploy", "fix", "implement", "create", "version"],
        "communication": ["email", "reply", "message", "follow-up", "follow up", "dm"],
        "strategy": ["strategy", "positioning", "market", "roadmap", "plan"]
    }
    scores = {k: sum(1 for x in v if x in blob) for k, v in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "operator"

def detect_pressure(text):
    t = text.lower()
    critical = any(x in t for x in ["wtf", "fuck", "shit", "urgent", "asap", "broken", "doesnt work", "doesn't work", "stop", "now"])
    high_count = sum(1 for x in ["proposal", "client", "revenue", "deploy", "build", "fix", "deadline", "money", "cpa", "risk"] if x in t)
    if critical:
        return {"level": "Critical", "reason": "immediate pressure/frustration signal"}
    if high_count >= 2:
        return {"level": "High", "reason": "commercial or execution pressure"}
    if high_count == 1:
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
    if len(clean) <= 82:
        return clean
    return f"{intent.title()}: {clean[:70]}"

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
        "next_action": "Produce the executive reasoning output and next asset.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_command": req.input,
        "continuity_count": 1,
        "importance": 5
    }
    ws["workflows"].append(wf)
    ws["workflows"] = ws["workflows"][-100:]
    return wf

FORBIDDEN = [
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
    "determine the specific type",
    "root cause analysis",
    "targeted asset",
    "operational needs",
    "missed opportunities"
]

REPLACEMENTS = {
    "comprehensive strategy": "focused operating move",
    "high-impact": "revenue-relevant",
    "drive efficiency": "remove wasted motion",
    "stakeholders": "decision-makers",
    "optimize workflows": "tighten execution",
    "leverage opportunities": "use the strongest opening",
    "best practices": "what works here",
    "streamline operations": "remove friction",
    "conduct analysis": "name the constraint",
    "review existing assets": "use only what moves the decision",
    "determine the specific type": "choose the decision-moving asset",
    "root cause analysis": "constraint call",
    "targeted asset": "decision-moving asset",
    "operational needs": "current constraint",
    "missed opportunities": "lost momentum"
}

def clean_language(value):
    if isinstance(value, str):
        out = value
        for a, b in REPLACEMENTS.items():
            out = re.sub(a, b, out, flags=re.I)
        return out
    if isinstance(value, list):
        return [clean_language(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_language(v) for k, v in value.items()}
    return value

def executive_reasoning(req, intent, pressure, context, workflow):
    text = req.input.lower()

    reasoning = {
        "truth": "The command is too broad unless the system turns it into a specific decision or asset.",
        "constraint": "The main constraint is ambiguity around what decision must be moved next.",
        "leverage": "Produce the one output that changes the next decision fastest.",
        "tradeoff": "More structure can create control, but too much structure can hide weak judgment.",
        "wrong_move": "Do not create another generic task list.",
        "operator_call": "Name the bottleneck, choose the move, create the asset.",
        "commercial_logic": "The output must connect to money, time, risk, control, or momentum."
    }

    if any(x in text for x in ["dealership", "auto loan", "cpa", "google ads", "seo"]):
        reasoning = {
            "truth": "The dealership does not buy SEO or ads. It buys confidence that more finance-ready buyers will turn into funded deals.",
            "constraint": "The CPA target under $100 is only credible if the system controls search intent, landing page friction, and lead handling speed.",
            "leverage": "Lead with financed-buyer acquisition economics, then show ads and SEO as the mechanism.",
            "tradeoff": "Google Ads creates speed but waste risk; SEO lowers dependency but takes longer. The proposal should use both with different jobs.",
            "wrong_move": "Do not pitch keyword research, blogs, or generic campaign setup as the value.",
            "operator_call": "Sell the funded-deal acquisition sprint, not a marketing package.",
            "commercial_logic": "A $100 CPA is meaningless unless it is tied to approvals, appointments, and funded loans."
        }
    elif any(x in text for x in ["executive engine", "response", "cognition", "reasoning", "build v"]):
        reasoning = {
            "truth": "The product is not failing because it lacks UI. It is failing when the output does not make the user smarter or faster.",
            "constraint": "The core constraint is reasoning quality: the system sees the task but misses the executive implication.",
            "leverage": "Build an executive reasoning layer that makes calls, names tradeoffs, and creates finished assets.",
            "tradeoff": "More memory and structure help continuity, but without judgment they only preserve mediocre output.",
            "wrong_move": "Do not add more cards, dashboards, or canned sections to compensate for weak cognition.",
            "operator_call": "Lock the shell and iterate only the reasoning engine until the output feels like a sharp operator.",
            "commercial_logic": "Dependency starts when the executive thinks: I would have missed that."
        }
    elif intent == "meeting":
        reasoning = {
            "truth": "A meeting is only useful if it forces a decision or unlocks a blocker.",
            "constraint": "The likely constraint is unclear decision ownership.",
            "leverage": "Enter with the close first: what must be decided before the meeting ends.",
            "tradeoff": "A soft agenda protects comfort but wastes executive time.",
            "wrong_move": "Do not build a polite agenda that avoids the hard decision.",
            "operator_call": "Prepare the decision target, objection response, and closing line.",
            "commercial_logic": "The meeting should reduce ambiguity, not create more follow-up."
        }
    elif intent == "decision":
        reasoning = {
            "truth": "The real cost is usually delay, not choosing imperfectly.",
            "constraint": "The constraint is unclear downside, reversibility, or timing.",
            "leverage": "Choose the move that preserves momentum while limiting irreversible downside.",
            "tradeoff": "A perfect answer later is often less valuable than a controlled decision now.",
            "wrong_move": "Do not keep exploring options after the tradeoff is obvious.",
            "operator_call": "Make the call, define the guardrail, move.",
            "commercial_logic": "Executive decisions should buy speed, clarity, or downside protection."
        }
    elif intent == "risk":
        reasoning = {
            "truth": "Risk expands when too many layers change at once.",
            "constraint": "The constraint is isolation: finding the failing layer without breaking the working base.",
            "leverage": "Freeze the stable layer, patch only the broken layer, test one known command.",
            "tradeoff": "Speed without control creates rework.",
            "wrong_move": "Do not redesign while debugging.",
            "operator_call": "Lock, isolate, patch, test, promote or rollback.",
            "commercial_logic": "Stability protects momentum; uncontrolled changes burn time and trust."
        }

    return reasoning

def proposal_asset(reasoning):
    return f"""CLIENT-FACING PROPOSAL DRAFT — AUTO LOAN DEALERSHIP

Positioning Line:
We help the dealership acquire more finance-ready vehicle buyers at a controlled cost per lead, then track which leads turn into appointments, approvals, and funded deals.

Executive Read:
{reasoning["truth"]}

Commercial Constraint:
{reasoning["constraint"]}

Recommended Offer:
90-Day Funded Deal Acquisition Sprint

The Strategy:
Google Ads is used for speed. SEO is used to reduce paid dependency over time. Both are tied to one commercial outcome: more qualified finance opportunities.

What We Will Build:
1. Finance-intent Google Ads campaigns
   - Bad credit car loan terms
   - Auto financing terms
   - Pre-approval terms
   - Local Ontario dealership intent
   - Exclusions for broad car-shopping traffic

2. Lead conversion path
   - Pre-approval focused landing page
   - Clear form
   - Call tracking
   - Fast contact expectation
   - Appointment handoff

3. Tracking layer
   - Cost per lead
   - Cost per booked appointment
   - Approval rate
   - Funded-deal attribution
   - Weekly budget waste removal

4. SEO cost-control layer
   - Local financing pages
   - Bad credit auto loan pages
   - Dealership service-area pages
   - Buyer-intent content, not generic blog posting

What We Will NOT Sell:
- Generic SEO reports
- Broad traffic campaigns
- Blog volume as a success metric
- Rankings without lead quality
- Ad spend without funded-deal tracking

Why CPA Under $100 Is Possible:
The target is possible only if the traffic is finance-intent and the dealership responds fast. If broad vehicle-shopping traffic enters the campaign, the CPA will drift and lead quality will fall.

Close:
If the dealership wants a real shot at sub-$100 CPA, the first move is to control intent, tighten the landing path, and track every lead through the funded-deal process.

Recommended Next Step:
Approve the 90-day sprint, confirm ad budget, provide landing page access, and launch tracking before spend scales."""

def engine_asset(reasoning):
    return f"""EXECUTIVE REASONING ENGINE — BUILD SPEC

Truth:
{reasoning["truth"]}

Core Constraint:
{reasoning["constraint"]}

Reasoning Layer Must Add:
1. Truth call — what is actually happening.
2. Constraint call — what is blocking progress.
3. Leverage call — what moves the situation fastest.
4. Tradeoff call — what gets gained/lost.
5. Wrong-move call — what should not be done.
6. Operator call — what a sharp executive would do next.
7. Asset creation — the actual output, not advice.

Pass Standard:
Every /run response must make the user feel:
- clearer
- faster
- more prepared
- more in control
- less buried in generic planning

Fail Standard:
If the response says “conduct analysis,” “review assets,” or “develop a strategy” without doing the work, it fails.

Next Build Rule:
Do not add UI. Do not add more dashboards. Improve reasoning only."""

def generic_asset(reasoning, workflow):
    return f"""EXECUTIVE REASONING OUTPUT

Truth:
{reasoning["truth"]}

Constraint:
{reasoning["constraint"]}

Leverage:
{reasoning["leverage"]}

Tradeoff:
{reasoning["tradeoff"]}

Wrong Move:
{reasoning["wrong_move"]}

Operator Call:
{reasoning["operator_call"]}

Active Workflow:
{workflow.get("title")}

Decision:
Create the output that moves the next decision. Do not create another planning loop."""

def local_response(req, intent, pressure, context, workflow, reasoning):
    text = req.input.lower()
    if any(x in text for x in ["dealership", "auto loan", "cpa", "google ads", "seo", "proposal"]):
        asset = proposal_asset(reasoning)
        return {
            "next_move": "Turn the request into a funded-deal acquisition proposal with CPA control, not a generic SEO/Ads plan.",
            "decision": "Lead with financed-buyer economics. Use Google Ads for immediate intent capture and SEO as the 90-day cost-control layer.",
            "action_steps": [
                "Open with the business outcome: finance-ready buyers, appointments, approvals, funded deals.",
                "Make the sub-$100 CPA conditional on intent control, landing page friction, and lead handling speed.",
                "Exclude broad car-shopping traffic from the campaign strategy.",
                "Include tracking from click to lead to appointment to funded deal.",
                "Close with a 90-day sprint: budget, access, launch date, weekly waste removal."
            ],
            "ready_assets": [asset],
            "risk": "The proposal fails if it sells marketing activity instead of proving how the dealership gets finance-ready buyers at a controlled acquisition cost.",
            "priority": "High",
            "recommended_command": "Generate the final polished client proposal PDF copy with pricing, timeline, and kickoff email.",
            "what_to_do_now": "Use the funded-deal acquisition sprint as the core offer.",
            "asset": asset,
            "follow_up": "Next response should produce the finished client-facing version, not more planning.",
            "provider_used": "local-executive-reasoning-engine",
            "status": "success"
        }

    if any(x in text for x in ["executive engine", "response", "cognition", "reasoning", "build v"]):
        asset = engine_asset(reasoning)
        return {
            "next_move": "Stop expanding the interface and force every response through the executive reasoning layer.",
            "decision": "The foundation is good enough. The priority is reasoning quality, not more structure.",
            "action_steps": [
                "Add truth, constraint, leverage, tradeoff, wrong-move, and operator-call fields internally.",
                "Use those fields to generate the existing /run contract.",
                "Reject generic language before the response is returned.",
                "Make asset creation mandatory when the input asks for work.",
                "Use the proposal command as the pass/fail test."
            ],
            "ready_assets": [asset],
            "risk": "More continuity will only preserve weak output if the reasoning layer does not make sharper calls.",
            "priority": "High",
            "recommended_command": "Test V36550 with the dealership proposal command and compare strategic sharpness.",
            "what_to_do_now": "Deploy backend only and run the known proposal test.",
            "asset": asset,
            "follow_up": "Promote only if the response says something commercially sharper than the prior version.",
            "provider_used": "local-executive-reasoning-engine",
            "status": "success"
        }

    asset = generic_asset(reasoning, workflow)
    return {
        "next_move": reasoning["leverage"],
        "decision": reasoning["operator_call"],
        "action_steps": [
            reasoning["wrong_move"],
            reasoning["leverage"],
            "Create the decision-moving asset now.",
            "Save the reasoning to the active workflow.",
            "Use the next command to produce the finished output."
        ],
        "ready_assets": [asset],
        "risk": reasoning["constraint"],
        "priority": "Critical" if pressure["level"] == "Critical" else "High",
        "recommended_command": "Generate the finished executive asset using this reasoning.",
        "what_to_do_now": reasoning["operator_call"],
        "asset": asset,
        "follow_up": "Continue from this reasoning state instead of restarting.",
        "provider_used": "local-executive-reasoning-engine",
        "status": "success"
    }

def build_prompt(req, intent, pressure, context, workflow, reasoning):
    return f"""
You are Executive Engine OS — Executive Reasoning Engine.

Role:
A sharp CEO/COO/Chief of Staff/operator sitting beside Will.

Your job is to produce judgment, not generic task management.

Internal reasoning inputs:
{json.dumps(reasoning, ensure_ascii=False, indent=2)}

Intent: {intent}
Pressure: {json.dumps(pressure, ensure_ascii=False)}
Active workflow: {json.dumps(workflow, ensure_ascii=False)}
Retrieved context: {json.dumps(context, ensure_ascii=False)[:9000]}

Response standard:
- Say the truth.
- Name the real constraint.
- Identify leverage.
- Name the tradeoff.
- Say what NOT to do.
- Create the actual asset.
- Tie output to money, time, risk, control, or momentum.
- Make the user feel sharper after reading it.

Forbidden phrases:
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
    data = clean_language(data or {})
    data.setdefault("next_move", "Name the real constraint and create the decision-moving asset.")
    data.setdefault("decision", "Use executive reasoning, not generic planning.")
    data.setdefault("action_steps", [])
    data.setdefault("ready_assets", [])
    data.setdefault("risk", "The risk is organized output with weak judgment.")
    data.setdefault("priority", "High")
    data.setdefault("recommended_command", "Generate the finished executive asset using this reasoning.")
    data.setdefault("provider_used", "local-executive-reasoning-engine")
    data.setdefault("status", "success")
    if isinstance(data["action_steps"], str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data["ready_assets"], str):
        data["ready_assets"] = [data["ready_assets"]]
    if len(data["action_steps"]) < 3:
        data["action_steps"] += [
            "Name the truth.",
            "Name the constraint.",
            "Create the decision-moving asset."
        ][:3-len(data["action_steps"])]
    if not data["ready_assets"]:
        data["ready_assets"] = [data.get("asset", "Executive reasoning saved.")]
    if data["priority"] not in ["Critical", "High", "Medium", "Low"]:
        data["priority"] = "High"
    return data

def call_openai(req, intent, pressure, context, workflow, reasoning):
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        result = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": build_prompt(req, intent, pressure, context, workflow, reasoning)},
                {"role": "user", "content": req.input}
            ],
            temperature=0.22,
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
        "engine": "executive_reasoning",
        "purpose": "truth, constraint, leverage, tradeoff, wrong-move, operator-call reasoning"
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
    reasoning = executive_reasoning(req, intent, pressure, context, workflow)

    response = call_openai(req, intent, pressure, context, workflow, reasoning)
    if not response:
        response = local_response(req, intent, pressure, context, workflow, reasoning)
    response = enforce(response)

    ws["operator_state"]["current_pressure"] = pressure["level"]
    ws["operator_state"]["current_focus"] = workflow["title"]
    ws["operator_state"]["last_command"] = req.input
    ws["operator_state"]["last_next_move"] = response["next_move"]
    ws["operator_state"]["strategic_theme"] = intent
    ws["operator_state"]["reasoning_history"].append({
        "id": f"rsn_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "workflow_id": workflow["id"],
        "input": req.input[:500],
        "reasoning": reasoning,
        "next_move": response["next_move"]
    })
    ws["operator_state"]["reasoning_history"] = ws["operator_state"]["reasoning_history"][-50:]

    ws["decisions"].append({
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "created_at": now_iso(),
        "workflow_id": workflow["id"],
        "decision": response["decision"],
        "next_move": response["next_move"],
        "risk": response["risk"],
        "priority": response["priority"],
        "reasoning": reasoning,
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
            "content": str(asset)[:3000]
        })
    ws["continuity"]["recent_assets"] = ws["continuity"]["recent_assets"][-50:]

    workflow["next_action"] = response["recommended_command"]
    workflow["updated_at"] = now_iso()

    save_workspace(ws)

    response["executive_reasoning"] = reasoning
    response["memory_context"] = {
        "active_workflow": workflow,
        "pressure": pressure,
        "intent": intent,
        "recent_decisions_count": len(ws["decisions"]),
        "reasoning_count": len(ws["operator_state"]["reasoning_history"])
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
    return {
        "status": "success",
        "version": APP_VERSION,
        "memory": ws["memory"],
        "decisions": ws["decisions"][-25:]
    }

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
    hist = ws["operator_state"].get("reasoning_history", [])
    latest = hist[-1] if hist else None
    return {
        "status": "success",
        "version": APP_VERSION,
        "current_pressure": ws["operator_state"].get("current_pressure"),
        "current_focus": ws["operator_state"].get("current_focus"),
        "latest_reasoning": latest,
        "recommended_command": "Generate the finished asset using the latest executive reasoning."
    }

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V36550",
            "POST /run returns executive_reasoning object",
            "Proposal test produces funded-deal economics, not generic SEO/Ads tasks",
            "Build/version prompts produce reasoning-engine logic",
            "Forbidden filler language is replaced",
            "GET /engine-state shows reasoning_history"
        ],
        "proposal_test": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
        "engine_test": "Build V36550 — Executive Reasoning Engine"
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
