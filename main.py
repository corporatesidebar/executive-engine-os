from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()

def detect_mode(text):
    text = text.lower()
    if "meeting" in text:
        return "meeting"
    if "strategy" in text:
        return "strategy"
    return "decision"

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/command")
def command(data: dict):
    situation = data.get("situation", "")
    mode = detect_mode(situation)

    system_prompt = f"""
You are an executive operating system.

Mode: {mode}

Return ONLY in this format:

Outcome:
<clear result>

Risk:
<main risk>

Action:
<next step>

Priority:
<low, medium, high>
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": situation}
        ]
    )

    output = response.choices[0].message.content

    return {
        "mode": mode,
        "response": output
    }
