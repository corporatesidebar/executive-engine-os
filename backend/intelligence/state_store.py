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
        "generated_assets": [],
        "stop_list": [],
        "delegate_list": [],
        "resource_history": [],
        "operator_state": {
            "pressure_level": "Normal",
            "operator_mode": None,
            "current_execution": None,
            "next_move": None,
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

    workspace["recent_runs"].append({
        "created_at": now_iso(),
        "input": user_input[:700],
        "operator_mode": response.get("operator_mode"),
        "pressure_level": response.get("pressure_level"),
        "decision": response.get("decision"),
        "next_move": response.get("next_move"),
        "risk": response.get("risk"),
    })
    workspace["recent_runs"] = workspace["recent_runs"][-50:]

    workspace["decisions"].append({
        "created_at": now_iso(),
        "decision": response.get("decision"),
        "real_problem": response.get("real_problem"),
        "highest_leverage_move": response.get("highest_leverage_move"),
        "follow_up_command": response.get("follow_up_command") or response.get("recommended_command"),
    })
    workspace["decisions"] = workspace["decisions"][-75:]

    for asset in response.get("generated_assets", [])[:5]:
        workspace["generated_assets"].append({
            "created_at": now_iso(),
            "content": str(asset)[:4000],
        })
    workspace["generated_assets"] = workspace["generated_assets"][-75:]

    for item in response.get("what_to_stop", []):
        if item and item not in workspace["stop_list"]:
            workspace["stop_list"].append(item)
    workspace["stop_list"] = workspace["stop_list"][-75:]

    for item in response.get("what_to_delegate", []):
        if item and item not in workspace["delegate_list"]:
            workspace["delegate_list"].append(item)
    workspace["delegate_list"] = workspace["delegate_list"][-75:]

    for r in response.get("tools_and_resources", []):
        workspace["resource_history"].append(r)
    workspace["resource_history"] = workspace["resource_history"][-100:]

    workspace["active_execution"] = {
        "executive_summary": response.get("executive_summary"),
        "execution_sequence": response.get("execution_sequence"),
        "time_to_value": response.get("time_to_value"),
    }

    workspace["operator_state"]["pressure_level"] = response.get("pressure_level")
    workspace["operator_state"]["operator_mode"] = response.get("operator_mode")
    workspace["operator_state"]["current_execution"] = response.get("executive_summary")
    workspace["operator_state"]["next_move"] = response.get("next_move")

    save_workspace(workspace)
