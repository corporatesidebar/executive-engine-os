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

# Optional Supabase config from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SYSTEM_PROMPT = """You are an elite executive decision engine.

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

Situation Summary:
(1-2 lines max)

Core Problem:
(brutally honest)

Decision Options:
1. Option A
2. Option B
3. Option C

Recommended Decision:
(pick ONE, no hedging)

Execution Plan:
1. Step 1
2. Step 2
3. Step 3

Risk:
(what could go wrong, real)
"""

def save_to_supabase(user_input: str, ai_output: str, mode: str) -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/items",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "input": user_input,
                "output": ai_output,
                "mode": mode,
            },
            timeout=15,
        )
    except Exception as e:
        print("Supabase save failed:", e)

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/command.html")
def command_page():
    return FileResponse("command.html")

@app.post("/command")
async def command(request: Request):
    data = await request.json()
    user_input = data.get("situation", "").strip()
    mode = data.get("mode", "strategy").strip() or "strategy"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\nCurrent mode: {mode}"},
            {"role": "user", "content": user_input},
        ],
    )

    output = response.choices[0].message.content
    save_to_supabase(user_input, output, mode)
    return {"response": output}
