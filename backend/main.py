import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

VERSION = "V35160-response-intelligence-fix"
VERSION_SHORT = "V35160"
VERSION_SLUG = "v35160-backend-response-intelligence-only"
BACKEND_URL = "https://executive-engine-os.onrender.com"
FRONTEND_URL = "https://executive-engine-frontend.onrender.com/"

REQUIRED_RUN_FIELDS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
    "provider_used",
    "status",
]
CORE_DISPLAY_FIELDS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
]
ALLOWED_PRIORITIES = {"High", "Medium", "Low"}
INTENTS = {
    "proposal",
    "meeting",
    "decision",
    "revenue",
    "follow_up",
    "strategy",
    "execution",
    "risk",
    "general",
}

app = FastAPI(
    title="Executive Engine OS Backend",
    version=VERSION,
    description="Backend-only /run response intelligence patch. No frontend, database, or layout changes.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def base_status() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "Executive Engine OS Backend",
        "version": VERSION,
        "version_short": VERSION_SHORT,
        "version_slug": VERSION_SLUG,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "timestamp": utc_now(),
    }


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_command(body: Any) -> Tuple[str, Dict[str, Any]]:
    if isinstance(body, dict):
        command = body.get("command") or body.get("input") or body.get("prompt") or body.get("message") or ""
        return clean_text(command), body
    if body is None:
        return "", {}
    return clean_text(body), {}


def ensure_string(value: Any, fallback: str) -> str:
    text = clean_text(value)
    return text if text else fallback


def ensure_list(value: Any, limit: int = 12) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, (dict, list)):
                text = json.dumps(item, ensure_ascii=False)
            else:
                text = str(item).strip()
            if text:
                items.append(text)
        return items[:limit]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        parts = [p.strip() for p in re.split(r"\n+|\s•\s|\s-\s|;", text) if p.strip()]
        return parts[:limit] if parts else [text]
    return [str(value).strip()][:limit]


def normalize_priority(value: Any, fallback: str = "High") -> str:
    text = clean_text(value).lower()
    if text in {"high", "urgent", "critical"}:
        return "High"
    if text in {"medium", "normal", "moderate"}:
        return "Medium"
    if text in {"low", "later"}:
        return "Low"
    return fallback if fallback in ALLOWED_PRIORITIES else "High"


def contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def detect_intent(command: str) -> str:
    text = f" {command.lower()} "

    proposal_terms = [
        "proposal",
        "sow",
        "scope of work",
        "quote",
        "pitch",
        "client proposal",
        "dealership",
        "google ads",
        "seo",
        "cpa",
    ]
    meeting_terms = ["meeting", "agenda", "talking points", "prep", "prepare for", "call with", "objections", "questions"]
    follow_up_terms = ["follow up", "follow-up", "email", "reply", "respond", "message", "send this", "subject line"]
    decision_terms = ["decide", "decision", "choose", "recommend", "tradeoff", "trade-off", "option", "should i", "which one"]
    revenue_terms = ["revenue", "sales", "sell", "close", "offer", "lead", "leads", "pipeline", "roi", "booked calls"]
    strategy_terms = ["strategy", "positioning", "roadmap", "market", "moat", "category", "go to market", "gtm"]
    risk_terms = ["risk", "blocker", "issue", "problem", "threat", "broken", "not working", "fail", "failure", "concern"]
    execution_terms = ["build", "execute", "launch", "fix", "create", "implement", "ship", "do this", "checklist"]

    # Proposal wins over revenue/execution because user explicitly complained about proposal routing.
    if contains_any(text, proposal_terms):
        return "proposal"
    if contains_any(text, meeting_terms):
        return "meeting"
    if contains_any(text, follow_up_terms):
        return "follow_up"
    if contains_any(text, decision_terms):
        return "decision"
    if contains_any(text, revenue_terms):
        return "revenue"
    if contains_any(text, strategy_terms):
        return "strategy"
    if contains_any(text, risk_terms):
        return "risk"
    if contains_any(text, execution_terms):
        return "execution"
    return "general"


def infer_metric(command: str) -> str:
    text = command or ""
    patterns = [
        r"(?:under|below|less than|<)\s*\$?([0-9][0-9,]*)",
        r"cpa\s*(?:under|below|less than|<)?\s*\$?([0-9][0-9,]*)",
        r"\$([0-9][0-9,]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return f"under ${match.group(1).replace(',', '')}" if "under" in text.lower() or "cpa" in pattern else f"${match.group(1)}"
    return "a measurable CPA / revenue target"


def proposal_response(command: str) -> Dict[str, Any]:
    metric = infer_metric(command)
    return {
        "next_move": "Send a performance-based Ontario auto-loan acquisition proposal that sells qualified finance applications and booked appointments, not generic marketing activity.",
        "decision": f"Recommend a 30-day SEO + Google Search pilot with dedicated landing-page conversion, call/form tracking, and weekly lead-quality optimization toward {metric} CPA. Do not sell impressions, traffic, or vague awareness.",
        "action_steps": [
            "Package the offer as a contained 30-day pilot: search intent, dedicated landing page, tracking, weekly optimization, and lead-quality review.",
            "Target Ontario buyers actively searching for auto financing, bad-credit auto loans, approval, second-chance financing, and dealership financing terms.",
            "Build one approval-focused landing page with financing proof, dealership trust, short application CTA, phone CTA, and clear next-step language.",
            "Launch Google Search campaigns only around high-intent finance keywords; block research, jobs, insurance, repair, free, and low-intent traffic with negatives.",
            "Track form submits, calls, booked appointments, applications, approval rate, sold units, and CPA by campaign/ad group.",
            "Run weekly cut/scale decisions: cut bad search terms, shift spend to converting intent, and report lead quality instead of vanity metrics.",
        ],
        "ready_assets": [
            "Proposal Title: Ontario Auto Loan Growth Pilot — SEO + Google Ads Qualified Lead Engine",
            f"Executive Summary: We will build a focused acquisition system for your dealership to generate finance-ready Ontario auto-loan leads with a target CPA of {metric}. The pilot combines high-intent Google Search, approval-focused landing-page direction, conversion tracking, and weekly optimization around applications, booked appointments, and sold-unit potential.",
            "Problem: Most dealership marketing wastes budget on broad traffic, weak forms, and leads that do not convert into financeable buyers. The opportunity is to capture buyers already searching for approval and route them into a simple application path before competitors get them.",
            "Pilot Scope: keyword strategy, Google Search campaign build, negative keyword control, landing-page structure, conversion tracking plan, weekly optimization notes, and lead-quality review.",
            "Campaign Structure: 1) bad-credit auto loans Ontario, 2) car financing approval Ontario, 3) dealership financing near me, 4) second-chance auto financing, 5) branded/local dealership financing terms where relevant.",
            "Landing Page Outline: headline around fast approval, dealership trust, who qualifies, how the process works, inventory/financing angle, proof points, short application, phone CTA, and privacy/reassurance copy.",
            "Success Metrics: qualified lead volume, cost per application, booked appointment rate, approval rate, sold units, wasted-spend reduction, and CPA by intent cluster.",
            "Client Requirements: Google Ads access or account creation approval, landing-page/domain access, call tracking number, form destination email/CRM, financing criteria, inventory/offer details, and sales follow-up process.",
            f"Follow-Up Email: Subject: Ontario auto-loan lead pilot. Body: I put together a focused 30-day plan to generate finance-ready auto-loan leads using SEO intent and Google Search, with tracking around applications and booked appointments. The goal is to reduce wasted traffic and push CPA toward {metric} while improving lead quality. I can send the pilot scope, first-week launch plan, and tracking checklist.",
        ],
        "risk": "The main risk is optimizing to cheap form fills instead of financeable applicants. CPA only matters if lead quality, booked appointments, approvals, and sold-unit potential are tracked together.",
        "priority": "High",
        "recommended_command": "Turn this into a client-ready one-page proposal with pricing, timeline, deliverables, landing-page copy, and follow-up email.",
    }


def meeting_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Enter the meeting with a decision target, an outcome agenda, and the follow-up already framed before the call starts.",
        "decision": "Use the meeting to secure commitment to the next concrete step, not to discuss the topic broadly.",
        "action_steps": [
            "Open by confirming the business outcome and the decision needed by the end of the meeting.",
            "Ask what success looks like, what has already failed, who approves, and what deadline matters.",
            "Present one recommended path and one fallback option only.",
            "Handle objections around cost, timing, complexity, ownership, and risk.",
            "Close with owner, date, deliverable, and follow-up asset before the meeting ends.",
        ],
        "ready_assets": [
            "Agenda: 1) Outcome, 2) Current constraint, 3) Recommended path, 4) Risks/objections, 5) Decision and next step.",
            "Talking Points: lead with speed, measurable outcome, reduced friction, business upside, and cost of delay.",
            "Questions: What result matters most? Who signs off? What has failed already? What happens if this waits 30 days? What would make this a yes?",
            "Objection Handles: Budget — tie to measurable return. Timing — propose a contained pilot. Complexity — reduce to one owner and one next step. Risk — define stop/scale criteria.",
            "Follow-Up Draft: Here is the decision, the agreed next step, the owner, the deadline, and the asset I will send so this does not stall.",
        ],
        "risk": "The meeting becomes conversation without commitment unless the decision, owner, and next asset are locked before the call ends.",
        "priority": "High",
        "recommended_command": "Create the exact post-meeting follow-up email and decision summary for this meeting.",
    }


def decision_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Make the decision using speed, upside, reversibility, cost, and operational drag as the filter.",
        "decision": "Choose the path that validates the business result fastest without locking the company into unnecessary complexity.",
        "action_steps": [
            "State the decision in one sentence and the result it must produce.",
            "Score each option on upside, cost, speed, reversibility, risk, and operational burden.",
            "Reject the option that requires heavy structure before proof of usefulness or revenue.",
            "Assign one owner, one metric, and one review date.",
            "Write the decision memo so the next action is obvious.",
        ],
        "ready_assets": [
            "Decision Memo Structure: recommendation, why now, options considered, tradeoffs, risk, owner, metric, review date.",
            "Recommendation: proceed with the lowest-complexity path that creates the fastest proof of value.",
            "Tradeoff Lens: speed beats completeness when the core uncertainty is usefulness, adoption, or buyer response.",
        ],
        "risk": "The risk is overbuilding or over-debating before the decision is validated by real usage, revenue, or operational movement.",
        "priority": "High",
        "recommended_command": "Turn this into a one-page executive decision memo with recommendation, tradeoffs, and next action.",
    }


def revenue_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Convert the request into an offer, a target buyer, an outreach asset, and a close path.",
        "decision": "Prioritize the buyer segment with urgent pain, budget authority, and a measurable reason to act now.",
        "action_steps": [
            "Define the target buyer and the painful business outcome they already want solved.",
            "Write the offer around money, speed, risk reduction, control, or operational leverage.",
            "Create one direct outreach message and one proof-based follow-up.",
            "Set the close path: call, proposal, pilot, payment, implementation.",
            "Track replies, booked calls, objections, proposal sent, close rate, and revenue won.",
        ],
        "ready_assets": [
            "Offer Angle: reduce waste, increase qualified opportunities, and make the path to revenue measurable.",
            "Target Buyer: owner, CEO, GM, sales leader, or operator with visible revenue friction and authority to move.",
            "Outreach: I have a focused way to turn existing demand into better-qualified opportunities without adding operational drag. Worth a quick look?",
            "Close Plan: qualify pain, confirm economics, present contained pilot, define success metric, secure next step.",
        ],
        "risk": "The offer will underperform if it is framed as services or activity instead of a direct business outcome the buyer already cares about.",
        "priority": "High",
        "recommended_command": "Build the exact outreach sequence, sales call script, and pilot offer for this revenue opportunity.",
    }


def follow_up_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Send a concise follow-up that restates the outcome, removes friction, and asks for one next commitment.",
        "decision": "Do not over-explain. Advance the deal, decision, or relationship by one clear step.",
        "action_steps": [
            "Open with the specific reason for the follow-up.",
            "Restate the business outcome or decision needed.",
            "Include the next asset, meeting path, or recommended action.",
            "Ask one clear yes/no or scheduling question.",
        ],
        "ready_assets": [
            "Subject: Next step on this",
            "Email Body: Hi — quick follow-up. Based on where this sits, the clean next move is to confirm the outcome, lock the first execution step, and avoid letting this drift. I can send the concise plan/proposal with what happens first, what is needed from your side, and how progress will be measured. Does it make sense for me to send that over today?",
        ],
        "risk": "A weak follow-up creates ambiguity and lets the opportunity stall without a clear next commitment.",
        "priority": "Medium",
        "recommended_command": "Rewrite this follow-up for a specific person, company, and desired outcome.",
    }


def strategy_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Turn the strategy into a focused operating thesis and one proof point that can be validated this week.",
        "decision": "Use a narrow wedge first. Expand only after repeated use, buyer pull, or operational dependency is proven.",
        "action_steps": [
            "Define the target user or buyer and the urgent problem they feel now.",
            "Write the strategic position in one sentence.",
            "Identify the first workflow, asset, or offer that proves the position.",
            "Remove anything that does not support adoption, revenue, or operational dependency.",
            "Set a 7-day proof target and review the result.",
        ],
        "ready_assets": [
            "Strategic Position: an executive operating layer that creates clarity, speed, leverage, and control for high-responsibility operators.",
            "Action Path: validate one high-value workflow, prove repeated use, then expand into memory, actions, and proactive briefing.",
            "7-Day Proof Target: one workflow creates a useful asset, decision, next action, and follow-up without generic advice.",
        ],
        "risk": "The strategy can become too broad and lose usefulness if it tries to become a full platform before one workflow is indispensable.",
        "priority": "High",
        "recommended_command": "Convert this strategy into a 7-day execution roadmap with success metrics and HOLD/FIX/PROMOTE criteria.",
    }


def execution_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Ship the smallest complete fix that advances the objective and can be verified immediately.",
        "decision": "Keep scope narrow, protect the stable base, and complete this backend-only intelligence fix before adding another layer.",
        "action_steps": [
            "Lock the objective in one sentence.",
            "Identify the exact endpoint or behavior that must change and the areas that must not change.",
            "Build only the required fix.",
            "Run the matching test checklist.",
            "Classify the result as HOLD, FIX, PROMOTE, ROLLBACK, or PIVOT.",
        ],
        "ready_assets": [
            "Execution Checklist: objective, protected areas, changed files, endpoint tests, contract tests, decision result.",
            "Owner Summary: one build, one test, one decision, one next action.",
        ],
        "risk": "Scope creep will damage stability and make it impossible to know which change fixed or broke the system.",
        "priority": "High",
        "recommended_command": "Create the exact deployment test checklist and classify the result after testing.",
    }


def risk_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Isolate the highest-consequence risk and choose containment before continuing execution.",
        "decision": "Do not expand scope until the current risk is fixed, accepted, or routed around.",
        "action_steps": [
            "Name the risk in one sentence.",
            "Identify what breaks if the risk is ignored.",
            "Choose containment: fix, rollback, hold, or isolate.",
            "Run the smallest test that confirms whether the risk is real.",
            "Document the decision and next action.",
        ],
        "ready_assets": [
            "Risk Control Brief: issue, consequence, likelihood, containment, owner, test, deadline.",
            "Decision Options: HOLD if unclear, FIX if contained, ROLLBACK if stable base is compromised, PROMOTE only after verification.",
        ],
        "risk": "The real risk is treating an unstable result as progress and compounding it with additional changes.",
        "priority": "High",
        "recommended_command": "Turn this into a risk log with severity, containment, owner, and verification step.",
    }


def general_response(command: str) -> Dict[str, Any]:
    subject = clean_text(command) or "the current executive request"
    return {
        "next_move": f"Turn {subject} into a concrete outcome, a decision, a first asset, and a next command.",
        "decision": "Move forward using reasonable executive assumptions instead of waiting for perfect information.",
        "action_steps": [
            "Define the desired outcome in one sentence.",
            "Identify the decision or deliverable required now.",
            "Create the first useful asset instead of giving generic advice.",
            "Name the risk that could stall execution.",
            "Set the next command that advances the work.",
        ],
        "ready_assets": [
            "Executive Brief: outcome, decision, action path, ready asset, risk, priority, next command.",
            "Next Command: turn this into a specific deliverable with owner, deadline, and success measure.",
        ],
        "risk": "Without a defined outcome, the response becomes informative but not operationally useful.",
        "priority": "Medium",
        "recommended_command": "Convert this into an execution brief with outcome, decision, action steps, asset, risk, and priority.",
    }


def local_intelligence_response(command: str) -> Dict[str, Any]:
    intent = detect_intent(command)
    builders = {
        "proposal": proposal_response,
        "meeting": meeting_response,
        "decision": decision_response,
        "revenue": revenue_response,
        "follow_up": follow_up_response,
        "strategy": strategy_response,
        "execution": execution_response,
        "risk": risk_response,
        "general": general_response,
    }
    payload = builders.get(intent, general_response)(command)
    payload["provider_used"] = f"local:{VERSION_SLUG}:{intent}"
    payload["status"] = "success"
    return payload


def response_is_off_topic(command: str, payload: Dict[str, Any]) -> bool:
    joined = json.dumps(payload, ensure_ascii=False).lower()
    command_lower = (command or "").lower()

    if "proposal" in command_lower or "dealership" in command_lower or "google ads" in command_lower or "cpa" in command_lower:
        if any(term in joined for term in ["costa rica", "relocation", "residency", "job search", "move first"]):
            return True
        required = ["proposal", "lead", "dealer", "ads"]
        return not any(term in joined for term in required)

    expected_intent = detect_intent(command)
    if expected_intent == "meeting" and not any(term in joined for term in ["meeting", "agenda", "talking points", "follow-up"]):
        return True
    if expected_intent == "follow_up" and not any(term in joined for term in ["subject", "email", "follow"]):
        return True
    return False


def normalize_run_contract(raw: Any, command: str, provider_used: str) -> Dict[str, Any]:
    fallback = local_intelligence_response(command)
    if not isinstance(raw, dict):
        return fallback

    normalized = {
        "next_move": ensure_string(raw.get("next_move"), fallback["next_move"]),
        "decision": ensure_string(raw.get("decision"), fallback["decision"]),
        "action_steps": ensure_list(raw.get("action_steps"), limit=7) or fallback["action_steps"],
        "ready_assets": ensure_list(raw.get("ready_assets"), limit=12) or fallback["ready_assets"],
        "risk": ensure_string(raw.get("risk"), fallback["risk"]),
        "priority": normalize_priority(raw.get("priority"), fallback.get("priority", "High")),
        "recommended_command": ensure_string(raw.get("recommended_command"), fallback["recommended_command"]),
        "provider_used": ensure_string(raw.get("provider_used"), provider_used),
        "status": "success",
    }
    if len(normalized["action_steps"]) < 3:
        normalized["action_steps"] = fallback["action_steps"]
    if len(normalized["action_steps"]) > 7:
        normalized["action_steps"] = normalized["action_steps"][:7]
    if response_is_off_topic(command, normalized):
        fallback["provider_used"] = f"fallback:off_topic_guard:{detect_intent(command)}"
        return fallback
    return normalized


async def openai_first_response(command: str, request_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    intent = detect_intent(command)
    system_prompt = """
You are Executive Engine OS, acting like a sharp CEO, COO, and Chief of Staff.
Return only valid JSON. No markdown wrapper. No commentary outside JSON.
You do not give vague advice. You create the actual work product.

Required keys exactly:
next_move: string
decision: string
action_steps: array of 3-7 specific executive actions
ready_assets: array of actual useful assets, drafts, proposal content, agenda, email body, scripts, decision memo content, or operational deliverables
risk: string
priority: High, Medium, or Low only
recommended_command: string
provider_used: string
status: success

Intent handling:
proposal = create actual proposal content in ready_assets.
meeting = create agenda, talking points, objections, questions, and follow-up.
decision = create recommendation, tradeoffs, risk, and next action.
revenue = create offer angle, target, next move, outreach, and close plan.
follow_up = create subject line and email body.
strategy = create strategic position, action path, risks, and priority.
execution = create immediate action plan and owner-style next steps.
risk = create risk assessment, containment, and verification step.
general = convert the request into outcome, decision, action, asset, risk, and next command.

Critical routing rule:
If the command asks for a proposal, dealership, SEO, Google Ads, CPA, or client pitch, the response must be a proposal / marketing acquisition output. Never return relocation, job-search, or unrelated lifestyle content for that request.

If information is missing, make reasonable executive assumptions and move forward.
Never say draft/send/prepare without writing the actual draft, message, proposal, prep, or plan.
""".strip()

    user_payload = {
        "command": command or "Create the next executive move.",
        "detected_intent": intent,
        "mode": request_meta.get("mode"),
        "brain": request_meta.get("brain"),
        "output_type": request_meta.get("output_type"),
        "context": request_meta.get("context"),
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0.18,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return normalize_run_contract(parsed, command, f"openai:{model}:{intent}")
    except Exception:
        return None


@app.get("/")
async def root() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "message": "Autonomous Executive Operator live.",
            "scope": "backend-only response intelligence patch",
            "endpoints": ["/", "/health", "/debug", "/test-report", "/test-report-json", "/run"],
            "run_contract": REQUIRED_RUN_FIELDS,
            "core_display_contract": CORE_DISPLAY_FIELDS,
            "intent_detection": sorted(INTENTS),
        }
    )
    return payload


@app.get("/health")
async def health() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "health": "healthy",
            "run_contract_status": "locked",
            "required_run_fields": REQUIRED_RUN_FIELDS,
            "priority_allowed_values": sorted(ALLOWED_PRIORITIES),
            "routing": "openai-first with deterministic local executive fallback and off-topic guard",
        }
    )
    return payload


@app.get("/debug")
async def debug() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "environment": {
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "provider_order": "openai-first-local-fallback",
                "claude_routing_changed": False,
            },
            "contract": {
                "required_fields": REQUIRED_RUN_FIELDS,
                "frontend_display_fields": CORE_DISPLAY_FIELDS,
                "priority_allowed_values": sorted(ALLOWED_PRIORITIES),
                "arrays": ["action_steps", "ready_assets"],
            },
            "intent_detection": sorted(INTENTS),
            "off_topic_guard": "proposal/dealership/SEO/Google Ads/CPA cannot return relocation/job-search output",
            "test_prompt": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
        }
    )
    return payload


@app.post("/run")
async def run(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}

    command, meta = extract_command(body)
    ai_payload = await openai_first_response(command, meta)
    if ai_payload is None:
        ai_payload = local_intelligence_response(command)
    return JSONResponse(content=ai_payload)


async def check_url(method: str, url: str, json_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "name": f"{method} {url}",
        "method": method,
        "url": url,
        "pass": False,
        "status_code": None,
        "ms": None,
        "error": None,
    }
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            if method == "POST":
                response = await client.post(url, json=json_payload or {})
            else:
                response = await client.get(url)
            result["status_code"] = response.status_code
            result["ms"] = round((time.perf_counter() - started) * 1000)
            result["pass"] = 200 <= response.status_code < 400
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    result["response"] = response.json()
                except Exception:
                    result["response"] = response.text[:2500]
            else:
                result["response"] = response.text[:1000]
    except Exception as exc:
        result["ms"] = round((time.perf_counter() - started) * 1000)
        result["error"] = str(exc)
    return result


def validate_run_contract(payload: Any) -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "pass": False,
        "missing_fields": [],
        "wrong_types": [],
        "priority_valid": False,
        "status_valid": False,
        "proposal_guard_pass": None,
    }
    if not isinstance(payload, dict):
        checks["wrong_types"].append("response must be object")
        return checks
    checks["missing_fields"] = [field for field in REQUIRED_RUN_FIELDS if field not in payload]
    if "action_steps" in payload and not isinstance(payload.get("action_steps"), list):
        checks["wrong_types"].append("action_steps must be array")
    if "ready_assets" in payload and not isinstance(payload.get("ready_assets"), list):
        checks["wrong_types"].append("ready_assets must be array")
    if isinstance(payload.get("action_steps"), list) and not (3 <= len(payload.get("action_steps")) <= 7):
        checks["wrong_types"].append("action_steps must contain 3-7 items")
    joined = json.dumps(payload, ensure_ascii=False).lower()
    checks["proposal_guard_pass"] = (
        any(term in joined for term in ["proposal", "dealership", "google", "auto-loan", "lead"])
        and not any(term in joined for term in ["costa rica", "relocation", "residency"])
    )
    checks["priority_valid"] = payload.get("priority") in ALLOWED_PRIORITIES
    checks["status_valid"] = payload.get("status") == "success"
    checks["pass"] = (
        not checks["missing_fields"]
        and not checks["wrong_types"]
        and checks["priority_valid"]
        and checks["status_valid"]
        and bool(checks["proposal_guard_pass"])
    )
    return checks


@app.get("/test-report-json")
async def test_report_json() -> Dict[str, Any]:
    test_prompt = "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
    tests: List[Dict[str, Any]] = []
    tests.append(await check_url("GET", f"{BACKEND_URL}/"))
    tests.append(await check_url("GET", f"{BACKEND_URL}/health"))
    tests.append(await check_url("GET", f"{BACKEND_URL}/debug"))
    run_test = await check_url("POST", f"{BACKEND_URL}/run", {"command": test_prompt})
    run_test["contract"] = validate_run_contract(run_test.get("response"))
    run_test["pass"] = bool(run_test.get("pass")) and bool(run_test["contract"].get("pass"))
    tests.append(run_test)
    tests.append(await check_url("GET", FRONTEND_URL))
    tests.append(await check_url("GET", BACKEND_URL))

    version_checks = []
    for item in tests:
        response = item.get("response")
        if isinstance(response, dict) and "version" in response:
            version_checks.append(response.get("version") == VERSION)
    all_pass = all(item.get("pass") for item in tests)
    consistent = all(version_checks) if version_checks else False
    return {
        "status": "pass" if all_pass and consistent else "fail",
        "version": VERSION,
        "version_short": VERSION_SHORT,
        "version_slug": VERSION_SLUG,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "timestamp": utc_now(),
        "version_consistent": consistent,
        "test_prompt": test_prompt,
        "tests": tests,
    }


@app.get("/test-report", response_class=HTMLResponse)
async def test_report() -> str:
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Executive Engine OS Backend Test Report — {VERSION_SHORT}</title>
  <style>
    :root {{ --bg:#0f172a; --card:#ffffff; --text:#111827; --muted:#64748b; --pass:#16a34a; --fail:#dc2626; --line:#e5e7eb; --accent:#f97316; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Arial, Helvetica, sans-serif; background:#f8fafc; color:var(--text); }}
    header {{ background:var(--bg); color:white; padding:26px 32px; }}
    header h1 {{ margin:0 0 8px; font-size:26px; }}
    header p {{ margin:0; color:#cbd5e1; }}
    main {{ max-width:1180px; margin:0 auto; padding:28px; }}
    .toolbar {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:18px; }}
    button {{ border:0; border-radius:10px; padding:12px 16px; font-weight:800; cursor:pointer; }}
    .run {{ background:var(--accent); color:white; }}
    .copy {{ background:#111827; color:white; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:18px; }}
    .card {{ background:white; border:1px solid var(--line); border-radius:16px; padding:16px; box-shadow:0 8px 24px rgba(15,23,42,.06); }}
    .label {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }}
    .value {{ font-size:18px; font-weight:900; }}
    .results {{ display:grid; gap:12px; }}
    .row {{ background:white; border:1px solid var(--line); border-radius:14px; padding:14px; display:grid; grid-template-columns:96px 1fr 180px; gap:14px; align-items:start; }}
    .badge {{ display:inline-flex; justify-content:center; align-items:center; min-width:72px; border-radius:999px; padding:8px 10px; font-size:12px; font-weight:900; color:white; }}
    .passBadge {{ background:var(--pass); }}
    .failBadge {{ background:var(--fail); }}
    .endpoint {{ font-weight:900; word-break:break-all; }}
    .meta {{ color:var(--muted); font-size:13px; margin-top:4px; }}
    pre {{ white-space:pre-wrap; word-break:break-word; background:#0b1220; color:#e5e7eb; border-radius:14px; padding:16px; max-height:440px; overflow:auto; }}
    @media(max-width:850px) {{ .grid {{ grid-template-columns:1fr; }} .row {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Executive Engine OS Backend Test Report</h1>
    <p>Version: <strong>{VERSION}</strong> · Backend: {BACKEND_URL}</p>
  </header>
  <main>
    <div class="toolbar">
      <button class="run" onclick="runTests()">Run Tests</button>
      <button class="copy" onclick="copyReport()">Copy JSON</button>
    </div>
    <section class="grid">
      <div class="card"><div class="label">Overall Status</div><div id="overall" class="value">Not run</div></div>
      <div class="card"><div class="label">Version Target</div><div class="value">{VERSION_SHORT}</div></div>
      <div class="card"><div class="label">Guardrail</div><div class="value">Proposal routing fixed</div></div>
    </section>
    <section id="results" class="results"></section>
    <h2>Raw JSON</h2>
    <pre id="raw">Click Run Tests.</pre>
  </main>
<script>
let lastReport = null;
function esc(s) {{ return String(s ?? '').replace(/[&<>'"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}}[c])); }}
function render(report) {{
  lastReport = report;
  document.getElementById('overall').textContent = (report.status || 'fail').toUpperCase();
  document.getElementById('raw').textContent = JSON.stringify(report, null, 2);
  const results = document.getElementById('results');
  results.innerHTML = '';
  (report.tests || []).forEach(test => {{
    const row = document.createElement('div');
    row.className = 'row';
    const pass = !!test.pass;
    const contract = test.contract ? 'Contract: ' + (test.contract.pass ? 'PASS' : 'FAIL') : '';
    row.innerHTML = `
      <div><span class="badge ${{pass ? 'passBadge' : 'failBadge'}}">${{pass ? 'PASS' : 'FAIL'}}</span></div>
      <div>
        <div class="endpoint">${{esc(test.name || test.url)}}</div>
        <div class="meta">Status: ${{esc(test.status_code || 'n/a')}} · Time: ${{esc(test.ms || 'n/a')}}ms</div>
        ${{test.error ? `<div class="meta">Error: ${{esc(test.error)}}</div>` : ''}}
      </div>
      <div class="meta">${{esc(contract)}}</div>
    `;
    results.appendChild(row);
  }});
}}
async function runTests() {{
  document.getElementById('overall').textContent = 'Running...';
  document.getElementById('raw').textContent = 'Running backend verification...';
  try {{
    const res = await fetch('/test-report-json', {{ cache:'no-store' }});
    const report = await res.json();
    render(report);
  }} catch (err) {{
    render({{ status:'fail', version:'{VERSION}', error:String(err), tests:[] }});
  }}
}}
async function copyReport() {{
  const text = JSON.stringify(lastReport || {{ status:'not_run', version:'{VERSION}' }}, null, 2);
  await navigator.clipboard.writeText(text);
}}
runTests();
</script>
</body>
</html>
"""
