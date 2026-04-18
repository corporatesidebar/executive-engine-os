from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
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
        "best_move": result["best_move"]
    }).execute()

    return result

# 🔥 NEW: INTELLIGENCE ENGINE
@app.get("/intelligence")
def intelligence():

    data = supabase.table("decisions").select("*").limit(20).execute().data

    all_moves = [d["best_move"] for d in data if d.get("best_move")]

    combined = "\n".join(all_moves)

    prompt = f"""
You are an elite operator.

These are recent actions:

{combined}

Your job:
- remove duplicates
- combine similar ideas
- prioritize impact

Return ONLY:

PRIORITIES:
1. ...
2. ...
3. ...
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return {"priorities": response.choices[0].message.content}
