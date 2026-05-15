import os
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

VERSION = "V35150B"
VERSION_SLUG = "v35150b-selective-run-response-quality-contract-patch"
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
]
ALLOWED_PRIORITIES = {"High", "Medium", "Low"}

app = FastAPI(
    title="Executive Engine OS Backend",
    version=VERSION,
    description="V35150B backend consistency and verification endpoint patch.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL.rstrip("/"),
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "https://executive-engine-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    command: Optional[str] = None
    input: Optional[str] = None
    prompt: Optional[str] = None
    mode: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def base_status() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "Executive Engine OS Backend",
        "version": VERSION,
        "version_slug": VERSION_SLUG,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "timestamp": utc_now(),
    }


def normalize_priority(value: Any) -> str:
    if isinstance(value, str):
        cleaned = value.strip().capitalize()
        if cleaned in ALLOWED_PRIORITIES:
            return cleaned
    return "High"


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [text]
    return [value]


def safe_text(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return fallback
    return str(value).strip() or fallback


def contract_fallback(command: str, reason: str = "structured fallback") -> Dict[str, Any]:
    clean_command = command.strip() if command else "Review current executive priority."
    return {
        "next_move": f"Clarify the highest-value outcome for: {clean_command}",
        "decision": "Proceed with a focused executive action plan using the available context.",
        "action_steps": [
            "Define the business outcome that must be won next.",
            "List the people, assets, constraints, and deadline connected to the request.",
            "Convert the request into one owner, one next action, and one measurable result.",
        ],
        "ready_assets": [
            "Executive action summary",
            "Next-step checklist",
        ],
        "risk": f"Limited source context may reduce precision; response generated through {reason}.",
        "priority": "High",
        "recommended_command": "Turn this into a board-ready execution brief with owners, timeline, risks, and next action.",
    }


def normalize_run_contract(raw: Any, command: str) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return contract_fallback(command, "non-dictionary AI response")

    fallback = contract_fallback(command, "contract normalization")
    normalized: Dict[str, Any] = {}
    normalized["next_move"] = safe_text(raw.get("next_move"), fallback["next_move"])
    normalized["decision"] = safe_text(raw.get("decision"), fallback["decision"])
    normalized["action_steps"] = ensure_list(raw.get("action_steps")) or fallback["action_steps"]
    normalized["ready_assets"] = ensure_list(raw.get("ready_assets"))
    normalized["risk"] = safe_text(raw.get("risk"), fallback["risk"])
    normalized["priority"] = normalize_priority(raw.get("priority"))
    normalized["recommended_command"] = safe_text(raw.get("recommended_command"), fallback["recommended_command"])
    return {field: normalized[field] for field in REQUIRED_RUN_FIELDS}


def local_executive_response(command: str) -> Dict[str, Any]:
    text = command.strip() if command else "No command provided."
    return {
        "next_move": f"Move the request into one executable path: {text}",
        "decision": "Advance with a practical execution response and keep the scope constrained to the current request.",
        "action_steps": [
            "Identify the desired business result.",
            "Separate required facts from assumptions.",
            "Create the smallest next deliverable that moves the work forward.",
            "Confirm the owner, timeline, and success measure.",
        ],
        "ready_assets": [
            "Structured execution plan",
            "Decision summary",
            "Follow-up command",
        ],
        "risk": "Execution quality depends on the completeness of the command and available context.",
        "priority": "High",
        "recommended_command": "Convert this into a 7-day execution plan with owner, deadline, risk, and success metric.",
    }


async def openai_first_response(command: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system_prompt = (
        "You are Executive Engine OS. Return only valid JSON with exactly these keys: "
        "next_move, decision, action_steps, ready_assets, risk, priority, recommended_command. "
        "action_steps and ready_assets must be arrays. priority must be High, Medium, or Low."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command or "Create the next executive move."},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=28) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return normalize_run_contract(parsed, command)
    except Exception:
        return None


@app.get("/")
async def root() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "message": "Autonomous Executive Operator live.",
            "endpoints": ["/", "/health", "/debug", "/test-report", "/test-report-json", "/run"],
            "run_contract": REQUIRED_RUN_FIELDS,
        }
    )
    return payload


@app.get("/health")
async def health() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "health": "healthy",
            "run_contract_status": "locked",
            "required_run_fields": REQUIRED_RUN_FIELDS,
        }
    )
    return payload


@app.get("/debug")
async def debug() -> Dict[str, Any]:
    payload = base_status()
    payload.update(
        {
            "environment": {
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "provider_order": "openai-first",
            },
            "contract": {
                "required_fields": REQUIRED_RUN_FIELDS,
                "priority_allowed_values": sorted(ALLOWED_PRIORITIES),
                "arrays": ["action_steps", "ready_assets"],
            },
        }
    )
    return payload


@app.post("/run")
async def run(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}

    command = ""
    if isinstance(body, dict):
        command = body.get("command") or body.get("input") or body.get("prompt") or ""
    else:
        command = str(body)

    ai_payload = await openai_first_response(command)
    if ai_payload is None:
        ai_payload = normalize_run_contract(local_executive_response(command), command)

    return JSONResponse(content=ai_payload)


async def check_url(method: str, url: str, json_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "name": f"{method} {url}",
        "method": method,
        "url": url,
        "pass": False,
        "status_code": None,
        "ms": None,
        "error": None,
    }
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            if method == "POST":
                response = await client.post(url, json=json_payload or {})
            else:
                response = await client.get(url)
            result["status_code"] = response.status_code
            result["ms"] = round((time.perf_counter() - started) * 1000)
            result["pass"] = 200 <= response.status_code < 400
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    result["response"] = response.json()
                except Exception:
                    result["response"] = response.text[:1000]
            else:
                result["response"] = response.text[:1000]
    except Exception as exc:
        result["ms"] = round((time.perf_counter() - started) * 1000)
        result["error"] = str(exc)
    return result


def validate_run_contract(payload: Any) -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "pass": False,
        "missing_fields": [],
        "wrong_types": [],
        "priority_valid": False,
    }
    if not isinstance(payload, dict):
        checks["wrong_types"].append("response must be object")
        return checks
    checks["missing_fields"] = [field for field in REQUIRED_RUN_FIELDS if field not in payload]
    if "action_steps" in payload and not isinstance(payload.get("action_steps"), list):
        checks["wrong_types"].append("action_steps must be array")
    if "ready_assets" in payload and not isinstance(payload.get("ready_assets"), list):
        checks["wrong_types"].append("ready_assets must be array")
    checks["priority_valid"] = payload.get("priority") in ALLOWED_PRIORITIES
    checks["pass"] = not checks["missing_fields"] and not checks["wrong_types"] and checks["priority_valid"]
    return checks


@app.get("/test-report-json")
async def test_report_json() -> Dict[str, Any]:
    tests: List[Dict[str, Any]] = []
    tests.append(await check_url("GET", f"{BACKEND_URL}/"))
    tests.append(await check_url("GET", f"{BACKEND_URL}/health"))
    tests.append(await check_url("GET", f"{BACKEND_URL}/debug"))
    run_test = await check_url("POST", f"{BACKEND_URL}/run", {"command": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."})
    run_test["contract"] = validate_run_contract(run_test.get("response"))
    run_test["pass"] = bool(run_test.get("pass")) and bool(run_test["contract"].get("pass"))
    tests.append(run_test)
    tests.append(await check_url("GET", FRONTEND_URL))
    tests.append(await check_url("GET", BACKEND_URL))

    version_checks = []
    for item in tests:
        response = item.get("response")
        if isinstance(response, dict) and "version" in response:
            version_checks.append(response.get("version") == VERSION)
    all_pass = all(item.get("pass") for item in tests)
    consistent = all(version_checks) if version_checks else False
    return {
        "status": "pass" if all_pass and consistent else "fail",
        "version": VERSION,
        "version_slug": VERSION_SLUG,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "timestamp": utc_now(),
        "version_consistent": consistent,
        "tests": tests,
    }


@app.get("/test-report", response_class=HTMLResponse)
async def test_report() -> str:
    return f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Executive Engine OS Backend Test Report — {VERSION}</title>
  <style>
    :root {{ --bg:#0f172a; --panel:#111827; --card:#ffffff; --text:#111827; --muted:#64748b; --pass:#16a34a; --fail:#dc2626; --line:#e5e7eb; --accent:#f97316; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Arial, Helvetica, sans-serif; background:#f8fafc; color:var(--text); }}
    header {{ background:var(--bg); color:white; padding:26px 32px; }}
    header h1 {{ margin:0 0 8px; font-size:26px; }}
    header p {{ margin:0; color:#cbd5e1; }}
    main {{ max-width:1180px; margin:0 auto; padding:28px; }}
    .toolbar {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:18px; }}
    button {{ border:0; border-radius:10px; padding:12px 16px; font-weight:700; cursor:pointer; }}
    .run {{ background:var(--accent); color:white; }}
    .copy {{ background:#111827; color:white; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:18px; }}
    .card {{ background:white; border:1px solid var(--line); border-radius:16px; padding:16px; box-shadow:0 8px 24px rgba(15,23,42,.06); }}
    .label {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }}
    .value {{ font-size:18px; font-weight:800; }}
    .results {{ display:grid; gap:12px; }}
    .row {{ background:white; border:1px solid var(--line); border-radius:14px; padding:14px; display:grid; grid-template-columns:96px 1fr 120px; gap:14px; align-items:start; }}
    .badge {{ display:inline-flex; justify-content:center; align-items:center; min-width:72px; border-radius:999px; padding:8px 10px; font-size:12px; font-weight:800; color:white; }}
    .passBadge {{ background:var(--pass); }}
    .failBadge {{ background:var(--fail); }}
    .endpoint {{ font-weight:800; word-break:break-all; }}
    .meta {{ color:var(--muted); font-size:13px; margin-top:4px; }}
    pre {{ white-space:pre-wrap; word-break:break-word; background:#0b1220; color:#e5e7eb; border-radius:14px; padding:16px; max-height:420px; overflow:auto; }}
    @media(max-width:850px) {{ .grid {{ grid-template-columns:1fr; }} .row {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Executive Engine OS Backend Test Report</h1>
    <p>Version: <strong>{VERSION}</strong> · Backend: {BACKEND_URL}</p>
  </header>
  <main>
    <div class=\"toolbar\">
      <button class=\"run\" onclick=\"runTests()\">Run Tests</button>
      <button class=\"copy\" onclick=\"copyReport()\">Copy JSON</button>
    </div>
    <section class=\"grid\">
      <div class=\"card\"><div class=\"label\">Overall Status</div><div id=\"overall\" class=\"value\">Not run</div></div>
      <div class=\"card\"><div class=\"label\">Version Target</div><div class=\"value\">{VERSION}</div></div>
      <div class=\"card\"><div class=\"label\">Run Contract</div><div class=\"value\">Locked</div></div>
    </section>
    <section id=\"results\" class=\"results\"></section>
    <h2>Raw JSON</h2>
    <pre id=\"raw\">Click Run Tests.</pre>
  </main>
<script>
let lastReport = null;
function render(report) {{
  lastReport = report;
  document.getElementById('overall').textContent = (report.status || 'fail').toUpperCase();
  document.getElementById('raw').textContent = JSON.stringify(report, null, 2);
  const results = document.getElementById('results');
  results.innerHTML = '';
  (report.tests || []).forEach(test => {{
    const row = document.createElement('div');
    row.className = 'row';
    const pass = !!test.pass;
    row.innerHTML = `
      <div><span class=\"badge ${{pass ? 'passBadge' : 'failBadge'}}\">${{pass ? 'PASS' : 'FAIL'}}</span></div>
      <div>
        <div class=\"endpoint\">${{test.name || test.url}}</div>
        <div class=\"meta\">Status: ${{test.status_code || 'n/a'}} · Time: ${{test.ms || 'n/a'}}ms</div>
        ${{test.error ? `<div class=\"meta\">Error: ${{test.error}}</div>` : ''}}
      </div>
      <div class=\"meta\">${{test.contract ? 'Contract: ' + (test.contract.pass ? 'PASS' : 'FAIL') : ''}}</div>
    `;
    results.appendChild(row);
  }});
}}
async function runTests() {{
  document.getElementById('overall').textContent = 'Running...';
  document.getElementById('raw').textContent = 'Running backend verification...';
  try {{
    const res = await fetch('/test-report-json', {{ cache: 'no-store' }});
    const report = await res.json();
    render(report);
  }} catch (err) {{
    render({{ status:'fail', version:'{VERSION}', error:String(err), tests:[] }});
  }}
}}
async function copyReport() {{
  const text = JSON.stringify(lastReport || {{ status:'not_run', version:'{VERSION}' }}, null, 2);
  await navigator.clipboard.writeText(text);
}}
runTests();
</script>
</body>
</html>
"""
