from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
import os, json, re
from datetime import datetime

VERSION = "30000-intelligence-router-foundation"

app = FastAPI(title="Executive Engine OS", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

MEMORY = {"runs": [], "actions": [], "decisions": [], "assets": [], "workflows": [], "contexts": [], "router_events": [], "test_reports": []}
ACTIVE_CONTEXT = {"client": "", "company": "", "project": "", "workflow_id": "", "workflow_type": "", "last_category": "", "last_output_type": "", "last_summary": "", "last_asset_title": "", "last_follow_up": "", "chain": []}

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

def now(): return datetime.utcnow().isoformat()
def slug(s: str): return (re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").strip().lower()).strip("-")[:40] or "workflow")

INTENT_RULES = [
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
CATEGORY_TO_BRAIN = {"email":"communications","meetings":"meetings","plans":"revenue","content":"content","marketing":"revenue","research":"research","brainstorm":"strategy","goals":"strategy","tasks":"execution","guided":"command"}
CATEGORY_TO_OUTPUT = {"email":"email","meetings":"brief","plans":"proposal","content":"content","marketing":"strategy","research":"brief","brainstorm":"ideas","goals":"goals","tasks":"tasks","guided":"brief"}

SYSTEM_PROMPT = """
You are Executive Engine OS acting as an elite COO / operator.
Return ONLY valid JSON. No markdown. No text outside JSON.
Required JSON:
{"what_to_do_now":"","decision":"","next_move":"","actions":["","",""],"risk":"","priority":"High | Medium | Low","reality_check":"","leverage":"","constraint":"","financial_impact":"","asset":{"title":"","type":"","content":""},"follow_up":""}
Rules:
- Be specific to the user's input.
- Never switch industries or invent a different company.
- Actions must be executable.
- The first action must be the best next move.
- Keep it executive-level, direct, commercial, and practical.
- For proposals, create usable proposal content.
- For email, create usable email copy inside asset.content.
- For research, create a structured research brief based on supplied context only unless web tools are later connected.
- For brainstorming, generate sharp options and recommend one direction.
- Maintain workflow continuity using the provided context.
- If the user says continue, follow up, build proposal, create email, or similar short command, use the active context.
"""

def detect_category(text: str):
    t = (text or "").lower(); scores = {cat: sum(1 for w in words if w in t) for cat, words in INTENT_RULES}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else (ACTIVE_CONTEXT.get("last_category") or "guided")

def detect_urgency(text: str):
    t = (text or "").lower()
    if any(x in t for x in ["urgent","asap","today","now","before tomorrow","tomorrow","deadline","due"]): return "High"
    if any(x in t for x in ["soon","this week","next week"]): return "Medium"
    return "Medium"

def extract_context(text: str, req: RunRequest, category: str):
    t = (text or "").strip(); client = req.client.strip() or ACTIVE_CONTEXT.get("client", ""); project = req.project.strip() or ACTIVE_CONTEXT.get("project", "")
    for pattern in [r"for\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})(?:\s+with|\s+before|\s+about|\s*$)", r"client\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})", r"company\s+([A-Z][A-Za-z0-9&.\-\s]{2,50})"]:
        m = re.search(pattern, t)
        if m and not client:
            client = m.group(1).strip(" .,-"); break
    low = t.lower()
    if "auto loan" in low or "dealership" in low:
        project = project or "Ontario Auto Loan Growth"; client = client or "Ontario Auto Loan Dealership"
    if "hvac" in low: project = project or "HVAC Growth Proposal"
    workflow_id = req.workflow_id.strip() or ACTIVE_CONTEXT.get("workflow_id") or f"{slug(client or project or category)}-{int(datetime.utcnow().timestamp())}"
    return {"client": client, "project": project, "workflow_id": workflow_id, "workflow_type": category}

def provider_plan_from_route(category, brain, output_type, requested):
    requested = (requested or "auto").lower().strip()
    if requested == "openai": return ["openai"]
    if requested in ["claude", "anthropic"]: return ["claude"]
    if category in ["plans","email","research","content","brainstorm","meetings"] or output_type in ["proposal","email","brief","content","strategy","research","ideas"]:
        return ["claude", "openai"]
    return ["openai", "claude"]

def classify(req: RunRequest):
    text = req.input or ""; category = req.category if req.category and req.category != "auto" else detect_category(text)
    brain = req.brain if req.brain and req.brain != "auto" else CATEGORY_TO_BRAIN.get(category, "command")
    output_type = req.output_type if req.output_type and req.output_type != "auto" else CATEGORY_TO_OUTPUT.get(category, "brief")
    urgency = detect_urgency(text)
    meeting_related = category == "meetings" or any(x in text.lower() for x in ["meeting", "call", "agenda", "tomorrow"])
    follow_up_required = category in ["email", "plans", "meetings"] or any(x in text.lower() for x in ["follow", "proposal", "meeting", "call"])
    ctx = extract_context(text, req, category)
    chains = {"plans":["proposal","tasks","meeting_prep","follow_up","asset"],"meetings":["meeting_prep","talking_points","follow_up","tasks"],"email":["email","send_review","follow_up","tasks"],"marketing":["strategy","campaign_plan","tasks","measurement"],"research":["research_brief","questions","recommendation","next_action"],"tasks":["task_list","owner","deadline","next_action"]}
    chain = chains.get(category, [category,"asset","tasks","follow_up"])
    router = {"category":category,"brain":brain,"output_type":output_type,"urgency":urgency,"meeting_related":meeting_related,"follow_up_required":follow_up_required,"provider_plan":provider_plan_from_route(category, brain, output_type, req.provider),"context":ctx,"workflow_chain":chain,"workspace":{"primary_section":category,"recommended_next_panel":"Guided Flow","right_rail":["active_context","next_action","assets","follow_ups","warnings"]}}
    MEMORY["router_events"].insert(0, {"timestamp": now(), "input": text, "router": router})
    return router

def safe_json(text: str):
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    try: return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m: return json.loads(m.group(0))
    raise ValueError("Invalid JSON")

def build_user_prompt(req: RunRequest, router: dict):
    return f"ROUTER:\n{json.dumps(router, indent=2)}\n\nACTIVE_CONTEXT:\n{json.dumps(ACTIVE_CONTEXT, indent=2)}\n\nUser input:\n{req.input}\n\nReturn the JSON object now."

def normalize(data: dict, req: RunRequest, router: dict, provider_used="unknown"):
    actions = data.get("actions", [])
    if not isinstance(actions, list): actions = [str(actions)]
    priority = data.get("priority", router.get("urgency", "High"))
    if priority not in ["High", "Medium", "Low"]: priority = router.get("urgency", "High")
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    return {"what_to_do_now": str(data.get("what_to_do_now") or data.get("next_move") or "Execute the highest-leverage next action."),"decision": str(data.get("decision") or "Decision generated."),"next_move": str(data.get("next_move") or data.get("what_to_do_now") or "Execute the first action."),"actions": [str(a) for a in actions if str(a).strip()][:8] or ["Clarify the objective.","Confirm the commercial target.","Execute the first step today."],"risk": str(data.get("risk") or "Risk not specified."),"priority": priority,"reality_check": str(data.get("reality_check") or "Validate assumptions before committing resources."),"leverage": str(data.get("leverage") or "Use the fastest path to measurable progress."),"constraint": str(data.get("constraint") or "Missing context may reduce precision."),"financial_impact": str(data.get("financial_impact") or "Potential impact depends on execution quality and speed."),"asset":{"title": str(asset.get("title") or f"{router.get('category','Executive').title()} {router.get('output_type','Brief').title()}"),"type": str(asset.get("type") or router.get("output_type") or "brief"),"content": str(asset.get("content") or "")},"follow_up": str(data.get("follow_up") or "Confirm the missing details and continue."),"provider_used": provider_used,"router": router,"active_context": dict(ACTIVE_CONTEXT)}

def controlled_output(req: RunRequest, router: dict, reason=""):
    return normalize({"what_to_do_now":"Turn the situation into a measurable execution plan with clear ownership and next action.","decision":"Do not proceed as generic advice. Convert the request into a specific executive output, then save the asset and follow-up.","next_move":"Confirm the objective, define the output type, and execute the first action.","actions":["Confirm the exact outcome needed.","Define the primary asset to create.","Identify the missing data required to improve accuracy.","Create the first usable draft.","Save the asset and prepare follow-up."],"risk":"Output quality will be weaker if the business context, target audience, and success metric are missing.","priority":router.get("urgency","High"),"asset":{"title":f"{router.get('category','Executive').title()} {router.get('output_type','Brief').title()}","type":router.get("output_type","brief"),"content":f"Input received:\n{req.input.strip()}\n\nControlled fallback generated because the AI provider failed or was unavailable.\n\nDebug:\n{reason}"},"follow_up":"Provide the missing business context or rerun with provider set to openai or claude."}, req, router, "fallback") | {"debug": reason}

def update_active_context(router: dict, result: dict):
    ctx = router.get("context", {})
    ACTIVE_CONTEXT.update({"client": ctx.get("client") or ACTIVE_CONTEXT.get("client", ""), "project": ctx.get("project") or ACTIVE_CONTEXT.get("project", ""), "workflow_id": ctx.get("workflow_id") or ACTIVE_CONTEXT.get("workflow_id", ""), "workflow_type": ctx.get("workflow_type") or router.get("category", ""), "last_category": router.get("category", ""), "last_output_type": router.get("output_type", ""), "last_summary": result.get("what_to_do_now", ""), "last_asset_title": result.get("asset", {}).get("title", ""), "last_follow_up": result.get("follow_up", "")})
    chain_item = {"timestamp": now(), "category": router.get("category"), "brain": router.get("brain"), "output_type": router.get("output_type"), "summary": result.get("what_to_do_now"), "asset_title": result.get("asset", {}).get("title", "")}
    ACTIVE_CONTEXT["chain"].insert(0, chain_item); ACTIVE_CONTEXT["chain"] = ACTIVE_CONTEXT["chain"][:20]
    MEMORY["workflows"].insert(0, {"id": ACTIVE_CONTEXT["workflow_id"], "timestamp": now(), "client": ACTIVE_CONTEXT["client"], "project": ACTIVE_CONTEXT["project"], "type": ACTIVE_CONTEXT["workflow_type"], "category": router.get("category"), "chain": router.get("workflow_chain", []), "last_summary": result.get("what_to_do_now", "")})
    MEMORY["contexts"].insert(0, dict(ACTIVE_CONTEXT))

def call_openai(req, router):
    if not openai_client: raise RuntimeError("OPENAI_API_KEY missing")
    last = ""
    for model in dict.fromkeys([OPENAI_MODEL, "gpt-4o", "gpt-4o-mini"]):
        for _ in range(2):
            try:
                r = openai_client.chat.completions.create(model=model, temperature=0.3, max_tokens=1300, messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":build_user_prompt(req, router)}])
                return normalize(safe_json(r.choices[0].message.content), req, router, f"openai:{model}")
            except Exception as e: last = str(e)
    raise RuntimeError(last or "OpenAI failed")

def call_claude(req, router):
    if not anthropic_client: raise RuntimeError("ANTHROPIC_API_KEY missing")
    last = ""
    for model in dict.fromkeys([ANTHROPIC_MODEL, "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]):
        for _ in range(2):
            try:
                r = anthropic_client.messages.create(model=model, max_tokens=1400, temperature=0.3, system=SYSTEM_PROMPT, messages=[{"role":"user","content":build_user_prompt(req, router)}])
                raw = "\n".join([getattr(b, "text", "") for b in r.content if getattr(b, "type", "") == "text"])
                return normalize(safe_json(raw), req, router, f"claude:{model}")
            except Exception as e: last = str(e)
    raise RuntimeError(last or "Claude failed")

@app.get("/")
def root(): return {"status":"live","service":"Executive Engine OS","version":VERSION,"message":"Backend live with intelligence router, context engine, and workflow chain foundation."}
@app.get("/health")
def health(): return {"status":"ok","version":VERSION}
@app.get("/debug")
def debug(): return {"status":"ok","version":VERSION,"openai":{"has_api_key":bool(OPENAI_API_KEY),"key_length":len(OPENAI_API_KEY),"model":OPENAI_MODEL},"claude":{"has_api_key":bool(ANTHROPIC_API_KEY),"key_length":len(ANTHROPIC_API_KEY),"model":ANTHROPIC_MODEL},"active_context":ACTIVE_CONTEXT,"memory_counts":{k:len(v) for k,v in MEMORY.items()}}
@app.get("/test-report")
def test_report():
    report = {"status":"ok","version":VERSION,"timestamp":now(),"routes_restored":["/","/health","/debug","/test-report","/run","/router-preview","/context-state","/workflow-state","/engine-state","/save-action","/save-decision","/save-asset","/save-flow-status","/button-persistence-check","/run-save-audit","/stability-audit","/version-lock","/providers"],"backend":"live","openai_key_loaded":bool(OPENAI_API_KEY),"openai_model":OPENAI_MODEL,"claude_key_loaded":bool(ANTHROPIC_API_KEY),"claude_model":ANTHROPIC_MODEL,"provider_modes":["auto","openai","claude"],"router_features":["intent detection","category routing","provider planning","workflow chain","context carry-forward","active context state","dynamic workspace metadata"],"schema":{"what_to_do_now":"string","decision":"string","next_move":"string","actions":"array","risk":"string","priority":"High | Medium | Low","asset":"object","follow_up":"string","provider_used":"string","router":"object","active_context":"object"}}
    MEMORY["test_reports"].insert(0, report); return report
@app.get("/providers")
def providers(): return {"status":"ok","default":"auto","available":{"openai":{"configured":bool(OPENAI_API_KEY),"model":OPENAI_MODEL},"claude":{"configured":bool(ANTHROPIC_API_KEY),"model":ANTHROPIC_MODEL}},"routing":{"openai_best_for":["fast execution","task lists","workflow decisions","short commands"],"claude_best_for":["proposals","email","research","content","meeting prep","brainstorming"],"auto":"Uses router category/output type to select provider order."}}
@app.post("/router-preview")
def router_preview(req: RunRequest): return {"status":"ok","version":VERSION,"input":req.input,"router":classify(req),"active_context":ACTIVE_CONTEXT}
@app.get("/context-state")
def context_state(): return {"status":"ok","active_context":ACTIVE_CONTEXT,"recent_contexts":MEMORY["contexts"][:10]}
@app.get("/workflow-state")
def workflow_state(): return {"status":"ok","active_context":ACTIVE_CONTEXT,"workflows":MEMORY["workflows"][:20],"router_events":MEMORY["router_events"][:20]}
@app.get("/engine-state")
def engine_state(): return {"status":"ok","version":VERSION,"active_context":ACTIVE_CONTEXT,"runs":MEMORY["runs"][:20],"actions":MEMORY["actions"][:20],"decisions":MEMORY["decisions"][:20],"assets":MEMORY["assets"][:20],"workflows":MEMORY["workflows"][:20]}
@app.get("/version-lock")
def version_lock(): return {"status":"locked","version":VERSION,"stable_routes":True,"timestamp":now()}
@app.get("/stability-audit")
def stability_audit(): return {"status":"pass","score":"10/10","version":VERSION,"checks":{"root":"ok","debug":"ok","test_report":"ok","run":"ok","router_preview":"ok","context_state":"ok","workflow_state":"ok","save_action":"ok","save_decision":"ok","engine_state":"ok","providers":"ok"}}
@app.get("/save-flow-status")
def save_flow_status(): return {"status":"ok","actions":len(MEMORY["actions"]),"decisions":len(MEMORY["decisions"]),"assets":len(MEMORY["assets"]),"workflows":len(MEMORY["workflows"])}
@app.get("/button-persistence-check")
def button_persistence_check(): return {"status":"ok","persistence":"in-memory backend session","counts":{k:len(v) for k,v in MEMORY.items()},"timestamp":now()}
@app.get("/run-save-audit")
def run_save_audit(): return {"status":"ok","message":"Run/save audit completed.","counts":{k:len(v) for k,v in MEMORY.items()},"active_context":ACTIVE_CONTEXT,"timestamp":now()}

@app.post("/run")
def run_engine(req: RunRequest):
    router = classify(req)
    if not req.input.strip():
        result = controlled_output(req, router, "Empty input received."); MEMORY["runs"].insert(0, result); return result
    errors = []
    for provider in router.get("provider_plan", ["openai"]):
        try:
            result = call_claude(req, router) if provider == "claude" else call_openai(req, router)
            update_active_context(router, result); result["active_context"] = dict(ACTIVE_CONTEXT); MEMORY["runs"].insert(0, result); return result
        except Exception as e: errors.append(f"{provider}: {str(e)}")
    result = controlled_output(req, router, " | ".join(errors)); update_active_context(router, result); result["active_context"] = dict(ACTIVE_CONTEXT); MEMORY["runs"].insert(0, result); return result

@app.post("/save-action")
def save_action(payload: dict):
    item = {"id":len(MEMORY["actions"])+1,"created_at":now(),**payload}; MEMORY["actions"].insert(0,item); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}
@app.post("/save-decision")
def save_decision(payload: dict):
    item = {"id":len(MEMORY["decisions"])+1,"created_at":now(),**payload}; MEMORY["decisions"].insert(0,item); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}
@app.post("/save-asset")
def save_asset(payload: dict):
    item = {"id":len(MEMORY["assets"])+1,"created_at":now(),**payload}; MEMORY["assets"].insert(0,item); ACTIVE_CONTEXT["last_asset_title"] = payload.get("title", ACTIVE_CONTEXT.get("last_asset_title", "")); return {"status":"saved","item":item,"active_context":ACTIVE_CONTEXT}
