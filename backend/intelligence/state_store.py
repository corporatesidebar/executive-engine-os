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
        "deployment_history": [],
        "send_ready_assets": [],
        "export_ready_assets": [],
        "implementation_checklists": [],
        "operator_state": {
            "last_deployment_asset": None,
            "last_next_move": None,
            "current_focus": None,
            "pressure_level": "Normal",
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

def save_deployment_state(workspace_id: str, user_id: str, user_input: str, response: dict):
    workspace = load_workspace(workspace_id, user_id)

    record = {
        "created_at": now_iso(),
        "input": user_input[:1000],
        "executive_summary": response.get("executive_summary"),
        "next_move": response.get("next_move"),
        "primary_asset_title": response.get("primary_asset", {}).get("title") if isinstance(response.get("primary_asset"), dict) else None,
        "follow_up_command": response.get("follow_up_command") or response.get("recommended_command"),
    }

    workspace["deployment_history"].append(record)
    workspace["deployment_history"] = workspace["deployment_history"][-75:]

    for asset in response.get("send_ready_assets", []):
        workspace["send_ready_assets"].append({"created_at": now_iso(), "asset": asset})
    workspace["send_ready_assets"] = workspace["send_ready_assets"][-75:]

    for asset in response.get("export_ready_assets", []):
        workspace["export_ready_assets"].append({"created_at": now_iso(), "asset": asset})
    workspace["export_ready_assets"] = workspace["export_ready_assets"][-75:]

    if response.get("implementation_checklist"):
        workspace["implementation_checklists"].append({
            "created_at": now_iso(),
            "items": response.get("implementation_checklist")
        })
    workspace["implementation_checklists"] = workspace["implementation_checklists"][-75:]

    workspace["operator_state"]["last_deployment_asset"] = record["primary_asset_title"]
    workspace["operator_state"]["last_next_move"] = response.get("next_move")
    workspace["operator_state"]["current_focus"] = response.get("executive_summary")
    workspace["operator_state"]["pressure_level"] = response.get("pressure_level", "High")

    save_workspace(workspace)
