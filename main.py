from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os, json

app = FastAPI()

# 🔥 BULLETPROOF CORS (no more blocking)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InputData(BaseModel):
    situation: str

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/command")
def command(data: InputData):

    prompt = f"""
Return JSON:
{{
 "outcome": "...",
 "context": "...",
 "required_action": "...",
 "next": "..."
}}
INPUT: {data.situation}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return json.loads(res.choices[0].message.content)
