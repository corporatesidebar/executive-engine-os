import json
from openai import OpenAI

from .intent_router import detect_intent
from .resource_engine import resources_for
from .sequencing_engine import sequence_for
from .execution_assets import asset_pack

def leverage_path(intent: str) -> dict:
    if intent == "monetization":
        return {
            "revenue_path": "Executive Engine audit + implementation retainers",
            "why": "It monetizes faster than SaaS because you can sell transformation before the product is fully mature.",
            "target_buyer": "CEO, COO, founder, agency owner, SMB operator",
            "pricing": "$5k audit, $15k implementation, $3k/month continuity",
            "stop_doing": ["Stop building broad features before selling a narrow transformation.", "Stop treating SaaS subscriptions as the first monetization step."]
        }

    if intent == "overload":
        return {
            "revenue_path": "Choose the project closest to cash or stability first.",
            "why": "Overload is created by active loops. Relief comes from elimination, not better organization.",
            "target_buyer": "Internal executive operator",
            "pricing": None,
            "stop_doing": ["Stop keeping every idea active.", "Stop improving systems that do not reduce pressure this week."]
        }

    if intent == "proposal":
        return {
            "revenue_path": "90-day financed-buyer acquisition sprint",
            "why": "Dealerships care about funded deals, not SEO/Ads deliverables.",
            "target_buyer": "Ontario auto loan dealership / finance manager / dealer principal",
            "pricing": "Pilot retainer + ad budget + performance review",
            "stop_doing": ["Stop selling generic SEO.", "Stop leading with traffic or rankings."]
        }

    return {
        "revenue_path": "Turn command into one executable outcome.",
        "why": "Movement beats interpretation.",
        "target_buyer": None,
        "pricing": None,
        "stop_doing": ["Stop adding generic steps.", "Stop leaving the user with the work."]
    }

def local_response(user_input: str, intent: str) -> dict:
    leverage = leverage_path(intent)
    resources = resources_for(intent)
    sequence = sequence_for(intent)
    assets = asset_pack(intent)

    if intent == "monetization":
        insight = "Executive Engine makes money fastest as a paid implementation offer, not as pure SaaS."
        decision = "Sell the transformation first. Productize after the workflow closes revenue."
        move = "Package and sell the Executive Operating System Audit this week."
        risk = "Waiting for perfect software delays market proof."
    elif intent == "overload":
        insight = "Your problem is not too many projects. It is too many projects still allowed to remain active."
        decision = "Keep one Cash item, one Stability item, one Obligation item. Pause the rest."
        move = "Create the active/pause list now and remove paused work from view."
        risk = "If everything stays active, the system will organize pressure instead of reducing it."
    elif intent == "proposal":
        insight = "The dealership does not buy marketing. It buys finance-ready buyers at a believable acquisition cost."
        decision = "Sell the 90-day financed-buyer acquisition sprint."
        move = "Write the proposal around CPA control, lead speed, and funded-deal tracking."
        risk = "If you lead with SEO and Google Ads deliverables, you sound like every agency."
    else:
        insight = "This needs to become an execution asset, not another thought loop."
        decision = "Create the first usable asset and put it in motion."
        move = "Build the asset now and test it."
        risk = "The risk is organized thinking without movement."

    operational_depth = {
        "leverage_path": leverage,
        "execution_sequence": sequence,
        "resources": resources,
        "assets_to_create": assets,
        "stop_doing": leverage["stop_doing"],
    }

    asset = f"""EXECUTIVE SCAN

{insight}

Decision:
{decision}

Move:
{move}

Risk:
{risk}

OPERATIONAL DEPTH

Revenue / Leverage Path:
{leverage['revenue_path']}

Why:
{leverage['why']}

Today:
- {sequence['today'][0]}
- {sequence['today'][1]}
- {sequence['today'][2]}

Resources:
""" + "\n".join([f"- {r['name']}: {r['url']} — {r['use']}" for r in resources]) + """

Assets:
""" + "\n\n".join(assets)

    return {
        "next_move": move,
        "decision": decision,
        "action_steps": sequence["today"],
        "ready_assets": [asset] + assets,
        "risk": risk,
        "priority": "High",
        "recommended_command": "Generate the first execution asset from the operational depth plan.",
        "what_to_do_now": move,
        "asset": asset,
        "follow_up": "Execute one Today item before expanding the plan.",
        "provider_used": "local-output-first-engine",
        "status": "success",
        "executive_scan": {
            "dominant_insight": insight,
            "decision": decision,
            "move": move,
            "risk": risk,
            "pressure": "High"
        },
        "operational_depth": operational_depth,
        "resource_links": resources,
        "stop_doing": leverage["stop_doing"],
        "execution_assets": assets,
    }

def prompt(user_input: str, workspace: dict, fallback: dict) -> str:
    return f"""
You are Executive Engine OS — Output-First Executive Execution Infrastructure.

The user does not want generic advice. They want usable movement.

Produce:
1. Executive scan: compressed insight, decision, move, risk.
2. Operational depth: exact steps, resources, tools, assets, sequence.
3. Actual generated assets where useful.

User input:
{user_input}

Fallback structure to improve:
{json.dumps(fallback, indent=2)}

Workspace context:
{json.dumps(workspace, indent=2)[:6000]}

Rules:
- Do not say obvious things without operationalizing them.
- Include specific websites/tools/resources when useful.
- Include stop-doing decisions.
- Generate usable assets, not just suggestions.
- Preserve every required contract field.
- Return only valid JSON.
"""

def enforce(data: dict, fallback: dict) -> dict:
    if not isinstance(data, dict):
        return fallback

    for key, value in fallback.items():
        data.setdefault(key, value)

    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]
    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]

    data.setdefault("executive_scan", fallback["executive_scan"])
    data.setdefault("operational_depth", fallback["operational_depth"])
    data.setdefault("resource_links", fallback["resource_links"])
    data.setdefault("stop_doing", fallback["stop_doing"])
    data.setdefault("execution_assets", fallback["execution_assets"])
    data.setdefault("status", "success")

    return data

def build_execution_response(user_input: str, mode: str, brain: str, output_type: str, workspace: dict, openai_api_key: str, model: str) -> dict:
    intent = detect_intent(user_input)
    fallback = local_response(user_input, intent)

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
            temperature=0.22,
            response_format={"type": "json_object"}
        )
        data = json.loads(result.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{model}"
        data["status"] = "success"
        return enforce(data, fallback)
    except Exception:
        return fallback
