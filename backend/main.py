from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Request(BaseModel):
    input: str

@app.post("/run")
async def run_engine(req: Request):

    prompt = f"""
You are an elite executive decision engine.

Return ONLY clean structured output:

decision:
next_move:
actions:
risk:
priority:

Input:
{req.input}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    text = response.choices[0].message.content

    def extract(key):
        import re
        m = re.search(f"{key}:(.*)", text)
        return m.group(1).strip() if m else ""

    return {
        "decision": extract("decision"),
        "next_move": extract("next_move"),
        "actions": [a.strip() for a in extract("actions").split(",") if a],
        "risk": extract("risk"),
        "priority": extract("priority")
    }
