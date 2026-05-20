def detect_intent(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["profitable", "profit", "money", "revenue", "cash", "monetize"]):
        return "monetization"
    if any(x in t for x in ["overwhelmed", "too many", "scattered", "chaos", "busy"]):
        return "overload"
    if any(x in t for x in ["proposal", "dealership", "seo", "ads", "cpa"]):
        return "proposal"
    if any(x in t for x in ["build", "deploy", "backend", "frontend", "engine"]):
        return "build"
    if any(x in t for x in ["pivot", "keep building", "should i"]):
        return "decision"
    return "operator"

def build_leverage_map(user_input: str, intent: str) -> dict:
    if intent == "monetization":
        return {
            "best_path": "Sell Executive Engine as a high-ticket operator implementation offer before trying to sell SaaS subscriptions.",
            "why": "Services monetize faster because you can sell transformation, not unfinished software. Productize what closes.",
            "pause": ["consumer-style app expansion", "new UI experiments", "broad feature building"],
            "focus": "One paid executive operating audit + implementation sprint.",
        }

    if intent == "overload":
        return {
            "best_path": "Convert overload into a ranked execution queue tied to cash, stability, and obligation.",
            "why": "The issue is not effort. The issue is too many active loops with no forced elimination.",
            "pause": ["new builds not tied to current validation", "random UI changes", "side ideas without revenue path"],
            "focus": "Pick one revenue move, one stability move, one personal/admin move.",
        }

    if intent == "proposal":
        return {
            "best_path": "Position the offer around funded vehicle deals, not SEO and Google Ads deliverables.",
            "why": "The dealership cares about financed buyers and acquisition economics, not marketing activity.",
            "pause": ["generic SEO reports", "blog calendars", "broad ad campaigns"],
            "focus": "90-day financed-buyer acquisition sprint.",
        }

    if intent == "build":
        return {
            "best_path": "Stop widening the system and ship one testable cognition improvement at a time.",
            "why": "The product improves when the response helps the user move forward, not when the architecture gets bigger.",
            "pause": ["layout changes", "new dashboards", "non-essential routes"],
            "focus": "Dual-layer output: executive scan plus operational depth.",
        }

    return {
        "best_path": "Turn the input into one executable outcome with resources and next actions.",
        "why": "The executive needs movement, not interpretation.",
        "pause": ["extra planning", "generic summaries", "unowned follow-ups"],
        "focus": "Concrete execution sequence.",
    }
