from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EngineRequest(BaseModel):
    input: str
    mode: str = "strategy"
    context: str = ""

@app.get("/")
def root():
    return {"status": "live", "service": "Executive Engine Backend", "endpoint": "/run"}

@app.get("/health")
def health():
    return {"status": "ok"}

def fallback_response(reason: str = "Fallback active"):
    return {
        "decision": "Focus on the highest-leverage next move.",
        "next_move": "Define the single action that creates the most progress today.",
        "risk": "The biggest risk is staying broad instead of choosing one clear path.",
        "action_items": [
            "Pick one priority for the next 24 hours",
            "Write the first concrete action required",
            "Schedule or execute that action today"
        ],
        "priority": "High",
        "feedback_overview": reason
    }

@app.post("/run")
def run_engine(req: EngineRequest):
    api_key = os.getenv("OPENAI_API_KEY")

    if not req.input.strip():
        return fallback_response("No input received.")

    if not api_key or OpenAI is None:
        return fallback_response("Backend is live, but OPENAI_API_KEY is missing or OpenAI package is unavailable.")

    try:
        client = OpenAI(api_key=api_key, timeout=20.0, max_retries=1)

        prompt = f"""
You are Executive Engine OS — a direct, operator-grade executive decision engine.

Mode: {req.mode}

User situation:
{req.input}

Optional context:
{req.context[:1500]}

Return ONLY valid JSON. No markdown. No explanation outside JSON.

Schema:
{{
  "decision": "one clear decision",
  "next_move": "the single most important action to take next",
  "risk": "the main risk to manage",
  "action_items": ["specific action 1", "specific action 2", "specific action 3"],
  "priority": "High | Medium | Low",
  "feedback_overview": "brief executive overview"
}}

Rules:
- Be specific.
- Do not be generic.
- Prioritize execution.
- If the user is unsure what to do, force clarity.
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.3,
        )

        text = response.output_text.strip()
        data = json.loads(text)

        if "next_move" not in data:
            data["next_move"] = data.get("action_items", ["Define next action."])[0]

        return data

    except Exception as e:
        return fallback_response(f"AI failed but backend is live. Error: {str(e)[:300]}")
