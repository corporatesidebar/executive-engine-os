import os
import json
import asyncio
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

supabase: Optional[Client] = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

app = FastAPI(title="Executive Engine OS V37")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str
    mode: str = "execution"

class RunResponse(BaseModel):
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str

SYSTEM_PROMPT = """
You are Executive Engine OS, an elite COO/operator decision engine.

Return ONLY valid JSON with this exact shape:
{
  "decision": "",
  "next_move": "",
  "actions": [],
  "risk": "",
  "priority": ""
}

Rules:
- No markdown.
- No explanation.
- No extra text.
- Always valid JSON.
- Make the next_move immediate and specific.
- Actions must be short, executable steps.
- Priority must be High, Medium, or Low.
"""

def fallback_response(reason: str) -> dict:
    return {
        "decision": "Backend fallback activated.",
        "next_move": "Confirm OpenAI API key is valid and /run is working.",
        "actions": [
            "Check Render environment variable OPENAI_API_KEY",
            "Check Render backend logs",
            "Redeploy backend after saving changes"
        ],
        "risk": reason,
        "priority": "High"
    }

def clean_output(data: dict) -> dict:
    actions = data.get("actions", [])
    if not isinstance(actions, list):
        actions = [str(actions)] if actions else []
    actions = [str(a) for a in actions if str(a).strip()]

    if not actions:
        actions = ["Clarify the objective", "Identify the blocker", "Execute the first step"]

    priority = str(data.get("priority", "High")).strip() or "High"
    if priority.lower() not in ["high", "medium", "low"]:
        priority = "High"

    return {
        "decision": str(data.get("decision", "Clarify the decision.")).strip(),
        "next_move": str(data.get("next_move", "Execute the highest-leverage next step.")).strip(),
        "actions": actions[:5],
        "risk": str(data.get("risk", "Execution clarity is missing.")).strip(),
        "priority": priority.capitalize()
    }

async def call_openai(user_prompt: str) -> dict:
    if not openai_client:
        return fallback_response("OPENAI_API_KEY is missing or not loaded.")

    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0.3,
                max_tokens=450,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
            ),
            timeout=15
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        return clean_output(parsed)

    except Exception as e:
        return fallback_response(f"OpenAI or JSON error: {str(e)[:160]}")

def fetch_memory(limit: int = 5):
    if not supabase:
        return []
    try:
        res = (
            supabase.table("items")
            .select("input,mode,decision,next_move,actions,risk,priority,created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data if res.data else []
    except Exception:
        return []

async def save_memory(input_text: str, mode: str, data: dict):
    if not supabase:
        return
    try:
        supabase.table("items").insert({
            "input": input_text,
            "mode": mode,
            "decision": data.get("decision"),
            "next_move": data.get("next_move"),
            "actions": data.get("actions"),
            "risk": data.get("risk"),
            "priority": data.get("priority")
        }).execute()
    except Exception:
        pass

@app.get("/")
async def root():
    return {"status": "ok", "service": "Executive Engine OS V37"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Executive Engine OS V37",
        "openai_configured": bool(OPENAI_API_KEY),
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY)
    }

@app.get("/memory")
async def memory():
    return {"memory": fetch_memory(5)}

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    recent_memory = fetch_memory(3)
    memory_text = "\n".join([
        f"- {m.get('mode','')}: {m.get('next_move') or m.get('decision') or m.get('input','')}"
        for m in recent_memory
    ]) or "No prior memory."

    prompt = f"""
Mode: {req.mode}

Recent memory:
{memory_text}

Current user input:
{req.input}

Create one clear executive decision, one next move, 3-5 action steps, risk, and priority.
"""

    result = await call_openai(prompt)
    asyncio.create_task(save_memory(req.input, req.mode, result))
    return result
