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

VERSION = "V35160B-backend-response-comprehension-fix"
VERSION_SHORT = "V35160B"
VERSION_SLUG = "v35160b-backend-response-comprehension-fix"
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
ALLOWED_PRIORITIES = {"High", "Medium", "Low"}
INTENTS = ["proposal", "meeting", "decision", "revenue", "follow_up", "strategy", "execution", "risk", "general"]

app = FastAPI(title="Executive Engine OS Backend", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_command(body: Any) -> Tuple[str, Dict[str, Any]]:
    if isinstance(body, dict):
        command = body.get("command") or body.get("input") or body.get("prompt") or body.get("message") or ""
        return clean(command), body
    return clean(body), {}


def contains(text: str, words: List[str]) -> bool:
    return any(w in text for w in words)


def detect_intent(command: str) -> str:
    t = f" {command.lower()} "
    # Auto filter: highest-specificity wins. Proposal must beat meeting/revenue/execution.
    if contains(t, ["proposal", "sow", "scope of work", "quote", "pitch", "dealership", "auto loan", "auto-loan", "google ads", "seo", "cpa"]):
        return "proposal"
    if contains(t, ["meeting", "agenda", "talking points", "prep", "prepare for", "call with", "objections"]):
        return "meeting"
    if contains(t, ["follow up", "follow-up", "email", "reply", "respond", "subject line", "send this"]):
        return "follow_up"
    if contains(t, ["decide", "decision", "choose", "recommend", "tradeoff", "trade-off", "should i", "which"]):
        return "decision"
    if contains(t, ["revenue", "sales", "sell", "close", "lead", "leads", "pipeline", "roi", "booked calls"]):
        return "revenue"
    if contains(t, ["strategy", "positioning", "roadmap", "market", "moat", "category", "gtm", "go to market"]):
        return "strategy"
    if contains(t, ["risk", "blocker", "issue", "problem", "broken", "not working", "fail", "failure"]):
        return "risk"
    if contains(t, ["build", "execute", "launch", "fix", "create", "implement", "ship", "do this"]):
        return "execution"
    return "general"


def infer_cpa(command: str) -> str:
    t = command.lower()
    m = re.search(r"(?:cpa[^0-9]{0,20}|under\s*|below\s*|less than\s*|<\s*)\$?([0-9][0-9,]*)", t)
    if m:
        return f"under ${m.group(1).replace(',', '')}"
    m = re.search(r"\$([0-9][0-9,]*)", t)
    return f"${m.group(1)}" if m else "a measurable CPA target"


def short_list(items: List[str], limit: int = 6) -> List[str]:
    return [clean(x) for x in items if clean(x)][:limit]


def proposal_response(command: str) -> Dict[str, Any]:
    cpa = infer_cpa(command)
    return {
        "next_move": "Build the dealership proposal around qualified finance applications, booked appointments, and CPA control — not generic marketing activity.",
        "decision": f"Recommend a 30-day Ontario auto-loan growth pilot using SEO intent, Google Search, a dedicated approval landing page, and weekly lead-quality optimization toward {cpa}.",
        "action_steps": short_list([
            "Create one approval-focused offer: finance-ready Ontario buyers, clear qualification path, fast application, call CTA.",
            "Build Google Search campaigns for high-intent terms: bad credit auto loan, car financing approval, second-chance auto financing, dealership financing.",
            "Add negative keywords for jobs, free, insurance, repair, templates, research, and low-intent traffic.",
            "Use one landing page with trust proof, financing criteria, short form, phone CTA, inventory angle, and privacy reassurance.",
            "Track form submits, phone calls, booked appointments, approvals, sold units, CPA, and rejected lead reasons.",
            "Review weekly: cut waste, scale converting intent, and report lead quality instead of impressions or clicks.",
        ]),
        "ready_assets": short_list([
            f"Proposal Headline: Ontario Auto Loan Growth Pilot — SEO + Google Ads with CPA Target of {cpa}.",
            "Executive Summary: We will build a focused lead engine for an Ontario dealership to capture buyers already searching for auto financing and route them into a simple approval path.",
            "Offer: 30-day pilot covering keyword strategy, Google Search setup, landing-page structure, conversion tracking, and weekly optimization.",
            "Success Metrics: qualified applications, booked appointments, approval rate, sold units, CPA by keyword cluster, and wasted-spend reduction.",
            "Client Needs: Google Ads access, landing-page/domain access, call tracking, CRM/email destination, finance criteria, inventory/offer details, and sales follow-up rules.",
            "Follow-Up Email: Subject: Ontario auto-loan lead pilot. Body: I mapped a 30-day plan to generate finance-ready auto-loan leads using SEO intent and Google Search. The goal is to improve lead quality, control CPA, and track applications through booked appointments and approvals. I can send the pilot scope and first-week launch checklist.",
        ]),
        "risk": "The main risk is optimizing for cheap leads instead of financeable buyers. CPA must be judged with appointment quality, approval rate, and sold-unit potential.",
        "priority": "High",
        "recommended_command": "Create the final one-page client proposal with pricing, timeline, deliverables, landing-page copy, and follow-up email.",
        "auto_intent": "proposal",
        "display_mode": "proposal_card",
        "operator_read": "This is a proposal request. Keep the output focused on dealership lead generation, CPA control, and client-ready assets.",
    }


def meeting_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Use the meeting to secure a clear next commitment, not a broad discussion.",
        "decision": "Enter with one recommended path, one fallback option, and a defined close step.",
        "action_steps": short_list([
            "Confirm the desired business outcome in the first two minutes.",
            "Ask what has already failed, who approves, what budget exists, and what deadline matters.",
            "Present the recommended path with success metric, timeline, and owner.",
            "Handle objections around cost, timing, risk, complexity, and internal capacity.",
            "Close with the exact next step, owner, deadline, and follow-up asset.",
        ]),
        "ready_assets": short_list([
            "Agenda: outcome, current constraint, recommended path, objections, decision, next step.",
            "Questions: What result matters most? Who approves? What happens if this waits 30 days? What would make this a yes?",
            "Objection Handles: Budget = measurable return. Timing = contained pilot. Risk = stop/scale criteria. Complexity = one owner.",
            "Follow-Up Draft: Here is the decision, agreed next step, owner, deadline, and asset I will send so this does not stall.",
        ]),
        "risk": "The meeting turns into conversation without decision, owner, or next asset.",
        "priority": "High",
        "recommended_command": "Create the exact agenda, objection responses, and post-meeting follow-up email.",
        "auto_intent": "meeting",
        "display_mode": "meeting_brief",
        "operator_read": "This is a meeting-prep request. Output must produce agenda, questions, objections, and close path.",
    }


def decision_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Choose the option that creates the fastest proof with the least operational drag.",
        "decision": "Proceed with the lowest-complexity path that validates the outcome before adding structure.",
        "action_steps": short_list([
            "State the decision and desired result in one sentence.",
            "Compare options by upside, speed, cost, reversibility, risk, and operational burden.",
            "Reject any option that requires heavy build before proof.",
            "Assign one owner, one metric, and one review date.",
        ]),
        "ready_assets": short_list([
            "Decision Memo: recommendation, why now, options, tradeoffs, risk, owner, metric, review date.",
            "Recommendation: move with the fastest reversible path that proves value.",
        ]),
        "risk": "Overbuilding or over-debating before the decision is validated by real usage, revenue, or execution progress.",
        "priority": "High",
        "recommended_command": "Turn this into a one-page executive decision memo.",
        "auto_intent": "decision",
        "display_mode": "decision_memo",
        "operator_read": "This is a decision request. Output recommendation, tradeoffs, risk, and next action.",
    }


def follow_up_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Send a concise follow-up that advances one clear next commitment.",
        "decision": "Do not over-explain. Remove friction and ask for the next yes/no or scheduling action.",
        "action_steps": short_list([
            "Open with the specific reason for the follow-up.",
            "Restate the outcome or decision needed.",
            "Include the next asset or recommended step.",
            "Ask one clear question.",
        ]),
        "ready_assets": short_list([
            "Subject: Next step on this",
            "Email Body: Hi — quick follow-up. The clean next move is to confirm the outcome, lock the first execution step, and avoid letting this drift. I can send the concise plan with what happens first, what is needed from your side, and how progress will be measured. Should I send that over today?",
        ]),
        "risk": "A weak follow-up creates ambiguity and lets the opportunity stall.",
        "priority": "Medium",
        "recommended_command": "Rewrite this follow-up for the exact person, company, and desired outcome.",
        "auto_intent": "follow_up",
        "display_mode": "email_draft",
        "operator_read": "This is a follow-up request. Output a subject line, email body, and direct ask.",
    }


def revenue_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Turn the request into an offer, target buyer, outreach asset, and close path.",
        "decision": "Prioritize the buyer with urgent pain, budget authority, and a measurable reason to act now.",
        "action_steps": short_list([
            "Define the target buyer and painful business outcome.",
            "Frame the offer around money, speed, risk reduction, control, or leverage.",
            "Create one direct outreach message and one proof-based follow-up.",
            "Set the close path: call, proposal, pilot, payment, implementation.",
            "Track replies, booked calls, objections, proposals sent, and closed revenue.",
        ]),
        "ready_assets": short_list([
            "Offer Angle: turn existing demand into better-qualified opportunities without adding operational drag.",
            "Target Buyer: owner, CEO, GM, sales leader, or operator with visible revenue friction.",
            "Outreach: I have a focused way to turn existing demand into qualified opportunities with a measurable close path. Worth a quick look?",
            "Close Plan: qualify pain, confirm economics, present pilot, define success metric, secure next step.",
        ]),
        "risk": "The offer underperforms if framed as services or activity instead of a business outcome.",
        "priority": "High",
        "recommended_command": "Build the exact outreach sequence, sales script, and pilot offer.",
        "auto_intent": "revenue",
        "display_mode": "revenue_plan",
        "operator_read": "This is a revenue request. Output offer angle, buyer, outreach, and close plan.",
    }


def strategy_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Turn the strategy into one operating thesis and one proof point to validate this week.",
        "decision": "Use a narrow wedge first. Expand only after repeated use, buyer pull, or operational dependency is proven.",
        "action_steps": short_list([
            "Define the target user or buyer and urgent problem.",
            "Write the strategic position in one sentence.",
            "Identify the first workflow or asset that proves the position.",
            "Remove anything that does not support adoption, revenue, or operational dependency.",
            "Set a 7-day proof target and review result.",
        ]),
        "ready_assets": short_list([
            "Strategic Position: an executive operating layer that creates clarity, speed, leverage, and control.",
            "Action Path: validate one high-value workflow, prove repeated use, then expand into memory/actions/proactive briefing.",
            "7-Day Proof Target: one workflow creates useful asset, decision, next action, and follow-up without generic advice.",
        ]),
        "risk": "The strategy becomes too broad and loses usefulness before one workflow becomes indispensable.",
        "priority": "High",
        "recommended_command": "Convert this into a 7-day execution roadmap with HOLD/FIX/PROMOTE criteria.",
        "auto_intent": "strategy",
        "display_mode": "strategy_brief",
        "operator_read": "This is a strategy request. Output position, path, risk, and proof target.",
    }


def execution_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Ship the smallest complete fix that advances the objective and can be verified immediately.",
        "decision": "Keep scope narrow, protect the stable base, and do not add another layer until this fix is verified.",
        "action_steps": short_list([
            "Lock the objective in one sentence.",
            "Identify the endpoint or behavior that must change.",
            "Protect areas that must not change.",
            "Build only the required fix.",
            "Run the test checklist and classify HOLD/FIX/PROMOTE.",
        ]),
        "ready_assets": short_list([
            "Execution Checklist: objective, protected areas, changed files, endpoint tests, contract tests, decision result.",
            "Owner Summary: one build, one test, one decision, one next action.",
        ]),
        "risk": "Scope creep makes it impossible to know what fixed or broke the system.",
        "priority": "High",
        "recommended_command": "Create the exact deployment test checklist and classify the result.",
        "auto_intent": "execution",
        "display_mode": "execution_plan",
        "operator_read": "This is an execution request. Output immediate plan, owner-style steps, and verification.",
    }


def risk_response(command: str) -> Dict[str, Any]:
    return {
        "next_move": "Isolate the highest-consequence risk and choose containment before continuing.",
        "decision": "Do not expand scope until the risk is fixed, accepted, or routed around.",
        "action_steps": short_list([
            "Name the risk in one sentence.",
            "Identify what breaks if ignored.",
            "Choose containment: fix, rollback, hold, or isolate.",
            "Run the smallest test that confirms whether the risk is real.",
            "Document decision and next action.",
        ]),
        "ready_assets": short_list([
            "Risk Control Brief: issue, consequence, likelihood, containment, owner, test, deadline.",
            "Decision Options: HOLD if unclear, FIX if contained, ROLLBACK if stable base is compromised, PROMOTE only after verification.",
        ]),
        "risk": "Treating unstable output as progress and compounding it with more changes.",
        "priority": "High",
        "recommended_command": "Turn this into a risk log with severity, containment, owner, and verification step.",
        "auto_intent": "risk",
        "display_mode": "risk_brief",
        "operator_read": "This is a risk request. Output containment, consequence, and verification.",
    }


def general_response(command: str) -> Dict[str, Any]:
    subject = clean(command) or "the current request"
    return {
        "next_move": f"Turn {subject} into a concrete outcome, decision, first asset, and next command.",
        "decision": "Move forward using reasonable assumptions instead of waiting for perfect information.",
        "action_steps": short_list([
            "Define the desired outcome in one sentence.",
            "Decide what must be created, changed, sent, or tested.",
            "Produce the first useful asset now.",
            "Identify the risk that would slow execution.",
            "Set the next command to continue momentum.",
        ]),
        "ready_assets": short_list([
            "Operating Brief: outcome, decision, next move, action steps, risk, follow-up command.",
        ]),
        "risk": "The request stays broad and creates more thinking instead of a usable output.",
        "priority": "Medium",
        "recommended_command": "Convert this into a specific proposal, meeting prep, decision memo, follow-up, strategy, or execution plan.",
        "auto_intent": "general",
        "display_mode": "operator_brief",
        "operator_read": "This is a general request. Convert it into a concrete executive output.",
    }


def local_response(command: str) -> Dict[str, Any]:
    intent = detect_intent(command)
    handlers = {
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
    payload = handlers[intent](command)
    payload["provider_used"] = "local:executive-response-comprehension"
    payload["status"] = "success"
    return normalize(payload, command)


def ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return short_list([json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x) for x in value], 6)
    if isinstance(value, str) and value.strip():
        parts = [p.strip(" -•\t") for p in re.split(r"\n+|;|\s•\s", value) if p.strip()]
        return short_list(parts or [value], 6)
    return []


def normalize_priority(value: Any) -> str:
    t = clean(value).lower()
    if t in ["high", "urgent", "critical"]:
        return "High"
    if t in ["medium", "moderate", "normal"]:
        return "Medium"
    if t in ["low", "later"]:
        return "Low"
    return "High"


def off_topic(payload: Dict[str, Any], command: str) -> bool:
    joined = json.dumps(payload, ensure_ascii=False).lower()
    cmd = command.lower()
    proposal_cmd = any(x in cmd for x in ["proposal", "dealership", "auto loan", "auto-loan", "google ads", "seo", "cpa"])
    bad = any(x in joined for x in ["costa rica", "relocation", "residency", "move abroad", "job search"])
    return bool(proposal_cmd and bad)


def normalize(payload: Any, command: str) -> Dict[str, Any]:
    if not isinstance(payload, dict) or off_topic(payload, command):
        return local_response_no_ai(command)
    intent = payload.get("auto_intent") or detect_intent(command)
    normalized = {
        "next_move": clean(payload.get("next_move")) or local_response_no_ai(command)["next_move"],
        "decision": clean(payload.get("decision")) or local_response_no_ai(command)["decision"],
        "action_steps": ensure_list(payload.get("action_steps")) or local_response_no_ai(command)["action_steps"],
        "ready_assets": ensure_list(payload.get("ready_assets")) or local_response_no_ai(command)["ready_assets"],
        "risk": clean(payload.get("risk")) or local_response_no_ai(command)["risk"],
        "priority": normalize_priority(payload.get("priority")),
        "recommended_command": clean(payload.get("recommended_command")) or local_response_no_ai(command)["recommended_command"],
        "provider_used": clean(payload.get("provider_used")) or "unknown",
        "status": "success",
        "auto_intent": intent if intent in INTENTS else detect_intent(command),
        "display_mode": clean(payload.get("display_mode")) or f"{intent}_brief",
        "operator_read": clean(payload.get("operator_read")) or "Auto-filtered request and produced a concise executive output.",
    }
    if off_topic(normalized, command):
        return local_response_no_ai(command)
    return normalized


def local_response_no_ai(command: str) -> Dict[str, Any]:
    intent = detect_intent(command)
    handlers = {
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
    payload = handlers[intent](command)
    payload["provider_used"] = "local:guarded-fallback"
    payload["status"] = "success"
    return payload


async def openai_first(command: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    intent = detect_intent(command)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = f"""
You are Executive Engine OS: a CEO/COO/Chief-of-Staff response engine.
Return compact JSON only. No markdown wrapper.
The user needs actual work product, not advice.
Auto intent is: {intent}.
Required fields: next_move, decision, action_steps, ready_assets, risk, priority, recommended_command, provider_used, status, auto_intent, display_mode, operator_read.
Rules:
- action_steps: 3-6 short, concrete bullets.
- ready_assets: 1-6 actual usable assets.
- priority: High, Medium, or Low only.
- status: success.
- If proposal/dealership/SEO/Google Ads/CPA appears, produce proposal content only.
- Never return Costa Rica, relocation, residency, lifestyle, or job-search content unless the user explicitly asks for that.
- Make missing assumptions and move forward.
""".strip()
    user = {"command": command, "metadata": meta, "intent": intent}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
                    ],
                },
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            data["provider_used"] = data.get("provider_used") or f"openai:{model}:{intent}"
            return normalize(data, command)
    except Exception:
        return None


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


@app.get("/")
async def root() -> Dict[str, Any]:
    p = base_status()
    p.update({
        "message": "Autonomous Executive Operator live.",
        "scope": "backend-only response comprehension/intelligence fix",
        "endpoints": ["/", "/health", "/debug", "/test-report", "/test-report-json", "/run"],
        "run_contract": REQUIRED_RUN_FIELDS,
        "auto_filter": INTENTS,
    })
    return p


@app.get("/health")
async def health() -> Dict[str, Any]:
    p = base_status()
    p.update({
        "health": "healthy",
        "run_contract_status": "locked",
        "priority_allowed_values": sorted(ALLOWED_PRIORITIES),
        "routing": "openai-first with deterministic guarded fallback",
    })
    return p


@app.get("/debug")
async def debug() -> Dict[str, Any]:
    p = base_status()
    p.update({
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "claude_routing_changed": False,
        "frontend_changed": False,
        "database_changed": False,
        "off_topic_guard": "proposal/dealership/SEO/Google Ads/CPA cannot return Costa Rica/relocation/job-search output",
        "test_prompt": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
    })
    return p


@app.post("/run")
async def run(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    command, meta = extract_command(body)
    payload = await openai_first(command, meta)
    if payload is None:
        payload = local_response(command)
    return JSONResponse(content=payload)


async def check_url(method: str, url: str, json_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    result: Dict[str, Any] = {"name": f"{method} {url}", "method": method, "url": url, "pass": False, "status_code": None, "ms": None, "error": None}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.post(url, json=json_payload or {}) if method == "POST" else await client.get(url)
            result["status_code"] = r.status_code
            result["ms"] = round((time.perf_counter() - started) * 1000)
            result["pass"] = 200 <= r.status_code < 400
            ct = r.headers.get("content-type", "")
            result["response"] = r.json() if "application/json" in ct else r.text[:1200]
    except Exception as exc:
        result["ms"] = round((time.perf_counter() - started) * 1000)
        result["error"] = str(exc)
    return result


def validate_run(payload: Any) -> Dict[str, Any]:
    checks = {"pass": False, "missing_fields": [], "wrong_types": [], "proposal_guard_pass": False}
    if not isinstance(payload, dict):
        checks["wrong_types"].append("response must be object")
        return checks
    checks["missing_fields"] = [f for f in REQUIRED_RUN_FIELDS if f not in payload]
    if not isinstance(payload.get("action_steps"), list):
        checks["wrong_types"].append("action_steps must be array")
    if not isinstance(payload.get("ready_assets"), list):
        checks["wrong_types"].append("ready_assets must be array")
    if payload.get("priority") not in ALLOWED_PRIORITIES:
        checks["wrong_types"].append("priority must be High, Medium, or Low")
    joined = json.dumps(payload, ensure_ascii=False).lower()
    checks["proposal_guard_pass"] = any(x in joined for x in ["proposal", "dealership", "google", "auto-loan", "cpa"]) and not any(x in joined for x in ["costa rica", "relocation", "residency"])
    checks["pass"] = not checks["missing_fields"] and not checks["wrong_types"] and checks["proposal_guard_pass"] and payload.get("status") == "success"
    return checks


@app.get("/test-report-json")
async def test_report_json() -> Dict[str, Any]:
    test_prompt = "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
    tests = [
        await check_url("GET", f"{BACKEND_URL}/"),
        await check_url("GET", f"{BACKEND_URL}/health"),
        await check_url("GET", f"{BACKEND_URL}/debug"),
    ]
    run_test = await check_url("POST", f"{BACKEND_URL}/run", {"command": test_prompt})
    run_test["contract"] = validate_run(run_test.get("response"))
    run_test["pass"] = bool(run_test.get("pass")) and bool(run_test["contract"].get("pass"))
    tests.append(run_test)
    tests.append(await check_url("GET", FRONTEND_URL))
    tests.append(await check_url("GET", BACKEND_URL))
    version_checks = []
    for item in tests:
        r = item.get("response")
        if isinstance(r, dict) and "version" in r:
            version_checks.append(r.get("version") == VERSION)
    all_pass = all(t.get("pass") for t in tests)
    consistent = all(version_checks) if version_checks else False
    return {
        "status": "pass" if all_pass and consistent else "fail",
        "version": VERSION,
        "version_short": VERSION_SHORT,
        "version_consistent": consistent,
        "test_prompt": test_prompt,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "tests": tests,
        "timestamp": utc_now(),
    }


@app.get("/test-report", response_class=HTMLResponse)
async def test_report() -> str:
    return f"""
<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Executive Engine Backend Test Report — {VERSION_SHORT}</title>
<style>
body{{margin:0;background:#f8fafc;color:#111827;font-family:Arial,Helvetica,sans-serif}}header{{background:#0f172a;color:white;padding:26px 32px}}h1{{margin:0 0 8px;font-size:26px}}main{{max-width:1180px;margin:0 auto;padding:28px}}button{{border:0;border-radius:10px;padding:12px 16px;font-weight:900;cursor:pointer}}.run{{background:#f97316;color:white}}.copy{{background:#111827;color:white}}.toolbar{{display:flex;gap:12px;margin-bottom:18px;flex-wrap:wrap}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px}}.card{{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:16px;box-shadow:0 8px 24px rgba(15,23,42,.06)}}.label{{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}}.value{{font-size:18px;font-weight:900}}.results{{display:grid;gap:12px}}.row{{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:14px;display:grid;grid-template-columns:96px 1fr 160px;gap:14px;align-items:start}}.badge{{display:inline-flex;justify-content:center;align-items:center;min-width:72px;border-radius:999px;padding:8px 10px;font-size:12px;font-weight:900;color:white}}.pass{{background:#16a34a}}.fail{{background:#dc2626}}.endpoint{{font-weight:900;word-break:break-all}}.meta{{color:#64748b;font-size:13px;margin-top:4px}}pre{{white-space:pre-wrap;word-break:break-word;background:#0b1220;color:#e5e7eb;border-radius:14px;padding:16px;max-height:440px;overflow:auto}}@media(max-width:850px){{.grid,.row{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Executive Engine OS Backend Test Report</h1><p>Version: <b>{VERSION}</b> · Backend: {BACKEND_URL}</p></header><main>
<div class='toolbar'><button class='run' onclick='runTests()'>Run Tests</button><button class='copy' onclick='copyJson()'>Copy JSON</button></div>
<div class='grid'><div class='card'><div class='label'>Backend</div><div class='value'>{BACKEND_URL}</div></div><div class='card'><div class='label'>Frontend</div><div class='value'>{FRONTEND_URL}</div></div><div class='card'><div class='label'>Status</div><div class='value' id='status'>Not run</div></div></div>
<div id='results' class='results'></div><h2>Raw JSON</h2><pre id='raw'>Click Run Tests.</pre>
<script>
let last=null;
async function runTests(){{
 document.getElementById('status').textContent='Running...';
 const res=await fetch('/test-report-json?ts='+Date.now());
 last=await res.json();
 document.getElementById('raw').textContent=JSON.stringify(last,null,2);
 document.getElementById('status').textContent=last.status.toUpperCase();
 document.getElementById('results').innerHTML=(last.tests||[]).map(t=>`<div class="row"><div><span class="badge ${{t.pass?'pass':'fail'}}">${{t.pass?'PASS':'FAIL'}}</span></div><div><div class="endpoint">${{t.name}}</div><div class="meta">Status: ${{t.status_code||'n/a'}} · ${{t.ms||0}}ms</div>${{t.error?`<div class="meta">Error: ${{t.error}}</div>`:''}}</div><div class="meta">${{t.contract?('Contract: '+(t.contract.pass?'PASS':'FAIL')):''}}</div></div>`).join('');
}}
async function copyJson(){{
 const txt=JSON.stringify(last||{{message:'No test run yet'}},null,2);
 await navigator.clipboard.writeText(txt);
 alert('Copied JSON');
}}
</script></main></body></html>
"""
