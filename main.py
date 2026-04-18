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

# KEYS
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# INPUT MODEL
class InputData(BaseModel):
    situation: str

# PARSER
def extract(text, section):
    pattern = rf"{section}:(.*?)(\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return [l.strip("- ").strip() for l in match.group(1).split("\n") if l.strip()]
    return []

# MAIN ENGINE
@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are APEX — an elite executive operator.

You think in leverage, risk, and decisive action.

INPUT:
{data.situation}

Return EXACT format:

WHAT MATTERS:
- ...

RISKS:
- ...

LEVERAGE:
- ...

BEST MOVE:
- one direct action sentence
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
        "best_move": extract(text,"BEST MOVE")[0] if extract(text,"BEST MOVE") else text
    }

    # SAVE TO MEMORY
    supabase.table("decisions").insert({
        "input": data.situation,
        "what_matters": str(result["what_matters"]),
        "risks": str(result["risks"]),
        "leverage": str(result["leverage"]),
        "best_move": result["best_move"]
    }).execute()

    return result

# HISTORY
@app.get("/history")
def history():
    data = supabase.table("decisions").select("*").limit(10).execute()
    return data.data
