from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Request(BaseModel):
    input: str

@app.post("/run")
def run_engine(req: Request):
    return {
        "outcome": "Clear next move",
        "risk": "Execution delay",
        "action": "Act immediately",
        "priority": "High"
    }
