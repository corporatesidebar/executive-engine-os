import asyncio
import json
from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI()

MEMORY = []

ALLOWED_PRIORITIES = {"High", "Medium", "Low"}

VERB_STARTERS = {
    "align", "assign", "audit", "build", "call", "check", "choose", "clarify",
    "close", "commit", "confirm", "contact", "create", "cut", "define",
    "delete", "deploy", "document", "draft", "execute", "finalize", "fix",
    "focus", "identify", "launch", "limit", "lock", "make", "map", "measure",
    "move", "open", "pause", "prioritize", "publish", "push", "reduce",
    "remove", "review", "run", "schedule", "send", "set", "ship", "simplify",
    "start", "stop", "test", "update", "validate", "write"
}


class RunRequest(BaseModel):
    input: str
    mode: str = "execution"


class RunResponse(BaseModel):
    what_to_do_now: str
    decision: str
    next_move: str
    actions: List[str]
    risk: str
    priority: str


SYSTEM_PROMPT = """
You are a high-performance COO.

You think in:
- leverage
- speed
- outcomes

Rules:
- No vague language
- No generic advice
- No filler
- Every response must feel like a real operator decision

Definitions:
- what_to_do_now = ONE immediate action (no explanation)
- decision = clear stance (commit to something)
- next_move = what happens right after
- actions = step-by-step execution (3–6 max, concrete)
- risk = real downside, not generic
- priority = High / Medium / Low based on impact

If input is vague:
→ make assumptions and move forward

If input is broad:
→ narrow to highest leverage move

Output ONLY valid JSON.
"""


def fallback_response(user_input: str = "", mode: str = "execution") -> dict:
    clean_input = (user_input or "").strip()

    if clean_input:
        return {
            "what_to_do_now": "Lock the single highest-leverage next move",
            "decision": "Move forward with a focused execution path instead of widening the scope",
            "next_move": "Convert the input into one concrete task and execute it first",
            "actions": [
                "Define the immediate outcome",
                "Remove every non-essential task",
                "Assign the next owner or tool",
                "Execute the first visible step",
                "Review the result before expanding scope"
            ],
            "risk": "Execution will drift if the request stays broad or overloaded",
            "priority": "High"
        }

    return {
        "what_to_do_now": "Enter the highest-priority objective",
        "decision": "Do not generate a plan until the core objective is stated",
        "next_move": "Submit one business problem, decision, or execution task",
        "actions": [
            "Write the objective",
            "Add the current constraint",
            "Identify the desired outcome",
            "Run the engine again"
        ],
        "risk": "Empty input produces low-value execution guidance",
        "priority": "High"
    }


def extract_json(content: str) -> dict:
    if not content:
        return {}

    text = content.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return {}

    return {}


async def call_model(user_input: str, mode: str) -> dict:
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.25,
                max_tokens=450,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Mode: {mode}\nInput: {user_input}"
                    }
                ],
            ),
            timeout=10
        )

        content = response.choices[0].message.content or ""
        parsed = extract_json(content)

        if not parsed:
            return fallback_response(user_input, mode)

        return parsed

    except Exception:
        return fallback_response(user_input, mode)


def clean_string(value, fallback_value: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else fallback_value


def starts_with_verb(action: str) -> bool:
    first_word = action.strip().split(" ")[0].lower().strip(":-—–,.!")
    return first_word in VERB_STARTERS or first_word.endswith(("e", "y"))


def force_verb_action(action: str) -> str:
    text = action.strip()
    if not text:
        return ""

    if starts_with_verb(text):
        return text[0].upper() + text[1:]

    return f"Execute: {text[0].lower() + text[1:]}"


def clean_actions(actions, fallback_actions: List[str]) -> List[str]:
    if not isinstance(actions, list):
        actions = []

    cleaned = []

    for action in actions:
        text = str(action).strip() if action is not None else ""
        if not text:
            continue

        cleaned_action = force_verb_action(text)
        if cleaned_action:
            cleaned.append(cleaned_action)

    if not cleaned:
        cleaned = fallback_actions

    return cleaned[:5]


def is_weak_output(output: dict) -> bool:
    required = ["what_to_do_now", "decision", "next_move", "actions", "risk", "priority"]

    for field in required:
        value = output.get(field)
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if field == "actions" and (not isinstance(value, list) or len(value) == 0):
            return True

    return False


def clean_output(raw_output: dict, user_input: str = "", mode: str = "execution") -> dict:
    base = fallback_response(user_input, mode)
    raw = raw_output if isinstance(raw_output, dict) else {}

    what_to_do_now = clean_string(raw.get("what_to_do_now"), base["what_to_do_now"])
    decision = clean_string(raw.get("decision"), base["decision"])
    next_move = clean_string(raw.get("next_move"), base["next_move"])
    risk = clean_string(raw.get("risk"), base["risk"])

    actions = clean_actions(raw.get("actions"), base["actions"])

    priority = clean_string(raw.get("priority"), "High")
    if priority not in ALLOWED_PRIORITIES:
        priority = "High"

    cleaned = {
        "what_to_do_now": what_to_do_now,
        "decision": decision,
        "next_move": next_move,
        "actions": actions,
        "risk": risk,
        "priority": priority
    }

    if is_weak_output(cleaned):
        cleaned["priority"] = "High"

    return cleaned


def save_memory(input_text: str, output: dict):
    global MEMORY

    MEMORY.append({
        "input": input_text,
        "decision": output.get("decision"),
        "next_move": output.get("next_move"),
        "actions": output.get("actions"),
        "timestamp": datetime.utcnow().isoformat()
    })

    MEMORY = MEMORY[-5:]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    try:
        raw = await call_model(req.input, req.mode)
        clean = clean_output(raw, req.input, req.mode)
        save_memory(req.input, clean)
        return clean
    except Exception:
        clean = clean_output(fallback_response(req.input, req.mode), req.input, req.mode)
        save_memory(req.input, clean)
        return clean


@app.get("/memory")
async def memory():
    return {"memory": MEMORY}
