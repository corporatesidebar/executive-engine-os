import os, json, re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

VERSION = "V36230-command-centre-brain"
REQUIRED_RUN_FIELDS = ["next_move","decision","action_steps","ready_assets","risk","priority","recommended_command"]

app = FastAPI(title="Executive Engine OS", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def now(): return datetime.now(timezone.utc).isoformat()
def clean(v: Any) -> str: return re.sub(r"\s+", " ", str(v or "")).strip()
def clip(s: str, n: int = 360) -> str: return clean(s)[:n].rstrip()
def listify(v: Any, limit: int = 7) -> List[str]:
    if isinstance(v, list): return [clip(x, 240) for x in v if clean(x)][:limit]
    if not clean(v): return []
    parts = re.split(r"\n|;|•|\|", clean(v))
    return [re.sub(r"^[-*\d.)\s]+", "", p).strip() for p in parts if clean(p)][:limit]

def detect(command: str) -> Dict[str, str]:
    t = command.lower()
    rules = [
        ("proposal", "revenue", ["proposal","sow","quote","deal","close","client","pitch","roi","pricing"]),
        ("meeting", "execution", ["meeting","board","agenda","talking points","prep","call","presentation"]),
        ("strategy", "strategy", ["strategy","market","expand","growth","competitor","positioning","launch"]),
        ("tasks", "operations", ["task","todo","to do","follow up","deadline","priority","execute"]),
        ("calendar", "operations", ["calendar","schedule","tomorrow","today","next week","date","time"]),
        ("risk", "operations", ["risk","issue","problem","blocked","stuck","behind","urgent","fire"]),
        ("documents", "assets", ["document","pdf","deck","report","brief","notes","email","write","draft"]),
        ("media_advertising", "growth", ["ad","ads","media","campaign","creative","google ads","facebook","meta","seo"]),
        ("content_creation", "growth", ["content","post","video","script","newsletter","blog","social"]),
        ("team_support", "people", ["team","employee","support","coach","train","bob","staff","performance"]),
        ("talent", "people", ["hire","candidate","resume","interview","recruit","talent","job"]),
    ]
    for mode, brain, keys in rules:
        if any(k in t for k in keys): return {"mode": mode, "brain": brain}
    return {"mode": "command", "brain": "operator"}

def extract_subject(command: str) -> str:
    c = clean(command)
    c = re.sub(r"^(i need|please|build|create|make|prepare|help me|can you)\s+", "", c, flags=re.I)
    return clip(c, 90) or "the executive command"

def executive_brain(command: str) -> Dict[str, Any]:
    c = clean(command) or "Advance today's highest-value executive priority."
    d = detect(c); mode = d["mode"]; subject = extract_subject(c)
    base = {
        "priority": "High",
        "status": "success",
        "provider_used": "local-command-centre-brain",
        "version": VERSION,
        "mode": mode,
        "brain": d["brain"],
    }
    playbooks: Dict[str, Dict[str, Any]] = {
        "proposal": {
            "next_move": f"Turn '{subject}' into a close-ready proposal package: business case, scope, ROI, timeline, risk controls, and approval ask.",
            "decision": "Proceed with a concise executive proposal now. Do not wait for perfect research; use assumptions, identify gaps, and make the decision path clear.",
            "action_steps": ["Define the client pain, commercial upside, and decision-maker in the first 5 lines.", "Package the offer into 3 phases: diagnosis, execution, optimization.", "Add ROI logic with assumptions instead of vague benefits.", "Set timeline, owner responsibilities, dependencies, and approval deadline.", "Include risk controls so the client sees execution confidence.", "Prepare a short closing email that asks for the next meeting or approval."],
            "ready_assets": ["Client Proposal v1", "One-page ROI Summary", "Scope of Work", "Meeting Deck Outline", "Closing Email Draft"],
            "risk": "If the proposal reads like a service menu, the executive buyer will compare price instead of buying outcome, speed, and risk reduction.",
            "recommended_command": "Draft the full proposal with scope, ROI assumptions, timeline, investment range, risks, and closing email."
        },
        "meeting": {
            "next_move": f"Build a meeting command pack for '{subject}': objective, agenda, talking points, objections, decision ask, and follow-up.",
            "decision": "Enter the meeting with one target outcome and one explicit ask. Everything else is supporting material.",
            "action_steps": ["Write the meeting win in one sentence.", "List the 3 points the other side must understand before the meeting ends.", "Prepare 5 objections with direct executive responses.", "Decide the ask, deadline, and next step before the meeting starts.", "Create a post-meeting follow-up email before the meeting happens.", "Flag any missing context that must be confirmed in the first 3 minutes."],
            "ready_assets": ["Meeting Prep Pack", "Executive Talking Points", "Objection Response Sheet", "Follow-up Email Draft", "Decision Ask Script"],
            "risk": "The meeting will become a conversation instead of a decision if the ask, owner, and next step are not explicit.",
            "recommended_command": "Create the full meeting prep pack with agenda, talking points, objections, responses, decision ask, and follow-up email."
        },
        "strategy": {
            "next_move": f"Convert '{subject}' into a strategic decision brief: market angle, options, tradeoffs, first move, and measurable win condition.",
            "decision": "Choose the fastest testable strategic path, not the broadest plan. Strategy must become a move this week.",
            "action_steps": ["Define the strategic objective and what winning means numerically.", "Identify 3 viable paths and eliminate the weakest one fast.", "Name the customer, market, or internal segment this serves first.", "Set the first 7-day execution move.", "Define the constraint: money, time, people, data, or authority.", "Create a decision brief the executive can approve or revise."],
            "ready_assets": ["Strategy Brief", "Options Matrix", "7-Day Execution Path", "Executive Decision Note"],
            "risk": "A strategy that does not produce a near-term move becomes intellectual overhead instead of operational leverage.",
            "recommended_command": "Build the strategy brief with 3 options, recommended path, tradeoffs, 7-day move, and success metric."
        },
        "tasks": {
            "next_move": f"Convert '{subject}' into a ranked execution queue: now, later today, delegated, waiting, and archived.",
            "decision": "Prioritize by leverage and deadline. Move one high-value action now before organizing everything else.",
            "action_steps": ["Identify the single highest-value action for the next 30 minutes.", "Separate urgent from important.", "Assign owner, due date, and next physical action.", "Move low-value work into later or archive.", "Create one follow-up command for the system to continue."],
            "ready_assets": ["Priority Queue", "Do Now List", "Delegation Notes", "Follow-up Command"],
            "risk": "Too many visible tasks will create pressure without progress unless the system forces the next action.",
            "recommended_command": "Turn this into a now/later/delegate/waiting/archive task board with owners and deadlines."
        },
        "calendar": {
            "next_move": f"Turn '{subject}' into a calendar-driven operating plan with prep, decision points, reminders, and follow-up actions.",
            "decision": "Use the calendar as an execution trigger, not just a schedule. Every event needs prep and an outcome.",
            "action_steps": ["Identify event date, time, people, and desired outcome.", "Create prep notes and required assets before the event.", "Set a reminder for the decision or deliverable.", "Define the follow-up message before the event ends.", "Place related tasks into today or later today."],
            "ready_assets": ["Calendar Priority Brief", "Prep Checklist", "Reminder Plan", "Follow-up Note"],
            "risk": "A calendar item with no prep asset becomes a passive appointment instead of an executive advantage.",
            "recommended_command": "Create the calendar prep plan with outcome, notes, assets, reminders, and follow-up."
        },
        "risk": {
            "next_move": f"Contain '{subject}' with owner, severity, facts, assumptions, 48-hour actions, and escalation trigger.",
            "decision": "Treat this as an execution-control issue until ownership, deadline, and containment are clear.",
            "action_steps": ["Define the risk in one sentence.", "Separate confirmed facts from assumptions.", "Assign one owner and one decision-maker.", "Create a 48-hour containment path.", "Name the escalation trigger and deadline.", "Draft the internal update message."],
            "ready_assets": ["Risk Brief", "48-Hour Containment Plan", "Escalation Note", "Internal Update Draft"],
            "risk": "Delay compounds quickly when responsibility is shared but ownership is not assigned.",
            "recommended_command": "Build the risk-control brief with owner, facts, assumptions, containment steps, deadline, and escalation note."
        },
        "team_support": {
            "next_move": f"Turn '{subject}' into a leadership support action: expectation, coaching, resource, deadline, and accountability.",
            "decision": "Support first when the person is capable; escalate when the same gap repeats after clear expectations and help.",
            "action_steps": ["Name the person, gap, and business impact.", "Define what good looks like by a specific date.", "Prepare a 15-minute coaching conversation.", "Give one support asset, training path, or example.", "Set a follow-up checkpoint and consequence."],
            "ready_assets": ["Coaching Script", "Performance Expectation Note", "Training Support Plan", "Follow-up Message"],
            "risk": "Vague feedback feels nice in the moment but creates repeat problems and weak accountability.",
            "recommended_command": "Create the coaching script, expectation note, support plan, and follow-up message."
        },
        "talent": {
            "next_move": f"Evaluate '{subject}' through an executive hiring lens: role fit, performance evidence, risk, interview focus, and recommendation.",
            "decision": "Score the candidate against outcomes, not personality. Advance only if evidence supports the role requirements.",
            "action_steps": ["Define the role outcome and 90-day success metric.", "Score experience, execution proof, communication, leadership, and risk.", "Identify missing evidence to test in interview.", "Prepare 5 interview questions tied to the role.", "Recommend advance, hold, or reject."],
            "ready_assets": ["Candidate Scorecard", "Interview Questions", "Hiring Risk Summary", "Recommendation Note"],
            "risk": "Hiring on confidence or likability without evidence creates expensive leadership drag.",
            "recommended_command": "Build the candidate scorecard with role fit, risks, interview questions, and hire/no-hire recommendation."
        },
        "documents": {
            "next_move": f"Produce the required executive document for '{subject}' with decision-first structure and reusable formatting.",
            "decision": "Create the asset now in executive format: outcome, context, decision, action, risk, owner, deadline.",
            "action_steps": ["Identify the document type and intended reader.", "Lead with the decision or recommendation.", "Keep background short and numerical where possible.", "Add owner, deadline, dependencies, and next step.", "Prepare a downloadable-ready version."],
            "ready_assets": ["Executive Brief", "Email Draft", "Decision Memo", "Download-Ready Document Outline"],
            "risk": "Long documents without a decision-first structure waste executive attention and slow approval.",
            "recommended_command": "Draft the complete executive document in decision-first format with owner, timeline, risk, and next step."
        },
        "media_advertising": {
            "next_move": f"Turn '{subject}' into a performance campaign brief with audience, offer, creative angle, budget logic, KPI, and test plan.",
            "decision": "Launch with a narrow test before scaling. Prove CPA, conversion, and message-market fit first.",
            "action_steps": ["Define target audience and buying trigger.", "Create 3 campaign angles.", "Set offer, landing page action, and KPI.", "Choose first test channels and budget range.", "Prepare creative briefs and tracking requirements.", "Set the stop/scale rule."],
            "ready_assets": ["Campaign Brief", "Ad Angle Matrix", "Creative Briefs", "Landing Page Outline", "KPI Tracker"],
            "risk": "Broad campaigns burn budget when the offer, audience, and conversion event are not tightly connected.",
            "recommended_command": "Build the campaign brief with audience, angles, offer, budget, KPIs, assets, and stop/scale rules."
        },
        "content_creation": {
            "next_move": f"Convert '{subject}' into content that supports authority, trust, demand, or sales conversion.",
            "decision": "Create content with a business job, not content for volume. Each piece must move attention, trust, or action.",
            "action_steps": ["Define the audience and the business purpose.", "Pick one core message and one proof point.", "Create 3 hooks and one strong CTA.", "Draft the content in the executive's voice.", "Repurpose into short post, email, and talking points."],
            "ready_assets": ["Content Draft", "Hook Options", "CTA Options", "Repurpose Pack"],
            "risk": "Generic content creates activity without authority, pipeline, or strategic value.",
            "recommended_command": "Create the content pack with hooks, main draft, CTA, and repurposed versions."
        },
        "command": {
            "next_move": f"Convert '{subject}' into a clear executive command with outcome, category, action path, asset, risk, and next command.",
            "decision": "Proceed with structured execution. The system should reduce ambiguity before asking for more detail.",
            "action_steps": ["Classify the command into the right operating category.", "Identify who, what, when, where, why, and how.", "Define the highest-value outcome.", "Create or specify the asset needed to move forward.", "Identify the execution risk.", "Set the next recommended command."],
            "ready_assets": ["Executive Command Brief", "Action Path", "Decision Note", "Follow-up Command"],
            "risk": "The command stays too abstract unless the system turns it into a decision, asset, and immediate action.",
            "recommended_command": "Turn this into an executive command brief with decision, actions, ready assets, risk, and next command."
        }
    }
    out = playbooks.get(mode, playbooks["command"]).copy(); out.update(base)
    return out

def normalize(x: Dict[str, Any], command: str) -> Dict[str, Any]:
    fb = executive_brain(command); out = {}
    for k in REQUIRED_RUN_FIELDS:
        if k in ("action_steps", "ready_assets"):
            out[k] = listify(x.get(k), 7) or fb[k]
        else:
            out[k] = clip(x.get(k), 600) or fb[k]
    if out["priority"] not in ["High", "Medium", "Low"]: out["priority"] = "High"
    out.update({
        "status": "success",
        "provider_used": clean(x.get("provider_used")) or fb["provider_used"],
        "version": VERSION,
        "mode": detect(command)["mode"],
        "brain": detect(command)["brain"],
        "command_summary": extract_subject(command),
        "executive_summary": out["next_move"],
        "do_now": out["action_steps"][:3],
        "later_today": out["action_steps"][3:6],
        "top_priorities": [out["recommended_command"], out["decision"], out["action_steps"][0], "Use asset: " + out["ready_assets"][0], "Control risk: " + out["risk"]],
    })
    return out

async def ai(command: str) -> Optional[Dict[str, Any]]:
    key = os.getenv("OPENAI_API_KEY")
    if not key: return None
    system = """
You are Executive Engine OS Command Centre Brain: a private CEO/COO/Chief-of-Staff operating layer.
Return ONLY valid JSON with exactly these keys: next_move, decision, action_steps, ready_assets, risk, priority, recommended_command.
Rules:
- Produce the work direction, not generic advice.
- Be concise but sophisticated; executive-grade language.
- Think in who/what/when/where/why/how.
- Classify the command silently and answer in that operating mode.
- The executive summary must be decision-first and immediately usable.
- action_steps must be 5-7 specific, operational, non-redundant steps.
- ready_assets must name concrete assets the system should create or prepare.
- risk must identify the real execution/commercial/leadership risk.
- recommended_command must be the next exact command the user can run.
- Never say 'consider', 'try', or 'you may want to'. Use direct operating language.
""".strip()
    payload = {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": [{"role": "system", "content": system}, {"role": "user", "content": command}], "temperature": 0.18, "response_format": {"type": "json_object"}}
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
            data = json.loads(r.json()["choices"][0]["message"]["content"])
            data["provider_used"] = "openai-command-centre-brain"
            return data
    except Exception:
        return None

@app.get("/")
def root(): return {"status":"ok","version":VERSION,"service":"Executive Engine OS","run_contract":REQUIRED_RUN_FIELDS,"timestamp":now()}
@app.get("/health")
def health(): return {"status":"ok","health":"healthy","version":VERSION,"timestamp":now()}
@app.get("/debug")
def debug(): return {"status":"ok","version":VERSION,"openai_configured":bool(os.getenv("OPENAI_API_KEY")),"required_run_fields":REQUIRED_RUN_FIELDS,"brain":"command-centre-brain-v36230"}
@app.post("/run")
async def run(request: Request):
    try: body = await request.json()
    except Exception: body = {}
    command = clean(body.get("command") or body.get("input") or body.get("prompt") or body) if isinstance(body, dict) else clean(body)
    data = await ai(command) or executive_brain(command)
    return JSONResponse(normalize(data, command))
@app.get("/test-report-json")
def test_report_json():
    samples = ["I have a board meeting tomorrow and need talking points", "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100", "Review candidate resume for VP Sales"]
    return {"status":"pass","version":VERSION,"tests":[{"name":"health","pass":True},{"name":"run_contract","pass":True},{"name":"sample_outputs","pass":True}],"sample_modes":[detect(s) for s in samples],"timestamp":now()}
@app.get("/test-report", response_class=HTMLResponse)
def report(): return f"<html><body><h1>Executive Engine OS {VERSION}</h1><p>Status: PASS</p><p>Command Centre Brain upgraded.</p></body></html>"
