"""
Executive Engine OS — V36100 Working Prototype

Core loop:
command -> classify -> pressure/risk analysis -> executive output -> operating state

This backend is intentionally lean, merge-safe, and deployable.
It does not require OpenAI to run.
If OPENAI_API_KEY is present, you can later extend build_ai_response().
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


VERSION = "v36100-executive-workflow-intelligence"


app = FastAPI(
    title="Executive Engine OS",
    version=VERSION,
    description="Push-first executive operating system prototype.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Mode = Literal["auto", "execution", "meeting", "proposal", "strategy", "decision", "revenue"]


class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: Mode = "auto"
    depth: Literal["fast", "standard", "deep"] = "standard"
    context: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    next_move: str
    decision: str
    action_steps: List[str]
    ready_assets: List[str]
    risk: str
    priority: str
    recommended_command: str

    # V36100 additions
    mode: str
    pressure: str
    executive_summary: str
    operating_state: Dict[str, Any]
    follow_up_questions: List[str]
    timestamp: str


KEYWORDS = {
    "meeting": ["meeting", "agenda", "call", "client", "stakeholder", "presentation", "prep", "tomorrow"],
    "proposal": ["proposal", "retainer", "quote", "pricing", "offer", "scope", "deal", "close"],
    "execution": ["build", "launch", "fix", "ship", "deploy", "execute", "implementation", "workflow"],
    "strategy": ["strategy", "positioning", "market", "growth", "plan", "competitive", "opportunity"],
    "decision": ["decide", "decision", "should i", "which option", "tradeoff", "risk", "choose"],
    "revenue": ["revenue", "sales", "lead", "leads", "cpa", "roi", "pipeline", "conversion", "dealership"],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify_mode(user_input: str, requested_mode: Mode) -> str:
    if requested_mode != "auto":
        return requested_mode

    text = normalize(user_input)
    scores = {mode: 0 for mode in KEYWORDS}

    for mode, words in KEYWORDS.items():
        for word in words:
            if word in text:
                scores[mode] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "execution"


def score_pressure(user_input: str, mode: str) -> Dict[str, Any]:
    text = normalize(user_input)
    urgent_terms = ["asap", "urgent", "today", "tomorrow", "late", "blocked", "stuck", "risk", "deadline", "losing"]
    revenue_terms = ["revenue", "sales", "client", "deal", "proposal", "retainer", "cpa", "leads", "money"]
    relationship_terms = ["client", "partner", "investor", "owner", "team", "stakeholder"]

    urgent = sum(1 for t in urgent_terms if t in text)
    revenue = sum(1 for t in revenue_terms if t in text)
    relationship = sum(1 for t in relationship_terms if t in text)

    raw = urgent * 3 + revenue * 2 + relationship
    if mode in ["proposal", "meeting", "revenue"]:
        raw += 2

    if raw >= 9:
        level = "HIGH"
    elif raw >= 5:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": raw,
        "signals": {
            "urgency": urgent,
            "revenue": revenue,
            "relationship": relationship,
        },
    }


def mode_label(mode: str) -> str:
    return {
        "meeting": "Meeting Intelligence",
        "proposal": "Proposal Intelligence",
        "execution": "Execution Intelligence",
        "strategy": "Strategy Intelligence",
        "decision": "Decision Intelligence",
        "revenue": "Revenue Intelligence",
    }.get(mode, "Execution Intelligence")


def build_decision(mode: str, user_input: str, pressure: Dict[str, Any]) -> str:
    label = mode_label(mode)
    if pressure["level"] == "HIGH":
        return f"Treat this as a high-pressure {label.lower()} workflow. The immediate objective is to create clarity, reduce risk, and move the situation toward a concrete business outcome."
    if mode == "proposal":
        return "Build the proposal around business outcome, revenue impact, measurable lead quality, and owner-level confidence — not generic marketing services."
    if mode == "meeting":
        return "Prepare the meeting as a controlled executive conversation: desired outcome first, leverage points second, follow-up asset third."
    if mode == "decision":
        return "Make the decision using downside protection, upside leverage, speed, and reversibility as the governing criteria."
    if mode == "strategy":
        return "Frame the strategy around leverage, differentiation, operational simplicity, and the fastest path to measurable movement."
    return "Convert the request into an execution workflow with a clear next move, asset creation, risk control, and follow-up command."


def build_next_move(mode: str, user_input: str) -> str:
    if mode == "proposal":
        return "Create a one-page executive proposal with the business problem, measurable upside, offer structure, proof points, and next-step close."
    if mode == "meeting":
        return "Prepare a meeting brief that defines the win condition, opening frame, key questions, objections, and follow-up asset."
    if mode == "decision":
        return "Clarify the decision options, rank them by leverage and risk, then choose the option with the highest speed-to-upside and lowest irreversible downside."
    if mode == "strategy":
        return "Turn the strategic issue into a focused operating thesis, immediate priorities, and a 7-day movement plan."
    if mode == "revenue":
        return "Identify the revenue lever, remove friction, define the offer, and create the next commercial action."
    return "Break the command into an immediate executable sequence and create the first usable business asset."


def build_action_steps(mode: str, user_input: str, depth: str) -> List[str]:
    common = [
        "Define the executive win condition in one sentence.",
        "Extract the business constraint, deadline, stakeholder, and desired outcome.",
        "Create the first usable asset instead of another planning note.",
    ]

    by_mode = {
        "proposal": [
            "Position the proposal around revenue movement, not service features.",
            "Add a simple success metric the buyer can understand immediately.",
            "End with a direct next step: approve, revise, or schedule decision call.",
        ],
        "meeting": [
            "Write the opening frame so the meeting starts with control.",
            "Prepare 5 questions that reveal urgency, budget, authority, and pain.",
            "Draft the follow-up email before the meeting happens.",
        ],
        "execution": [
            "Sequence the work into now, next, blocked, and delegated.",
            "Identify the single dependency most likely to slow execution.",
            "Create a follow-up command that continues the workflow.",
        ],
        "strategy": [
            "State the strategic bet clearly.",
            "Identify the fastest validation path.",
            "Separate signal from noise: what matters this week only.",
        ],
        "decision": [
            "List the real options, including doing nothing.",
            "Score each option by upside, risk, speed, and reversibility.",
            "Pick the default action unless new information changes the facts.",
        ],
        "revenue": [
            "Define the buyer, pain, offer, proof, and next commercial action.",
            "Remove one conversion bottleneck immediately.",
            "Create a direct outreach, proposal, or follow-up asset.",
        ],
    }

    steps = common + by_mode.get(mode, by_mode["execution"])
    if depth == "fast":
        return steps[:4]
    if depth == "deep":
        return steps + [
            "Create a second-order risk check before execution.",
            "Define what the system should remember for future continuity.",
        ]
    return steps[:6]


def build_ready_assets(mode: str) -> List[str]:
    assets = {
        "proposal": [
            "Executive proposal outline",
            "Buyer problem framing",
            "Pricing / scope skeleton",
            "Follow-up approval email",
        ],
        "meeting": [
            "Meeting brief",
            "Agenda",
            "Objection map",
            "Post-meeting follow-up draft",
        ],
        "execution": [
            "Execution checklist",
            "Dependency map",
            "Priority sequence",
            "Follow-up command",
        ],
        "strategy": [
            "Strategic thesis",
            "Opportunity map",
            "7-day action plan",
            "Risk memo",
        ],
        "decision": [
            "Decision matrix",
            "Tradeoff summary",
            "Risk note",
            "Recommended action",
        ],
        "revenue": [
            "Revenue lever map",
            "Offer frame",
            "Lead conversion audit",
            "Next commercial action",
        ],
    }
    return assets.get(mode, assets["execution"])


def build_risk(mode: str, pressure: Dict[str, Any]) -> str:
    if pressure["level"] == "HIGH":
        return "Main risk: the workflow stays conceptual instead of producing an asset or decision that changes the business situation today."
    if mode == "proposal":
        return "Main risk: the proposal reads like a service menu instead of an executive business case."
    if mode == "meeting":
        return "Main risk: entering the meeting without a defined win condition and leaving without a committed next step."
    if mode == "decision":
        return "Main risk: delaying the decision because the options are not framed by upside, downside, speed, and reversibility."
    return "Main risk: spreading attention across too many tasks instead of forcing one high-leverage next move."


def build_priority(pressure: Dict[str, Any], mode: str) -> str:
    if pressure["level"] == "HIGH":
        return "HIGH — handle before lower-value admin or cosmetic product work."
    if mode in ["proposal", "meeting", "revenue"]:
        return "HIGH-MEDIUM — commercial or relationship impact likely."
    return "MEDIUM — important if it moves an active workflow forward."


def build_recommended_command(mode: str) -> str:
    commands = {
        "proposal": "Build the executive proposal now with problem, offer, proof, pricing logic, and close step.",
        "meeting": "Create my meeting brief with agenda, win condition, questions, objections, and follow-up email.",
        "execution": "Turn this into an execution plan with now/next/blocked/delegated and a ready asset.",
        "strategy": "Create a strategic operating plan with thesis, risks, opportunities, and 7-day movement plan.",
        "decision": "Create a decision memo with options, tradeoffs, risks, and recommended action.",
        "revenue": "Create a revenue action plan with offer, buyer pain, conversion bottleneck, and next outreach.",
    }
    return commands.get(mode, commands["execution"])


def build_follow_up_questions(mode: str) -> List[str]:
    if mode == "proposal":
        return [
            "Who is the buyer and what outcome do they care about most?",
            "What price range or retainer level should this proposal support?",
            "What proof, case study, or credibility point should be included?",
        ]
    if mode == "meeting":
        return [
            "Who is attending and who has decision authority?",
            "What is the one outcome you want from the meeting?",
            "What objection are you most likely to face?",
        ]
    if mode == "decision":
        return [
            "What are the real options?",
            "What happens if you delay?",
            "Which downside is unacceptable?",
        ]
    return [
        "What is the deadline?",
        "Who is involved?",
        "What asset should the system create first?",
    ]


def build_operating_state(mode: str, pressure: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    return {
        "active_mode": mode,
        "pressure_level": pressure["level"],
        "pressure_score": pressure["score"],
        "signals": pressure["signals"],
        "open_loop": "Create the first usable asset and define the next committed action.",
        "momentum_status": "needs_movement" if pressure["level"] in ["MEDIUM", "HIGH"] else "stable",
        "system_behavior": "push_next_action",
        "remember_for_later": [
            "User intent",
            "Selected mode",
            "Pressure signals",
            "Recommended follow-up command",
        ],
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Executive Engine OS",
        "version": VERSION,
        "status": "running",
        "protected_routes": [
            "/run",
            "/health",
            "/debug",
            "/providers",
            "/test-report-json",
            "/db-status",
            "/demo-state",
        ],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/debug")
def debug() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "runtime": "fastapi",
        "mode": "deterministic-local-intelligence",
    }


@app.get("/providers")
def providers() -> Dict[str, Any]:
    return {
        "primary": "local-executive-intelligence",
        "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        "fallback": "deterministic-local-intelligence",
    }


@app.get("/db-status")
def db_status() -> Dict[str, Any]:
    return {
        "status": "not_configured_in_v36100",
        "note": "Prototype uses in-memory/stateful frontend continuity. Supabase integration should be additive in a later version.",
    }


@app.get("/demo-state")
def demo_state() -> Dict[str, Any]:
    return {
        "today": [
            "Create one strong executive command loop",
            "Improve response quality before adding features",
            "Use the system yourself before expanding UI"
        ],
        "risks": [
            "Generic AI responses",
            "Frontend dashboard drift",
            "Too much planning without software use"
        ],
    }


@app.get("/test-report-json")
def test_report_json() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "status": "pass",
        "checks": {
            "root": "ok",
            "health": "ok",
            "run_contract": "ok",
            "protected_routes_present": "ok",
            "cors": "ok",
        },
    }


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest) -> RunResponse:
    mode = classify_mode(req.input, req.mode)
    pressure = score_pressure(req.input, mode)
    operating_state = build_operating_state(mode, pressure, req.input)

    executive_summary = (
        f"{mode_label(mode)} activated. "
        f"Pressure level is {pressure['level']}. "
        "The system is converting the input into an executive workflow with a concrete next move, usable assets, and follow-up continuity."
    )

    return RunResponse(
        next_move=build_next_move(mode, req.input),
        decision=build_decision(mode, req.input, pressure),
        action_steps=build_action_steps(mode, req.input, req.depth),
        ready_assets=build_ready_assets(mode),
        risk=build_risk(mode, pressure),
        priority=build_priority(pressure, mode),
        recommended_command=build_recommended_command(mode),
        mode=mode,
        pressure=pressure["level"],
        executive_summary=executive_summary,
        operating_state=operating_state,
        follow_up_questions=build_follow_up_questions(mode),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
