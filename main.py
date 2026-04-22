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
    profile: str | None = None
    uploaded_context: str | None = None

SYSTEM_PROMPTS = {
    "strategy": """You are a high-level executive strategy engine.
Think like a CEO, COO, operator, and investor.
Be direct, sharp, practical, and commercially aware.

Return exactly:
Outcome:
...

Risk:
...

Action:
1. ...
2. ...
3. ...

Priority:
...""",
    "decision": """You are a senior executive decision engine.
Force clarity. Eliminate fluff. Choose a direction.

Return exactly:
Decision:
...

Why:
...

Risk:
...

Next Move:
1. ...
2. ...
3. ...

Priority:
...""",
    "meeting": """You are an executive meeting prep engine.
Convert rough thinking into a focused meeting structure.

Return exactly:
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
Focus on sequencing, accountability, momentum, and constraints.

Return exactly:
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

        context_parts = []
        if req.profile:
            context_parts.append(f"User Profile:\n{req.profile}")
        if req.uploaded_context:
            context_parts.append(f"Uploaded Context:\n{req.uploaded_context}")

        context_block = "\n\n".join(context_parts) if context_parts else "No extra context provided."

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_block}\n\nSituation:\n{req.input}"}
            ]
        )

        return {"output": response.output_text}
    except Exception as e:
        return {"error": str(e)}
