def sequence_for(intent: str) -> dict:
    if intent == "monetization":
        return {
            "today": [
                "Package the Executive Operating System Audit.",
                "Create Stripe or booking link.",
                "Record a 2-minute Loom demo."
            ],
            "next_24_hours": [
                "Build a one-page Framer landing page.",
                "Write one outreach message.",
                "Build a list of 50 CEO/COO/operator prospects."
            ],
            "next_7_days": [
                "Send 50 targeted messages.",
                "Book 5 calls.",
                "Close 1 paid audit."
            ]
        }

    if intent == "overload":
        return {
            "today": [
                "List every active project.",
                "Classify each as Cash, Stability, Obligation, or Noise.",
                "Pause everything except one item in the first three categories."
            ],
            "next_24_hours": [
                "Move paused work out of view.",
                "Execute only the Cash or Stability item.",
                "Close one open loop."
            ],
            "next_7_days": [
                "Review active list once daily.",
                "Do not add new work unless it replaces current work.",
                "Close or kill one loop per day."
            ]
        }

    if intent == "proposal":
        return {
            "today": [
                "Write proposal around funded-deal economics.",
                "Define sub-$100 CPA conditions.",
                "Create the 90-day sprint scope."
            ],
            "next_24_hours": [
                "Create landing page outline.",
                "Build keyword intent list.",
                "Draft dealership follow-up email."
            ],
            "next_7_days": [
                "Send proposal.",
                "Book decision call.",
                "Close pilot budget and tracking access."
            ]
        }

    return {
        "today": ["Choose one outcome.", "Create the first usable asset.", "Send or test it."],
        "next_24_hours": ["Review response.", "Remove weak actions.", "Double down on the strongest signal."],
        "next_7_days": ["Repeat working motion.", "Package the process.", "Turn it into a repeatable system."]
    }
