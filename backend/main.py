import json
import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI


APP_NAME = "Executive Engine OS Backend V35"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FALLBACK_MODELS = [DEFAULT_MODEL, "gpt-4o", "gpt-4o-mini"]

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=18.0,
    max_retries=1,
)


class RunRequest(BaseModel):
    input: str
    mode: Optional[str] = "strategy"


class EngineResponse(BaseModel):
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str


def fallback_response(reason: str = "AI service unavailable") -> dict:
    return {
        "decision": "Reset execution around one clear business objective before adding more work.",
        "next_move": "Write the exact outcome you want, then choose the single action that moves it forward today.",
        "actions": [
            "Define the desired result in one sentence.",
            "Identify the main bottleneck blocking execution.",
            "Assign one next action with an owner and deadline."
        ],
        "risk": f"{reason}. The main execution risk is moving without enough clarity.",
        "priority": "High"
    }


def strip_to_json(text: str) -> dict:
    cleaned = (text or "").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")

    return json.loads(cleaned[start:end + 1])


def normalize_response(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")

    required = ["decision", "next_move", "actions", "risk", "priority"]
    for key in required:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    actions = data.get("actions")
    if not isinstance(actions, list):
        actions = [str(actions)]

    priority = str(data.get("priority", "Medium")).strip().title()
    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"

    return {
        "decision": str(data.get("decision", "")).strip(),
        "next_move": str(data.get("next_move", "")).strip(),
        "actions": [str(action).strip() for action in actions if str(action).strip()][:5],
        "risk": str(data.get("risk", "")).strip(),
        "priority": priority,
    }


SYSTEM_PROMPT = """
Act as an elite COO / operator.

You make sharp executive decisions and convert messy business input into a clear execution path.

Rules:
- Be direct, useful, and action-first.
- No motivational fluff.
- No vague advice.
- No markdown.
- No explanations outside JSON.
- Return only valid JSON.

Required JSON format:
{
  "decision": "clear executive decision",
  "next_move": "single most important next action",
  "actions": ["action 1", "action 2", "action 3"],
  "risk": "main risk",
  "priority": "High | Medium | Low"
}
""".strip()


@app.get("/")
def health_check():
    return {
        "status": "live",
        "service": APP_NAME,
        "model": DEFAULT_MODEL,
    }


@app.get("/debug")
def debug():
    return {
        "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "model": DEFAULT_MODEL,
    }


@app.post("/run", response_model=EngineResponse)
def run_engine(request: RunRequest):
    user_input = request.input.strip()
    mode = (request.mode or "strategy").strip().lower()

    if not user_input:
        return fallback_response("No input provided")

    if not os.getenv("OPENAI_API_KEY"):
        return fallback_response("OPENAI_API_KEY missing")

    user_prompt = f"""
Mode: {mode}

Executive input:
{user_input}

Return strict JSON only.
""".strip()

    unique_models = []
    for model in FALLBACK_MODELS:
        if model and model not in unique_models:
            unique_models.append(model)

    last_error = "AI service unavailable"

    for model in unique_models:
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content
            parsed = strip_to_json(content)
            normalized = normalize_response(parsed)

            if not normalized["decision"] or not normalized["next_move"]:
                raise ValueError("Empty decision or next_move")

            if not normalized["actions"]:
                normalized["actions"] = ["Choose one owner, one deadline, and one measurable outcome."]

            return normalized

        except Exception as error:
            last_error = str(error)[:160]
            continue

    return fallback_response(last_error)
