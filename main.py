from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
import os, json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

class InputData(BaseModel):
    situation: str

# 🔥 DECISION ENGINE
@app.post("/analyze")
def analyze(data: InputData):

    prompt = f"""
You are APEX — elite executive operator.

Be decisive. No fluff.

INPUT:
{data.situation}

Return JSON:

{{
 "objective": "...",
 "direction": "...",
 "next_step": "...",
 "support": ["proposal","contract","meeting","content"]
}}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    text = res.choices[0].message.content

    try:
        result = json.loads(text)
    except:
        result = {"objective":"","direction":"","next_step":text,"support":[]}

    supabase.table("decisions").insert({
        "input": data.situation,
        "next_step": result["next_step"]
    }).execute()

    return result


# 🔥 DASHBOARD INTELLIGENCE (NEW)
@app.get("/dashboard")
def dashboard():

    data = supabase.table("decisions").select("*").limit(10).execute().data

    combined = "\n".join([d["next_step"] for d in data])

    prompt = f"""
You are an executive system.

Summarize into:

WHAT:
DIRECTION:
NEXT:
SUPPORT OPTIONS:
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":combined}]
    )

    return {"data": res.choices[0].message.content}
