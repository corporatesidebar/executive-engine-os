import json
from openai import OpenAI
from .leverage_engine import detect_intent, build_leverage_map
from .resources_engine import recommend_resources
from .sequencing_engine import build_sequence

FORBIDDEN = [
    "focus on priorities",
    "clarify your goals",
    "conduct analysis",
    "review assets",
    "optimize workflows",
    "high-impact",
    "stakeholders",
]

def local_dual_layer(user_input: str, intent: str, leverage: dict, resources: list, sequence: dict) -> dict:
    if intent == "overload":
        insight = "Your overload is not a workload problem. It is an active-loop problem."
        decision = "Reduce the active field to three lanes: cash, stability, obligation. Everything else pauses."
        risk = "If every project remains active, the system will organize chaos instead of reducing it."
        next_move = "Create the active/pause list now and remove every paused item from view."
    elif intent == "monetization":
        insight = "Executive Engine monetizes fastest as an implementation offer, not as pure SaaS."
        decision = "Sell the transformation first. Productize later."
        risk = "Trying to perfect the software before selling will delay market proof."
        next_move = "Package the Executive Operating System Audit and sell the first paid sprint."
    elif intent == "proposal":
        insight = "The dealership does not buy marketing. It buys funded-deal economics."
        decision = "Sell a 90-day financed-buyer acquisition sprint."
        risk = "If the proposal leads with SEO and Ads deliverables, it sounds like every agency."
        next_move = "Write the proposal around intent control, lead handling speed, and funded-deal tracking."
    else:
        insight = leverage["best_path"]
        decision = "Move from reflection to execution."
        risk = "The risk is staying organized without creating movement."
        next_move = "Create the first usable asset and put it in motion."

    operational_depth = {
        "leverage_path": leverage,
        "execution_sequence": sequence,
        "resources": resources,
        "assets_to_create": [
            "one-page offer",
            "2-minute Loom walkthrough",
            "outreach message",
            "pricing structure",
            "proof/demo asset"
        ],
        "stop_doing": leverage.get("pause", []),
    }

    asset = f"""EXECUTIVE SCAN

{insight}

Decision:
{decision}

Move:
{next_move}

Risk:
{risk}

OPERATIONAL DEPTH

Leverage Path:
{leverage.get("best_path")}

Why:
{leverage.get("why")}

Today:
- {sequence["today"][0]}
- {sequence["today"][1]}
- {sequence["today"][2]}

Resources:
""" + "\n".join([f"- {r['name']}: {r['url']} — {r['use']}" for r in resources])

    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": sequence["today"],
        "ready_assets": [asset],
        "risk": risk,
        "priority": "High",
        "recommended_command": "Generate the first asset from the operational depth plan.",
        "what_to_do_now": next_move,
        "asset": asset,
        "follow_up": "Execute one item from Today before expanding the plan.",
        "provider_used": "local-dual-layer-engine",
        "status": "success",
        "executive_scan": {
            "dominant_insight": insight,
            "decision": decision,
            "pressure": "High",
            "move": next_move,
            "risk": risk,
        },
        "operational_depth": operational_depth,
    }

def build_prompt(user_input: str, mode: str, brain: str, output_type: str, workspace: dict, leverage: dict, resources: list, sequence: dict) -> str:
    return f"""
You are Executive Engine OS — Dual-Layer Executive Intelligence Engine.

The user does not want generic insight. They want something they can use to move forward.

Return dual-layer output:
1. executive_scan: short, decisive, high-signal.
2. operational_depth: detailed, actionable, resources/tools/assets/sequencing.

User command:
{user_input}

Leverage map:
{json.dumps(leverage, indent=2)}

Resources:
{json.dumps(resources, indent=2)}

Sequence:
{json.dumps(sequence, indent=2)}

Recent workspace context:
{json.dumps(workspace, indent=2)[:5000]}

Rules:
- Do not say obvious advice like "focus on priorities" without specifying which priority and what to do.
- Include actual tools/resources when relevant.
- Include assets to create.
- Include today / next 24 hours / next 7 days.
- Preserve required response contract.
- Return only valid JSON.

Required JSON keys:
next_move, decision, action_steps, ready_assets, risk, priority, recommended_command, what_to_do_now, asset, follow_up, provider_used, status, executive_scan, operational_depth
"""

def enforce(data: dict, fallback: dict) -> dict:
    if not isinstance(data, dict):
        return fallback
    for k, v in fallback.items():
        data.setdefault(k, v)
    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]
    if not data.get("executive_scan"):
        data["executive_scan"] = fallback["executive_scan"]
    if not data.get("operational_depth"):
        data["operational_depth"] = fallback["operational_depth"]
    return data

def build_dual_layer_response(user_input: str, mode: str, brain: str, output_type: str, workspace: dict, openai_api_key: str, model: str) -> dict:
    intent = detect_intent(user_input)
    leverage = build_leverage_map(user_input, intent)
    resources = recommend_resources(intent)
    sequence = build_sequence(intent)

    fallback = local_dual_layer(user_input, intent, leverage, resources, sequence)

    if not openai_api_key:
        return fallback

    try:
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_prompt(user_input, mode, brain, output_type, workspace, leverage, resources, sequence)},
                {"role": "user", "content": user_input}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{model}"
        data["status"] = "success"
        return enforce(data, fallback)
    except Exception:
        return fallback
