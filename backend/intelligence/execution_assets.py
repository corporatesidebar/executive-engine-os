def build_offer_asset() -> str:
    return """OFFER STRUCTURE — EXECUTIVE ENGINE IMPLEMENTATION

Offer Name:
Executive Operating System Audit

Price:
$5,000 audit
$15,000 implementation sprint
$3,000/month continuity retainer

Buyer:
Founder, CEO, COO, operator, agency owner, SMB leader.

Promise:
We turn scattered executive work into a private operating system that reduces pressure, clarifies execution, and creates visible momentum.

Deliverables:
- executive workflow audit
- command center setup
- daily briefing structure
- priority and pressure map
- execution asset library
- follow-up and decision system
- 30-day operating cadence

Close:
Start with the audit. If the workflow creates clarity, convert to implementation."""

def build_outreach_asset() -> str:
    return """OUTREACH MESSAGE

Subject: Quick idea for executive workflow

Hey [Name] — I’m building a private Executive Operating System for operators who are managing too many priorities, meetings, follow-ups, and decisions across scattered tools.

The value is simple:
less pressure, clearer execution, and a daily command layer that shows what matters next.

I’m offering a small number of executive workflow audits where I map the current operating drag and build a practical execution system around it.

Worth a quick look this week?"""

def build_dealership_asset() -> str:
    return """DEALERSHIP PROPOSAL SPINE

Positioning:
This is not an SEO and Google Ads package. It is a financed-buyer acquisition sprint.

Commercial Promise:
Generate more finance-ready auto loan opportunities while controlling CPA and tracking lead quality through booked appointments and funded deals.

90-Day Sprint:
1. Finance-intent Google Ads
2. Pre-approval landing page
3. Call/form tracking
4. Funded-deal attribution
5. Weekly waste removal
6. SEO pages to reduce paid dependency

Do Not Sell:
- broad traffic
- blog calendars
- ranking reports
- generic ad setup

Close:
If the dealership wants sub-$100 CPA, the campaign must control intent and lead handling speed from day one."""

def asset_pack(intent: str) -> list:
    if intent == "monetization":
        return [build_offer_asset(), build_outreach_asset()]
    if intent == "proposal":
        return [build_dealership_asset()]
    if intent == "overload":
        return ["""ACTIVE / PAUSE DECISION SHEET

Active:
1. Cash path:
2. Stability path:
3. Obligation path:

Paused:
- 
- 
- 

Rule:
Nothing paused gets reopened this week unless it replaces an active item."""]

    return ["""EXECUTION ASSET

Decision:
Move from thinking to execution.

Next:
Create one usable asset, send it, test response, then adjust."""]
