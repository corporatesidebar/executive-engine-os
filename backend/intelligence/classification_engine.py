def classify_request(text: str) -> dict:
    t = text.lower()

    classes = {
        "revenue_pressure": ["revenue", "money", "cash", "profit", "profitable", "monetize", "pricing", "sales"],
        "operational_overload": ["overwhelmed", "too many", "busy", "chaos", "scattered", "stressed"],
        "strategic_confusion": ["strategy", "confused", "what should", "direction", "pivot"],
        "execution_bottleneck": ["stuck", "not working", "blocked", "bottleneck", "cant", "can't"],
        "decision_paralysis": ["should i", "decide", "decision", "choose", "option"],
        "delegation_failure": ["delegate", "team", "assistant", "who should", "hire"],
        "client_acquisition": ["client", "lead", "outreach", "dealership", "proposal", "customer"],
        "proposal_generation": ["proposal", "sow", "quote", "pitch", "offer"],
        "meeting": ["meeting", "call", "agenda", "prep"],
        "build_execution": ["build", "deploy", "backend", "frontend", "engine", "version"],
        "time_fragmentation": ["too much time", "wasting time", "all over", "fragmented"],
        "operational_scaling": ["scale", "system", "workflow", "process", "ops"]
    }

    scores = {k: sum(1 for w in v if w in t) for k, v in classes.items()}
    primary = max(scores, key=scores.get)
    if scores[primary] == 0:
        primary = "execution_bottleneck"

    if any(x in t for x in ["wtf", "fuck", "shit", "urgent", "asap", "overwhelmed", "broken"]):
        pressure = "Critical"
    elif scores[primary] >= 2:
        pressure = "High"
    else:
        pressure = "Medium"

    return {
        "operator_mode": primary,
        "pressure_level": pressure,
        "scores": scores
    }
