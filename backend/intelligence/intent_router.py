def detect_intent(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["profit", "profitable", "monetize", "money", "cash", "revenue", "pricing"]):
        return "monetization"
    if any(x in t for x in ["overwhelmed", "too many", "scattered", "chaos", "busy", "stressed"]):
        return "overload"
    if any(x in t for x in ["proposal", "dealership", "seo", "google ads", "cpa", "client"]):
        return "proposal"
    if any(x in t for x in ["stop doing", "kill", "pause", "remove", "ignore", "delegate"]):
        return "elimination"
    if any(x in t for x in ["build", "deploy", "backend", "frontend", "engine", "version"]):
        return "build"
    if any(x in t for x in ["meeting", "call", "agenda", "prep"]):
        return "meeting"
    if any(x in t for x in ["pivot", "should i", "decide", "decision"]):
        return "decision"
    return "operator"
