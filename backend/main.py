import os
import json
import asyncio
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

app = FastAPI(title="Executive Engine V37")

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
Act as an elite COO / operator.

Return ONLY valid JSON:
{
  "decision": "",
  "next_move": "",
  "actions": [],
  "risk": "",
  "priority": ""
}

Rules:
- No markdown
- No explanation
- No extra text
- Always valid JSON
"""

async def call_openai(prompt: str) -> dict:
    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
            ),
            timeout=10
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception:
        return {
            "decision": "Fallback triggered",
            "next_move": "Retry request",
            "actions": ["Retry request","Check logs","Validate API keys"],
            "risk": "Model/JSON failure",
            "priority": "High"
        }

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

def fetch_memory(limit: int = 5):
    if not supabase:
        return []
    try:
        res = supabase.table("items") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return res.data if res.data else []
    except Exception:
        return []

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/memory")
async def memory():
    return {"memory": fetch_memory(5)}

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    prompt = f"Mode: {req.mode}\nInput: {req.input}"
    result = await call_openai(prompt)

    clean = {
        "decision": str(result.get("decision","")),
        "next_move": str(result.get("next_move","")),
        "actions": result.get("actions",[]) if isinstance(result.get("actions"), list) else [],
        "risk": str(result.get("risk","")),
        "priority": str(result.get("priority",""))
    }

    asyncio.create_task(save_memory(req.input, req.mode, clean))
    return clean
