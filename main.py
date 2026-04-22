from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RequestModel(BaseModel):
    input: str

@app.post("/api/command")
async def command(req: RequestModel):
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"Analyze this situation and give structured output: {req.input}"
        )

        return {"output": response.output_text}

    except Exception as e:
        return {"error": str(e)}
