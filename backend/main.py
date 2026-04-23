from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import requests
import os
import json
from typing import Any, Dict, List, Optional

app = FastAPI(title="Executive Engine V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set")
if not SUPABASE_URL:
    print("WARNING: SUPABASE_URL is not set")
if not SUPABASE_KEY:
    print("WARNING: SUPABASE_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

BASE_SYSTEM_PROMPT = """
You are Executive Engine, an elite executive operating system for real-world business execution.

You think like a CEO, operator, strategist, and dealmaker.
You do not sound generic, soft, vague, or academic.
You cut through noise, expose tradeoffs, prioritize leverage, and recommend practical moves.

Your output must ALWAYS be valid JSON only.
Do not use markdown.
Do not include code fences.
Do not add commentary outside the JSON.

Return this exact schema:
{
  "executive_summary": "2-4 sentence summary",
  "outcome": "clear direction or decision",
  "priority": "High",
  "risks": ["risk 1", "risk 2"],
  "actions": [
    {"title": "action title", "detail": "what to do", "owner": "You", "timing": "Now"},
    {"title": "action title", "detail": "what to do", "owner": "You", "timing": "Next"}
  ],
  "assumptions": ["assumption 1", "assumption 2"],
  "follow_up_questions": ["question 1", "question 2"]
}

Rules:
- executive_summary: 2-4 sentences, commercially sharp
- outcome: direct and decisive
- priority: one of High, Medium, Low
- risks: 2-5 concise bullets
- actions: 3-6 items, ordered by importance
- assumptions: 0-4 items max
- follow_up_questions: 0-4 items max
- do not hedge excessively
- do not restate the prompt
- prefer actionability over explanation
"""

MODE_PROMPTS = {
    "decision": """
Mode: Decision
Purpose:
- make a call
- compare tradeoffs
- reduce hesitation
- recommend the strongest path

Bias:
- decisiveness over over-analysis
- downside awareness without paralysis
- clear recommendation with execution path
""",
    "strategy": """
Mode: Strategy
Purpose:
- think beyond the immediate problem
- identify leverage
- sequence moves intelligently
- create structural advantage

Bias:
- leverage over busyness
- sequencing over random effort
- durable upside over short-term noise
""",
    "meeting": """
Mode: Meeting
Purpose:
- turn messy discussion into clarity
- isolate what matters
- align stakeholders
- make next steps obvious

Bias:
- clarity over rambling
- accountability over ambiguity
- decisions and owners over discussion loops
""",
    "proposal": """
Mode: Proposal
Purpose:
- present a strong recommendation
- sharpen commercial framing
- make approval easier
- reduce friction and confusion

Bias:
- persuasive structure
- clear value framing
- confidence without fluff
"""
}

def supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def normalize_mode(mode: Optional[str]) -> str:
    mode = (mode or "strategy").strip().lower()
    return mode if mode in MODE_PROMPTS else "strategy"

def get_recent_memory(limit: int = 8, mode: Optional[str] = None) -> List[Dict[str, Any]]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    query = f"{SUPABASE_URL}/rest/v1/items?select=input,output,mode,created_at&order=created_at.desc&limit={limit}"
    if mode:
        query += f"&mode=eq.{mode}"

    try:
        response = requests.get(query, headers=supabase_headers(), timeout=15)
        if response.status_code != 200:
            return []
        items = response.json()
        return items if isinstance(items, list) else []
    except Exception:
        return []

def build_memory_block(memories: List[Dict[str, Any]]) -> str:
    if not memories:
        return "No relevant memory found."

    trimmed = []
    for index, item in enumerate(memories, start=1):
        output = str(item.get("output", "")).strip()
        if len(output) > 650:
            output = output[:650].rstrip() + "..."
        trimmed.append(
            f"Memory {index}\n"
            f"Mode: {item.get('mode', 'strategy')}\n"
            f"Input: {str(item.get('input', '')).strip()}\n"
            f"Output: {output}"
        )
    return "\n\n".join(trimmed)

def save_to_supabase(user_input: str, ai_output: str, mode: str) -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    payload = {
        "input": user_input,
        "output": ai_output,
        "mode": mode,
    }

    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/items",
            json=payload,
            headers=supabase_headers(),
            timeout=15
        )
    except Exception:
        pass

def safe_json_parse(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return fallback_response("No response returned from model.")

    try:
        data = json.loads(text)
        return validate_response_shape(data)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start:end + 1])
                return validate_response_shape(data)
            except Exception:
                pass
    return fallback_response(text)

def fallback_response(raw_text: str) -> Dict[str, Any]:
    clean = raw_text.strip() or "No usable output returned."
    return {
        "executive_summary": clean[:300],
        "outcome": clean[:300],
        "priority": "High",
        "risks": ["Model returned an invalid structured response."],
        "actions": [
            {
                "title": "Retry prompt",
                "detail": "Run the request again or tighten the request context.",
                "owner": "You",
                "timing": "Now"
            }
        ],
        "assumptions": [],
        "follow_up_questions": []
    }

def validate_response_shape(data: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "executive_summary": str(data.get("executive_summary", "")).strip(),
        "outcome": str(data.get("outcome", "")).strip(),
        "priority": str(data.get("priority", "High")).strip().title(),
        "risks": data.get("risks", []),
        "actions": data.get("actions", []),
        "assumptions": data.get("assumptions", []),
        "follow_up_questions": data.get("follow_up_questions", [])
    }

    if result["priority"] not in {"High", "Medium", "Low"}:
        result["priority"] = "High"

    if not isinstance(result["risks"], list):
        result["risks"] = [str(result["risks"])]
    result["risks"] = [str(x).strip() for x in result["risks"] if str(x).strip()][:5]

    normalized_actions = []
    if isinstance(result["actions"], list):
        for item in result["actions"][:6]:
            if isinstance(item, dict):
                normalized_actions.append({
                    "title": str(item.get("title", "")).strip() or "Action",
                    "detail": str(item.get("detail", "")).strip() or "",
                    "owner": str(item.get("owner", "You")).strip() or "You",
                    "timing": str(item.get("timing", "Now")).strip() or "Now",
                })
            else:
                normalized_actions.append({
                    "title": str(item).strip() or "Action",
                    "detail": "",
                    "owner": "You",
                    "timing": "Now",
                })
    result["actions"] = normalized_actions

    for key in ["assumptions", "follow_up_questions"]:
        if not isinstance(result[key], list):
            result[key] = [str(result[key])]
        result[key] = [str(x).strip() for x in result[key] if str(x).strip()][:4]

    if not result["executive_summary"]:
        result["executive_summary"] = result["outcome"] or "No executive summary returned."
    if not result["outcome"]:
        result["outcome"] = "No clear outcome returned."

    if not result["actions"]:
        result["actions"] = [{
            "title": "Clarify next step",
            "detail": "Add more specific business context and rerun the request.",
            "owner": "You",
            "timing": "Now",
        }]

    return result

@app.get("/")
def home():
    return {
        "status": "live",
        "app": "Executive Engine V2"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "openai_configured": bool(OPENAI_API_KEY),
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY)
    }

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = str(body.get("message", "")).strip()
    mode = normalize_mode(body.get("mode"))

    if not user_input:
        return {
            "response": fallback_response("No message provided."),
            "mode": mode
        }

    recent_mode_memory = get_recent_memory(limit=5, mode=mode)
    recent_general_memory = get_recent_memory(limit=3, mode=None)

    combined_memory = []
    seen = set()
    for item in recent_mode_memory + recent_general_memory:
        key = (
            str(item.get("created_at", "")),
            str(item.get("input", "")),
            str(item.get("output", "")),
        )
        if key not in seen:
            combined_memory.append(item)
            seen.add(key)

    memory_block = build_memory_block(combined_memory[:6])

    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "system", "content": MODE_PROMPTS[mode]},
        {
            "role": "user",
            "content": (
                f"Current request:\n{user_input}\n\n"
                f"Relevant recent memory:\n{memory_block}\n\n"
                "Return the strongest executive response in the required JSON schema."
            ),
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.35,
    )

    raw_output = response.choices[0].message.content or ""
    parsed_output = safe_json_parse(raw_output)

    save_to_supabase(user_input, json.dumps(parsed_output), mode)

    return {
        "response": parsed_output,
        "mode": mode
    }
