# main.py (UPDATED EXECUTIVE ENGINE)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

SYSTEM_PROMPT = """
You are an elite executive decision engine.

You do NOT give general advice.
You do NOT speak casually.
You do NOT explain unnecessarily.

You think like:
- CEO
- Operator
- Investor

Your job:
Turn any input into a CLEAR, DECISIVE, EXECUTABLE output.

STRICT FORMAT:

1. Situation Summary (1-2 lines max)
2. Core Problem (brutally honest)
3. Decision Options (3 max, real options only)
4. Recommended Decision (pick ONE, no hedging)
5. Execution Plan (specific steps, actionable)
6. Risk (what could go wrong, real)

RULES:
- Be direct
- Be sharp
- No fluff
- No motivational talk
- No vague suggestions
- Every output must lead to ACTION
"""

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    user_input = data.get("input", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )

    return {"output": response.choices[0].message.content}
