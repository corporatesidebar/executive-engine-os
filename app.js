
const API_URL = "https://executive-engine-os.onrender.com/run";

const els = {
  input: document.getElementById("commandInput"),
  execute: document.getElementById("executeBtn"),
  clear: document.getElementById("clearBtn"),
  thread: document.getElementById("thread"),
  summary: document.getElementById("summaryRail"),
  intel: document.getElementById("intelRail"),
};

const state = {
  messages: [],
  currentCommand: "",
  isLoading: false,
  lastResponse: null,
  executionObjects: [],
  rightRailState: null,
  error: null,
};

function uid(){ return "m_" + Math.random().toString(36).slice(2) + Date.now().toString(36); }
function now(){ return new Date().toLocaleString([], { month:"numeric", day:"numeric", year:"numeric", hour:"numeric", minute:"2-digit" }); }
function esc(v=""){ return String(v ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c])); }
function arr(v){ if(v == null || v === "") return []; return Array.isArray(v) ? v : [v]; }
function textOf(v){
  if(v == null) return "";
  if(typeof v === "string") return v;
  if(typeof v === "number") return String(v);
  if(Array.isArray(v)) return v.map(textOf).filter(Boolean).join(", ");
  if(typeof v === "object") return v.title || v.name || v.summary || v.description || v.content || v.next_move || v.executive_summary || JSON.stringify(v);
  return String(v);
}
function first(v){ return textOf(Array.isArray(v) ? v[0] : v); }
function label(s){ return String(s || "object").replace(/_/g, " ").replace(/\b\w/g, m => m.toUpperCase()); }

function payload(command){
  return {
    input: command,
    mode: "execution",
    brain: "operator",
    output_type: "standard",
    depth: "auto",
    provider: "openai"
  };
}

function parseResponse(data){
  const r = data && typeof data === "object" ? data : {};
  const scan = r.executive_scan || {};
  const executionObjects = normalizeObjects(r);

  return {
    raw: r,
    executive_summary: r.executive_summary || scan.dominant_insight || r.summary || r.next_move || "Execution response generated.",
    next_move: r.next_move || scan.move || r.what_to_do_now || "Review the prepared execution package and choose the next action.",
    decision: r.decision || r.operator_decision || scan.decision || "Proceed with the highest-leverage execution path.",
    action_steps: arr(r.action_steps || r.immediate_actions || r.execution_sequence || r.deployment_sequence).slice(0, 8),
    ready_assets: arr(r.ready_assets || r.generated_assets || r.deployment_assets || r.export_ready_assets).slice(0, 8),
    risk: r.risk || r.risk_control || scan.risk || "Execution risk should be controlled before deployment.",
    priority: r.priority || r.pressure_level || "High",
    recommended_command: r.recommended_command || r.follow_up_command || r.next_execution_package || "Generate the next deployment-ready asset.",
    execution_objects: executionObjects,
    deployment_sequence: arr(r.deployment_sequence || r.implementation_plan || r.execution_sequence).slice(0, 8),
    provider_used: r.provider_used || "backend",
    status: r.status || "success"
  };
}

function normalizeObjects(r){
  const objects = [];
  arr(r.execution_objects).forEach((o, i) => objects.push(normalizeObject(o, i)));
  [
    ["primary_object", "primary_object"],
    ["primary_asset", "primary_asset"],
    ["execution_packages", "execution_package"],
    ["deployment_assets", "deployment_asset"],
    ["generated_assets", "generated_asset"],
    ["proposal", "proposal"],
    ["crm_system", "crm_pipeline"],
    ["kpi_system", "kpi_scorecard"],
    ["outbound_systems", "outreach_sequence"],
    ["automation_stack", "automation_stack"],
    ["delegation_map", "delegation_map"],
    ["implementation_plan", "implementation_plan"],
    ["deployment_sequence", "deployment_checklist"]
  ].forEach(([key, type]) => {
    if(!r[key]) return;
    arr(r[key]).forEach((o, i) => objects.push(normalizeObject(o, objects.length + i, type)));
  });
  const unique = [];
  const seen = new Set();
  objects.forEach(o => {
    const key = `${o.type}:${o.title}`;
    if(!seen.has(key)){ seen.add(key); unique.push(o); }
  });
  return unique.slice(0, 10);
}

function normalizeObject(o, i, fallbackType="execution_object"){
  if(!o || typeof o !== "object"){
    return { id: uid(), type: fallbackType, title: `${label(fallbackType)} ${i + 1}`, status: "Ready", purpose: textOf(o), details: o };
  }
  const payload = o.payload && typeof o.payload === "object" ? o.payload : o;
  return {
    id: uid(),
    type: o.object_type || o.asset_type || o.type || fallbackType,
    title: o.title || o.asset_name || o.name || payload.title || payload.offer || `${label(fallbackType)} ${i + 1}`,
    status: o.status || o.deployment_priority || "Ready",
    purpose: o.purpose || payload.purpose || payload.positioning || payload.business_problem || payload.promise || textOf(payload).slice(0, 180),
    details: payload
  };
}

async function submitCommand(){
  const command = (els.input?.value || "").trim();
  if(!command || state.isLoading) return;

  state.error = null;
  state.currentCommand = command;
  state.isLoading = true;

  const userMsg = { id: uid(), role: "user", status: "success", content: command, created: now() };
  const loadingId = uid();
  const loadingMsg = { id: loadingId, role: "assistant", status: "loading", content: "Building execution package", created: now() };

  state.messages.push(userMsg, loadingMsg);
  if(els.input) els.input.value = "";
  renderApp();

  try{
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload(command))
    });

    const bodyText = await res.text();
    let data = {};
    try { data = JSON.parse(bodyText); }
    catch { data = { executive_summary: bodyText || "Backend returned an unreadable response." }; }

    if(!res.ok) throw new Error(data.detail || data.error || `Backend returned HTTP ${res.status}`);

    const parsed = parseResponse(data);
    state.lastResponse = parsed;
    state.executionObjects = parsed.execution_objects || [];
    state.rightRailState = parsed;

    const idx = state.messages.findIndex(m => m.id === loadingId);
    if(idx >= 0){
      state.messages[idx] = { id: loadingId, role: "assistant", status: "success", content: parsed.executive_summary, response: parsed, created: now() };
    }

  }catch(err){
    const message = err?.message || "Frontend could not connect to backend.";
    state.error = message;
    const idx = state.messages.findIndex(m => m.id === loadingId);
    if(idx >= 0){
      state.messages[idx] = { id: loadingId, role: "assistant", status: "error", content: message, created: now() };
    }
  }finally{
    state.isLoading = false;
    renderApp();
  }
}

function renderApp(){
  renderThread();
  renderRightSummary();
  renderIntelRail();
  if(els.execute){
    els.execute.disabled = state.isLoading;
    els.execute.textContent = state.isLoading ? "Executing..." : "Execute →";
  }
}

function renderThread(){
  if(!els.thread) return;
  if(!state.messages.length){
    els.thread.innerHTML = `<div class="empty-thread"><div><b>No active command thread yet.</b><span>Enter a command above to create live executive output. No fake thread data is preloaded.</span></div></div>`;
    return;
  }
  els.thread.innerHTML = state.messages.map(renderMessage).join("");
  els.thread.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", () => navigator.clipboard?.writeText(btn.getAttribute("data-copy") || ""));
  });
  els.thread.scrollTop = els.thread.scrollHeight;
}

function renderMessage(m){
  if(m.role === "user"){
    return `<div class="msg"><div class="bubble-avatar">W</div><div><div class="meta"><strong>You</strong><span>${esc(m.created)}</span></div><div class="copy">${esc(m.content)}</div></div></div>`;
  }
  if(m.status === "loading"){
    return `<div class="msg loading"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div><div class="copy"><span class="loading-dots">${esc(m.content)}</span></div></div></div>`;
  }
  if(m.status === "error"){
    return `<div class="msg"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div><div class="error-box">${esc(m.content)}</div></div></div>`;
  }
  return `<div class="msg engine"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div>${renderAssistantResponse(m.response)}</div></div>`;
}

function renderAssistantResponse(r){
  if(!r) return `<div class="copy">Response received.</div>`;
  const actions = r.action_steps.length ? `<div class="exec-mini"><b>Action Path</b><ul>${r.action_steps.map(x => `<li>${esc(textOf(x))}</li>`).join("")}</ul></div>` : "";
  const assets = r.ready_assets.length ? `<div class="exec-mini"><b>Ready Assets</b><ul>${r.ready_assets.slice(0,4).map(x => `<li>${esc(first(x))}</li>`).join("")}</ul></div>` : "";
  const objects = r.execution_objects.length ? `<div class="object-cards">${r.execution_objects.map(renderObjectCard).join("")}</div>` : "";

  return `
    <div class="copy">${esc(r.executive_summary)}</div>
    <div class="exec-package">
      <div class="exec-head">
        <div><div class="exec-type">Execution Package</div><strong>${esc(r.next_move)}</strong></div>
        <button data-copy="${esc(JSON.stringify(r.raw || r, null, 2))}">Copy</button>
      </div>
      <div class="exec-body">
        <div class="exec-grid">
          <div class="exec-mini"><b>Decision</b><p>${esc(r.decision)}</p></div>
          <div class="exec-mini"><b>Risk Control</b><p>${esc(r.risk)}</p></div>
          ${actions}
          ${assets}
        </div>
        ${objects}
      </div>
    </div>`;
}

function renderObjectCard(o){
  return `<div class="object-card"><div class="object-card-top"><div><strong>${esc(o.title)}</strong><small>${esc(label(o.type))} · ${esc(o.status)}</small></div><button data-copy="${esc(JSON.stringify(o.details, null, 2))}">Copy</button></div><p>${esc(o.purpose || "Deployment-ready execution object.")}</p></div>`;
}

function renderRightSummary(){
  if(!els.summary) return;
  const r = state.rightRailState;
  if(!r){
    els.summary.innerHTML = `
      <div class="section-head">EXECUTIVE SUMMARY</div>
      <div class="section-sub">Live updates from the conversation</div>
      ${summaryCard("orange", "NEXT MOVE", "Enter a command to generate the next move.", 1)}
      ${summaryCard("blue", "DECISION", "No live decision yet.", 1)}
      ${summaryCard("green", "ACTION STEPS", ["Awaiting command."], 1)}
      ${summaryCard("purple", "READY ASSETS", ["No assets generated yet."], 0)}
      ${summaryCard("red", "ACTIVE RISKS", "No live risk detected yet.", 0)}
      ${summaryCard("orange", "PRIORITY", "Normal", "—")}
      ${summaryCard("blue", "RECOMMENDED COMMAND", "Run a command to begin.", 1)}
    `;
    return;
  }
  els.summary.innerHTML = `
    <div class="section-head">EXECUTIVE SUMMARY</div>
    <div class="section-sub">Live updates from the current command</div>
    ${summaryCard("orange", "NEXT MOVE", r.next_move, 1)}
    ${summaryCard("blue", "DECISION", r.decision, 1)}
    ${summaryCard("green", "ACTION STEPS", r.action_steps, r.action_steps.length)}
    ${summaryCard("purple", "READY ASSETS", r.ready_assets.length ? r.ready_assets : r.execution_objects.map(o => o.title), r.ready_assets.length || r.execution_objects.length)}
    ${summaryCard("red", "ACTIVE RISKS", r.risk, 1)}
    ${summaryCard("orange", "PRIORITY", r.priority, "High")}
    ${summaryCard("blue", "RECOMMENDED COMMAND", r.recommended_command, 1)}
  `;
}

function summaryCard(color, title, body, count){
  const content = Array.isArray(body) ? `<ul>${body.slice(0,5).map(x => `<li>${esc(textOf(x))}</li>`).join("")}</ul>` : `<p>${esc(textOf(body))}</p>`;
  return `<div class="sum-card ${esc(color)}"><div class="badge">${esc(count)}</div><div class="sum-title">${esc(title)}</div>${content}<div class="note">＋ Add note</div></div>`;
}

function renderIntelRail(){
  if(!els.intel) return;
  const r = state.rightRailState;
  const objects = r?.execution_objects || [];
  els.intel.innerHTML = `
    <h3>EXECUTIVE INTELLIGENCE</h3>
    <div class="search">⌕ Search files, notes, and context... <span style="margin-left:auto">☷</span></div>
    <div class="rail-card"><div class="rail-title">◆ KEY INSIGHT</div><p>${esc(r ? r.executive_summary : "Executive Engine converts commands into saved execution assets.")}</p><div class="link">View insight →</div></div>
    <div class="rail-card"><div class="rail-title">▧ MEMORY</div><p>${esc(objects.length ? `${objects.length} execution object${objects.length === 1 ? "" : "s"} prepared from the latest command.` : "No generated execution objects yet.")}</p><div class="link">View all memory →</div></div>
    <div class="rail-card"><div class="rail-title">▣ READY TO REVIEW</div>${objects.length ? objects.slice(0,5).map((o,i) => `<div class="priority-row"><div class="num">${i+1}</div><div><strong>${esc(o.title)}</strong><br><span>${esc(label(o.type))}</span></div></div>`).join("") : `<p>Run a command to generate review-ready assets.</p>`}<div class="link">View all →</div></div>
    <div class="rail-card"><div class="rail-title">♙ EXECUTION STATE</div><div class="team"><span>Status</span><strong class="ok">${esc(state.isLoading ? "Working" : "Ready")}</strong></div><div class="team"><span>Objects</span><strong>${esc(objects.length)}</strong></div><div class="team"><span>Priority</span><strong>${esc(r?.priority || "Normal")}</strong></div></div>
  `;
}

function bindEvents(){
  els.execute?.addEventListener("click", submitCommand);
  els.clear?.addEventListener("click", () => { if(els.input) els.input.value = ""; });
  els.input?.addEventListener("keydown", e => {
    if(e.key === "Enter" && (e.ctrlKey || e.metaKey)){ e.preventDefault(); submitCommand(); }
  });
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      if(els.input) els.input.value = chip.textContent.trim();
      submitCommand();
    });
  });
}

bindEvents();
renderApp();
