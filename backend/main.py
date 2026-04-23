
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import json
from typing import Optional

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
    uploaded_context: Optional[str] = None
    request_attachment_context: Optional[str] = None

MODE_GUIDANCE = {
    "strategy": "Choose a direction and make the tradeoff explicit.",
    "decision": "Force a decision and explain why this option wins.",
    "meeting": "Turn the situation into a focused meeting outcome with immediate next steps.",
    "execution": "Sequence the work, remove blockers, and make action immediate.",
    "personal": "Be direct, practical, and grounded."
}

def trimmed_context(req: RequestModel) -> str:
    parts = []
    if req.profile_role:
        parts.append(f"Role Target: {req.profile_role}")
    if req.profile_industry:
        parts.append(f"Industry: {req.profile_industry}")
    if req.profile_tone:
        parts.append(f"Tone: {req.profile_tone}")
    if req.profile_goal:
        parts.append(f"Goal: {req.profile_goal}")
    if req.personal_context:
        parts.append(f"Personal Context: {req.personal_context[:500]}")
    if req.uploaded_context:
        parts.append("Personal Knowledge: " + req.uploaded_context[:1500])
    if req.request_attachment_context:
        parts.append("Request Attachment: " + req.request_attachment_context[:1000])
    return "\n".join(parts)

SYSTEM_PROMPT = """
You are Executive Engine, an operator-grade decision system.

Your job is not to coach, hedge, or nag.
Your job is to make a call, explain the logic, identify the main risk, and give immediate next actions.

Rules:
- Be decisive.
- No filler.
- No motivational language.
- No generic advice.
- Make the output practical and commercially intelligent.
- Prefer clarity over comprehensiveness.
- If context is weak, still make the best call and state the key assumption briefly.
- Keep action items concrete and executable.

Return ONLY valid JSON with this exact shape:
{
  "decision": "string",
  "why": "string",
  "risk": "string",
  "action_items": ["string", "string", "string"],
  "priority": "High | Medium | Low",
  "feedback_overview": "string"
}
"""

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        context_block = trimmed_context(req)
        user_prompt = f"""Mode: {req.mode}
Mode Guidance: {MODE_GUIDANCE.get(req.mode, MODE_GUIDANCE['strategy'])}

Relevant Context:
{context_block if context_block else 'None'}

Situation:
{req.input}"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        text = response.output_text.strip()
        structured = json.loads(text)

        if not isinstance(structured.get("action_items"), list):
            structured["action_items"] = [str(structured.get("action_items", ""))]

        structured["action_items"] = [str(x) for x in structured["action_items"][:5] if str(x).strip()]

        return {"structured": structured}
    except Exception as e:
        return {
            "structured": {
                "decision": "Engine response failed",
                "why": f"The backend could not complete the structured response: {str(e)}",
                "risk": "The system returned no usable decision output.",
                "action_items": [
                    "Retry with a shorter input",
                    "Reduce large uploaded context",
                    "Run the request again"
                ],
                "priority": "Medium",
                "feedback_overview": "The request failed before a structured decision could be generated."
            }
        }
