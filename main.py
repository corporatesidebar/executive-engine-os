from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
import os
import re
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class InputData(BaseModel):
    situation: str

def extract(text, section):
    pattern = rf"{section}:(.*?)(\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return [l.strip("- ").strip() for l in match.group(1).split("\n") if l.strip()]
    return []

@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are APEX — elite executive operator.

INPUT:
{data.situation}

Return:

WHAT MATTERS:
- ...

RISKS:
- ...

LEVERAGE:
- ...

BEST MOVE:
- one direct action
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    text = response.choices[0].message.content

    result = {
        "what_matters": extract(text,"WHAT MATTERS"),
        "risks": extract(text,"RISKS"),
        "leverage": extract(text,"LEVERAGE"),
        "best_move": extract(text,"BEST MOVE")[0]
    }

    supabase.table("decisions").insert({
        "input": data.situation,
        "what_matters": str(result["what_matters"]),
        "risks": str(result["risks"]),
        "leverage": str(result["leverage"]),
        "best_move": result["best_move"],
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return result

# 🔥 INTELLIGENCE ENGINE (UPGRADED)
@app.get("/intelligence")
def intelligence():

    data = supabase.table("decisions").select("*").limit(30).execute().data

    moves = [d["best_move"] for d in data if d.get("best_move")]
    combined = "\n".join(moves)

    prompt = f"""
You are an elite operator.

These are recent actions:
{combined}

Analyze and return:

PRIORITIES:
1. top action
2. second action
3. third action

URGENCY:
1. what must be done immediately
2. what can wait

REVENUE IMPACT:
1. highest revenue action
2. secondary revenue action
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return {"data": response.choices[0].message.content}
