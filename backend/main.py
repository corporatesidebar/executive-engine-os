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
    return {"status": "live", "service": "Executive Engine Backend"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run_engine(req: EngineRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    fallback = {
        "decision": "Focus on the highest-leverage next move.",
        "why": "The system is running. Add an OpenAI API key for dynamic executive-grade responses.",
        "risk": "Execution slows down if the next action is not specific.",
        "action_items": [
            "Define the highest-leverage next action",
            "Assign a clear priority",
            "Execute or schedule it today"
        ],
        "priority": "High",
        "feedback_overview": "Baseline response active. Backend is connected."
    }

    if not api_key or not OpenAI:
        return fallback

    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""You are Executive Engine OS, an operator-grade executive decision system.

Mode: {req.mode}

Context:
{req.context[:1500]}

User situation:
{req.input}

Your job:
- Give one clear decision.
- Give the most important next move first.
- Give concrete execution actions.
- Be direct, useful, and operator-level.
- Avoid generic coaching language.

Return ONLY valid JSON:
{{
  "decision": "one clear executive decision",
  "why": "brief reason this is the right decision",
  "risk": "main risk to manage",
  "action_items": ["specific action 1", "specific action 2", "specific action 3"],
  "priority": "High | Medium | Low",
  "feedback_overview": "brief executive overview"
}}"""
        response = client.responses.create(model="gpt-4o-mini", input=prompt)
        return json.loads(response.output_text.strip())

    except Exception as e:
        return {
            "decision": "AI response failed but backend is live.",
            "why": str(e),
            "risk": "Model/API configuration needs review.",
            "action_items": [
                "Check OPENAI_API_KEY in Render",
                "Confirm OpenAI billing is active",
                "Retry with a shorter input"
            ],
            "priority": "High",
            "feedback_overview": "Backend is reachable, but AI generation failed."
        }
