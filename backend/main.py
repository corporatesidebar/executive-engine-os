from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import json
import requests

app = FastAPI(title="Executive Engine OS - Memory Layer V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class RunRequest(BaseModel):
    input: str
    mode: str | None = "strategy"

SYSTEM_MESSAGE = "You are a decisive, execution-focused COO. You prioritize speed, clarity, leverage, and results."

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def get_recent_memory(limit: int = 5):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    try:
        url = f"{SUPABASE_URL}/rest/v1/items?select=input,decision,next_move,actions,risk,priority,mode,created_at&order=created_at.desc&limit={limit}"
        res = requests.get(url, headers=supabase_headers(), timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    return []

def format_memory(memory):
    if not memory:
        return "No prior memory available."

    lines = []
    for item in memory:
        lines.append(
            f"- Mode: {item.get('mode','')}; "
            f"Input: {item.get('input','')}; "
            f"Decision: {item.get('decision','')}; "
            f"Next Move: {item.get('next_move','')}; "
            f"Priority: {item.get('priority','')}"
        )
    return "\n".join(lines)

def save_memory(req: RunRequest, output: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    payload = {
        "input": req.input,
        "mode": req.mode,
        "decision": output.get("decision", ""),
        "next_move": output.get("next_move", ""),
        "actions": output.get("actions", []),
        "risk": output.get("risk", ""),
        "priority": output.get("priority", ""),
    }

    try:
        url = f"{SUPABASE_URL}/rest/v1/items"
        requests.post(url, headers=supabase_headers(), json=payload, timeout=10)
    except Exception:
        pass

@app.get("/")
def root():
    return {"status": "ok", "service": "Executive Engine OS Memory Layer V1"}

@app.get("/memory")
def memory():
    return {"memory": get_recent_memory(10)}

@app.post("/run")
async def run(req: RunRequest):
    recent_memory = get_recent_memory(5)
    memory_context = format_memory(recent_memory)

    prompt = f'''
You are Executive Engine OS, an elite executive operator system.

Mode:
{req.mode}

Recent memory:
{memory_context}

Current input:
{req.input}

Your job:
- Make a clear executive decision
- Identify the highest leverage next move
- Break it into specific execution steps
- Highlight the real risk
- Set priority

Rules:
- Be direct
- No fluff
- No theory
- No generic advice
- Use memory only if relevant
- Do not mention memory unless it directly matters
- Output STRICT JSON only

Return this exact JSON structure:

{{
  "decision": "clear, confident decision",
  "next_move": "single highest leverage action to take immediately",
  "actions": [
    "specific action 1",
    "specific action 2",
    "specific action 3"
  ],
  "risk": "biggest real risk or blocker",
  "priority": "High | Medium | Low"
}}
'''

    res = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=450,
    )

    raw = res.choices[0].message.content.strip()

    try:
        output = json.loads(raw)
    except Exception:
        output = {
            "decision": "Make the highest leverage decision based on the current constraint.",
            "next_move": "Clarify the immediate blocker and execute the next measurable step.",
            "actions": [
                "Clarify the objective",
                "Identify the blocker",
                "Execute the next step"
            ],
            "risk": "The main risk is lack of execution clarity.",
            "priority": "High"
        }

    if not isinstance(output.get("actions"), list):
        output["actions"] = [str(output.get("actions", ""))]

    save_memory(req, output)

    return output
