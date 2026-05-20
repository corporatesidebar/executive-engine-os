# V36750 — Asset Generation Engine
# Backend-only module patch.

ASSET_CLASSIFICATIONS = {
    "proposal_generation": ["proposal", "pitch", "client", "deal", "presentation"],
    "sales_system_generation": ["sales", "pipeline", "crm", "close", "lead"],
    "lead_generation_systems": ["lead generation", "outbound", "prospect", "appointment"],
    "delegation_systems": ["delegate", "team", "staff", "assistant", "hire"],
    "operational_systems": ["operations", "workflow", "system", "process"],
    "ai_automation_systems": ["automation", "ai", "zapier", "make", "agent"],
    "revenue_systems": ["revenue", "monetize", "profit", "income", "growth"],
}

BANNED_PHRASES = [
    "focus on", "consider", "brainstorm", "review priorities",
    "assess your goals", "think about", "identify opportunities", "create a plan",
]

def classify_asset_request(user_input: str) -> str:
    text = (user_input or "").lower()
    for category, keywords in ASSET_CLASSIFICATIONS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "operational_systems"

def primary_asset_for(category: str, user_input: str) -> dict:
    if category == "proposal_generation":
        return {
            "title": "Client Acquisition Proposal",
            "type": "proposal",
            "content": """EXECUTIVE PROPOSAL STRUCTURE

Objective:
Convert the target prospect into an active revenue client.

Offer:
Strategy + implementation + KPI tracking + weekly execution review.

Pricing Model:
- Setup fee
- Monthly retainer
- Performance incentive

Execution Timeline:
Week 1:
- Discovery
- Setup
- KPI alignment

Week 2:
- Launch campaigns
- Reporting infrastructure
- Optimization system

Close:
Approve pilot, confirm access, launch within 7 days."""
        }

    if category == "lead_generation_systems":
        return {
            "title": "Outbound Lead Engine",
            "type": "outbound_system",
            "content": """OUTBOUND EXECUTION SYSTEM

Daily Motion:
- 50 targeted prospects
- LinkedIn + email
- AI-personalized first line
- 3-step follow-up

Tools:
- Apollo
- Clay
- Instantly or Smartlead
- HubSpot

KPI:
- 50 contacts/day
- 8-12% reply rate
- 3-5 booked calls/week"""
        }

    if category == "sales_system_generation":
        return {
            "title": "Sales Pipeline System",
            "type": "crm_workflow",
            "content": """SALES PIPELINE SYSTEM

Stages:
1. Lead captured
2. Qualified
3. Discovery booked
4. Proposal sent
5. Follow-up active
6. Closed won/lost

KPIs:
- response rate
- booked calls
- proposal close rate
- average deal value
- revenue generated"""
        }

    return {
        "title": "Operational Execution System",
        "type": "workflow",
        "content": """EXECUTION OPERATING SYSTEM

1. Name the business outcome.
2. Build the first usable asset.
3. Put it in front of a buyer, user, or decision-maker.
4. Measure response.
5. Kill weak path or scale winning path."""
    }

def build_v36750_response(user_input: str) -> dict:
    category = classify_asset_request(user_input)
    primary_asset = primary_asset_for(category, user_input)

    supporting_assets = [
        "Follow-up automation sequence",
        "Delegation checklist",
        "Execution KPI tracker",
        "Weekly review framework",
        "Operational accountability workflow",
    ]

    automation_stack = [
        "OpenAI API",
        "Claude API",
        "Zapier",
        "Make.com",
        "HubSpot CRM",
        "Notion",
        "Airtable",
    ]

    delegation_structure = [
        "Executive keeps decision-making and final approval.",
        "VA handles outbound list building and CRM updates.",
        "Automation handles reminders and follow-ups.",
        "Admin handles reporting cleanup.",
    ]

    return {
        "executive_summary": "Operational asset generated for immediate deployment.",
        "real_problem": "Execution is stalled because no deployable asset exists yet.",
        "execution_objective": "Create usable infrastructure that produces measurable movement.",
        "generated_assets": [primary_asset["title"]] + supporting_assets,
        "primary_asset": primary_asset,
        "supporting_assets": supporting_assets,
        "execution_system": ["Build", "Deploy", "Measure", "Optimize", "Scale"],
        "implementation_sequence": [
            "Generate operational asset.",
            "Assign ownership.",
            "Deploy first live version.",
            "Measure operational performance.",
            "Optimize execution bottlenecks.",
        ],
        "delegation_structure": delegation_structure,
        "automation_stack": automation_stack,
        "tools_and_resources": [
            "https://zapier.com",
            "https://make.com",
            "https://hubspot.com",
            "https://airtable.com",
            "https://notion.so",
        ],
        "revenue_impact": "High leverage if asset is deployed to a buyer, prospect, or decision-maker.",
        "execution_timeframe": "24-72 hours to first operational deployment.",
        "risk_control": "Avoid overbuilding before operational validation.",
        "next_execution_asset": "Generate deployment-ready sendable version.",
        "follow_up_command": "Build automation workflow for this system.",
        "operator_mode": "Asset Generation",
        "pressure_level": "Moderate",
        "status": "success",
        # frontend compatibility
        "next_move": "Deploy the generated primary asset to a real recipient or workflow.",
        "decision": "Generate the asset first; optimize after response signal.",
        "action_steps": [
            "Use the primary asset.",
            "Assign owner.",
            "Deploy within 24 hours.",
            "Measure response.",
        ],
        "ready_assets": [primary_asset["content"]],
        "risk": "Overbuilding before validation.",
        "priority": "High",
        "recommended_command": "Generate the deployment-ready version of the primary asset.",
    }
