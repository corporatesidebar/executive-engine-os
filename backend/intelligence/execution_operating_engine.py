import json
from openai import OpenAI

from .classification_engine import classify_request
from .operating_logic import build_operating_plan, enrich_plan

FRONTEND_COMPAT_KEYS = {
    "next_move": "",
    "decision": "",
    "action_steps": [],
    "ready_assets": [],
    "risk": "",
    "priority": "High",
    "recommended_command": "",
    "what_to_do_now": "",
    "asset": "",
    "follow_up": "",
    "provider_used": "",
    "status": "success"
}

GENERIC_PHRASES = [
    "focus on",
    "consider",
    "prioritize",
    "define your outcome",
    "identify goals",
    "review current projects",
    "assess opportunities",
    "brainstorm",
    "think about",
    "choose a direction"
]

def fallback_response(user_input: str, classification: dict) -> dict:
    mode = classification["operator_mode"]
    pressure = classification["pressure_level"]

    plan = enrich_plan(build_operating_plan(user_input, mode), mode)

    asset = f"""EXECUTION OPERATING BRIEF

Executive Summary:
{plan['executive_summary']}

Real Problem:
{plan['real_problem']}

Decision:
{plan['decision']}

Highest Leverage Move:
{plan['highest_leverage_move']}

Immediate Actions:
- {plan['immediate_actions'][0]}
- {plan['immediate_actions'][1]}
- {plan['immediate_actions'][2]}

What To Stop:
- {plan['what_to_stop'][0]}
- {plan['what_to_stop'][1]}

Tools:
""" + "\n".join([f"- {r['name']}: {r['url']} — {r['use']}" for r in plan["tools_and_resources"][:6]]) + """

Generated Assets:
""" + "\n\n".join(plan["generated_assets"][:2])

    response = {
        **plan,
        "pressure_level": pressure,
        "status": "success",

        # frontend compatibility
        "next_move": plan["highest_leverage_move"],
        "action_steps": plan["immediate_actions"],
        "ready_assets": [asset] + plan["generated_assets"],
        "risk": plan["risk_control"],
        "priority": "Critical" if pressure == "Critical" else "High",
        "recommended_command": plan["follow_up_command"],
        "what_to_do_now": plan["highest_leverage_move"],
        "asset": asset,
        "follow_up": plan["follow_up_command"],
        "provider_used": "local-execution-operating-engine",

        # extra compatibility with newer frontend attempts
        "executive_scan": {
            "dominant_insight": plan["executive_summary"],
            "decision": plan["decision"],
            "move": plan["highest_leverage_move"],
            "risk": plan["risk_control"],
            "pressure": pressure
        },
        "operational_depth": {
            "real_problem": plan["real_problem"],
            "why_this_matters": plan["why_this_matters"],
            "execution_sequence": plan["execution_sequence"],
            "tools_and_resources": plan["tools_and_resources"],
            "generated_assets": plan["generated_assets"],
            "what_to_stop": plan["what_to_stop"],
            "what_to_delegate": plan["what_to_delegate"],
            "revenue_opportunities": plan["revenue_opportunities"],
            "time_to_value": plan["time_to_value"]
        }
    }
    return response

def prompt(user_input: str, workspace: dict, fallback: dict) -> str:
    return f"""
You are Executive Engine OS — Execution Operating Engine.

Your job is not advice. Your job is operational execution.

User input:
{user_input}

Fallback execution plan:
{json.dumps(fallback, indent=2)}

Workspace:
{json.dumps(workspace, indent=2)[:6000]}

Rules:
- Identify the real operational issue.
- Make a decision.
- Produce assets, systems, sequences, tools, and revenue paths.
- Say what to stop.
- Say what to delegate.
- Provide immediate actions and execution sequence.
- Do not use these phrases: {GENERIC_PHRASES}
- Preserve both the new execution structure and old frontend-compatible keys.
- Return only valid JSON.

Required new keys:
executive_summary, real_problem, decision, why_this_matters, highest_leverage_move, what_to_stop, what_to_delegate, immediate_actions, execution_sequence, generated_assets, tools_and_resources, revenue_opportunities, risk_control, time_to_value, follow_up_command, operator_mode, pressure_level, status

Required frontend keys:
next_move, action_steps, ready_assets, risk, priority, recommended_command, what_to_do_now, asset, follow_up, provider_used
"""

def enforce(data: dict, fallback: dict) -> dict:
    if not isinstance(data, dict):
        data = fallback

    for key, value in fallback.items():
        data.setdefault(key, value)

    for key, value in FRONTEND_COMPAT_KEYS.items():
        data.setdefault(key, fallback.get(key, value))

    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]

    data["status"] = "success"

    return data

def build_execution_operating_response(user_input: str, mode: str, brain: str, output_type: str, workspace: dict, openai_api_key: str, model: str) -> dict:
    classification = classify_request(user_input)
    fallback = fallback_response(user_input, classification)

    if not openai_api_key:
        return fallback

    try:
        client = OpenAI(api_key=openai_api_key)
        result = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt(user_input, workspace, fallback)},
                {"role": "user", "content": user_input}
            ],
            temperature=0.18,
            response_format={"type": "json_object"}
        )
        data = json.loads(result.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{model}"
        return enforce(data, fallback)
    except Exception:
        return fallback
