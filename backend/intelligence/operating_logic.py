from .asset_generator import assets_for
from .resources_engine import resource_bank

def build_operating_plan(user_input: str, mode: str) -> dict:
    if mode == "operational_overload":
        return {
            "executive_summary": "The overload is caused by too many active loops, not too much work.",
            "real_problem": "No elimination system exists, so every project is psychologically active.",
            "decision": "Keep one cash path, one stability path, and one obligation path. Pause the rest.",
            "why_this_matters": "Executive pressure drops when the active field shrinks.",
            "highest_leverage_move": "Create an Active/Pause operating sheet and move paused work out of sight.",
            "what_to_stop": ["Stop keeping every project active.", "Stop improving systems that do not reduce pressure this week."],
            "what_to_delegate": ["Formatting, file organization, recurring admin, research gathering."],
            "immediate_actions": ["List every project.", "Classify each as Cash, Stability, Obligation, or Noise.", "Pause everything except one in each core category."],
            "execution_sequence": ["Create the list.", "Mark paused items.", "Remove paused items from daily view.", "Execute the cash or stability item first."],
            "revenue_opportunities": ["Recover time for the nearest cash-generating offer or client path."],
            "risk_control": "If everything stays active, the system organizes chaos instead of reducing it.",
            "time_to_value": "30–60 minutes to reduce pressure; 24 hours to regain execution clarity."
        }

    if mode == "revenue_pressure":
        return {
            "executive_summary": "The fastest revenue path is selling Executive Engine as an implementation offer, not waiting for SaaS perfection.",
            "real_problem": "Revenue is delayed because the product is being treated as software first instead of transformation first.",
            "decision": "Sell the Executive Operating System Audit now. Productize after paid proof.",
            "why_this_matters": "Implementation revenue validates the market faster than subscription polish.",
            "highest_leverage_move": "Package a $5k audit and $15k implementation sprint.",
            "what_to_stop": ["Stop broad feature building before market proof.", "Stop treating SaaS subscriptions as the first monetization step."],
            "what_to_delegate": ["Landing page formatting, lead list building, CRM setup, follow-up tracking."],
            "immediate_actions": ["Create the audit offer.", "Record a Loom demo.", "Send 25 targeted outreach messages."],
            "execution_sequence": ["Define offer.", "Build one-page landing page.", "Create payment/booking link.", "Send outreach.", "Book calls.", "Close first audit."],
            "revenue_opportunities": ["$5k audit", "$15k sprint", "$3k/month continuity retainer", "operator workflow consulting"],
            "risk_control": "Waiting for a perfect product delays paid proof.",
            "time_to_value": "48 hours to launch offer; 7 days to book calls; 14 days to close first audit."
        }

    if mode in ["proposal_generation", "client_acquisition"]:
        return {
            "executive_summary": "The buyer does not need deliverables. The buyer needs proof that spend turns into business outcomes.",
            "real_problem": "The offer risks sounding like generic agency work instead of a measurable business system.",
            "decision": "Sell the business outcome first; present deliverables as the mechanism.",
            "why_this_matters": "Executives buy outcomes, risk reduction, and confidence.",
            "highest_leverage_move": "Build the proposal around ROI mechanics, not services.",
            "what_to_stop": ["Stop leading with SEO or task lists.", "Stop selling traffic without conversion proof."],
            "what_to_delegate": ["Keyword list creation, landing page wireframe, reporting dashboard setup."],
            "immediate_actions": ["Write the outcome promise.", "Define the 90-day sprint.", "Create the follow-up message."],
            "execution_sequence": ["Position outcome.", "Build proposal spine.", "Attach tracking plan.", "Send proposal.", "Book decision call."],
            "revenue_opportunities": ["pilot retainer", "implementation fee", "monthly optimization retainer"],
            "risk_control": "Generic service framing weakens perceived value.",
            "time_to_value": "Same day proposal; 3–7 days to decision call."
        }

    return {
        "executive_summary": "This needs to become an asset, system, or decision that moves reality.",
        "real_problem": "The command is still at the thinking layer, not the execution layer.",
        "decision": "Create one usable asset and test it.",
        "why_this_matters": "Movement creates signal. More interpretation does not.",
        "highest_leverage_move": "Build the first usable asset and put it in front of the relevant person or market.",
        "what_to_stop": ["Stop adding generic steps.", "Stop leaving the work unowned."],
        "what_to_delegate": ["Research, formatting, list building, documentation cleanup."],
        "immediate_actions": ["Name the outcome.", "Create the asset.", "Send or test it."],
        "execution_sequence": ["Choose outcome.", "Generate asset.", "Run test.", "Capture signal.", "Improve."],
        "revenue_opportunities": ["Turn the asset into a paid offer if it solves a real business problem."],
        "risk_control": "The risk is organized thinking with no market or operational signal.",
        "time_to_value": "Same day if an asset is created and tested."
    }

def enrich_plan(plan: dict, mode: str) -> dict:
    plan["generated_assets"] = assets_for(mode)
    plan["tools_and_resources"] = resource_bank(mode)
    plan["follow_up_command"] = "Generate the first execution asset and send-ready version."
    plan["operator_mode"] = mode
    return plan
