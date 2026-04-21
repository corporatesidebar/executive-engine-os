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
            {"role": "user", "content": text}
        ]
    )

    return {"response": response.choices[0].message.content}
