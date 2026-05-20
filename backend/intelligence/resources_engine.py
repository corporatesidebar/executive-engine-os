def recommend_resources(intent: str) -> list:
    if intent == "monetization":
        return [
            {"name": "Loom", "url": "https://www.loom.com", "use": "Record a 2-minute executive workflow demo."},
            {"name": "Framer", "url": "https://www.framer.com", "use": "Build a premium landing page fast."},
            {"name": "Tally", "url": "https://tally.so", "use": "Create executive intake form."},
            {"name": "Apollo", "url": "https://www.apollo.io", "use": "Find CEOs, COOs, founders, operators."},
            {"name": "Clay", "url": "https://www.clay.com", "use": "Enrich and segment outreach lists."},
            {"name": "Stripe", "url": "https://stripe.com", "use": "Create payment links for audit / implementation offer."},
        ]

    if intent == "proposal":
        return [
            {"name": "Google Keyword Planner", "url": "https://ads.google.com/home/tools/keyword-planner/", "use": "Validate finance-intent search terms."},
            {"name": "Google Ads", "url": "https://ads.google.com", "use": "Launch controlled acquisition test."},
            {"name": "Looker Studio", "url": "https://lookerstudio.google.com", "use": "Report CPA, appointments, funded deal tracking."},
            {"name": "Unbounce", "url": "https://unbounce.com", "use": "Build focused pre-approval landing page."},
        ]

    return [
        {"name": "Loom", "url": "https://www.loom.com", "use": "Turn the idea into a walkthrough."},
        {"name": "Notion", "url": "https://www.notion.so", "use": "Capture execution plan and assets."},
        {"name": "Tally", "url": "https://tally.so", "use": "Collect structured input quickly."},
    ]
