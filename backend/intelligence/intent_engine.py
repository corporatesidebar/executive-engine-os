def detect_deployment_intent(text: str) -> str:
    t = (text or "").lower()

    if any(x in t for x in ["dealership", "auto loan", "seo", "google ads", "cpa", "proposal"]):
        return "dealership_proposal"

    if any(x in t for x in ["profitable", "profit", "monetize", "money", "revenue", "cash"]):
        return "monetization"

    if any(x in t for x in ["outreach", "linkedin", "email", "campaign", "lead", "prospect"]):
        return "outreach_campaign"

    if any(x in t for x in ["overwhelmed", "too many", "scattered", "busy", "chaos"]):
        return "overload_system"

    if any(x in t for x in ["meeting", "call", "agenda", "prep"]):
        return "meeting_brief"

    return "general_execution_asset"
