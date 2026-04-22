from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from openai import OpenAI
from supabase import create_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/command.html")
def command():
    return FileResponse("command.html")

@app.post("/api/command")
async def command_api(data: dict):
    user_input = data.get("input", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an executive decision engine. Respond in structured format: Situation Summary, Key Problems, Strategic Options, Recommended Action, Next Steps."},
                {"role": "user", "content": user_input}
            ],
        )

        output = response.choices[0].message.content

        supabase.table("items").insert({
            "input": user_input,
            "output": output
        }).execute()

        return {"output": output}

    except Exception as e:
        return {"error": str(e)}
