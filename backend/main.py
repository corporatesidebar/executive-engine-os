import os
import json
import asyncio
from typing import List, Optional

from fastapi import FastAPI
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

app = FastAPI()

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
"""

async def call_openai(prompt: str) -> dict:
    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=300,
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
            "decision": "Fallback",
            "next_move": "Retry",
            "actions": [],
            "risk": "Error",
            "priority": "High"
        }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run")
async def run(req: RunRequest):
    prompt = f"Mode: {req.mode}\nInput: {req.input}"
    result = await call_openai(prompt)
    return result
