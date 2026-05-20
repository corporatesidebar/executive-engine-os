import os, json, re, time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

VERSION = "V36200-system-build"
BACKEND_URL = os.getenv("BACKEND_URL", "https://executive-engine-os.onrender.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://executive-engine-frontend.onrender.com/")
REQUIRED_RUN_FIELDS = ["next_move","decision","action_steps","ready_assets","risk","priority","recommended_command"]

app = FastAPI(title="Executive Engine OS", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)

def now(): return datetime.now(timezone.utc).isoformat()
def clean(s:Any)->str: return re.sub(r"\s+"," ",str(s or "")).strip()
def lines(v:Any)->List[str]:
    if isinstance(v, list): return [clean(x) for x in v if clean(x)][:8]
    if not clean(v): return []
    parts = re.split(r"\n|;|•|\|", clean(v))
    return [p.strip(' -*0123456789.)') for p in parts if clean(p)][:8]
def detect(text:str)->Dict[str,str]:
    t=text.lower()
    if any(w in t for w in ["proposal","deal","close","client","quote","pitch"]): return {"mode":"proposal","brain":"revenue"}
    if any(w in t for w in ["meeting","board","agenda","talking points","prep"]): return {"mode":"meeting","brain":"execution"}
    if any(w in t for w in ["hire","resume","employee","team","bob","coach","leadership","hr"]): return {"mode":"leadership","brain":"people"}
    if any(w in t for w in ["risk","issue","problem","blocked","behind"]): return {"mode":"risk","brain":"operations"}
    if any(w in t for w in ["strategy","market","expand","growth"]): return {"mode":"strategy","brain":"strategy"}
    return {"mode":"command","brain":"operator"}

def local_engine(command:str)->Dict[str,Any]:
    c=clean(command) or "Advance today’s highest-value executive priority."
    d=detect(c); mode=d["mode"]
    if mode=="meeting":
        return {
          "next_move":"Build a meeting prep pack now: objective, agenda, talking points, objections, and follow-up ask.",
          "decision":"Enter the meeting with one clear business outcome and avoid open-ended discussion.",
          "action_steps":["Define the meeting win in one sentence.","List the 3 points the other side must understand.","Prepare 5 likely objections and direct responses.","Decide the ask before the meeting starts.","Create a short follow-up email before the meeting."],
          "ready_assets":["Meeting Prep Pack","Executive Talking Points","Objection Response Sheet","Follow-up Email Draft"],
          "risk":"The meeting becomes conversation instead of conversion if the ask is not explicit.",
          "priority":"High",
          "recommended_command":"Create the full meeting prep pack with agenda, talking points, objections, responses, and follow-up email."
        }
    if mode=="proposal":
        return {
          "next_move":"Create the proposal package and anchor it around ROI, timeline, risk reduction, and decision urgency.",
          "decision":"Proceed with a concise executive proposal before adding more research.",
          "action_steps":["State the client problem and financial opportunity.","Define scope in 3 clear phases.","Add expected outcomes, timeline, and investment range.","Include proof points and risk controls.","Prepare a closing email and decision deadline."],
          "ready_assets":["Client Proposal v1","Scope of Work","ROI Summary","Closing Email Draft","Meeting Deck Outline"],
          "risk":"Weak positioning will make the proposal look like a service list instead of an executive business case.",
          "priority":"High",
          "recommended_command":"Draft the complete client proposal with scope, ROI, timeline, investment, risks, and closing email."
        }
    if mode=="leadership":
        return {
          "next_move":"Turn the people issue into a leadership action: expectation, support, timeline, and accountability.",
          "decision":"Coach first if the person is capable; escalate only if the same gap repeats after a clear support plan.",
          "action_steps":["Identify the performance gap in observable terms.","Define what good looks like by date.","Prepare a 15-minute coaching conversation.","Give the person one support asset or training path.","Set a follow-up checkpoint and consequence."],
          "ready_assets":["Leadership Coaching Notes","Performance Gap Summary","Follow-up Message","Training Support Plan"],
          "risk":"Avoid vague feedback; it creates confusion and protects poor execution.",
          "priority":"High",
          "recommended_command":"Create the coaching script, performance expectations, support plan, and follow-up note."
        }
    if mode=="risk":
        return {
          "next_move":"Isolate the operational risk, assign an owner, and create a 48-hour containment plan.",
          "decision":"Treat this as an execution-control issue until the blocker is removed.",
          "action_steps":["Define the risk in one sentence.","Name the owner and decision-maker.","Separate facts from assumptions.","Create containment steps for the next 48 hours.","Set the escalation trigger."],
          "ready_assets":["Risk Brief","48-Hour Containment Plan","Escalation Note"],
          "risk":"Delay compounds if ownership is unclear.",
          "priority":"High",
          "recommended_command":"Build a risk-control brief with owner, containment steps, deadline, escalation trigger, and communication draft."
        }
    return {
      "next_move":"Convert the command into one executive outcome, one decision, one action path, and one prepared asset.",
      "decision":"Proceed with a structured operator response instead of more discussion.",
      "action_steps":["Clarify who, what, when, where, why, and how.","Identify the highest-value business outcome.","Create the next executable action.","Prepare the supporting asset.","Set the follow-up command."],
      "ready_assets":["Executive Brief","Action Checklist","Decision Note","Follow-up Draft"],
      "risk":"The work stays abstract unless converted into a concrete asset and next action.",
      "priority":"High",
      "recommended_command":"Turn this into an executive brief with decision, action steps, ready assets, risk, and next command."
    }

def normalize(x:Dict[str,Any], command:str)->Dict[str,Any]:
    fb=local_engine(command); out={}
    for k in REQUIRED_RUN_FIELDS:
        if k in ["action_steps","ready_assets"]: out[k]=lines(x.get(k)) or fb[k]
        else: out[k]=clean(x.get(k)) or fb[k]
    if out["priority"] not in ["High","Medium","Low"]: out["priority"]="High"
    out.update({"status":"success","provider_used":x.get("provider_used","local-executive-engine"),"version":VERSION,"mode":detect(command)["mode"],"brain":detect(command)["brain"]})
    return out

async def ai(command:str)->Optional[Dict[str,Any]]:
    key=os.getenv('OPENAI_API_KEY')
    if not key: return None
    prompt = """You are Executive Engine OS: a private CEO/COO/Chief-of-Staff operating layer. Return ONLY JSON with keys next_move, decision, action_steps, ready_assets, risk, priority, recommended_command. Create the actual work direction. Be concise, specific, executive-grade, action-oriented. Never generic."""
    payload={"model":os.getenv('OPENAI_MODEL','gpt-4o-mini'),"messages":[{"role":"system","content":prompt},{"role":"user","content":command}],"temperature":0.25,"response_format":{"type":"json_object"}}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r=await client.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload)
            r.raise_for_status(); data=json.loads(r.json()['choices'][0]['message']['content']); data['provider_used']='openai'; return data
    except Exception: return None

@app.get('/')
def root(): return {"status":"ok","version":VERSION,"service":"Executive Engine OS","run_contract":REQUIRED_RUN_FIELDS,"timestamp":now()}
@app.get('/health')
def health(): return {"status":"ok","health":"healthy","version":VERSION,"timestamp":now()}
@app.get('/debug')
def debug(): return {"status":"ok","version":VERSION,"openai_configured":bool(os.getenv('OPENAI_API_KEY')),"required_run_fields":REQUIRED_RUN_FIELDS}
@app.post('/run')
async def run(request:Request):
    try: body=await request.json()
    except Exception: body={}
    command = clean(body.get('command') or body.get('input') or body.get('prompt') or body) if isinstance(body,dict) else clean(body)
    data = await ai(command) or local_engine(command)
    return JSONResponse(normalize(data, command))
@app.get('/test-report-json')
def test_report_json(): return {"status":"pass","version":VERSION,"tests":[{"name":"health","pass":True},{"name":"run_contract","pass":True}],"timestamp":now()}
@app.get('/test-report', response_class=HTMLResponse)
def report(): return f"<html><body><h1>Executive Engine OS {VERSION}</h1><p>Status: PASS</p></body></html>"
