from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
import os, json, asyncio
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

memory_store = []

SYSTEM_PROMPT = """
You are a high-performance COO.

You think in:
- leverage
- speed
- outcomes

Rules:
- No vague language
- No generic advice
- No filler
- Each response must be specific to the input
- Each action must be executable
- Think like a COO executing TODAY

Definitions:
- what_to_do_now = ONE immediate action
- decision = clear stance
- next_move = immediate next step
- actions = 3–5 concrete steps
- risk = real downside
- priority = High | Medium | Low

If input is vague:
→ assume context and act

Output ONLY valid JSON.
"""

class RequestModel(BaseModel):
    input: str
    mode: str = "execution"

def clean_response(data):
    if not isinstance(data, dict):
        return fallback()

    actions = data.get("actions", [])
    if isinstance(actions, list):
        actions = [a for a in actions if isinstance(a, str) and a.strip()][:5]
    else:
        actions = []

    return {
        "what_to_do_now": data.get("what_to_do_now") or "Define immediate execution step",
        "decision": data.get("decision") or "Proceed with highest leverage action",
        "next_move": data.get("next_move") or "Execute next logical step",
        "actions": actions if actions else ["Execute priority task"],
        "risk": data.get("risk") or "Execution delay",
        "priority": data.get("priority") or "High"
    }

def fallback():
    return {
        "what_to_do_now": "Check backend connection",
        "decision": "System fallback triggered",
        "next_move": "Verify /run endpoint",
        "actions": [
            "Check Render logs",
            "Verify API key",
            "Restart service"
        ],
        "risk": "System not responding",
        "priority": "High"
    }

def save_memory(input_text, mode, response):
    memory_store.append({
        "input": input_text,
        "mode": mode,
        "decision": response.get("decision"),
        "next_move": response.get("next_move"),
        "actions": response.get("actions"),
        "timestamp": datetime.utcnow().isoformat()
    })
    if len(memory_store) > 5:
        memory_store.pop(0)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/memory")
async def memory():
    return {"memory": memory_store[-5:]}

@app.post("/run")
async def run(req: RequestModel):
    try:
        timeout = 15

        async def call():
            res = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.input}
                ]
            )
            return res.choices[0].message.content

        raw = await asyncio.wait_for(call(), timeout=timeout)

        try:
            data = json.loads(raw)
        except:
            return fallback()

        cleaned = clean_response(data)
        save_memory(req.input, req.mode, cleaned)

        return cleaned

    except:
        return fallback()
