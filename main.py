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
    profile_role: str = ""
    profile_industry: str = ""
    profile_tone: str = ""
    profile_goal: str = ""
    personal_context: str = ""
    uploaded_context: str | None = None

SYSTEM_PROMPTS = {
    "strategy": """You are a high-level executive strategy engine.
Think like a CEO, COO, operator, and investor.
Be direct, sharp, commercially aware, and practical.

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
    "personal": """You are a thoughtful personal advisor.
Be warm, clear, grounded, and useful.
Do not force executive/business framing unless the user asks for it.

Return exactly:
What Matters:
...

Best Move:
...

Watch Out For:
...

Next Step:
...""",
}

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        system_prompt = SYSTEM_PROMPTS.get(req.mode, SYSTEM_PROMPTS["strategy"])

        profile_parts = []
        if req.profile_role:
            profile_parts.append(f"Role Target: {req.profile_role}")
        if req.profile_industry:
            profile_parts.append(f"Industry: {req.profile_industry}")
        if req.profile_tone:
            profile_parts.append(f"Tone: {req.profile_tone}")
        if req.profile_goal:
            profile_parts.append(f"Goal: {req.profile_goal}")
        if req.personal_context:
            profile_parts.append(f"Personal Context: {req.personal_context}")

        context_parts = []
        if profile_parts:
            context_parts.append("User Profile:\n" + "\n".join(profile_parts))
        if req.uploaded_context:
            context_parts.append("Uploaded Context:\n" + req.uploaded_context)

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
