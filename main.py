Will Webb <corporatesidebar@gmail.com>
7:55 AM (0 minutes ago)
to me

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ THIS FIXES YOUR ERROR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow ALL domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    allow_origins=["*"],  # allow ALL domains
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
            "Focus on outcome alignment",
            "Control value perception",
            "Clarify leverage position"
        ],
        "risks": [
            "Weak framing",
            "Missing key context"
        ],
        "leverage": [
            "Reframe value perception",
            "Control narrative early"
        ],
        "best_move": "Clarify objective → reframe → lead decisively"
    }
