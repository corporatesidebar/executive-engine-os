from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import os
import json

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CommandInput(BaseModel):
    input: str
    mode: str = "Strategy"

SYSTEM_PROMPT = """
You are Executive Engine, an elite executive strategist.
You help founders and operators think faster and more clearly.

Return STRICT JSON ONLY with exactly these keys:
{
  "outcome": "...",
  "risk": "...",
  "action": "...",
  "priority": "Low | Medium | High"
}

Rules:
- Be sharp, practical, concise, and business-focused.
- No fluff.
- No markdown.
- No extra keys.
- Outcome = the best directional conclusion.
- Risk = the main downside or threat.
- Action = the clearest next move.
- Priority = Low, Medium, or High only.
- Keep each field under 35 words where possible.
"""

@app.post("/api/command")
def command(data: CommandInput):
    mode = (data.mode or "Strategy").strip()
    user_input = (data.input or "").strip()

    user_prompt = f"""
Mode: {mode}

User input:
{user_input}

Interpret the mode this way:
- Strategy = direction, leverage, positioning, sequencing
- Decision = choose between options with tradeoffs
- Execution = immediate next steps, momentum, accountability
- Meeting = talking points, structure, objectives, alignment
- Personal = clear advice for the user's situation, still practical and direct

Return JSON only.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )

    text = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {
            "outcome": text,
            "risk": "",
            "action": "",
            "priority": "Medium"
        }

    return {
        "outcome": parsed.get("outcome", ""),
        "risk": parsed.get("risk", ""),
        "action": parsed.get("action", ""),
        "priority": parsed.get("priority", "Medium")
    }

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/style.css")
def style():
    return FileResponse(FRONTEND_DIR / "style.css")

@app.get("/script.js")
def script():
    return FileResponse(FRONTEND_DIR / "script.js")
