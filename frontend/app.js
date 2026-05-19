const API_URL = localStorage.getItem("ee_api_url") || "http://127.0.0.1:8000";

let activeMode = "auto";
let historyState = {
  decisions: [],
  risks: [],
  assets: [],
  context: []
};

const els = {
  backendStatus: document.getElementById("backendStatus"),
  activeMode: document.getElementById("activeMode"),
  commandInput: document.getElementById("commandInput"),
  runBtn: document.getElementById("runBtn"),
  emptyState: document.getElementById("emptyState"),
  outputContent: document.getElementById("outputContent"),
  outputTitle: document.getElementById("outputTitle"),
  pressureBadge: document.getElementById("pressureBadge"),
  nextMove: document.getElementById("nextMove"),
  decision: document.getElementById("decision"),
  actionSteps: document.getElementById("actionSteps"),
  readyAssets: document.getElementById("readyAssets"),
  risk: document.getElementById("risk"),
  priority: document.getElementById("priority"),
  recommendedCommand: document.getElementById("recommendedCommand"),
  stateMode: document.getElementById("stateMode"),
  statePressure: document.getElementById("statePressure"),
  stateMomentum: document.getElementById("stateMomentum"),
  recentDecisions: document.getElementById("recentDecisions"),
  activeRisks: document.getElementById("activeRisks"),
  followUps: document.getElementById("followUps"),
};

function setList(element, items) {
  element.innerHTML = "";
  if (!items || !items.length) {
    const li = document.createElement("li");
    li.textContent = "—";
    element.appendChild(li);
    return;
  }
  items.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  });
}

function setPressureBadge(level) {
  const clean = (level || "NONE").toUpperCase();
  els.pressureBadge.textContent = clean + " PRESSURE";
  els.pressureBadge.className = "badge " + (
    clean === "HIGH" ? "high" :
    clean === "MEDIUM" ? "medium" :
    clean === "LOW" ? "low" : "neutral"
  );
}

function renderResponse(data) {
  els.emptyState.classList.add("hidden");
  els.outputContent.classList.remove("hidden");

  els.outputTitle.textContent = data.executive_summary || "Executive Output Ready";
  setPressureBadge(data.pressure);

  els.nextMove.textContent = data.next_move;
  els.decision.textContent = data.decision;
  els.risk.textContent = data.risk;
  els.priority.textContent = data.priority;
  els.recommendedCommand.textContent = data.recommended_command;

  setList(els.actionSteps, data.action_steps);
  setList(els.readyAssets, data.ready_assets);

  els.stateMode.textContent = (data.mode || "—").toUpperCase();
  els.statePressure.textContent = data.pressure || "—";
  els.stateMomentum.textContent = data.operating_state?.momentum_status || "—";

  historyState.decisions.unshift(data.decision);
  historyState.risks.unshift(data.risk);
  historyState.assets = [...(data.ready_assets || []), ...historyState.assets];

  setList(els.recentDecisions, historyState.decisions.slice(0, 4));
  setList(els.activeRisks, historyState.risks.slice(0, 4));
  setList(els.followUps, data.follow_up_questions || []);
}

async function checkBackend() {
  try {
    const res = await fetch(`${API_URL}/health`);
    if (!res.ok) throw new Error("Backend returned " + res.status);
    const data = await res.json();
    els.backendStatus.textContent = `${data.status} · ${data.version}`;
  } catch (err) {
    els.backendStatus.textContent = `Local backend not connected. Using ${API_URL}`;
  }
}

async function runCommand() {
  const input = els.commandInput.value.trim();
  if (!input) return;

  els.runBtn.disabled = true;
  els.runBtn.textContent = "Thinking...";

  try {
    const res = await fetch(`${API_URL}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input, mode: activeMode, depth: "standard" })
    });

    if (!res.ok) {
      throw new Error(`Backend error ${res.status}`);
    }

    const data = await res.json();
    renderResponse(data);
  } catch (err) {
    renderResponse({
      pressure: "HIGH",
      mode: activeMode,
      executive_summary: "Backend connection issue. The command loop is ready, but the frontend cannot reach the API.",
      next_move: "Start the FastAPI backend locally or update API_URL in frontend/app.js to your Render backend URL.",
      decision: "Do not continue frontend work until the backend route is reachable.",
      action_steps: [
        "Run backend with uvicorn main:app --reload --port 8000.",
        "Open /health and confirm status ok.",
        "Retry this command from the frontend.",
      ],
      ready_assets: ["Backend test checklist", "API route contract", "Deployment settings"],
      risk: "The app will feel broken if the frontend points to the wrong backend URL.",
      priority: "HIGH — fix API connectivity before product testing.",
      recommended_command: "Check backend health and reconnect frontend API URL.",
      operating_state: { momentum_status: "blocked_by_api_connection" },
      follow_up_questions: ["Is the backend running locally?", "Are you using Render or localhost?", "What API URL should the frontend use?"]
    });
  } finally {
    els.runBtn.disabled = false;
    els.runBtn.textContent = "Run Command";
  }
}

document.querySelectorAll(".mode").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeMode = btn.dataset.mode;
    els.activeMode.textContent = activeMode.toUpperCase();
  });
});

document.querySelectorAll(".sample").forEach(btn => {
  btn.addEventListener("click", () => {
    els.commandInput.value = btn.textContent;
    runCommand();
  });
});

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  });
});

els.runBtn.addEventListener("click", runCommand);
els.commandInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    runCommand();
  }
});

checkBackend();
