import os
import json
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

APP_VERSION = "rebuild-minimum-v1"

app = FastAPI(title="Executive Engine OS", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    input: str
    mode: Optional[str] = "execution"


class RunResponse(BaseModel):
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str
    mode: str
    provider_used: str
    version: str


SYSTEM_PROMPT = """
You are Executive Engine OS, a senior executive operating system.
Return only valid JSON with these exact keys:
decision, next_move, actions, risk, priority.
Rules:
- Be direct.
- No fluff.
- Make action steps specific.
- Use executive/operator language.
- Priority must be High, Medium, or Low.
- actions must be an array of 3 to 6 strings.
"""


def fallback_response(user_input: str, mode: str, reason: str = "fallback") -> RunResponse:
    return RunResponse(
        decision="Proceed with a focused execution pass and stabilize the highest-value next action.",
        next_move="Clarify the objective, identify the blocker, and move one concrete action forward now.",
        actions=[
            "Define the outcome in one sentence.",
            "Identify the single constraint slowing execution.",
            "Choose the highest-leverage next action.",
            "Assign ownership and deadline.",
            "Review risk before moving to the next task."
        ],
        risk=f"AI provider unavailable or response failed validation. Reason: {reason}.",
        priority="High",
        mode=mode or "execution",
        provider_used="fallback-local",
        version=APP_VERSION,
    )


def normalize_payload(payload: dict, mode: str) -> RunResponse:
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        actions = [
            "Confirm the objective.",
            "Identify the decision owner.",
            "Move the next action forward."
        ]

    priority = str(payload.get("priority", "High")).strip().title()
    if priority not in {"High", "Medium", "Low"}:
        priority = "High"

    return RunResponse(
        decision=str(payload.get("decision", "Proceed with focused execution.")),
        next_move=str(payload.get("next_move", "Move the highest-value action forward now.")),
        actions=[str(item) for item in actions[:6]],
        risk=str(payload.get("risk", "Execution risk requires review.")),
        priority=priority,
        mode=mode or "execution",
        provider_used="openai",
        version=APP_VERSION,
    )


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Executive Engine OS Backend",
        "version": APP_VERSION,
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/debug")
def debug():
    return {
        "version": APP_VERSION,
        "routes": ["/", "/health", "/debug", "/run"],
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    user_input = (req.input or "").strip()
    mode = (req.mode or "execution").strip().lower()

    if not user_input:
        return fallback_response(user_input, mode, "empty_input")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return fallback_response(user_input, mode, "openai_not_configured")

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Mode: {mode}\nExecutive request: {user_input}",
                },
            ],
            temperature=0.25,
            response_format={"type": "json_object"},
            timeout=35,
        )
        content = completion.choices[0].message.content or "{}"
        payload = json.loads(content)
        return normalize_payload(payload, mode)
    except Exception as exc:
        return fallback_response(user_input, mode, str(exc)[:220])
