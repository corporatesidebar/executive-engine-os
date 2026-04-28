import os, json, re, asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from openai import AsyncOpenAI

APP_NAME = "Executive Engine OS V87"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "40"))
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title=APP_NAME)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")], allow_methods=["*"], allow_headers=["*"])

class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None
    mode: Optional[str] = "execution"
    depth: Optional[str] = "standard"

def fallback():
    return {"what_to_do_now":"Clarify the situation and execute the next concrete move.","decision":"Proceed with the clearest immediate action.","next_move":"Define the desired outcome, then take the first action.","actions":["Clarify outcome","Identify constraint","Execute first move"],"risk":"Moving without clarity can waste time and energy.","priority":"high","reality_check":"The output is only as strong as the context provided.","leverage":"Focus on the move that creates the most progress with the least friction.","constraint":"Insufficient context.","what_to_ignore":"Low-value distractions.","financial_impact":"Depends on execution quality.","strategic_read":"Start simple and convert ambiguity into action."}

def extract_json(text):
    try: return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text or "")
        if m: return json.loads(m.group(0))
    raise ValueError("Invalid JSON")

def normalize(d):
    base = fallback()
    if isinstance(d, dict): base.update({k:v for k,v in d.items() if v not in [None, ""]})
    if not isinstance(base.get("actions"), list): base["actions"] = [str(base["actions"])]
    return base

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots(): return "User-agent: *\nDisallow: /\n"

@app.get("/")
async def root(): return {"ok": True, "service": APP_NAME}

@app.get("/health")
async def health(): return {"ok": True, "service": APP_NAME, "openai_key_set": bool(os.getenv("OPENAI_API_KEY")), "model": MODEL}

@app.get("/debug")
async def debug(): return {"ok": True, "version": "V87", "routes": ["/", "/health", "/run", "/robots.txt"], "model": MODEL}

@app.post("/run")
async def run(req: RunRequest):
    system = """You are Executive Engine OS V87. Act like an elite CEO/COO/President operator.
Return ONLY valid JSON. No markdown.
Schema:
{"what_to_do_now":"","decision":"","next_move":"","actions":[""],"risk":"","priority":"low|medium|high|critical","reality_check":"","leverage":"","constraint":"","what_to_ignore":"","financial_impact":"","strategic_read":""}
Rules:
- Be specific, direct, and execution-focused.
- No generic advice.
- Actions must be executable today.
- Adapt to mode: execution, daily_brief, decision, meeting, personal, content, learning.
- For content mode, include creative direction and next asset steps.
- For learning mode, analyze patterns and propose improvements without claiming external DB access."""
    try:
        res = await asyncio.wait_for(client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":system},{"role":"user","content":f"MODE: {req.mode}\n\nCONTEXT:\n{req.context or ''}\n\nINPUT:\n{req.input}"}],
            temperature=0.2,
            response_format={"type":"json_object"}
        ), timeout=TIMEOUT)
        return normalize(extract_json(res.choices[0].message.content))
    except Exception:
        return fallback()
