from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

class RequestModel(BaseModel):
    input: str

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"""
You are a high-level executive decision engine.

You do NOT give generic advice.
You think like a CEO, strategist, and operator.

For every input, return:

1. Outcome
2. Risk
3. Action
4. Priority

Be direct, sharp, and real-world focused.
No fluff.

User input:
{req.input}
"""
        )
        return {"output": response.output_text}
    except Exception as e:
        return {"error": str(e)}
