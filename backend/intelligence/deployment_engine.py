import json
from openai import OpenAI

from .intent_engine import detect_deployment_intent
from .asset_library import (
    dealership_proposal_assets,
    monetization_assets,
    overload_assets,
    general_assets,
)

FORBIDDEN_GENERIC = [
    "create the asset",
    "define the outcome",
    "focus on",
    "consider",
    "brainstorm",
    "review priorities",
    "assess your goals",
    "think about"
]

def base_assets(intent: str):
    if intent == "dealership_proposal":
        primary, followup, checklist = dealership_proposal_assets()
        return {
            "summary": "Generated a send-ready dealership acquisition proposal package.",
            "problem": "The buyer needs acquisition economics, not marketing deliverables.",
            "decision": "Sell a 90-day financed-buyer acquisition sprint.",
            "asset_type": "proposal",
            "primary_title": "90-Day Financed-Buyer Acquisition Sprint Proposal",
            "primary_content": primary,
            "send_ready": [{"title": "Dealership Follow-Up Email", "content": followup}],
            "checklist": checklist,
            "risk": "Generic SEO/Ads framing will reduce perceived value.",
            "next": "Send the dealership follow-up email and attach the pilot scope.",
            "time": "Same-day proposal; 3-7 days to decision call.",
            "impact": "High if pilot closes; medium if no tracking access is provided."
        }

    if intent == "monetization":
        primary, followup, checklist = monetization_assets()
        return {
            "summary": "Generated a monetization package for Executive Engine implementation revenue.",
            "problem": "Revenue is delayed because the product is being treated as software first instead of transformation first.",
            "decision": "Sell the Executive Operating System Audit before pure SaaS subscriptions.",
            "asset_type": "offer",
            "primary_title": "Executive Operating System Audit Offer",
            "primary_content": primary,
            "send_ready": [{"title": "Executive Engine Outreach Message", "content": followup}],
            "checklist": checklist,
            "risk": "Waiting for product perfection delays paid proof.",
            "next": "Record the Loom demo and send 25 targeted messages.",
            "time": "48 hours to launch offer; 7-14 days to first paid audit.",
            "impact": "$5k audit, $15k sprint, $3k/month continuity retainer."
        }

    if intent == "overload_system":
        primary, followup, checklist = overload_assets()
        return {
            "summary": "Generated an active/pause operating system to reduce executive load.",
            "problem": "Pressure is coming from too many active loops, not lack of effort.",
            "decision": "Keep one cash path, one stability path, one obligation path. Pause the rest.",
            "asset_type": "operating_sheet",
            "primary_title": "Active / Pause Operating Sheet",
            "primary_content": primary,
            "send_ready": [{"title": "Internal Operating Instruction", "content": followup}],
            "checklist": checklist,
            "risk": "If everything remains active, pressure remains operationally unresolved.",
            "next": "Fill the Active/Pause sheet and remove paused items from view.",
            "time": "30-60 minutes to reduce pressure; same day to regain execution clarity.",
            "impact": "High executive pressure reduction."
        }

    primary, followup, checklist = general_assets()
    return {
        "summary": "Generated a deployable execution asset framework.",
        "problem": "The command is still internal until an asset reaches a real recipient, system, or market.",
        "decision": "Deploy one usable asset and measure external signal.",
        "asset_type": "execution_framework",
        "primary_title": "Deployable Execution Asset",
        "primary_content": primary,
        "send_ready": [{"title": "Follow-Up Note", "content": followup}],
        "checklist": checklist,
        "risk": "Organized thinking without external signal creates false progress.",
        "next": "Deploy the asset to a real recipient or workflow within 24 hours.",
        "time": "Same day.",
        "impact": "Medium unless tied to revenue or a decision-maker."
    }

def local_response(user_input: str, intent: str) -> dict:
    assets = base_assets(intent)

    primary_asset = {
        "title": assets["primary_title"],
        "type": assets["asset_type"],
        "content": assets["primary_content"]
    }

    export_ready_assets = [
        primary_asset,
        *assets["send_ready"]
    ]

    implementation_checklist = assets["checklist"]

    asset_block = f"""DEPLOYMENT PACKAGE

Executive Summary:
{assets['summary']}

Real Problem:
{assets['problem']}

Decision:
{assets['decision']}

Primary Asset:
{assets['primary_title']}

{assets['primary_content']}

Send-Ready Asset:
{assets['send_ready'][0]['title']}

{assets['send_ready'][0]['content']}

Implementation Checklist:
""" + "\n".join([f"- {item}" for item in implementation_checklist]) + f"""

Time To Value:
{assets['time']}

Revenue / Business Impact:
{assets['impact']}

Risk Control:
{assets['risk']}
"""

    return {
        "executive_summary": assets["summary"],
        "real_problem": assets["problem"],
        "deployment_decision": assets["decision"],
        "primary_asset": primary_asset,
        "deployment_assets": export_ready_assets,
        "send_ready_assets": assets["send_ready"],
        "export_ready_assets": export_ready_assets,
        "implementation_checklist": implementation_checklist,
        "execution_sequence": implementation_checklist,
        "tools_and_resources": [
            {"name": "Loom", "url": "https://www.loom.com", "use": "Record demo/walkthrough."},
            {"name": "Notion", "url": "https://www.notion.so", "use": "Store asset library and SOPs."},
            {"name": "HubSpot", "url": "https://www.hubspot.com", "use": "Track prospects and follow-ups."},
            {"name": "Zapier", "url": "https://zapier.com", "use": "Automate asset follow-up workflow."}
        ],
        "time_to_value": assets["time"],
        "business_impact": assets["impact"],
        "risk_control": assets["risk"],
        "next_execution_asset": assets["next"],
        "follow_up_command": "Generate the next send-ready asset and deployment checklist.",
        "operator_mode": "Deployment Engine",
        "pressure_level": "High",
        "status": "success",

        # Frontend compatibility
        "next_move": assets["next"],
        "decision": assets["decision"],
        "action_steps": implementation_checklist,
        "ready_assets": [asset_block],
        "risk": assets["risk"],
        "priority": "High",
        "recommended_command": "Generate the next send-ready asset and deployment checklist.",
        "what_to_do_now": assets["next"],
        "asset": asset_block,
        "follow_up": "Deploy the asset and measure response.",
        "provider_used": "local-deployment-engine",

        # Existing newer compatibility
        "executive_scan": {
            "dominant_insight": assets["summary"],
            "decision": assets["decision"],
            "move": assets["next"],
            "risk": assets["risk"],
            "pressure": "High"
        },
        "operational_depth": {
            "primary_asset": primary_asset,
            "send_ready_assets": assets["send_ready"],
            "implementation_checklist": implementation_checklist,
            "tools_and_resources": [
                "Loom",
                "Notion",
                "HubSpot",
                "Zapier"
            ],
            "time_to_value": assets["time"],
            "business_impact": assets["impact"]
        }
    }

def build_prompt(user_input: str, workspace: dict, fallback: dict, depth: str) -> str:
    return f"""
You are Executive Engine OS — Deployment Engine.

The user does not want advice. The user needs deploy-ready assets.

Produce real assets:
- proposal
- outreach
- sales script
- offer
- operating sheet
- follow-up
- checklist
- implementation system
- automation workflow

Do NOT over-compress. Preserve useful detail.
Do NOT return labels only.
Do NOT say: {FORBIDDEN_GENERIC}

User input:
{user_input}

Fallback package:
{json.dumps(fallback, indent=2)}

Workspace:
{json.dumps(workspace, indent=2)[:7000]}

Rules:
- Generate the actual asset inline.
- Include send-ready copy where relevant.
- Include implementation checklist.
- Include time to value.
- Include risk control.
- Preserve frontend-compatible keys.
- Return only valid JSON.
"""

def enforce(data: dict, fallback: dict) -> dict:
    if not isinstance(data, dict):
        return fallback

    for key, value in fallback.items():
        data.setdefault(key, value)

    required_frontend = [
        "next_move", "decision", "action_steps", "ready_assets", "risk", "priority",
        "recommended_command", "what_to_do_now", "asset", "follow_up", "provider_used", "status"
    ]

    for key in required_frontend:
        data.setdefault(key, fallback.get(key))

    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]
    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]

    data["status"] = "success"
    return data

def build_deployment_response(user_input: str, workspace: dict, openai_api_key: str, model: str, depth: str = "detailed") -> dict:
    intent = detect_deployment_intent(user_input)
    fallback = local_response(user_input, intent)

    if not openai_api_key:
        return fallback

    try:
        client = OpenAI(api_key=openai_api_key)
        result = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_prompt(user_input, workspace, fallback, depth)},
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
