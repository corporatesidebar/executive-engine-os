import os, json, re
from datetime import datetime, timezone

DATA_DIR = os.getenv("EE_DATA_DIR", "/tmp/executive_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def safe_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", value or "default")

def workspace_path(workspace_id: str, user_id: str) -> str:
    return os.path.join(DATA_DIR, f"workspace_{safe_key(workspace_id)}_{safe_key(user_id)}.json")

def default_workspace(workspace_id: str, user_id: str):
    return {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "recent_runs": [],
        "decisions": [],
        "assets": [],
        "operator_state": {
            "current_focus": None,
            "pressure": "Normal",
            "last_next_move": None
        }
    }

def load_workspace(workspace_id: str = "default", user_id: str = "will"):
    path = workspace_path(workspace_id, user_id)
    if not os.path.exists(path):
        return default_workspace(workspace_id, user_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_workspace(workspace_id, user_id)
        for k, v in base.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return default_workspace(workspace_id, user_id)

def save_workspace(workspace):
    workspace["updated_at"] = now_iso()
    path = workspace_path(workspace["workspace_id"], workspace["user_id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(workspace, f, indent=2, ensure_ascii=False)

def save_run_context(workspace_id: str, user_id: str, user_input: str, response: dict):
    workspace = load_workspace(workspace_id, user_id)
    workspace["recent_runs"].append({
        "created_at": now_iso(),
        "input": user_input[:500],
        "next_move": response.get("next_move"),
        "decision": response.get("decision"),
        "priority": response.get("priority"),
    })
    workspace["recent_runs"] = workspace["recent_runs"][-30:]

    workspace["decisions"].append({
        "created_at": now_iso(),
        "decision": response.get("decision"),
        "risk": response.get("risk"),
        "recommended_command": response.get("recommended_command"),
    })
    workspace["decisions"] = workspace["decisions"][-50:]

    for asset in response.get("ready_assets", [])[:3]:
        workspace["assets"].append({
            "created_at": now_iso(),
            "content": str(asset)[:2000],
        })
    workspace["assets"] = workspace["assets"][-50:]

    workspace["operator_state"]["current_focus"] = response.get("executive_scan", {}).get("dominant_insight")
    workspace["operator_state"]["last_next_move"] = response.get("next_move")
    workspace["operator_state"]["pressure"] = response.get("executive_scan", {}).get("pressure", "Normal")

    save_workspace(workspace)
