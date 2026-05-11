import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

VERSION = "V35150-real-output-contract"

app = FastAPI(title="Executive Engine OS", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_KEYS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
]

VALID_PRIORITIES = {"High", "Medium", "Low"}


class RunRequest(BaseModel):
    input: str = ""
    mode: Optional[str] = "execution"


def fallback_contract(user_input: str = "", mode: str = "execution") -> Dict[str, Any]:
    clean_input = (user_input or "").strip()
    mode_label = (mode or "execution").strip() or "execution"

    if clean_input:
        next_move = f"Clarify the immediate executive outcome for: {clean_input[:140]}"
        decision = "Proceed with a structured execution pass using the current stable workflow."
        recommended = f"Run a sharper {mode_label} command with owner, deadline, and success metric."
    else:
        next_move = "Enter the highest-value business outcome that needs movement today."
        decision = "Hold execution until the command includes a clear objective."
        recommended = "Define the objective, deadline, owner, and desired result."

    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": [
            "Confirm the business outcome and deadline.",
            "Identify the owner and the next concrete action.",
            "Define the risk, priority, and expected finished asset.",
        ],
        "ready_assets": [],
        "risk": "Execution may drift if the command lacks owner, timing, or measurable outcome.",
        "priority": "High" if clean_input else "Medium",
        "recommended_command": recommended,
    }


def as_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        output: List[str] = []
        for item in value:
            text = as_string(item)
            if text:
                output.append(text)
        return output
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        lines = [line.strip(" -•\t") for line in text.splitlines()]
        cleaned = [line for line in lines if line]
        return cleaned or [text]
    return [as_string(value)] if as_string(value) else []


def normalize_contract(raw: Any, user_input: str = "", mode: str = "execution") -> Dict[str, Any]:
    base = fallback_contract(user_input=user_input, mode=mode)

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}

    if not isinstance(raw, dict):
        raw = {}

    result = {
        "next_move": as_string(raw.get("next_move"), base["next_move"]) or base["next_move"],
        "decision": as_string(raw.get("decision"), base["decision"]) or base["decision"],
        "action_steps": as_list(raw.get("action_steps")) or base["action_steps"],
        "ready_assets": as_list(raw.get("ready_assets")),
        "risk": as_string(raw.get("risk"), base["risk"]) or base["risk"],
        "priority": as_string(raw.get("priority"), base["priority"]).title() or base["priority"],
        "recommended_command": as_string(raw.get("recommended_command"), base["recommended_command"])
        or base["recommended_command"],
    }

    if result["priority"] not in VALID_PRIORITIES:
        result["priority"] = base["priority"] if base["priority"] in VALID_PRIORITIES else "Medium"

    return {key: result[key] for key in REQUIRED_KEYS}


def extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def build_system_prompt() -> str:
    return """
You are Executive Engine OS, a private executive operating system.
Return only valid JSON. Do not include markdown, commentary, or extra keys.
Required exact keys:
next_move, decision, action_steps, ready_assets, risk, priority, recommended_command.
Rules:
- next_move: one immediate executive move.
- decision: one clear decision.
- action_steps: array of 3 to 6 concrete actions.
- ready_assets: array of assets that can be prepared now; empty array if none.
- risk: one direct operational risk.
- priority: High, Medium, or Low only.
- recommended_command: one command the executive should run next.
""".strip()


def run_ai(user_input: str, mode: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return {}

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": json.dumps({"mode": mode, "input": user_input}, ensure_ascii=False),
            },
        ],
        timeout=30,
    )

    content = response.choices[0].message.content if response.choices else ""
    return extract_json(content or "")


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Executive Engine OS",
        "version": VERSION,
        "status": "live",
        "message": "Autonomous Executive Operator live.",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "contract": REQUIRED_KEYS,
    }


@app.post("/run")
def run(payload: RunRequest) -> Dict[str, Any]:
    user_input = payload.input or ""
    mode = payload.mode or "execution"

    try:
        ai_output = run_ai(user_input=user_input, mode=mode)
    except Exception:
        ai_output = {}

    return normalize_contract(ai_output, user_input=user_input, mode=mode)
