import json
from openai import OpenAI

from .intent_engine import detect_intent
from .object_factory import (
    dealership_objects,
    monetization_objects,
    overload_objects,
    general_objects,
)

def object_text(obj: dict) -> str:
    title = obj.get("title", "Execution Object")
    object_type = obj.get("object_type", "object")
    payload = obj.get("payload", {})
    return f"{title} ({object_type})\n{json.dumps(payload, indent=2, ensure_ascii=False)}"

def objects_for_intent(intent: str):
    if intent == "dealership_proposal":
        return dealership_objects()
    if intent in ["monetization", "client_acquisition"]:
        return monetization_objects()
    if intent == "overload":
        return overload_objects()
    return general_objects()

def local_response(user_input: str, intent: str) -> dict:
    objects = objects_for_intent(intent)

    if intent == "dealership_proposal":
        summary = "Generated a structured dealership acquisition package: proposal, follow-up, CRM, KPI scorecard, and deployment checklist."
        problem = "The dealership needs funded-deal economics, not generic SEO or Ads deliverables."
        decision = "Sell the 90-day financed-buyer acquisition sprint."
        next_move = "Send the dealership follow-up and attach the 90-day pilot scope."
        risk = "Generic marketing framing weakens perceived value."
        pressure = "High"
    elif intent in ["monetization", "client_acquisition"]:
        summary = "Generated a structured monetization package for Executive Engine: offer, landing page, outbound, CRM, and KPI system."
        problem = "Revenue is delayed because the product is being treated as software first instead of transformation first."
        decision = "Sell the Executive Operating System Audit before pure SaaS subscriptions."
        next_move = "Publish the audit offer and send 25 targeted outreach messages."
        risk = "Waiting for product perfection delays paid proof."
        pressure = "High"
    elif intent == "overload":
        summary = "Generated a structured operating system to reduce executive pressure and remove active-loop overload."
        problem = "The active field is too large; everything is psychologically treated as live."
        decision = "Keep one cash path, one stability path, one obligation path; pause the rest."
        next_move = "Fill the Active/Pause sheet and remove paused work from daily view."
        risk = "If everything remains active, pressure remains unresolved."
        pressure = "High"
    else:
        summary = "Generated structured execution objects that can be deployed, assigned, measured, and improved."
        problem = "The command needs to become an operational object, not another text response."
        decision = "Convert the input into deployable execution objects."
        next_move = "Deploy the first generated object within 24 hours."
        risk = "Organized thinking without external signal creates false progress."
        pressure = "Medium"

    execution_package_text = "\n\n---\n\n".join([object_text(o) for o in objects])

    return {
        "executive_summary": summary,
        "real_problem": problem,
        "operator_decision": decision,
        "execution_objective": "Convert command input into structured operational objects.",
        "executive_scan": {
            "dominant_insight": summary,
            "decision": decision,
            "move": next_move,
            "risk": risk,
            "pressure_level": pressure
        },
        "execution_objects": objects,
        "primary_object": objects[0] if objects else None,
        "object_count": len(objects),
        "renderer_mode": "structured_objects",
        "deployment_sequence": [
            {"step": 1, "task": "Use the primary object.", "owner": "Executive", "timeline": "Today"},
            {"step": 2, "task": "Deploy send-ready or workflow object.", "owner": "Executive / delegate", "timeline": "24 hours"},
            {"step": 3, "task": "Track response and signal.", "owner": "Operator", "timeline": "48-72 hours"},
            {"step": 4, "task": "Improve, kill, or scale based on signal.", "owner": "Executive", "timeline": "7 days"}
        ],
        "memory_state": {
            "active_object_type": objects[0].get("object_type") if objects else None,
            "active_object_title": objects[0].get("title") if objects else None,
            "continuity_status": "saved_to_workspace_state"
        },
        "risk_control": risk,
        "time_to_value": "Same day deployment if primary object is used immediately.",
        "follow_up_command": "Generate the next execution object and deployment-ready version.",
        "operator_mode": "Structured Execution Object Engine",
        "pressure_level": pressure,
        "status": "success",

        # Legacy frontend compatibility
        "next_move": next_move,
        "decision": decision,
        "action_steps": [item["task"] for item in [
            {"task": "Use the primary structured object."},
            {"task": "Deploy it to a real recipient/system."},
            {"task": "Measure signal within 48-72 hours."}
        ]],
        "ready_assets": [execution_package_text],
        "risk": risk,
        "priority": "High" if pressure == "High" else "Medium",
        "recommended_command": "Generate the next execution object and deployment-ready version.",
        "what_to_do_now": next_move,
        "asset": execution_package_text,
        "follow_up": "Deploy the primary object and measure signal.",
        "provider_used": "local-structured-execution-object-engine"
    }

def build_prompt(user_input: str, workspace: dict, fallback: dict) -> str:
    return f"""
You are Executive Engine OS — Structured Execution Object Engine.

Do not return generic text.
Return operational objects.

Required object types when relevant:
- proposal
- outreach_sequence
- crm_pipeline
- kpi_scorecard
- deployment_checklist
- landing_page
- offer
- pricing_model
- operating_system
- delegation_map
- follow_up_system

User input:
{user_input}

Fallback structured response:
{json.dumps(fallback, indent=2, ensure_ascii=False)}

Workspace:
{json.dumps(workspace, indent=2, ensure_ascii=False)[:7000]}

Rules:
- Generate structured execution_objects.
- Preserve legacy frontend keys.
- Do not over-compress useful object payload.
- Include deployable content inside object payloads.
- Return only valid JSON.
"""

def enforce(data: dict, fallback: dict) -> dict:
    if not isinstance(data, dict):
        return fallback

    for key, value in fallback.items():
        data.setdefault(key, value)

    required_legacy = [
        "next_move", "decision", "action_steps", "ready_assets", "risk", "priority",
        "recommended_command", "what_to_do_now", "asset", "follow_up", "provider_used", "status"
    ]

    for key in required_legacy:
        data.setdefault(key, fallback.get(key))

    if isinstance(data.get("ready_assets"), str):
        data["ready_assets"] = [data["ready_assets"]]
    if isinstance(data.get("action_steps"), str):
        data["action_steps"] = [data["action_steps"]]

    data.setdefault("execution_objects", fallback.get("execution_objects", []))
    data.setdefault("renderer_mode", "structured_objects")
    data["status"] = "success"
    return data

def build_structured_execution_response(
    user_input: str,
    workspace: dict,
    openai_api_key: str,
    model: str,
    depth: str = "auto",
    mode: str = "execution",
    brain: str = "operator",
    output_type: str = "standard",
) -> dict:
    intent = detect_intent(user_input)
    fallback = local_response(user_input, intent)

    if not openai_api_key:
        return fallback

    try:
        client = OpenAI(api_key=openai_api_key)
        result = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_prompt(user_input, workspace, fallback)},
                {"role": "user", "content": user_input}
            ],
            temperature=0.16,
            response_format={"type": "json_object"}
        )
        data = json.loads(result.choices[0].message.content or "{}")
        data["provider_used"] = f"openai:{model}"
        return enforce(data, fallback)
    except Exception:
        return fallback
