from fastapi import FastAPI
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"status": "live"}

@app.get("/debug")
def debug():
    return {
        "has_api_key": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.post("/run")
async def run_engine(data: dict):
    try:
        prompt = data.get("input", "")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return JSON with: decision, next_move, actions (array), risk, priority."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"output": response.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}
