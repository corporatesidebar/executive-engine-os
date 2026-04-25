from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import json
import requests

app = FastAPI(title="Executive Engine V33")

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

class Req(BaseModel):
    input: str
    mode: str | None = "execution"

def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def get_memory(limit=10):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/items?select=input,mode,decision,next_move,actions,risk,priority,created_at&order=created_at.desc&limit={limit}"
        r = requests.get(url, headers=headers(), timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def save_memory(req, output):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    payload = {
        "input": req.input,
        "mode": req.mode,
        "decision": output.get("decision", ""),
        "next_move": output.get("next_move", ""),
        "actions": output.get("actions", []),
        "risk": output.get("risk", ""),
        "priority": output.get("priority", "")
    }

    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/items", headers=headers(), json=payload, timeout=10)
    except Exception:
        pass

@app.get("/")
def root():
    return {"status": "ok", "service": "Executive Engine V33"}

@app.get("/memory")
def memory():
    return {"memory": get_memory(10)}

@app.post("/run")
async def run(req: Req):
    memory_items = get_memory(5)

    memory_text = "\n".join([
        f"Previous Input: {m.get('input','')} | Next Move: {m.get('next_move','')}"
        for m in memory_items
    ]) or "No prior memory."

    prompt = f'''
You are Executive Engine OS, a decision weapon for operators and executives.

Mode: {req.mode}

Recent memory:
{memory_text}

Current input:
{req.input}

Return STRICT JSON only:
{{
  "decision": "clear executive decision",
  "next_move": "single highest leverage action to do now",
  "actions": ["specific task 1", "specific task 2", "specific task 3"],
  "risk": "main risk/blocker",
  "priority": "High | Medium | Low"
}}

Rules:
- No markdown
- No explanation
- No generic advice
- Actions must be executable
- Next move must be immediate and force execution
'''

    res = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=450
    )

    raw = res.choices[0].message.content.strip()

    try:
        output = json.loads(raw)
    except Exception:
        output = {
            "decision": "Clarify the highest leverage objective.",
            "next_move": "Identify the immediate blocker and take the first measurable step.",
            "actions": ["Clarify the objective", "Identify the blocker", "Execute the next step"],
            "risk": "Execution clarity is missing.",
            "priority": "High"
        }

    if not isinstance(output.get("actions"), list):
        output["actions"] = [str(output.get("actions", ""))]

    save_memory(req, output)
    return output
