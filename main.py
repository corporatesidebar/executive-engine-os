from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    situation: str
    objective: str
    constraints: str
    context: str
    leverage_goal: str

@app.get("/")
def root():
    return {"status": "running"}

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are a high-level executive decision strategist.

Break this down clearly and concisely:

SITUATION: {data.situation}
OBJECTIVE: {data.objective}
CONSTRAINTS: {data.constraints}
CONTEXT: {data.context}
LEVERAGE GOAL: {data.leverage_goal}

Return ONLY:

WHAT MATTERS:
- bullet points

RISKS:
- bullet points

LEVERAGE:
- bullet points

BEST MOVE:
- one decisive sentence
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content

    return {
        "what_matters": [text],
        "risks": [],
        "leverage": [],
        "best_move": text
    }
