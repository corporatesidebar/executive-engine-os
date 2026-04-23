
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandInput(BaseModel):
    input: str
    mode: str = "strategy"
    profile_role: Optional[str] = ""
    profile_industry: Optional[str] = ""
    profile_tone: Optional[str] = ""
    profile_goal: Optional[str] = ""
    personal_context: Optional[str] = ""
    uploaded_context: Optional[str] = ""

def mock_response(req: CommandInput):
    mode = req.mode.title()
    prompt = req.input.strip()

    return {
        "structured": {
            "decision": f"{mode}: make a direct call on '{prompt[:100]}'",
            "why": "This version is wired for live structured output and can be switched to OpenAI or Claude by adding API keys.",
            "risk": "The current response is a fallback until live model credentials are configured.",
            "action_items": [
                "Confirm the product direction",
                "Define the top 3 decision criteria",
                "Execute the first next step today"
            ],
            "priority": "High",
            "feedback_overview": "System wiring is complete. Live model integration is the next upgrade."
        }
    }

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/api/command")
async def api_command(req: CommandInput):
    return mock_response(req)
