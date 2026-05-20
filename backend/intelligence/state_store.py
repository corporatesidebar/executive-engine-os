import os, json, re
from datetime import datetime, timezone

DATA_DIR = os.getenv("EE_DATA_DIR", "/tmp/executive_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def safe(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", value or "default")

def path(workspace_id: str, user_id: str) -> str:
    return os.path.join(DATA_DIR, f"workspace_{safe(workspace_id)}_{safe(user_id)}.json")

def default_workspace(workspace_id: str, user_id: str) -> dict:
    return {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "active_projects": [],
        "active_decisions": [],
        "execution_objects": [],
        "generated_assets": [],
        "follow_up_items": [],
        "revenue_lanes": [],
        "stalled_workflows": [],
        "people_companies": [],
        "operator_state": {
            "current_focus": None,
            "active_pressure": "Normal",
            "last_object_type": None,
            "last_next_move": None,
            "last_command": None,
        }
    }

def load_workspace(workspace_id: str = "default", user_id: str = "will") -> dict:
    p = path(workspace_id, user_id)
    if not os.path.exists(p):
        return default_workspace(workspace_id, user_id)
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_workspace(workspace_id, user_id)
        for k, v in base.items():
            data.setdefault(k, v)
        data.setdefault("operator_state", base["operator_state"])
        return data
    except Exception:
        return default_workspace(workspace_id, user_id)

def save_workspace(workspace: dict):
    workspace["updated_at"] = now_iso()
    with open(path(workspace["workspace_id"], workspace["user_id"]), "w", encoding="utf-8") as f:
        json.dump(workspace, f, indent=2, ensure_ascii=False)

def save_structured_execution_state(workspace_id: str, user_id: str, user_input: str, response: dict):
    workspace = load_workspace(workspace_id, user_id)

    objects = response.get("execution_objects", []) or []
    for obj in objects:
        workspace["execution_objects"].append({
            "created_at": now_iso(),
            "object_type": obj.get("object_type"),
            "title": obj.get("title"),
            "status": obj.get("status", "generated"),
            "payload": obj,
        })

        if obj.get("object_type") in ["proposal", "outreach_sequence", "landing_page", "operating_system"]:
            workspace["generated_assets"].append({
                "created_at": now_iso(),
                "title": obj.get("title"),
                "object_type": obj.get("object_type"),
                "payload": obj,
            })

        if obj.get("object_type") in ["revenue_lane", "offer", "pricing_model"]:
            workspace["revenue_lanes"].append({
                "created_at": now_iso(),
                "title": obj.get("title"),
                "payload": obj,
            })

        if obj.get("object_type") in ["follow_up_system", "deployment_checklist"]:
            workspace["follow_up_items"].append({
                "created_at": now_iso(),
                "title": obj.get("title"),
                "payload": obj,
            })

    workspace["execution_objects"] = workspace["execution_objects"][-150:]
    workspace["generated_assets"] = workspace["generated_assets"][-100:]
    workspace["follow_up_items"] = workspace["follow_up_items"][-100:]
    workspace["revenue_lanes"] = workspace["revenue_lanes"][-75:]

    scan = response.get("executive_scan", {}) or {}
    workspace["operator_state"]["current_focus"] = scan.get("dominant_insight") or response.get("executive_summary")
    workspace["operator_state"]["active_pressure"] = scan.get("pressure_level") or response.get("pressure_level", "High")
    workspace["operator_state"]["last_object_type"] = objects[0].get("object_type") if objects else None
    workspace["operator_state"]["last_next_move"] = response.get("next_move")
    workspace["operator_state"]["last_command"] = user_input[:1000]

    save_workspace(workspace)
