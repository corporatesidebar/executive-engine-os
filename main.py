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
            input=f"You are an executive decision engine. User input: {req.input}"
        )
        return {"output": response.output_text}
    except Exception as e:
        return {"error": str(e)}
