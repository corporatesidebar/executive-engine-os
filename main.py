from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SUPABASE_URL = "https://asmajwoyfygkabhhaye.supabase.co"
SUPABASE_KEY = "sb_publishable_X44x716G4WW1u4Q5msuTwA_DYZzLmvg"

memory = []

PROMPTS = {
    "strategy": "You are a high-level business strategist. Focus on long-term leverage and positioning.",
    "hiring": "You are a hiring expert. Focus on talent ROI, ramp time, and risk.",
    "finance": "You are a financial operator. Focus on cost, ROI, and capital allocation.",
    "execution": "You are an execution expert. Focus on steps, speed, and priorities."
}

FORMAT = """You MUST follow this exact structure. No extra text.

Situation Summary:
(2-3 sentences max)

Key Problems:
- Bullet 1
- Bullet 2
- Bullet 3

Strategic Options:
1. Option A
2. Option B
3. Option C

Recommended Action:
(1 clear decision)

Next Steps:
1. Step 1
2. Step 2
3. Step 3
"""

def save_to_supabase(user_input, ai_output, mode):
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/items",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json={
                "input": user_input,
                "output": ai_output,
                "mode": mode
            },
            timeout=15
        )
    except Exception as e:
        print("Supabase save failed:", e)

@app.get("/")
def root():
    return FileResponse("index.html")

@app.get("/command.html")
def command_page():
    return FileResponse("command.html")

@app.post("/command")
async def command(request: Request):
    data = await request.json()
    text = data.get("situation", "").strip()
    mode = data.get("mode", "strategy")

    system_prompt = PROMPTS.get(mode, PROMPTS["strategy"]) + "\n\n" + FORMAT
    context = "\n".join(memory[-5:])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context + "\n\n" + text}
        ]
    )

    output = response.choices[0].message.content

    memory.append(f"[{mode}] {text} -> {output[:120]}")
    save_to_supabase(text, output, mode)

    return {"response": output}
