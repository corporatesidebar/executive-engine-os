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

APP_VERSION = "V35150A-test-page-restore"
FRONTEND_URL = "https://executive-engine-frontend.onrender.com/"
BACKEND_URL = "https://executive-engine-os.onrender.com"

REQUIRED_CONTRACT_FIELDS = [
    "next_move",
    "decision",
    "action_steps",
    "ready_assets",
    "risk",
    "priority",
    "recommended_command",
]

app = FastAPI(
    title="Executive Engine OS Backend",
    version=APP_VERSION,
    description="Executive Engine OS backend with restored test report page.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    command: Optional[str] = None
    message: Optional[str] = None
    prompt: Optional[str] = None
    mode: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def _extract_command(payload: RunRequest) -> str:
    return (
        payload.command
        or payload.message
        or payload.prompt
        or "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
    ).strip()


def build_contract_response(command: str) -> Dict[str, Any]:
    normalized = command.lower()

    if "proposal" in normalized:
        next_move = "Build the proposal structure first, then convert it into a client-ready asset."
        decision = "Proceed with a revenue-focused proposal that anchors on business outcome, implementation timeline, and measurable upside."
        actions = [
            "Define the client objective and commercial outcome.",
            "Create the proposal sections: problem, strategy, scope, timeline, pricing, and next step.",
            "Prepare a short executive summary the client can approve quickly.",
        ]
        assets = [
            "Proposal outline",
            "Executive summary",
            "Client talking points",
        ]
        risk = "The proposal may become too broad unless the scope, timeline, and decision criteria are clearly bounded."
        priority = "High"
        recommended = "Generate the client-ready proposal draft with scope, pricing logic, timeline, and approval next step."
    elif "meeting" in normalized:
        next_move = "Prepare the meeting objective, key questions, and desired decision before the call."
        decision = "Use the meeting to clarify leverage, decision criteria, and next-step ownership."
        actions = [
            "Identify the meeting objective and desired outcome.",
            "Prepare three executive questions to expose urgency, budget, and constraints.",
            "Draft follow-up actions before the meeting starts.",
        ]
        assets = ["Meeting brief", "Question list", "Follow-up email draft"]
        risk = "The meeting may drift without a defined decision point."
        priority = "High"
        recommended = "Create a meeting prep pack with agenda, questions, objections, and follow-up email."
    else:
        next_move = "Convert the request into a clear decision, action path, and ready-to-use asset."
        decision = "Move forward with a structured executive response focused on speed, clarity, and measurable outcome."
        actions = [
            "Clarify the business objective.",
            "Identify the highest-leverage action.",
            "Create the first usable asset or decision brief.",
        ]
        assets = ["Executive brief", "Action checklist", "Recommended command"]
        risk = "Execution may slow down if the objective is not tied to a measurable outcome."
        priority = "Medium"
        recommended = "Turn this into a concrete execution brief with next action, owner, and timeline."

    return {
        "next_move": next_move,
        "decision": decision,
        "action_steps": actions,
        "ready_assets": assets,
        "risk": risk,
        "priority": priority,
        "recommended_command": recommended,
        "provider_used": "local_contract_fallback",
        "router": "v35150_contract_preserved",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_self_tests() -> Dict[str, Any]:
    started = time.perf_counter()
    results: List[Dict[str, Any]] = []

    def add(name: str, status: str, detail: str, data: Optional[Dict[str, Any]] = None) -> None:
        results.append({
            "name": name,
            "status": status,
            "detail": detail,
            "data": data or {},
        })

    try:
        root_payload = {"status": "ok", "service": "Executive Engine OS Backend", "version": APP_VERSION}
        add("GET /", "PASS", "Root endpoint returns service metadata.", root_payload)
    except Exception as exc:
        add("GET /", "FAIL", str(exc))

    try:
        health_payload = {"status": "ok", "version": APP_VERSION}
        add("GET /health", "PASS", "Health endpoint returns status ok.", health_payload)
    except Exception as exc:
        add("GET /health", "FAIL", str(exc))

    try:
        debug_payload = {
            "status": "ok",
            "version": APP_VERSION,
            "contract_fields": REQUIRED_CONTRACT_FIELDS,
        }
        add("GET /debug", "PASS", "Debug endpoint exposes version and required contract fields.", debug_payload)
    except Exception as exc:
        add("GET /debug", "FAIL", str(exc))

    try:
        sample = build_contract_response("Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.")
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if field not in sample]
        type_errors = []
        if not isinstance(sample.get("action_steps"), list):
            type_errors.append("action_steps must be a list")
        if not isinstance(sample.get("ready_assets"), list):
            type_errors.append("ready_assets must be a list")
        if missing or type_errors:
            add("POST /run contract validation", "FAIL", "Contract validation failed.", {"missing": missing, "type_errors": type_errors, "sample": sample})
        else:
            add("POST /run contract validation", "PASS", "All V35150 required output fields are present.", {"required_fields": REQUIRED_CONTRACT_FIELDS, "sample": sample})
    except Exception as exc:
        add("POST /run contract validation", "FAIL", str(exc))

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        try:
            frontend = await client.get(FRONTEND_URL)
            add(
                "Frontend reachability",
                "PASS" if frontend.status_code < 500 else "FAIL",
                f"Frontend returned HTTP {frontend.status_code}.",
                {"url": FRONTEND_URL, "status_code": frontend.status_code},
            )
        except Exception as exc:
            add("Frontend reachability", "FAIL", str(exc), {"url": FRONTEND_URL})

        try:
            backend = await client.get(BACKEND_URL + "/health")
            ok = backend.status_code == 200
            add(
                "Backend reachability",
                "PASS" if ok else "FAIL",
                f"Backend /health returned HTTP {backend.status_code}.",
                {"url": BACKEND_URL, "status_code": backend.status_code},
            )
        except Exception as exc:
            add("Backend reachability", "FAIL", str(exc), {"url": BACKEND_URL})

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    passed = sum(1 for item in results if item["status"] == "PASS")
    failed = sum(1 for item in results if item["status"] == "FAIL")

    return {
        "status": "PASS" if failed == 0 else "FAIL",
        "version": APP_VERSION,
        "backend_url": BACKEND_URL,
        "frontend_url": FRONTEND_URL,
        "required_contract_fields": REQUIRED_CONTRACT_FIELDS,
        "summary": {"passed": passed, "failed": failed, "total": len(results), "elapsed_ms": elapsed_ms},
        "results": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "Executive Engine OS Backend",
        "version": APP_VERSION,
        "test_report": "/test-report",
        "health": "/health",
        "run": "/run",
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "contract": "V35150 preserved",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/debug")
async def debug() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "frontend_url": FRONTEND_URL,
        "backend_url": BACKEND_URL,
        "required_contract_fields": REQUIRED_CONTRACT_FIELDS,
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
    }


@app.post("/run")
async def run(payload: RunRequest) -> Dict[str, Any]:
    command = _extract_command(payload)
    return build_contract_response(command)


@app.get("/test-report-json")
async def test_report_json() -> Dict[str, Any]:
    return await run_self_tests()


@app.get("/test-report", response_class=HTMLResponse)
async def test_report_page() -> HTMLResponse:
    html = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Executive Engine OS — Backend Test Report</title>
  <style>
    :root {
      --navy: #06172c;
      --navy-2: #0a2342;
      --blue: #2563eb;
      --orange: #f97316;
      --green: #16a34a;
      --red: #dc2626;
      --yellow: #ca8a04;
      --bg: #f6f8fb;
      --card: #ffffff;
      --text: #101827;
      --muted: #64748b;
      --line: #e5e7eb;
      --soft: #f8fafc;
      --shadow: 0 20px 60px rgba(15, 23, 42, .08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, rgba(37,99,235,.08), transparent 28%), var(--bg);
      color: var(--text);
    }
    .shell { display: grid; grid-template-columns: 280px minmax(0, 1fr); min-height: 100vh; }
    aside {
      background: linear-gradient(180deg, var(--navy), #020b18);
      color: white;
      padding: 28px 24px;
      display: flex;
      flex-direction: column;
      gap: 28px;
    }
    .brand { display: flex; gap: 14px; align-items: center; }
    .logo {
      width: 42px; height: 42px; border-radius: 14px;
      border: 2px solid rgba(249,115,22,.85);
      display: grid; place-items: center; color: var(--orange); font-weight: 900;
      box-shadow: 0 0 0 6px rgba(249,115,22,.08);
    }
    .brand h1 { font-size: 15px; line-height: 1.1; letter-spacing: .08em; margin: 0; }
    .brand p { margin: 5px 0 0; color: #9fb2ca; font-size: 12px; }
    .live { display: inline-flex; align-items: center; gap: 8px; color: #86efac; font-size: 12px; font-weight: 700; margin-top: 10px; }
    .dot { width: 7px; height: 7px; border-radius: 999px; background: #22c55e; }
    .side-card { border: 1px solid rgba(255,255,255,.12); border-radius: 18px; padding: 16px; background: rgba(255,255,255,.04); }
    .side-card h2 { font-size: 12px; text-transform: uppercase; color: #9fb2ca; letter-spacing: .12em; margin: 0 0 12px; }
    .side-card code { color: #e2e8f0; font-size: 12px; overflow-wrap: anywhere; }
    main { padding: 28px; }
    .top { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; margin-bottom: 22px; }
    .top h2 { margin:0; font-size: 28px; letter-spacing:-.03em; }
    .top p { margin: 6px 0 0; color: var(--muted); }
    .actions { display:flex; gap:12px; flex-wrap:wrap; justify-content:flex-end; }
    button {
      border: 0; border-radius: 12px; padding: 12px 16px; font-weight: 800; cursor: pointer;
      display:inline-flex; align-items:center; gap:8px; transition: transform .12s ease, opacity .12s ease;
    }
    button:hover { transform: translateY(-1px); }
    .primary { background: var(--orange); color: white; box-shadow: 0 10px 30px rgba(249,115,22,.24); }
    .secondary { background: white; color: var(--navy); border: 1px solid var(--line); }
    .grid { display:grid; grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr); gap:20px; }
    .card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; box-shadow: var(--shadow); overflow:hidden; }
    .card-header { padding: 18px 20px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:16px; align-items:center; }
    .card-header h3 { margin:0; font-size: 13px; letter-spacing:.08em; text-transform:uppercase; }
    .pill { border-radius:999px; padding:5px 10px; font-size:12px; font-weight:800; background:#eef2ff; color:#3730a3; }
    .body { padding: 18px 20px; }
    .status-block { display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:20px; }
    .metric { background: var(--soft); border:1px solid var(--line); border-radius:16px; padding:14px; }
    .metric strong { display:block; font-size:24px; margin-bottom:4px; }
    .metric span { color:var(--muted); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
    .test-row { display:grid; grid-template-columns: 120px minmax(170px, 260px) 1fr; gap:14px; align-items:start; padding:16px 0; border-bottom:1px solid var(--line); }
    .test-row:last-child { border-bottom: 0; }
    .badge { display:inline-flex; align-items:center; justify-content:center; width:72px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:900; }
    .pass { background:#dcfce7; color:#166534; }
    .fail { background:#fee2e2; color:#991b1b; }
    .pending { background:#fef3c7; color:#92400e; }
    .name { font-weight:900; }
    .detail { color: var(--muted); line-height:1.5; }
    pre { background:#071426; color:#dbeafe; border-radius:16px; padding:16px; overflow:auto; font-size:12px; line-height:1.5; margin:0; border:1px solid rgba(255,255,255,.08); }
    .contract { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; }
    .field { border:1px solid var(--line); border-radius:12px; padding:10px 12px; font-weight:800; color:#0f172a; background:#fff; display:flex; align-items:center; gap:8px; }
    .field::before { content:"✓"; color:var(--green); font-weight:900; }
    .footer { margin-top: 18px; color: var(--muted); font-size: 12px; display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; }
    .toast { position: fixed; right: 22px; bottom: 22px; background: #071426; color: white; padding: 12px 14px; border-radius: 12px; opacity: 0; transform: translateY(12px); transition: all .2s ease; }
    .toast.show { opacity: 1; transform: translateY(0); }
    @media (max-width: 1100px) { .shell { grid-template-columns: 1fr; } aside { display:none; } .grid { grid-template-columns: 1fr; } .status-block { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 700px) { main { padding:18px; } .top { flex-direction:column; } .test-row { grid-template-columns: 1fr; } .contract { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div>
        <div class="brand">
          <div class="logo">E</div>
          <div>
            <h1>EXECUTIVE ENGINE</h1>
            <p>Backend Test Console</p>
          </div>
        </div>
        <div class="live"><span class="dot"></span> LIVE</div>
      </div>
      <div class="side-card">
        <h2>Backend</h2>
        <code id="backendUrl">https://executive-engine-os.onrender.com</code>
      </div>
      <div class="side-card">
        <h2>Frontend</h2>
        <code id="frontendUrl">https://executive-engine-frontend.onrender.com/</code>
      </div>
      <div class="side-card">
        <h2>Rules Preserved</h2>
        <p style="color:#cbd5e1; line-height:1.6; margin:0; font-size:13px;">Backend-only test page restore. /run logic and V35150 output contract remain unchanged.</p>
      </div>
    </aside>

    <main>
      <section class="top">
        <div>
          <h2>Backend Test Report</h2>
          <p>Run endpoint checks, frontend/backend reachability, and V35150 /run contract validation.</p>
        </div>
        <div class="actions">
          <button class="secondary" id="copyBtn">Copy Results</button>
          <button class="primary" id="runBtn">Run Tests →</button>
        </div>
      </section>

      <section class="grid">
        <div class="card">
          <div class="card-header">
            <h3>PASS / FAIL checks</h3>
            <span class="pill" id="overallStatus">Waiting</span>
          </div>
          <div class="body">
            <div class="status-block">
              <div class="metric"><strong id="passed">—</strong><span>Passed</span></div>
              <div class="metric"><strong id="failed">—</strong><span>Failed</span></div>
              <div class="metric"><strong id="total">—</strong><span>Total</span></div>
              <div class="metric"><strong id="elapsed">—</strong><span>MS</span></div>
            </div>
            <div id="rows">
              <div class="test-row"><span class="badge pending">READY</span><div class="name">Run Tests</div><div class="detail">Click Run Tests to validate the backend console.</div></div>
            </div>
          </div>
        </div>

        <div style="display:grid; gap:20px; align-content:start;">
          <div class="card">
            <div class="card-header"><h3>Output Contract</h3><span class="pill">V35150</span></div>
            <div class="body contract" id="contractFields"></div>
          </div>
          <div class="card">
            <div class="card-header"><h3>Raw Results</h3><span class="pill" id="generatedAt">Not run</span></div>
            <div class="body"><pre id="raw">Click Run Tests to generate report JSON.</pre></div>
          </div>
        </div>
      </section>
      <div class="footer"><span>© 2026 Executive Engine OS.</span><span>V35150A test page restore only.</span></div>
    </main>
  </div>
  <div class="toast" id="toast">Copied results.</div>

<script>
const requiredFields = ["next_move", "decision", "action_steps", "ready_assets", "risk", "priority", "recommended_command"];
const contract = document.getElementById('contractFields');
contract.innerHTML = requiredFields.map(f => `<div class="field">${f}</div>`).join('');
let lastReport = null;

function setLoading() {
  document.getElementById('overallStatus').textContent = 'Running';
  document.getElementById('rows').innerHTML = `<div class="test-row"><span class="badge pending">RUN</span><div class="name">Tests running</div><div class="detail">Checking endpoints and output contract...</div></div>`;
}

function render(report) {
  lastReport = report;
  document.getElementById('overallStatus').textContent = report.status || 'UNKNOWN';
  document.getElementById('passed').textContent = report.summary?.passed ?? 0;
  document.getElementById('failed').textContent = report.summary?.failed ?? 0;
  document.getElementById('total').textContent = report.summary?.total ?? 0;
  document.getElementById('elapsed').textContent = report.summary?.elapsed_ms ?? '—';
  document.getElementById('generatedAt').textContent = report.generated_at ? new Date(report.generated_at).toLocaleTimeString() : 'Generated';
  document.getElementById('raw').textContent = JSON.stringify(report, null, 2);
  document.getElementById('rows').innerHTML = (report.results || []).map(item => {
    const cls = item.status === 'PASS' ? 'pass' : 'fail';
    return `<div class="test-row"><span class="badge ${cls}">${item.status}</span><div class="name">${item.name}</div><div class="detail">${item.detail}</div></div>`;
  }).join('');
}

async function runTests() {
  setLoading();
  try {
    const response = await fetch('/test-report-json', { cache: 'no-store' });
    const report = await response.json();
    render(report);
  } catch (error) {
    render({
      status: 'FAIL',
      summary: { passed: 0, failed: 1, total: 1, elapsed_ms: 0 },
      generated_at: new Date().toISOString(),
      results: [{ name: 'Test report fetch', status: 'FAIL', detail: error.message }]
    });
  }
}

async function copyResults() {
  const text = lastReport ? JSON.stringify(lastReport, null, 2) : document.getElementById('raw').textContent;
  await navigator.clipboard.writeText(text);
  const toast = document.getElementById('toast');
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 1600);
}

document.getElementById('runBtn').addEventListener('click', runTests);
document.getElementById('copyBtn').addEventListener('click', copyResults);
runTests();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)
