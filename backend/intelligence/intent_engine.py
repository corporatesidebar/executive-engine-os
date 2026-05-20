def detect_intent(text: str) -> str:
    t = (text or "").lower()

    if any(x in t for x in ["dealership", "auto loan", "seo", "google ads", "cpa", "proposal"]):
        return "dealership_proposal"

    if any(x in t for x in ["10 clients", "clients", "lead", "outreach", "linkedin", "email campaign", "prospect"]):
        return "client_acquisition"

    if any(x in t for x in ["profitable", "profit", "monetize", "money", "revenue", "cash", "pricing"]):
        return "monetization"

    if any(x in t for x in ["overwhelmed", "too many", "scattered", "chaos", "busy"]):
        return "overload"

    if any(x in t for x in ["meeting", "call", "agenda", "prep"]):
        return "meeting"

    return "general_execution"
