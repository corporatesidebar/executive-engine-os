def resource_bank(mode: str) -> list:
    common = [
        {"name": "Loom", "url": "https://www.loom.com", "use": "Record demos, walkthroughs, and internal handoffs."},
        {"name": "Notion", "url": "https://www.notion.so", "use": "Store operating docs, execution plans, and asset libraries."},
        {"name": "Tally", "url": "https://tally.so", "use": "Create intake forms and structured client inputs."},
    ]

    if mode in ["revenue_pressure", "client_acquisition", "proposal_generation"]:
        return [
            {"name": "Apollo", "url": "https://www.apollo.io", "use": "Find executive buyers and sales prospects."},
            {"name": "Clay", "url": "https://www.clay.com", "use": "Enrich prospects and personalize outbound."},
            {"name": "LinkedIn Sales Navigator", "url": "https://business.linkedin.com/sales-solutions/sales-navigator", "use": "Find CEOs, COOs, founders, operators, and buyers."},
            {"name": "Stripe", "url": "https://stripe.com", "use": "Create payment links for audits, retainers, and implementation offers."},
            {"name": "Framer", "url": "https://www.framer.com", "use": "Build a high-quality landing page quickly."},
        ] + common

    if mode == "operational_overload":
        return [
            {"name": "Sunsama", "url": "https://www.sunsama.com", "use": "Daily planning and shutdown rituals."},
            {"name": "Motion", "url": "https://www.usemotion.com", "use": "Auto-schedule priority work."},
            {"name": "Trello", "url": "https://trello.com", "use": "Simple active/pause execution board."},
        ] + common

    if mode == "proposal_generation":
        return [
            {"name": "Google Docs", "url": "https://docs.google.com", "use": "Draft and share the proposal."},
            {"name": "Canva", "url": "https://www.canva.com", "use": "Create polished proposal visuals."},
        ] + common

    return common
