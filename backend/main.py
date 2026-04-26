import os
import json
import asyncio
from datetime import datetime
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

try:
    from supabase import create_client
except Exception:
    create_client = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "items")

app = FastAPI(title="Executive Engine OS", version="V39")
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

MEMORY = []

SYSTEM_PROMPT = """
You are a high-performance COO.

You think in:
- leverage
- speed
- outcomes

Rules:
- No greetings
- No vague language
- No generic advice
- No filler
- Force specificity
- Each response must be specific to the input
- Include real actions, not vague advice
- Each action must be executable today
- Avoid generic business advice
- Think like a COO executing TODAY
- Every response must feel like a real operator decision

Definitions:
- what_to_do_now = ONE immediate action, no explanation
- decision = clear stance, commit to something
- next_move = what happens right after
- actions = 3-5 concrete executable steps
- risk = real downside specific to the input
- priority = High / Medium / Low based on impact

If input is vague:
make assumptions and move forward.

If input is broad:
narrow to the highest leverage move.

Output ONLY valid JSON:
{
  "what_to_do_now": "",
  "decision": "",
  "next_move": "",
  "actions": [],
  "risk": "",
  "priority": "High"
}
"""

class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: str = "execution"

class RunResponse(BaseModel):
    what_to_do_now: str
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str

def fallback_response(user_input: str = "", reason: str = "fallback") -> dict:
    text = (user_input or "").strip()
    if not text:
        return {
            "what_to_do_now": "Enter one clear execution objective",
            "decision": "Do not proceed until the core objective is written",
            "next_move": "Submit one business problem, decision, or task",
            "actions": [
                "Write the objective",
                "Add the constraint",
                "Define the wanted outcome",
                "Run the engine again"
            ],
            "risk": "Empty input creates low-value guidance",
            "priority": "High"
        }

    return {
        "what_to_do_now": "Execute the highest-leverage next step from the request",
        "decision": "Move forward with a narrow execution path instead of expanding scope",
        "next_move": "Turn the request into one concrete task and complete it first",
        "actions": [
            "Define the immediate outcome",
            "Remove every non-essential task",
            "Assign the owner or tool",
            "Complete the first visible step",
            "Review the result before expanding scope"
        ],
        "risk": f"Execution will stall if this stays broad or unclear. Trigger: {reason}",
        "priority": "High"
    }

def extract_json(content: str) -> dict:
    if not content:
        return {}
    text = content.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return {}
    return {}

def clean_string(value, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback

def clean_actions(actions, fallback_actions: List[str]) -> List[str]:
    if not isinstance(actions, list):
        actions = []
    cleaned = []
    for action in actions:
        text = str(action).strip() if action is not None else ""
        if text:
            cleaned.append(text[0].upper() + text[1:])
    if not cleaned:
        cleaned = fallback_actions
    return cleaned[:5]

def clean_output(raw: dict, user_input: str, reason: str = "cleaner") -> dict:
    base = fallback_response(user_input, reason)
    raw = raw if isinstance(raw, dict) else {}
    priority = clean_string(raw.get("priority"), "High")
    if priority not in ["High", "Medium", "Low"]:
        priority = "High"
    return {
        "what_to_do_now": clean_string(raw.get("what_to_do_now"), base["what_to_do_now"]),
        "decision": clean_string(raw.get("decision"), base["decision"]),
        "next_move": clean_string(raw.get("next_move"), base["next_move"]),
        "actions": clean_actions(raw.get("actions"), base["actions"]),
        "risk": clean_string(raw.get("risk"), base["risk"]),
        "priority": priority
    }

async def call_openai(user_input: str, mode: str) -> dict:
    if not client:
        return fallback_response(user_input, "OPENAI_API_KEY missing")

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.25,
                max_tokens=550,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Mode: {mode}\nInput: {user_input}"}
                ],
            ),
            timeout=18
        )
        content = response.choices[0].message.content or ""
        parsed = extract_json(content)
        return parsed if parsed else fallback_response(user_input, "model returned invalid JSON")
    except Exception as e:
        return fallback_response(user_input, f"OpenAI error: {type(e).__name__}")

def save_memory(input_text: str, mode: str, output: dict):
    global MEMORY
    row = {
        "input": input_text,
        "mode": mode,
        "decision": output.get("decision"),
        "next_move": output.get("next_move"),
        "actions": output.get("actions"),
        "risk": output.get("risk"),
        "priority": output.get("priority"),
        "created_at": datetime.utcnow().isoformat()
    }

    MEMORY.append(row)
    MEMORY = MEMORY[-5:]

    if supabase:
        try:
            supabase.table(SUPABASE_TABLE).insert(row).execute()
        except Exception:
            pass

def fetch_memory():
    if supabase:
        try:
            res = supabase.table(SUPABASE_TABLE).select("*").order("created_at", desc=True).limit(5).execute()
            data = getattr(res, "data", None)
            if data:
                return data
        except Exception:
            pass
    return list(reversed(MEMORY[-5:]))

@app.get("/")
async def root():
    return {"service": "Executive Engine OS", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "openai": "configured" if bool(OPENAI_API_KEY) else "missing",
        "database": "connected" if bool(supabase) else "not_connected",
        "table": SUPABASE_TABLE
    }

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    try:
        raw = await call_openai(req.input, req.mode)
        clean = clean_output(raw, req.input, "post-process")
        save_memory(req.input, req.mode, clean)
        return clean
    except Exception as e:
        clean = clean_output(fallback_response(req.input, f"server error: {type(e).__name__}"), req.input, "server")
        save_memory(req.input, req.mode, clean)
        return clean

@app.get("/memory")
async def memory():
    return {"memory": fetch_memory()}
