import asyncio
import json
from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from openai import AsyncOpenAI

# ======================
# INIT
# ======================
app = FastAPI()
client = AsyncOpenAI()

# ======================
# IN-MEMORY STORAGE
# ======================
MEMORY = []

# ======================
# MODELS
# ======================
class RunRequest(BaseModel):
    input: str
    mode: str

class RunResponse(BaseModel):
    what_to_do_now: str
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str

# ======================
# SYSTEM PROMPT
# ======================
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
- Every response must feel like a real operator decision

Definitions:
- what_to_do_now = ONE immediate action (no explanation)
- decision = clear stance (commit to something)
- next_move = what happens right after
- actions = step-by-step execution (3–6 max, concrete)
- risk = real downside, not generic
- priority = High / Medium / Low based on impact

If input is vague:
→ make assumptions and move forward

If input is broad:
→ narrow to highest leverage move

Output ONLY valid JSON.
"""

# ======================
# HELPERS
# ======================
def fallback():
    return {
        "what_to_do_now": "Define the single highest-leverage objective",
        "decision": "Pause non-critical activity and refocus execution",
        "next_move": "Reassess priorities and re-run with clarity",
        "actions": [
            "Identify the core objective",
            "Remove non-essential tasks",
            "Rebuild execution plan",
            "Execute highest leverage step",
            "Review outcome immediately"
        ],
        "risk": "Misaligned execution wastes time and resources",
        "priority": "High"
    }

async def call_model(user_input: str, mode: str):
    try:
        res = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Mode: {mode}\nInput: {user_input}"}
                ]
            ),
            timeout=10
        )

        content = res.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except:
            return fallback()

    except:
        return fallback()

def clean_actions(actions):
    if not isinstance(actions, list):
        return []
    cleaned = []
    for a in actions:
        if not a:
            continue
        a = str(a).strip()
        if not a:
            continue
        # Ensure action starts with verb-like structure
        if not a.split()[0].endswith("e"):
            a = a[0].upper() + a[1:]
        cleaned.append(a)
    return cleaned[:5]

def clean_output(output):
    base = fallback()

    what_to_do_now = str(output.get("what_to_do_now", "")).strip() or base["what_to_do_now"]
    decision = str(output.get("decision", "")).strip() or base["decision"]
    next_move = str(output.get("next_move", "")).strip() or base["next_move"]
    risk = str(output.get("risk", "")).strip() or base["risk"]

    actions = clean_actions(output.get("actions", []))
    if not actions:
        actions = base["actions"]

    priority = str(output.get("priority", "")).strip()
    if priority not in ["High", "Medium", "Low"]:
        priority = "High"

    return {
        "what_to_do_now": what_to_do_now,
        "decision": decision,
        "next_move": next_move,
        "actions": actions,
        "risk": risk,
        "priority": priority
    }

def save_memory(input_text, output):
    global MEMORY

    MEMORY.append({
        "input": input_text,
        "decision": output.get("decision"),
        "next_move": output.get("next_move"),
        "actions": output.get("actions"),
        "timestamp": datetime.utcnow().isoformat()
    })

    MEMORY = MEMORY[-5:]

# ======================
# ROUTES
# ======================
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    raw = await call_model(req.input, req.mode)
    clean = clean_output(raw)

    save_memory(req.input, clean)

    return clean

@app.get("/memory")
async def memory():
    return {"memory": MEMORY}
