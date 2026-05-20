def build_sequence(intent: str) -> dict:
    if intent == "monetization":
        return {
            "today": [
                "Define one paid offer: Executive Operating System Audit.",
                "Set pricing: $5k audit, $15k implementation, $3k/month continuity.",
                "Record a Loom showing before/after executive workflow."
            ],
            "next_24_hours": [
                "Build one-page landing page.",
                "Create Stripe payment or booking link.",
                "Write 3-message outreach sequence."
            ],
            "next_7_days": [
                "Contact 50 CEOs/operators/founders.",
                "Book 5 calls.",
                "Close 1 paid audit."
            ],
        }

    if intent == "overload":
        return {
            "today": [
                "List every active project.",
                "Mark each as Cash, Stability, Obligation, or Noise.",
                "Keep only one Cash, one Stability, one Obligation item active."
            ],
            "next_24_hours": [
                "Create pause list.",
                "Move paused items out of view.",
                "Execute only the highest cash or stability item."
            ],
            "next_7_days": [
                "Review active list daily.",
                "Do not add new work unless it replaces existing work.",
                "Close one loop per day."
            ],
        }

    return {
        "today": ["Choose one outcome.", "Create the first usable asset.", "Send or test it."],
        "next_24_hours": ["Review result.", "Remove weak actions.", "Double down on the highest signal."],
        "next_7_days": ["Repeat the working motion.", "Document what converts.", "Package the repeatable system."],
    }
