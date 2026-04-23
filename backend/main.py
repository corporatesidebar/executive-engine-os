
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
    request_attachment_context: str | None = None
    prior_summary: str | None = None

SYSTEM_PROMPTS = {
    "strategy": """You are an executive strategy engine.
Be sharp, concise, and operator-grade.
No praise, no coaching tone, no emotional padding.

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
    "decision": """You are an executive decision engine.
Force clarity. Choose a direction. Be concise and commercially aware.
No praise, no coaching tone, no emotional padding.

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
Turn rough ideas into a focused meeting structure.
No praise, no coaching tone, no emotional padding.

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
No praise, no coaching tone, no emotional padding.

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
    "personal": """You are a direct personal advisor.
Be clear, grounded, and practical.
No praise, no coaching tone, no emotional padding.

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

SUMMARY_SYSTEM = """You are updating an executive summary panel.
Be concise and factual. Compress signal.

Return exactly:
Objective:
...

Current Situation:
...

Key Risks:
- ...
- ...

Active Strategy:
...

Next Moves:
- ...
- ...
- ..."""

@app.get("/")
def root():
    return {"status": "live"}

def build_context(req: RequestModel) -> str:
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
        context_parts.append("Personal Knowledge Files:\n" + req.uploaded_context[:6000])
    if req.request_attachment_context:
        context_parts.append("Files Attached To This Request:\n" + req.request_attachment_context[:4000])
    if req.prior_summary:
        context_parts.append("Prior Executive Summary:\n" + req.prior_summary)

    return "\n\n".join(context_parts) if context_parts else "No extra context provided."

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        context_block = build_context(req)

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPTS.get(req.mode, SYSTEM_PROMPTS["strategy"])},
                {"role": "user", "content": f"{context_block}\n\nCurrent Mode: {req.mode}\n\nSituation:\n{req.input}"}
            ]
        )
        output = response.output_text

        summary_response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SUMMARY_SYSTEM},
                {"role": "user", "content": f"{context_block}\n\nUser Input:\n{req.input}\n\nEngine Output:\n{output}"}
            ]
        )

        return {"output": output, "summary": summary_response.output_text}
    except Exception as e:
        return {"error": str(e)}
