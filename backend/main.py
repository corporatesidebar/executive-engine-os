from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Input(BaseModel):
    input: str

@app.post("/run-engine")
def run_engine(data: Input):
    return {
        "outcome": "Clear next move",
        "risk": "Moderate",
        "action": "Take first step immediately",
        "priority": "High"
    }
