from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import requests
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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SYSTEM_PROMPT = """
You are a high-level executive operator.

Be decisive. No fluff.

Return:

Outcome:
...

Risk:
...

Action:
...

Priority:
...
"""

def save_to_supabase(user_input, ai_output):
try:
if not SUPABASE_URL or not SUPABASE_KEY:
return

```
    requests.post(
        f"{SUPABASE_URL}/rest/v1/items",
        json={
            "input": user_input,
            "output": ai_output
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    )
except Exception as e:
    print("Supabase error:", e)
```

@app.get("/")
def root():
return {"status": "live"}

@app.post("/command")
async def command(request: Request):
body = await request.json()
user_input = body.get("situation")

```
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ],
    temperature=0.4
)

ai_output = response.choices[0].message.content

save_to_supabase(user_input, ai_output)

return {"response": ai_output}
```
