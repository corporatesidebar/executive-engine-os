import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

VERSION = "V35150A-restore-test-report"

app = FastAPI(title="Executive Engine OS", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_KEYS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
]

VALID_PRIORITIES = {"High", "Medium", "Low"}


class RunRequest(BaseModel):
    input: str = ""
    mode: Optional[str] = "execution"


def fallback_contract(user_input: str = "", mode: str = "execution") -> Dict[str, Any]:
    clean_input = (user_input or "").strip()
    mode_label = (mode or "execution").strip() or "execution"

    if clean_input:
        next_move = f"Clarify the immediate executive outcome for: {clean_input[:140]}"
        decision = "Proceed with a structured execution pass using the current stable workflow."
        recommended = f"Run a sharper {mode_label} command with owner, deadline, and success metric."
    else:
        next_move = "Enter the highest-value business outcome that needs movement today."
        decision = "Hold execution until the command includes a clear objective."
        recommended = "Define the objective, deadline, owner, and desired result."

    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": [
            "Confirm the business outcome and deadline.",
            "Identify the owner and the next concrete action.",
            "Define the risk, priority, and expected finished asset.",
        ],
        "ready_assets": [],
        "risk": "Execution may drift if the command lacks owner, timing, or measurable outcome.",
        "priority": "High" if clean_input else "Medium",
        "recommended_command": recommended,
    }


def as_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        output: List[str] = []
        for item in value:
            text = as_string(item)
            if text:
                output.append(text)
        return output
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        lines = [line.strip(" -•\t") for line in text.splitlines()]
        cleaned = [line for line in lines if line]
        return cleaned or [text]
    return [as_string(value)] if as_string(value) else []


def normalize_contract(raw: Any, user_input: str = "", mode: str = "execution") -> Dict[str, Any]:
    base = fallback_contract(user_input=user_input, mode=mode)

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}

    if not isinstance(raw, dict):
        raw = {}

    result = {
        "next_move": as_string(raw.get("next_move"), base["next_move"]) or base["next_move"],
        "decision": as_string(raw.get("decision"), base["decision"]) or base["decision"],
        "action_steps": as_list(raw.get("action_steps")) or base["action_steps"],
        "ready_assets": as_list(raw.get("ready_assets")),
        "risk": as_string(raw.get("risk"), base["risk"]) or base["risk"],
        "priority": as_string(raw.get("priority"), base["priority"]).title() or base["priority"],
        "recommended_command": as_string(raw.get("recommended_command"), base["recommended_command"])
        or base["recommended_command"],
    }

    if result["priority"] not in VALID_PRIORITIES:
        result["priority"] = base["priority"] if base["priority"] in VALID_PRIORITIES else "Medium"

    return {key: result[key] for key in REQUIRED_KEYS}


def extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def build_system_prompt() -> str:
    return """
You are Executive Engine OS, a private executive operating system.
Return only valid JSON. Do not include markdown, commentary, or extra keys.
Required exact keys:
next_move, decision, action_steps, ready_assets, risk, priority, recommended_command.
Rules:
- next_move: one immediate executive move.
- decision: one clear decision.
- action_steps: array of 3 to 6 concrete actions.
- ready_assets: array of assets that can be prepared now; empty array if none.
- risk: one direct operational risk.
- priority: High, Medium, or Low only.
- recommended_command: one command the executive should run next.
""".strip()


def run_ai(user_input: str, mode: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return {}

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": json.dumps({"mode": mode, "input": user_input}, ensure_ascii=False),
            },
        ],
        timeout=30,
    )

    content = response.choices[0].message.content if response.choices else ""
    return extract_json(content or "")


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Executive Engine OS",
        "version": VERSION,
        "status": "live",
        "message": "Autonomous Executive Operator live.",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "contract": REQUIRED_KEYS,
    }




@app.get("/debug")
def debug() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "endpoints": ["/", "/health", "/debug", "/run", "/test-report"],
        "contract": REQUIRED_KEYS,
    }


@app.get("/test-report", response_class=HTMLResponse)
def test_report() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Executive Engine OS Backend Test Report</title>
  <style>
    :root { color-scheme: light; }
    body { margin: 0; font-family: Arial, sans-serif; background: #f6f8fb; color: #0b1220; }
    main { max-width: 980px; margin: 0 auto; padding: 32px 18px; }
    .card { background: #fff; border: 1px solid #dbe3ef; border-radius: 14px; padding: 22px; box-shadow: 0 10px 30px rgba(11,18,32,.08); }
    h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: -0.03em; }
    .sub { color: #526173; margin: 0 0 18px; }
    .grid { display: grid; gap: 10px; margin-top: 18px; }
    .row { display: grid; grid-template-columns: 1fr 110px; gap: 12px; align-items: center; border: 1px solid #edf1f7; border-radius: 10px; padding: 12px 14px; }
    .name { font-weight: 700; }
    .detail { font-size: 13px; color: #526173; margin-top: 4px; word-break: break-word; }
    .status { text-align: center; font-weight: 800; border-radius: 999px; padding: 7px 10px; font-size: 13px; }
    .pending { background: #eef2f7; color: #526173; }
    .pass { background: #e8f7ee; color: #126b35; }
    .fail { background: #fdecec; color: #a21c1c; }
    .skip { background: #fff6df; color: #875a00; }
    button { background: #f97316; color: #fff; border: 0; border-radius: 10px; padding: 11px 15px; font-weight: 800; cursor: pointer; }
    pre { white-space: pre-wrap; background: #0b1220; color: #e5edf8; padding: 14px; border-radius: 10px; overflow: auto; }
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Executive Engine OS Backend Test Report</h1>
      <p class="sub">V35150A backend-only test page. Checks backend endpoints, output contract, and frontend reachability.</p>
      <button onclick="runTests()">Run Tests</button>
      <div id="results" class="grid"></div>
      <h2>Contract</h2>
      <pre>next_move\ndecision\naction_steps\nready_assets\nrisk\npriority\nrecommended_command</pre>
    </section>
  </main>
<script>
const REQUIRED_KEYS = ["next_move", "decision", "action_steps", "ready_assets", "risk", "priority", "recommended_command"];
const FRONTEND_URL = "https://executive-engine-frontend.onrender.com/";
const BACKEND_URL = "https://executive-engine-os.onrender.com";

function renderRow(id, name, detail) {
  const wrap = document.getElementById("results");
  const row = document.createElement("div");
  row.className = "row";
  row.id = id;
  row.innerHTML = `<div><div class="name">${name}</div><div class="detail">${detail || ""}</div></div><div class="status pending">PENDING</div>`;
  wrap.appendChild(row);
}

function setStatus(id, status, detail) {
  const row = document.getElementById(id);
  const badge = row.querySelector(".status");
  const detailEl = row.querySelector(".detail");
  badge.className = "status " + status.toLowerCase();
  badge.textContent = status;
  if (detail) detailEl.textContent = detail;
}

async function checkGet(id, url, allowSkip404=false) {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (allowSkip404 && res.status === 404) return setStatus(id, "SKIP", "Endpoint not present; skipped by design.");
    if (!res.ok) return setStatus(id, "FAIL", `HTTP ${res.status}`);
    setStatus(id, "PASS", `HTTP ${res.status}`);
  } catch (err) {
    setStatus(id, "FAIL", err.message || String(err));
  }
}

async function checkRun() {
  try {
    const res = await fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: "Test V35150A output contract", mode: "execution" })
    });
    if (!res.ok) return setStatus("post-run", "FAIL", `HTTP ${res.status}`);
    const data = await res.json();
    const keys = Object.keys(data);
    const missing = REQUIRED_KEYS.filter(k => !(k in data));
    const extra = keys.filter(k => !REQUIRED_KEYS.includes(k));
    const arraysOk = Array.isArray(data.action_steps) && Array.isArray(data.ready_assets);
    const priorityOk = ["High", "Medium", "Low"].includes(data.priority);
    if (missing.length || extra.length || !arraysOk || !priorityOk) {
      return setStatus("post-run", "FAIL", `missing=${missing.join(",") || "none"}; extra=${extra.join(",") || "none"}; arraysOk=${arraysOk}; priorityOk=${priorityOk}`);
    }
    setStatus("post-run", "PASS", "HTTP 200; exact V35150 contract confirmed.");
  } catch (err) {
    setStatus("post-run", "FAIL", err.message || String(err));
  }
}

async function checkReachability(id, url) {
  try {
    await fetch(url, { method: "GET", mode: "no-cors", cache: "no-store" });
    setStatus(id, "PASS", `Reachability request completed: ${url}`);
  } catch (err) {
    setStatus(id, "FAIL", err.message || String(err));
  }
}

async function runTests() {
  const wrap = document.getElementById("results");
  wrap.innerHTML = "";
  renderRow("get-root", "GET /", "Backend root endpoint");
  renderRow("get-health", "GET /health", "Backend health endpoint");
  renderRow("get-debug", "GET /debug", "Debug endpoint if present");
  renderRow("post-run", "POST /run", "V35150 exact output contract");
  renderRow("frontend", "Frontend URL reachability", FRONTEND_URL);
  renderRow("backend-url", "Backend URL reachability", BACKEND_URL);

  await checkGet("get-root", "/");
  await checkGet("get-health", "/health");
  await checkGet("get-debug", "/debug", true);
  await checkRun();
  await checkReachability("frontend", FRONTEND_URL);
  await checkReachability("backend-url", BACKEND_URL);
}
runTests();
</script>
</body>
</html>
"""


@app.post("/run")
def run(payload: RunRequest) -> Dict[str, Any]:
    user_input = payload.input or ""
    mode = payload.mode or "execution"

    try:
        ai_output = run_ai(user_input=user_input, mode=mode)
    except Exception:
        ai_output = {}

    return normalize_contract(ai_output, user_input=user_input, mode=mode)
