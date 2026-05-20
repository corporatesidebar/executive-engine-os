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
        "active_execution": None,
        "recent_runs": [],
        "decisions": [],
        "assets": [],
        "paused_items": [],
        "resource_history": [],
        "operator_state": {
            "pressure": "Normal",
            "current_focus": None,
            "next_move": None,
            "revenue_path": None,
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

def save_execution_state(workspace_id: str, user_id: str, user_input: str, response: dict):
    workspace = load_workspace(workspace_id, user_id)

    run = {
        "created_at": now_iso(),
        "input": user_input[:700],
        "decision": response.get("decision"),
        "next_move": response.get("next_move"),
        "priority": response.get("priority"),
        "risk": response.get("risk"),
    }

    workspace["recent_runs"].append(run)
    workspace["recent_runs"] = workspace["recent_runs"][-40:]

    workspace["decisions"].append({
        "created_at": now_iso(),
        "decision": response.get("decision"),
        "recommended_command": response.get("recommended_command"),
        "risk": response.get("risk"),
    })
    workspace["decisions"] = workspace["decisions"][-75:]

    for asset in response.get("ready_assets", [])[:5]:
        workspace["assets"].append({
            "created_at": now_iso(),
            "content": str(asset)[:3000],
        })
    workspace["assets"] = workspace["assets"][-75:]

    for item in response.get("stop_doing", []):
        if item and item not in workspace["paused_items"]:
            workspace["paused_items"].append(item)
    workspace["paused_items"] = workspace["paused_items"][-50:]

    for r in response.get("resource_links", []):
        workspace["resource_history"].append(r)
    workspace["resource_history"] = workspace["resource_history"][-100:]

    workspace["active_execution"] = response.get("operational_depth")
    workspace["operator_state"]["pressure"] = response.get("executive_scan", {}).get("pressure", "High")
    workspace["operator_state"]["current_focus"] = response.get("executive_scan", {}).get("dominant_insight")
    workspace["operator_state"]["next_move"] = response.get("next_move")
    workspace["operator_state"]["revenue_path"] = response.get("operational_depth", {}).get("revenue_path")

    save_workspace(workspace)
