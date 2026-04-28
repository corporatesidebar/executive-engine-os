import os, json, re, asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

APP_NAME = "Executive Engine OS V84"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "40"))

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None
    mode: Optional[str] = "execution"
    depth: Optional[str] = "standard"

def safe_response():
    return {
        "what_to_do_now": "Clarify the situation and execute the next concrete move.",
        "decision": "Proceed with the clearest immediate action.",
        "next_move": "Define the desired outcome, then take the first action.",
        "actions": ["Clarify outcome", "Identify constraint", "Execute first move"],
        "risk": "Moving without clarity can waste time and energy.",
        "priority": "high",
        "reality_check": "The output is only as strong as the context provided.",
        "leverage": "Focus on the move that creates the most progress with the least friction.",
        "constraint": "Insufficient context.",
        "what_to_ignore": "Low-value distractions.",
        "financial_impact": "Depends on execution quality.",
        "strategic_read": "Start simple and convert ambiguity into action."
    }

def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text or "")
        if match:
            return json.loads(match.group(0))
    raise ValueError("Invalid JSON")

def normalize(data):
    if not isinstance(data, dict):
        return safe_response()
    base = safe_response()
    base.update({k:v for k,v in data.items() if v not in [None, ""]})
    if not isinstance(base.get("actions"), list):
        base["actions"] = [str(base["actions"])]
    return base

def build_messages(req: RunRequest):
    mode = req.mode or "execution"
    return [
        {"role":"system","content":"""
You are Executive Engine OS V84. Act like an elite CEO/COO/President operator.
Return ONLY valid JSON. No markdown. No extra text.

Output schema:
{
 "what_to_do_now": "",
 "decision": "",
 "next_move": "",
 "actions": [""],
 "risk": "",
 "priority": "low|medium|high|critical",
 "reality_check": "",
 "leverage": "",
 "constraint": "",
 "what_to_ignore": "",
 "financial_impact": "",
 "strategic_read": ""
}

Rules:
- Be specific, direct, and execution-focused.
- No generic advice.
- Actions must be executable today.
- If context is weak, still give a useful next move and ask one sharp question.
- Think like an operator who values speed, clarity, leverage, and risk control.
"""},
        {"role":"user","content":f"MODE: {mode}\n\nCONTEXT:\n{req.context or ''}\n\nINPUT:\n{req.input}"}
    ]

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /\n"

@app.get("/")
async def root():
    return {"ok": True, "service": APP_NAME}

@app.get("/health")
async def health():
    return {"ok": True, "service": APP_NAME, "openai_key_set": bool(os.getenv("OPENAI_API_KEY")), "model": MODEL}

@app.get("/debug")
async def debug():
    return {"ok": True, "version": "V84", "routes": ["/", "/health", "/run", "/robots.txt"], "model": MODEL, "openai_key_set": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/run")
async def run(req: RunRequest):
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                messages=build_messages(req),
                temperature=0.2,
                response_format={"type": "json_object"},
            ),
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        content = response.choices[0].message.content
        return normalize(extract_json(content))
    except Exception:
        return safe_response()
