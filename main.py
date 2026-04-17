from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    situation: str
    objective: str
    constraints: str
    context: str
    leverage_goal: str

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/analyze")
def analyze(data: InputData):
    return {
        "what_matters": [
            "Clarity of objective",
            "Strong positioning",
            "Execution speed"
        ],
        "risks": [
            "Unclear direction",
            "Weak leverage"
        ],
        "leverage": [
            "Control narrative",
            "Act decisively"
        ],
        "best_move": "Clarify → position → execute"
    }
