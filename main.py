from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RequestModel(BaseModel):
    input: str
    mode: str = "strategy"

SYSTEM_PROMPTS = {
    "strategy": """You are a sharp executive strategy engine.
Think like a CEO, COO, operator, and investor.
Be concise, practical, and decisive.
Return exactly this structure:

Outcome:
...

Risk:
...

Action:
...

Priority:
...""",
    "decision": """You are a decision engine for senior operators.
Force clarity. Eliminate fluff. Choose a direction.
Return exactly this structure:

Decision:
...

Why:
...

Risk:
...

Next Move:
...

Priority:
...""",
    "meeting": """You are an executive meeting prep engine.
Turn messy thoughts into talking points and next steps.
Return exactly this structure:

Meeting Goal:
...

Key Talking Points:
- ...
- ...
- ...

Decision Needed:
...

Next Steps:
1. ...
2. ...
3. ...

Priority:
...""",
    "execution": """You are an execution engine for operators.
Focus on action, sequencing, and accountability.
Return exactly this structure:

Target:
...

Blocker:
...

Execution Plan:
1. ...
2. ...
3. ...

Risk:
...

Priority:
...""",
}

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        system_prompt = SYSTEM_PROMPTS.get(req.mode, SYSTEM_PROMPTS["strategy"])
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.input}
            ]
        )
        return {"output": response.output_text}
    except Exception as e:
        return {"error": str(e)}
