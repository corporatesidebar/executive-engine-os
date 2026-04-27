import os
import json
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AsyncOpenAI


APP_NAME = "Executive Engine OS"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "40"))

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_KEYS = [
    "what_to_do_now",
    "decision",
    "next_move",
    "actions",
    "risk",
    "priority",
]


class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None
    mode: Optional[str] = "execution"


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_response():
    return {
        "what_to_do_now": "Retry with clear input",
        "decision": "Fallback triggered",
        "next_move": "Send new request",
        "actions": ["Retry request"],
        "risk": "Temporary failure",
        "priority": "high",
    }


def extract_json(text: str):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
    raise ValueError("Invalid JSON")


def normalize(data):
    if not isinstance(data, dict):
        return safe_response()

    return {
        "what_to_do_now": data.get("what_to_do_now") or "Execute next step",
        "decision": data.get("decision") or "Proceed",
        "next_move": data.get("next_move") or "Continue",
        "actions": data.get("actions") or ["Execute"],
        "risk": data.get("risk") or "None",
        "priority": str(data.get("priority", "medium")).lower(),
    }


def build_prompt(user_input):
    return [
        {
            "role": "system",
            "content": """
Return ONLY valid JSON.

{
 "what_to_do_now": "",
 "decision": "",
 "next_move": "",
 "actions": [""],
 "risk": "",
 "priority": "low|medium|high|critical"
}
""",
        },
        {"role": "user", "content": user_input},
    ]


@app.get("/health")
async def health():
    return {
        "ok": True,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/run")
async def run(req: RunRequest):
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                messages=build_prompt(req.input),
                temperature=0.2,
                response_format={"type": "json_object"},
            ),
            timeout=OPENAI_TIMEOUT_SECONDS,
        )

        content = response.choices[0].message.content
        parsed = extract_json(content)
        return normalize(parsed)

    except Exception:
        return safe_response()
