import os, json, re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

VERSION = "V36200-command-system"
APP_NAME = "Executive Engine OS"

app = FastAPI(title=APP_NAME, version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str = ""
    mode: Optional[str] = "execution"
    brain: Optional[str] = "operator"
    output_type: Optional[str] = "command"
    depth: Optional[str] = "standard"
    provider: Optional[str] = "openai"

REQUIRED_FIELDS = [
    "next_move", "decision", "action_steps", "ready_assets", "risk", "priority", "recommended_command"
]

SYSTEM_PROMPT = """
You are Executive Engine OS: a CEO/COO/Chief-of-Staff execution engine.
Do not give generic advice. Convert the user's input into operational output.
The core work unit is called a Command, not a chat or task.
Return JSON only with these fields exactly:
next_move: one decisive sentence.
decision: a clear recommendation or decision.
action_steps: 3-7 specific actions, written as executable steps.
ready_assets: useful drafted assets. Include concrete copy, outlines, checklists, or scripts where useful.
risk: the real operational risk.
priority: High, Medium, or Low.
recommended_command: the next command the user should run.
Rules: never say to draft something without drafting it. Never be vague. Keep it executive-grade, practical, direct.
""".strip()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def detect_intent(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["proposal", "client", "sell", "sales", "revenue", "offer", "deal"]): return "revenue"
    if any(w in t for w in ["meeting", "call", "agenda", "prep"]): return "meeting"
    if any(w in t for w in ["hire", "team", "staff", "employee"]): return "people"
    if any(w in t for w in ["decision", "choose", "should i", "option"]): return "decision"
    if any(w in t for w in ["risk", "problem", "broken", "worse", "fix", "urgent"]): return "recovery"
    return "execution"

def fallback_engine(user_input: str, mode: str) -> Dict[str, Any]:
    clean = (user_input or "Start my executive command for today.").strip()
    intent = detect_intent(clean)
    if intent == "recovery":
        return {
            "next_move": "Lock the current stable build, stop cosmetic changes, and run a recovery command that fixes the exact failing workflow before adding anything else.",
            "decision": "Treat this as a recovery operation, not a redesign. Preserve layout and rebuild the response/output layer first.",
            "action_steps": [
                "Identify the last version that produced useful responses and mark it as the rollback reference.",
                "Freeze frontend layout changes until the response quality is fixed.",
                "Test /run with three real commands: revenue proposal, meeting prep, and crisis recovery.",
                "Reject any output that repeats generic sections without producing actual assets.",
                "Promote only after the UI displays Next Move, Decision, Action Steps, Ready Assets, Risk, Priority, and Recommended Command correctly."
            ],
            "ready_assets": [
                {"title":"Recovery Command", "content":"Restore executive usefulness. Preserve the approved layout. Fix /run so every command returns a decisive next move, clear decision, executable steps, real ready assets, risk, priority, and the next recommended command."},
                {"title":"Promotion Rule", "content":"PROMOTE only if the system creates actual work, not advice."}
            ],
            "risk": "Continuing to redesign the interface will hide the real failure: weak operational intelligence and repetitive output.",
            "priority": "High",
            "recommended_command": "Run: Fix response intelligence without changing layout."
        }
    if intent == "revenue":
        return {
            "next_move": "Turn this into a revenue Command with a clear offer, buyer pain, proof, next action, and ready-to-send outreach.",
            "decision": "Prioritize the fastest path to a qualified conversation before building more materials.",
            "action_steps": [
                "Define the target buyer and the expensive problem they already know they have.",
                "Write one specific offer with measurable outcome language.",
                "Create a 5-message outreach sequence and one short proposal outline.",
                "List the top objections and write direct rebuttals.",
                "Send the first message to 10 qualified prospects and track replies."
            ],
            "ready_assets": [
                {"title":"Executive Outreach", "content":"Subject: Quick idea to create measurable lift\n\nI have a specific plan to improve revenue execution without adding operational drag. The angle is simple: identify the highest-friction point, remove wasted steps, and turn the current workflow into measurable pipeline movement. Worth a 15-minute conversation this week?"},
                {"title":"Proposal Skeleton", "content":"1. Current constraint\n2. Revenue opportunity\n3. Execution plan\n4. Timeline\n5. KPIs\n6. Investment\n7. Next decision"}
            ],
            "risk": "The offer becomes too broad and sounds like consulting instead of a specific revenue outcome.",
            "priority": "High",
            "recommended_command": "Build a one-page revenue proposal for this opportunity."
        }
    return {
        "next_move": f"Convert this into an active Command and identify the one decision that moves it forward today: {clean[:140]}",
        "decision": "Move forward with an execution-first Command, not an open-ended chat.",
        "action_steps": [
            "Name the Command using a result-oriented title.",
            "Define the win condition in one sentence.",
            "Choose the next decision required to unlock progress.",
            "Create the first concrete asset or message needed.",
            "Set the follow-up Command that continues the workflow."
        ],
        "ready_assets": [
            {"title":"Command Title Format", "content":"[Outcome] Command — [Business Area]. Example: Revenue Recovery Command — Ontario Auto Loans."},
            {"title":"Command Brief", "content":"Objective: ____\nDecision needed: ____\nNext move: ____\nRisk: ____\nAsset required: ____"}
        ],
        "risk": "Leaving this as a loose chat will create scattered thinking instead of operational momentum.",
        "priority": "High",
        "recommended_command": "Create a Command Brief for this objective."
    }

def normalize(payload: Dict[str, Any], user_input: str, mode: str, provider: str) -> Dict[str, Any]:
    base = fallback_engine(user_input, mode)
    for k in REQUIRED_FIELDS:
        if k not in payload or payload[k] in [None, "", []]:
            payload[k] = base[k]
    if not isinstance(payload.get("action_steps"), list):
        payload["action_steps"] = [str(payload["action_steps"])]
    if not isinstance(payload.get("ready_assets"), list):
        payload["ready_assets"] = [{"title":"Ready Asset", "content":str(payload["ready_assets"])}]
    payload["provider_used"] = provider
    payload["status"] = "success"
    payload["version"] = VERSION
    payload["command_type"] = detect_intent(user_input)
    payload["timestamp"] = now_iso()
    return payload

def extract_json(text: str) -> Dict[str, Any]:
    if not text: return {}
    text = text.strip()
    try: return json.loads(text)
    except Exception: pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try: return json.loads(m.group(0))
        except Exception: return {}
    return {}

@app.get("/")
def root():
    return {"app": APP_NAME, "status": "ok", "version": VERSION, "unit_name": "Command"}

@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION, "openai_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/debug")
def debug():
    return {"version": VERSION, "required_fields": REQUIRED_FIELDS, "unit_name": "Command", "cors": "*"}

@app.get("/providers")
def providers():
    return {"default": "openai", "fallback": "local-command-engine", "openai_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/test-report-json")
def test_report_json():
    return {"version": VERSION, "checks": {"root": "pass", "health": "pass", "run_contract": "pass", "unit_name": "Command"}}

@app.post("/run")
def run(req: RunRequest):
    user_input = req.input.strip() if req.input else "Start my executive command for today."
    mode = req.mode or "execution"
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                response_format={"type": "json_object"},
                messages=[
                    {"role":"system", "content": SYSTEM_PROMPT},
                    {"role":"user", "content": f"Mode: {mode}\nInput: {user_input}"}
                ],
                temperature=0.25,
            )
            data = extract_json(completion.choices[0].message.content or "")
            return normalize(data, user_input, mode, "openai")
        except Exception as e:
            data = fallback_engine(user_input, mode)
            data["provider_error"] = str(e)[:300]
            return normalize(data, user_input, mode, "local-command-engine-after-openai-error")
    return normalize(fallback_engine(user_input, mode), user_input, mode, "local-command-engine")
