from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

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

class Request(BaseModel):
    input: str
    mode: str = "strategy"
    context: str = ""

@app.get("/")
def root():
    return {"status": "live", "service": "Executive Engine Backend"}

@app.post("/run")
def run_engine(req: Request):
    api_key = os.getenv("OPENAI_API_KEY")

    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            prompt = f'''
You are Executive Engine, an operator-grade decision system.

Mode: {req.mode}
Context: {req.context[:1500]}

Situation:
{req.input}

Return ONLY JSON:
{{
  "decision": "clear decision",
  "why": "short reason",
  "risk": "main risk",
  "action_items": ["specific action 1", "specific action 2", "specific action 3"],
  "priority": "High | Medium | Low",
  "feedback_overview": "brief executive overview"
}}
'''
            response = client.responses.create(
                model="gpt-4o-mini",
                input=prompt
            )
            import json
            return json.loads(response.output_text)
        except Exception as e:
            return {
                "decision": "AI call failed",
                "why": str(e),
                "risk": "The backend connected but the model response failed.",
                "action_items": ["Check OPENAI_API_KEY", "Retry with shorter input", "Confirm billing is active"],
                "priority": "High",
                "feedback_overview": "Backend is live, but the AI request failed."
            }

    return {
        "decision": "Use this as the working baseline.",
        "why": "The app is connected and responding. Add OpenAI key to turn this into a live AI engine.",
        "risk": "Without the OpenAI key, responses are static.",
        "action_items": [
            "Confirm frontend loads",
            "Confirm backend /run responds",
            "Add OPENAI_API_KEY in Render environment"
        ],
        "priority": "High",
        "feedback_overview": "System baseline is live. Next step is AI activation."
    }
