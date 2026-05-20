RESOURCE_BANK = {
    "monetization": [
        {"name": "Loom", "url": "https://www.loom.com", "use": "Record a 2-minute executive workflow demo."},
        {"name": "Framer", "url": "https://www.framer.com", "use": "Build a premium offer landing page quickly."},
        {"name": "Tally", "url": "https://tally.so", "use": "Create executive intake and audit forms."},
        {"name": "Apollo", "url": "https://www.apollo.io", "use": "Find CEOs, COOs, founders, agency owners, and operators."},
        {"name": "Clay", "url": "https://www.clay.com", "use": "Enrich lists and personalize outbound."},
        {"name": "Stripe", "url": "https://stripe.com", "use": "Create payment links for audit and implementation offers."},
        {"name": "Calendly", "url": "https://calendly.com", "use": "Book audit calls with low friction."},
    ],
    "proposal": [
        {"name": "Google Ads Keyword Planner", "url": "https://ads.google.com/home/tools/keyword-planner/", "use": "Validate finance-intent search demand."},
        {"name": "Google Ads", "url": "https://ads.google.com", "use": "Launch controlled lead acquisition tests."},
        {"name": "Looker Studio", "url": "https://lookerstudio.google.com", "use": "Build CPA and funded-deal reporting."},
        {"name": "Unbounce", "url": "https://unbounce.com", "use": "Create focused pre-approval landing pages."},
    ],
    "overload": [
        {"name": "Notion", "url": "https://www.notion.so", "use": "Store active/pause lists."},
        {"name": "Trello", "url": "https://trello.com", "use": "Simple visible active queue."},
        {"name": "Sunsama", "url": "https://www.sunsama.com", "use": "Daily planning and workday shutdown."},
        {"name": "Motion", "url": "https://www.usemotion.com", "use": "Auto-schedule priority work."},
    ],
    "default": [
        {"name": "Loom", "url": "https://www.loom.com", "use": "Make a fast walkthrough."},
        {"name": "Notion", "url": "https://www.notion.so", "use": "Capture operating plan."},
        {"name": "Tally", "url": "https://tally.so", "use": "Collect structured input."},
    ]
}

def resources_for(intent: str) -> list:
    return RESOURCE_BANK.get(intent, RESOURCE_BANK["default"])
