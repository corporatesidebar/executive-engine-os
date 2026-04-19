
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os, json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://willwebb.ca",
        "https://www.willwebb.ca"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ACTIVE_CONTEXT = {"text": ""}
ASSETS = []

class InputData(BaseModel):
    situation: str

class ActionData(BaseModel):
    type: str
    context: str = ""

class SaveData(BaseModel):
    type: str
    content: str

@app.post("/command")
def command(data: InputData):
    ACTIVE_CONTEXT["text"] = data.situation

    prompt = f"""
Return JSON:
{{
 "outcome": "...",
 "context": "...",
 "required_action": "...",
 "support": ["meeting","proposal","content","strategy"],
 "next": "..."
}}
INPUT: {data.situation}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return json.loads(res.choices[0].message.content)

@app.post("/action")
def action(data: ActionData):
    prompt = f"Generate {data.type} based on: {data.context or ACTIVE_CONTEXT['text']}"

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return {"result": res.choices[0].message.content}

@app.post("/save")
def save(data: SaveData):
    ASSETS.append({"type": data.type, "content": data.content})
    return {"status": "saved"}

@app.get("/assets")
def get_assets():
    return ASSETS
