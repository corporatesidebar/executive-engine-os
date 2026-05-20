def monetization_asset() -> str:
    return """EXECUTIVE ENGINE MONETIZATION OFFER

Offer:
Executive Operating System Audit

Pricing:
- $5,000 audit
- $15,000 implementation sprint
- $3,000/month continuity retainer

Buyer:
CEO, COO, founder, agency owner, SMB operator.

Promise:
Reduce executive pressure by turning scattered priorities, meetings, follow-ups, and decisions into a private operating system.

Deliverables:
- executive workflow audit
- pressure map
- priority compression
- command center setup
- daily briefing structure
- decision/follow-up system
- 30-day operating cadence

Close:
Start with the audit. If the workflow creates clarity, convert into implementation."""

def outreach_asset() -> str:
    return """OUTREACH MESSAGE

Subject: Executive workflow audit

Hey [Name] — I’m building a private Executive Operating System for operators managing too many priorities, meetings, follow-ups, and decisions across scattered tools.

The value is simple:
less pressure, clearer execution, and a daily command layer that shows what matters next.

I’m offering a small number of executive workflow audits where I map current operating drag and build a practical execution system around it.

Worth a quick look this week?"""

def overload_asset() -> str:
    return """ACTIVE / PAUSE OPERATING SHEET

ACTIVE THIS WEEK:
1. Cash path:
2. Stability path:
3. Obligation path:

PAUSED:
-
-
-

RULE:
Paused work is not dead. It is removed from the active operating field.

DECISION:
Nothing new enters unless it replaces one active item."""

def dealership_asset() -> str:
    return """AUTO LOAN DEALERSHIP PROPOSAL SPINE

Positioning:
This is not an SEO and Google Ads package. It is a financed-buyer acquisition sprint.

Commercial Promise:
Generate finance-ready auto loan opportunities while controlling CPA and tracking lead quality through appointment and funded-deal outcomes.

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
If the dealership wants sub-$100 CPA, intent control and lead handling speed must be managed from day one."""

def meeting_asset() -> str:
    return """MEETING OPERATING FRAMEWORK

Decision Target:
What decision must be made before the meeting ends?

Required Inputs:
- current constraint
- decision owner
- risk if delayed
- options to eliminate
- final next action

Close:
Before we end, we need one owner, one deadline, and one next action."""

def assets_for(mode: str) -> list:
    if mode == "revenue_pressure":
        return [monetization_asset(), outreach_asset()]
    if mode == "client_acquisition":
        return [outreach_asset(), monetization_asset()]
    if mode == "proposal_generation":
        return [dealership_asset()]
    if mode == "operational_overload":
        return [overload_asset()]
    if mode == "meeting":
        return [meeting_asset()]
    return ["""EXECUTION SYSTEM

Decision:
Convert this from a thought into a usable asset.

System:
1. Name the business outcome.
2. Remove one unnecessary path.
3. Create the asset.
4. Put it in front of a person, buyer, user, or decision-maker.
5. Measure response."""]
