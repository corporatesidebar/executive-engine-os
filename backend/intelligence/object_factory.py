def obj(object_type: str, title: str, payload: dict, status: str = "generated") -> dict:
    return {
        "object_type": object_type,
        "title": title,
        "status": status,
        "payload": payload
    }

def dealership_objects():
    proposal = obj("proposal", "90-Day Financed-Buyer Acquisition Sprint Proposal", {
        "recipient": "Ontario auto loan dealership",
        "positioning": "This is not an SEO and Google Ads package. It is a financed-buyer acquisition system.",
        "business_problem": "Most dealership marketing produces traffic and form fills. The dealership needs finance-ready buyers, faster lead handling, and visibility into appointments and funded deals.",
        "offer": "90-Day Financed-Buyer Acquisition Sprint",
        "outcomes": [
            "Generate finance-intent leads from Google Search.",
            "Reduce wasted ad spend from broad car-shopping traffic.",
            "Improve lead-to-appointment conversion.",
            "Track CPA, booked appointments, and funded-deal contribution.",
            "Build SEO pages that reduce long-term paid dependency."
        ],
        "scope": [
            "Finance-intent keyword map",
            "Google Ads campaign structure",
            "Pre-approval landing page",
            "Call/form tracking setup",
            "Weekly waste removal",
            "SEO content map for local finance terms",
            "Reporting dashboard for CPA, appointments, and funded deals"
        ],
        "pricing_options": [
            {"name": "Pilot Sprint", "price": "$2,500 setup + $1,500/month management + ad spend"},
            {"name": "Growth Sprint", "price": "$5,000 setup + $3,000/month management + ad spend"},
            {"name": "Performance Partnership", "price": "Base retainer + bonus tied to funded-deal volume or qualified appointment targets"}
        ],
        "decision_ask": "Approve a 90-day pilot with tracking access, campaign budget, and lead handling accountability."
    })

    outreach = obj("outreach_sequence", "Dealership Follow-Up Sequence", {
        "channel": "email",
        "messages": [
            {
                "day": 1,
                "subject": "90-day finance lead sprint",
                "body": "Hi [Name], I mapped the fastest way to test whether we can generate finance-ready auto loan opportunities under a controlled CPA. The recommendation is a 90-day financed-buyer acquisition sprint: finance-intent Google Ads, pre-approval landing page, call/form tracking, weekly waste removal, and reporting tied to CPA, booked appointments, and funded-deal contribution. This is not a generic SEO or Ads package. The goal is to prove predictable buyer flow with real acquisition economics. Worth reviewing the pilot structure this week?"
            },
            {
                "day": 3,
                "subject": "Re: finance lead sprint",
                "body": "Quick follow-up. The key difference is tracking the path from search intent to appointment/funded deal instead of reporting only clicks and leads. If sub-$100 CPA is the goal, we need intent control and lead response speed from day one."
            },
            {
                "day": 7,
                "subject": "Close the loop?",
                "body": "Should I close the loop on this, or would it be useful to send a one-page pilot scope for a 90-day test?"
            }
        ]
    })

    crm = obj("crm_pipeline", "Dealership Pilot CRM Pipeline", {
        "stages": [
            {"stage": "Target Dealer Identified", "owner": "Sales", "automation": "Create account record"},
            {"stage": "Proposal Sent", "owner": "Sales", "automation": "Follow-up email scheduled for day 3"},
            {"stage": "Decision Call Booked", "owner": "Sales", "automation": "Add meeting prep checklist"},
            {"stage": "Pilot Approved", "owner": "Operator", "automation": "Create campaign setup task list"},
            {"stage": "Tracking Live", "owner": "Media/Tech", "automation": "Weekly KPI report reminder"},
            {"stage": "90-Day Review", "owner": "Executive", "automation": "Prepare renewal/scale proposal"}
        ]
    })

    kpis = obj("kpi_scorecard", "Dealership Acquisition KPI Scorecard", {
        "metrics": [
            {"metric": "Cost per lead", "target": "< $100 initial target"},
            {"metric": "Booked appointment rate", "target": "20%+"},
            {"metric": "Lead response time", "target": "< 5 minutes"},
            {"metric": "Qualified finance application rate", "target": "tracked weekly"},
            {"metric": "Funded-deal contribution", "target": "tracked monthly"}
        ]
    })

    checklist = obj("deployment_checklist", "Dealership Proposal Deployment Checklist", {
        "items": [
            "Confirm dealership target geography.",
            "Confirm monthly pilot ad budget.",
            "Confirm lead response owner.",
            "Build finance-intent keyword map.",
            "Create pre-approval landing page wireframe.",
            "Send proposal and follow-up email.",
            "Book decision call."
        ]
    })

    return [proposal, outreach, crm, kpis, checklist]

def monetization_objects():
    offer = obj("offer", "Executive Operating System Audit Offer", {
        "buyer": "CEO, COO, founder, agency owner, consultant, SMB operator",
        "pain": "Executives are buried in priorities, meetings, follow-ups, decisions, scattered tools, and operational pressure.",
        "promise": "In 7 days, map operating drag and install a practical command system that reduces pressure, clarifies execution, and creates visible momentum.",
        "deliverables": [
            "Executive workflow audit",
            "Pressure map",
            "Active/pause priority structure",
            "Daily command briefing workflow",
            "Follow-up and decision tracker",
            "Execution asset library",
            "30-day operating cadence"
        ],
        "pricing": [
            "$5,000 audit",
            "$15,000 implementation sprint",
            "$3,000/month continuity retainer"
        ]
    })

    landing = obj("landing_page", "Executive Engine Audit Landing Page Copy", {
        "hero": "Install a private operating system for executive execution.",
        "subhero": "Reduce pressure, clarify priorities, and turn scattered work into decisions, actions, assets, and follow-ups.",
        "cta": "Book Executive Workflow Audit",
        "sections": [
            {"title": "The Problem", "copy": "Executives are not short on effort. They are drowning in fragmented priorities and unresolved decisions."},
            {"title": "The Audit", "copy": "We map your operating drag, identify pressure sources, and build the command structure for execution."},
            {"title": "The Outcome", "copy": "A clearer operating rhythm, fewer open loops, and a system that shows what matters next."}
        ]
    })

    outbound = obj("outreach_sequence", "Executive Engine Buyer Outreach", {
        "channel": "LinkedIn + Email",
        "messages": [
            {
                "day": 1,
                "body": "Hey [Name] — I’m building a private Executive Operating System for operators managing too many priorities, meetings, follow-ups, and decisions across scattered tools. I’m offering a small number of executive workflow audits where I map current operating drag and build a practical execution system around it. Worth a quick look this week?"
            },
            {
                "day": 3,
                "body": "The audit is designed to identify where execution pressure is coming from: open loops, scattered priorities, stalled decisions, or missing follow-up structure. The output is a practical command system, not a report."
            },
            {
                "day": 7,
                "body": "Should I send over the short audit scope? It is built for CEOs/operators who want less pressure and cleaner execution."
            }
        ]
    })

    crm = obj("crm_pipeline", "Executive Engine Sales Pipeline", {
        "stages": [
            {"stage": "Prospect Identified", "owner": "VA / Sales", "automation": "Add company/person to CRM"},
            {"stage": "Outreach Sent", "owner": "Sales", "automation": "Schedule day 3 follow-up"},
            {"stage": "Interest", "owner": "Executive", "automation": "Send audit scope"},
            {"stage": "Audit Call Booked", "owner": "Executive", "automation": "Create meeting prep brief"},
            {"stage": "Audit Sold", "owner": "Executive", "automation": "Create onboarding checklist"},
            {"stage": "Implementation Upsell", "owner": "Executive", "automation": "Prepare implementation proposal"}
        ]
    })

    kpi = obj("kpi_scorecard", "Executive Engine 30-Day Revenue KPI System", {
        "metrics": [
            {"metric": "Target prospects/day", "target": "25"},
            {"metric": "Reply rate", "target": "8-12%"},
            {"metric": "Booked calls/week", "target": "3-5"},
            {"metric": "Paid audit closes", "target": "1-2/month initial"},
            {"metric": "Implementation conversion", "target": "30-50% of audits"}
        ]
    })

    return [offer, landing, outbound, crm, kpi]

def overload_objects():
    operating = obj("operating_system", "Active / Pause Executive Operating Sheet", {
        "active_this_week": [
            {"lane": "Cash Path", "item": ""},
            {"lane": "Stability Path", "item": ""},
            {"lane": "Obligation Path", "item": ""}
        ],
        "paused": [],
        "kill_or_archive": [],
        "rule": "Nothing new enters unless it replaces one active item.",
        "daily_review_questions": [
            "What creates money?",
            "What protects stability?",
            "What must be handled?",
            "What is noise?",
            "What can be delegated?"
        ]
    })

    delegation = obj("delegation_map", "Executive Delegation Map", {
        "executive_keeps": ["final decisions", "revenue calls", "relationship leverage", "strategic tradeoffs"],
        "delegate": ["research gathering", "file organization", "CRM updates", "report formatting", "lead list building"],
        "automate": ["follow-up reminders", "weekly reports", "task creation", "meeting prep checklists"]
    })

    checklist = obj("deployment_checklist", "Pressure Reduction Deployment Checklist", {
        "items": [
            "List every open project.",
            "Mark each as Cash, Stability, Obligation, Noise, or Dead.",
            "Keep only one active item per first three categories.",
            "Move paused work out of view.",
            "Delegate admin/research/formatting.",
            "Execute cash or stability item first.",
            "Review active list once per day."
        ]
    })

    return [operating, delegation, checklist]

def general_objects():
    system = obj("operating_system", "Deployable Execution Object System", {
        "standard": "A command is not complete until it produces an object that can be sent, assigned, tested, sold, or measured.",
        "workflow": [
            "Convert input into operational object.",
            "Attach owner or recipient.",
            "Deploy object.",
            "Measure response.",
            "Kill, improve, or scale."
        ]
    })

    checklist = obj("deployment_checklist", "General Deployment Checklist", {
        "items": [
            "Name business outcome.",
            "Choose recipient/system.",
            "Generate object.",
            "Deploy within 24 hours.",
            "Measure signal.",
            "Improve or kill path."
        ]
    })

    return [system, checklist]
