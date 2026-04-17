from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import re

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class InputData(BaseModel):
    situation: str
    objective: str
    constraints: str
    context: str
    leverage_goal: str

# OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Health check
@app.get("/")
def root():
    return {"status": "running"}

# Helper to extract sections
def extract_section(text, section):
    pattern = rf"{section}:(.*?)(\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        lines = match.group(1).strip().split("\n")
        return [line.replace("- ", "").strip() for line in lines if line.strip()]
    return []

# MAIN ANALYSIS
@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are an elite executive strategist.

Analyze the following:

SITUATION: {data.situation}
OBJECTIVE: {data.objective}
CONSTRAINTS: {data.constraints}
CONTEXT: {data.context}
LEVERAGE GOAL: {data.leverage_goal}

Return EXACTLY in this format:

WHAT MATTERS:
- ...

RISKS:
- ...

LEVERAGE:
- ...

BEST MOVE:
- one decisive sentence
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content

        what_matters = extract_section(text, "WHAT MATTERS")
        risks = extract_section(text, "RISKS")
        leverage = extract_section(text, "LEVERAGE")
        best_move = extract_section(text, "BEST MOVE")

        return {
            "what_matters": what_matters,
            "risks": risks,
            "leverage": leverage,
            "best_move": best_move[0] if best_move else text
        }

    except Exception as e:
        return {
            "what_matters": ["ERROR"],
            "risks": [str(e)],
            "leverage": [],
            "best_move": "Check API key / deployment"
        }
