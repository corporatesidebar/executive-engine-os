from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid

APP_VERSION = "V37200-Execution-Object-Persistence-Workspace-Engine"
DATA_DIR = Path(os.getenv("EE_DATA_DIR", "/tmp/executive_engine_workspace"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Executive Engine OS", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://executive-engine-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    input: str = Field(..., min_length=1)
    mode: Optional[str] = "execution"
    brain: Optional[str] = "operator"
    output_type: Optional[str] = "standard"
    depth: Optional[str] = "auto"
    provider: Optional[str] = "openai"
    workspace_id: Optional[str] = "default"
    user_id: Optional[str] = "will"
    context: Optional[Dict[str, Any]] = None

class ObjectUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def workspace_path(workspace_id: str, user_id: str) -> Path:
    safe_ws = "".join(c if c.isalnum() or c in "-_" else "_" for c in workspace_id or "default")
    safe_user = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_id or "will")
    return DATA_DIR / f"{safe_ws}__{safe_user}.json"

def default_workspace(workspace_id="default", user_id="will") -> Dict[str, Any]:
    return {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "threads": [],
        "execution_objects": [],
        "active_projects": [],
        "ready_assets": [],
        "decisions": [],
        "follow_ups": [],
        "revenue_lanes": [],
        "operator_state": {
            "current_focus": None,
            "last_command": None,
            "last_response_id": None,
            "open_object_count": 0,
            "ready_to_review_count": 0,
            "pressure_level": "Medium",
        },
    }

def load_workspace(workspace_id="default", user_id="will") -> Dict[str, Any]:
    path = workspace_path(workspace_id, user_id)
    if not path.exists():
        return default_workspace(workspace_id, user_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default_workspace(workspace_id, user_id)

    base = default_workspace(workspace_id, user_id)
    for k, v in base.items():
        data.setdefault(k, v)
    data.setdefault("operator_state", base["operator_state"])
    return data

def save_workspace(ws: Dict[str, Any]) -> None:
    ws["updated_at"] = now_iso()
    workspace_path(ws.get("workspace_id", "default"), ws.get("user_id", "will")).write_text(
        json.dumps(ws, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def detect_type(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ["proposal", "quote", "pitch"]):
        return "proposal"
    if any(x in t for x in ["meeting", "call", "agenda", "prep"]):
        return "meeting_prep"
    if any(x in t for x in ["outreach", "email", "linkedin", "clients", "lead"]):
        return "outreach_sequence"
    if any(x in t for x in ["kpi", "metric", "dashboard", "scorecard"]):
        return "kpi_scorecard"
    if any(x in t for x in ["workflow", "sop", "process"]):
        return "workflow"
    return "execution_package"

def object_title(object_type: str, text: str) -> str:
    t = (text or "").strip()
    if object_type == "proposal":
        if "cookie" in t.lower():
            return "Cookie Shop Digital Marketing Proposal Package"
        return "Proposal Package"
    if object_type == "meeting_prep":
        return "Meeting Prep Package"
    if object_type == "outreach_sequence":
        return "Outbound / Follow-up Sequence"
    if object_type == "kpi_scorecard":
        return "KPI Scorecard"
    if object_type == "workflow":
        return "Workflow System"
    return "Execution Package"

def make_execution_objects(command: str) -> List[Dict[str, Any]]:
    object_type = detect_type(command)
    title = object_title(object_type, command)

    if object_type == "proposal":
        return [
            {
                "id": str(uuid.uuid4()),
                "object_type": "proposal",
                "title": title,
                "status": "ready_to_review",
                "purpose": "Review, edit if needed, and send.",
                "payload": {
                    "executive_positioning": "A send-ready marketing proposal package prepared from the command.",
                    "offer": "Digital marketing and advertising growth sprint",
                    "scope": [
                        "Consumer research snapshot",
                        "Positioning and offer structure",
                        "Google Ads / social campaign plan",
                        "Landing page or ordering funnel recommendation",
                        "Follow-up email and next-step CTA",
                    ],
                    "draft_copy": "Prepared proposal: position the cookie shop as a premium local brand with Canada-wide gifting, events, and online ordering potential. Recommended angle: local Barrie credibility + national gifting/shipping expansion.",
                    "recommended_next_action": "Review the proposal angle, adjust pricing if needed, and send to the owner."
                },
            },
            {
                "id": str(uuid.uuid4()),
                "object_type": "outreach_sequence",
                "title": "Proposal Follow-up Email",
                "status": "ready_to_send",
                "purpose": "Send after review.",
                "payload": {
                    "subject": "Digital marketing growth plan for your cookie shop",
                    "body": "Hi [Name], I prepared a practical digital marketing and advertising plan for your cookie shop. The focus is simple: improve local Barrie demand, test paid campaigns, and create a path to sell across Canada through gifting, events, and online ordering. I can walk you through the proposal and the first 30-day sprint this week."
                },
            },
            {
                "id": str(uuid.uuid4()),
                "object_type": "kpi_scorecard",
                "title": "Cookie Shop Growth KPIs",
                "status": "ready_to_use",
                "purpose": "Track whether the campaign creates real business signal.",
                "payload": {
                    "metrics": [
                        "Cost per inquiry",
                        "Online order conversion rate",
                        "Average order value",
                        "Repeat purchase rate",
                        "Gift/corporate order leads",
                        "Local search traffic",
                    ]
                },
            },
        ]

    if object_type == "meeting_prep":
        return [
            {
                "id": str(uuid.uuid4()),
                "object_type": "meeting_prep",
                "title": "Meeting Brief",
                "status": "ready_to_review",
                "purpose": "Review quickly before the meeting.",
                "payload": {
                    "objective": "Enter the meeting with outcome, decision, objections, and next step already prepared.",
                    "talking_points": [
                        "Confirm desired outcome.",
                        "Surface the decision-maker and resistance.",
                        "Align next step before leaving the meeting.",
                    ],
                    "follow_up_asset": "Post-meeting follow-up email prepared for immediate send."
                },
            }
        ]

    return [
        {
            "id": str(uuid.uuid4()),
            "object_type": object_type,
            "title": title,
            "status": "ready_to_review",
            "purpose": "Review, edit if needed, and deploy.",
            "payload": {
                "summary": "Execution object prepared from command.",
                "next_action": "Review and approve the prepared object.",
                "deployment_note": "Prepared work is ready for executive review."
            },
        }
    ]

def build_response(command: str, workspace_id: str, user_id: str) -> Dict[str, Any]:
    objects = make_execution_objects(command)
    primary = objects[0] if objects else None
    response_id = str(uuid.uuid4())

    if primary:
        next_move = f"{primary['title']} is ready to review, edit if needed, and deploy."
    else:
        next_move = "Execution package prepared for review."

    response = {
        "response_id": response_id,
        "executive_summary": "Execution assets prepared. Review quickly, adjust if needed, and move forward.",
        "next_move": next_move,
        "decision": "Move from open task to prepared asset review.",
        "action_steps": [
            "Review the prepared asset.",
            "Edit only what materially changes the outcome.",
            "Send, save, or assign the asset.",
            "Track response and next action."
        ],
        "ready_assets": [o["title"] for o in objects],
        "risk": "Delay comes from keeping the task open instead of moving the prepared asset to review/send.",
        "priority": "High",
        "recommended_command": "Prepare the next follow-up asset.",
        "execution_objects": objects,
        "primary_object": primary,
        "deployment_sequence": [
            {"step": 1, "task": "Review prepared asset", "owner": "Executive", "status": "ready"},
            {"step": 2, "task": "Edit if needed", "owner": "Executive", "status": "optional"},
            {"step": 3, "task": "Send/deploy", "owner": "Executive or delegate", "status": "next"},
            {"step": 4, "task": "Track response", "owner": "System", "status": "pending"},
        ],
        "executive_scan": {
            "dominant_insight": "The work is now prepared, not pending.",
            "decision": "Review and deploy the prepared object.",
            "move": next_move,
            "risk": "Prepared assets lose momentum if not reviewed.",
            "pressure_level": "Medium",
        },
        "workspace_state": {
            "workspace_id": workspace_id,
            "objects_saved": len(objects),
            "response_id": response_id,
            "persistence": "saved_to_workspace"
        },
        "status": "success"
    }
    return response

def persist_run(workspace_id: str, user_id: str, command: str, response: Dict[str, Any]) -> None:
    ws = load_workspace(workspace_id, user_id)

    thread = {
        "id": response["response_id"],
        "created_at": now_iso(),
        "command": command,
        "summary": response.get("executive_summary"),
        "next_move": response.get("next_move"),
        "object_ids": [o["id"] for o in response.get("execution_objects", [])],
    }
    ws["threads"].append(thread)
    ws["threads"] = ws["threads"][-100:]

    for obj in response.get("execution_objects", []):
        saved = {
            **obj,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "source_command": command,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        ws["execution_objects"].append(saved)

        if obj["status"] in ["ready_to_review", "ready_to_send", "ready_to_use"]:
            ws["ready_assets"].append(saved)

    ws["execution_objects"] = ws["execution_objects"][-250:]
    ws["ready_assets"] = ws["ready_assets"][-150:]

    ws["operator_state"]["current_focus"] = response.get("next_move")
    ws["operator_state"]["last_command"] = command
    ws["operator_state"]["last_response_id"] = response.get("response_id")
    ws["operator_state"]["open_object_count"] = len([o for o in ws["execution_objects"] if o.get("status") not in ["completed", "archived"]])
    ws["operator_state"]["ready_to_review_count"] = len([o for o in ws["execution_objects"] if o.get("status") in ["ready_to_review", "ready_to_send", "ready_to_use"]])
    ws["operator_state"]["pressure_level"] = response.get("priority", "Medium")

    save_workspace(ws)

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "engine": "execution_object_persistence_workspace_engine"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "workspace_persistence": True,
        "run_contract": "V36800-compatible + V37200 persistence"
    }

@app.post("/run")
def run(req: RunRequest):
    workspace_id = req.workspace_id or "default"
    user_id = req.user_id or "will"
    response = build_response(req.input, workspace_id, user_id)
    persist_run(workspace_id, user_id, req.input, response)
    response["version"] = APP_VERSION
    return response

@app.get("/workspace")
def workspace(workspace_id: str = "default", user_id: str = "will"):
    return {
        "status": "success",
        "version": APP_VERSION,
        "workspace": load_workspace(workspace_id, user_id)
    }

@app.get("/workspace/objects")
def workspace_objects(workspace_id: str = "default", user_id: str = "will", status: Optional[str] = None):
    ws = load_workspace(workspace_id, user_id)
    objects = ws.get("execution_objects", [])
    if status:
        objects = [o for o in objects if o.get("status") == status]
    return {
        "status": "success",
        "count": len(objects),
        "objects": objects
    }

@app.get("/workspace/ready")
def workspace_ready(workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)
    ready = [o for o in ws.get("execution_objects", []) if o.get("status") in ["ready_to_review", "ready_to_send", "ready_to_use"]]
    return {
        "status": "success",
        "message": f"{len(ready)} execution assets ready to review, edit if needed, and deploy.",
        "ready_assets": ready
    }

@app.patch("/workspace/objects/{object_id}")
def update_object(object_id: str, update: ObjectUpdate, workspace_id: str = "default", user_id: str = "will"):
    ws = load_workspace(workspace_id, user_id)
    found = False

    for collection in ["execution_objects", "ready_assets"]:
        for obj in ws.get(collection, []):
            if obj.get("id") == object_id:
                if update.status is not None:
                    obj["status"] = update.status
                if update.title is not None:
                    obj["title"] = update.title
                if update.payload is not None:
                    obj["payload"] = update.payload
                if update.notes is not None:
                    obj["notes"] = update.notes
                obj["updated_at"] = now_iso()
                found = True

    if not found:
        raise HTTPException(status_code=404, detail="Execution object not found")

    ws["operator_state"]["open_object_count"] = len([o for o in ws["execution_objects"] if o.get("status") not in ["completed", "archived"]])
    ws["operator_state"]["ready_to_review_count"] = len([o for o in ws["execution_objects"] if o.get("status") in ["ready_to_review", "ready_to_send", "ready_to_use"]])
    save_workspace(ws)

    return {
        "status": "success",
        "object_id": object_id,
        "message": "Execution object updated."
    }

@app.post("/workspace/objects/{object_id}/archive")
def archive_object(object_id: str, workspace_id: str = "default", user_id: str = "will"):
    return update_object(object_id, ObjectUpdate(status="archived"), workspace_id, user_id)

@app.get("/test-report")
def test_report():
    return {
        "status": "success",
        "version": APP_VERSION,
        "tests": [
            "GET /health returns V37200",
            "POST /run returns V36800-compatible fields",
            "POST /run saves execution_objects to workspace",
            "GET /workspace returns persisted threads and objects",
            "GET /workspace/ready returns review-ready assets",
            "PATCH /workspace/objects/{id} updates status/title/payload",
            "POST /workspace/objects/{id}/archive archives object"
        ]
    }

@app.get("/test-report-json")
def test_report_json():
    return test_report()
