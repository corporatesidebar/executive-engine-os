from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an elite executive decision system.

You MUST follow this exact structure. No extra text. No explanations outside sections.

FORMAT:

Situation Summary:
(2-3 sentences max)

Key Problems:
- Bullet 1
- Bullet 2
- Bullet 3

Strategic Options:
1. Option A (short)
2. Option B (short)
3. Option C (short)

Recommended Action:
(1 clear decision, no hedging)

Next Steps:
1. Step 1
2. Step 2
3. Step 3
"""

@app.get("/")
def root():
    return FileResponse("index.html")

@app.get("/command.html")
def command_page():
    return FileResponse("command.html")

@app.post("/command")
async def command(request: Request):
    data = await request.json()
    text = data.get("situation", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    )

    return {"response": response.choices[0].message.content}
