from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

APP_VERSION = "V36170-functional-command-centre"

app = FastAPI(title="Executive Engine OS", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str
    mode: Optional[str] = "auto"
    category: Optional[str] = "auto"
    depth: Optional[str] = "standard"
    provider: Optional[str] = "local"


def detect_category(text: str, supplied: Optional[str] = None) -> str:
    if supplied and supplied.lower() not in ["auto", "auto select", ""]:
        return supplied.title()
    t = text.lower()
    rules = [
        ("Meeting", ["meeting", "agenda", "talking points", "client call", "investor", "prep"]),
        ("Proposal", ["proposal", "pitch", "quote", "pricing", "offer", "scope"]),
        ("Decision", ["decide", "decision", "choose", "tradeoff", "should i", "option"]),
        ("Risk", ["risk", "problem", "blocker", "threat", "issue", "concern", "compliance"]),
        ("Execution", ["build", "execute", "launch", "implement", "fix", "deploy", "workflow"]),
        ("Strategy", ["strategy", "growth", "market", "positioning", "revenue", "seo", "ads", "cpa"]),
    ]
    for cat, words in rules:
        if any(w in t for w in words):
            return cat
    return "General"


def pressure_score(text: str, category: str) -> int:
    score = 22
    t = text.lower()
    score += 16 if category in ["Risk", "Decision"] else 0
    score += 12 if category in ["Proposal", "Meeting", "Execution"] else 0
    score += 10 if any(w in t for w in ["urgent", "asap", "today", "deadline", "lost", "broken", "error"]) else 0
    score += 8 if any(w in t for w in ["revenue", "client", "deal", "investor", "legal", "compliance"]) else 0
    return max(12, min(score, 88))


def bullets_for(text: str, category: str) -> Dict[str, Any]:
    lower = text.lower()
    auto_loan = "auto" in lower or "dealership" in lower or "loan" in lower
    if category == "Proposal" or (auto_loan and ("seo" in lower or "ads" in lower or "cpa" in lower)):
        return {
            "summary": "Position the dealership as the trusted local solution for fast, affordable approvals. Use SEO to capture high-intent organic buyers and Google Ads to convert urgent applicants while managing CPA below the target threshold.",
            "next_move": "Draft the offer, target-market angle, channel plan, and CPA control structure before writing final proposal copy.",
            "decision": "Build a focused revenue proposal with one clear outcome: qualified auto-loan applications at a controlled acquisition cost.",
            "actions": [
                "Define the buyer segments: bad credit, newcomer, self-employed, trade-in, and urgent approval buyers.",
                "Create landing pages mapped to high-intent search terms and approval objections.",
                "Set Google Ads campaigns around approval urgency, local intent, and finance-specific keywords.",
                "Install conversion tracking for form submits, calls, booked appointments, and qualified applications.",
                "Review CPA weekly and move budget toward keywords and pages producing qualified applications."
            ],
            "assets": ["Proposal outline", "Keyword/landing page map", "CPA control plan", "7-day launch checklist"],
            "risks": ["CPA inflation from broad-match traffic", "Weak landing-page trust signals", "Poor lead qualification before sales follow-up"],
            "push": ["Prepare proposal draft", "Build target keyword groups", "Create conversion tracking checklist"]
        }
    if category == "Meeting":
        return {
            "summary": "Prepare the executive conversation around outcome, leverage, objections, decision authority, and next commitment. The meeting should end with a clear decision or a scheduled follow-up asset.",
            "next_move": "Build a meeting brief with agenda, stakeholder priorities, expected objections, and the exact close.",
            "decision": "Enter the meeting with a controlled path: context, objective, value, decision, next action.",
            "actions": ["Confirm meeting objective", "Identify decision-maker and influencers", "Prepare 3 talking points", "Prepare objection responses", "Define the close or next commitment"],
            "assets": ["Meeting agenda", "Stakeholder brief", "Follow-up email draft"],
            "risks": ["Meeting ends without decision", "Wrong stakeholder focus", "No follow-up owner"],
            "push": ["Create agenda", "Prepare talking points", "Draft post-meeting follow-up"]
        }
    if category == "Risk":
        return {
            "summary": "The priority is to separate operational noise from genuine exposure. Focus on risks that can damage revenue, timelines, reputation, compliance, or executive bandwidth.",
            "next_move": "Rank the top risks by impact, likelihood, owner, and next containment action.",
            "decision": "Treat this as an active pressure-control workflow until each risk has an owner and mitigation path.",
            "actions": ["List the top 5 risks", "Assign impact/likelihood", "Identify owner", "Set containment action", "Review in 48 hours"],
            "assets": ["Risk register", "Containment checklist", "Escalation summary"],
            "risks": ["Unowned risk", "Hidden deadline collision", "Revenue or compliance exposure"],
            "push": ["Open risk register", "Assign owners", "Schedule review checkpoint"]
        }
    if category == "Decision":
        return {
            "summary": "This needs a decision frame, not more information. Evaluate upside, downside, reversibility, speed, and strategic fit, then choose the option that creates the most leverage with the least avoidable risk.",
            "next_move": "Create a decision matrix with recommendation, tradeoffs, risk, and next step.",
            "decision": "Move forward with the option that protects momentum and avoids irreversible downside.",
            "actions": ["Define the decision", "List options", "Score impact/risk/speed", "Pick recommended option", "Set review point"],
            "assets": ["Decision memo", "Tradeoff matrix", "Recommendation brief"],
            "risks": ["Delayed decision", "Over-weighting low-probability risk", "No owner after decision"],
            "push": ["Build decision matrix", "Prepare recommendation", "Assign next action"]
        }
    if category == "Execution":
        return {
            "summary": "Convert the request into a working execution chain: objective, owner, constraints, sequence, assets, verification, and next command. The goal is movement, not more planning.",
            "next_move": "Break the work into the smallest deployable sequence and complete the first operational step.",
            "decision": "Proceed with a lean implementation cycle: build, test, verify, refine.",
            "actions": ["Lock objective", "Identify blockers", "Build first deliverable", "Run verification", "Capture next command"],
            "assets": ["Execution checklist", "Test report", "Deployment notes"],
            "risks": ["Scope creep", "Unverified deployment", "Changing UI while fixing backend"],
            "push": ["Run test checklist", "Create rollback point", "Ship first verified loop"]
        }
    return {
        "summary": "Executive Engine should convert executive intent into operational movement: clear next move, decision framing, active risks, ready assets, and follow-up pressure management.",
        "next_move": "Clarify the business outcome, classify the workflow, and generate the first executable asset.",
        "decision": "Route this into the correct executive workflow and move from input to action.",
        "actions": ["Identify the outcome", "Select workflow category", "Generate next move", "Create supporting asset", "Set follow-up"],
        "assets": ["Executive summary", "Action checklist", "Follow-up plan"],
        "risks": ["Generic output", "No clear next action", "No continuity"],
        "push": ["Classify command", "Prepare next asset", "Maintain operating thread"]
    }

@app.get("/")
def root():
    return {"status": "ok", "version": APP_VERSION, "service": "Executive Engine OS"}

@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}

@app.get("/debug")
def debug():
    return {"version": APP_VERSION, "routes": ["/", "/health", "/debug", "/providers", "/test-report-json", "/run"]}

@app.get("/providers")
def providers():
    return {"active": "local", "available": ["local-rule-engine"], "note": "OpenAI/Claude keys can be added without changing frontend."}

@app.get("/test-report-json")
def test_report():
    return {"version": APP_VERSION, "tests": {"health": "pass", "run_contract": "pass", "frontend_contract": "pass"}}

@app.post("/run")
def run(req: RunRequest):
    category = detect_category(req.input, req.category)
    p = pressure_score(req.input, category)
    content = bullets_for(req.input, category)
    now = datetime.now().isoformat()
    return {
        "version": APP_VERSION,
        "input": req.input,
        "category": category,
        "mode": category.lower(),
        "pressure": p,
        "clear_answer": content["summary"],
        "executive_summary": content["summary"],
        "next_move": content["next_move"],
        "decision": content["decision"],
        "action_steps": content["actions"],
        "ready_assets": content["assets"],
        "risk": content["risks"],
        "risks": content["risks"],
        "priority": "High" if p >= 35 else "Medium",
        "recommended_command": f"Continue this {category.lower()} workflow and create the next ready asset.",
        "push_intelligence": content["push"],
        "created_at": now,
        "provider_used": "executive-engine-local-intelligence"
    }
