from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InputData(BaseModel):
    situation: str
    objective: str
    constraints: str
    context: str
    leverage_goal: str

@app.get("/")
def root():
    return {"status": "running"}

def extract(text, section):
    pattern = rf"{section}:(.*?)(\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return [l.strip("- ").strip() for l in match.group(1).split("\n") if l.strip()]
    return []

@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are a ruthless executive operator.

No fluff. No generic advice. No safe answers.

INPUT:
{data.situation}

Rules:
- Think like a CEO under pressure
- Focus on leverage and execution
- Be specific and direct

Return EXACT format:

WHAT MATTERS:
- bullet

RISKS:
- bullet

LEVERAGE:
- bullet

BEST MOVE:
- one clear decisive sentence
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )

        text = response.choices[0].message.content

        return {
            "what_matters": extract(text,"WHAT MATTERS"),
            "risks": extract(text,"RISKS"),
            "leverage": extract(text,"LEVERAGE"),
            "best_move": extract(text,"BEST MOVE")[0] if extract(text,"BEST MOVE") else text
        }

    except Exception as e:
        return {
            "what_matters": ["ERROR"],
            "risks": [str(e)],
            "leverage": [],
            "best_move": "Check API / billing"
        }
