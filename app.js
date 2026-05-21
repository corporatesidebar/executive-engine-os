const API_URL = "https://executive-engine-os.onrender.com/run";

const els = {
  input: document.getElementById("commandInput"),
  execute: document.getElementById("executeBtn"),
  clear: document.getElementById("clearBtn"),
  thread: document.getElementById("thread"),
  summary: document.getElementById("summaryRail"),
  intel: document.getElementById("intelRail"),
  composer: document.querySelector(".composer"),
};

const state = {
  messages: [],
  decisions: [],
  actions: [],
  assets: [],
  risks: [],
  contexts: [],
  savedDecisions: [],
  lastResponse: null,
  lastCommand: "",
  isLoading: false,
};

function uid(){ return "m_" + Math.random().toString(36).slice(2) + Date.now().toString(36); }
function now(){ return new Date().toLocaleString([], { month:"numeric", day:"numeric", hour:"numeric", minute:"2-digit" }); }
function esc(v=""){ return String(v ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c])); }
function normalizeText(v){
  if(v == null || v === "") return "";
  if(typeof v === "string") return v;
  if(typeof v === "number" || typeof v === "boolean") return String(v);
  if(Array.isArray(v)) return v.map(normalizeText).filter(Boolean).join("\n");
  if(typeof v === "object") return v.title || v.name || v.summary || v.description || v.content || v.text || JSON.stringify(v);
  return String(v);
}
function toArray(v){
  if(v == null || v === "") return [];
  if(Array.isArray(v)) return v.map(x => typeof x === "object" ? x : { title: normalizeText(x) }).filter(x => normalizeText(x.title || x.description || x));
  const raw = normalizeText(v);
  return raw.split(/\n|;|•/).map(x => x.trim()).filter(Boolean).map(x => ({ title:x }));
}
function firstValue(obj, keys){
  for(const key of keys){ if(obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== "") return obj[key]; }
  return "";
}
function compact(v, fallback){ return normalizeText(v).trim() || fallback; }
function label(s){ return String(s || "asset").replace(/_/g," ").replace(/\b\w/g, m => m.toUpperCase()); }

function buildPayload(command){
  return { input: command, mode:"execution", brain:"operator", output_type:"standard", depth:"standard", provider:"openai" };
}

function parseResponse(raw){
  const r = raw && typeof raw === "object" ? raw : { next_move: normalizeText(raw) };
  const scan = r.executive_scan || r.scan || {};
  const nextMove = compact(firstValue(r,["next_move","nextMove","what_to_do_now","recommendation"]) || scan.move, "Confirm the objective, then move the highest-leverage action forward.");
  const decision = compact(firstValue(r,["decision","recommended_decision","operator_decision"]) || scan.decision, "Proceed, but only after the objective, owner, deadline, and asset are clear.");
  const actions = toArray(firstValue(r,["action_steps","actions","steps","next_steps","immediate_actions","execution_sequence"]));
  const assets = toArray(firstValue(r,["ready_assets","assets","prepared_assets","deliverables","generated_assets"]));
  const risk = compact(firstValue(r,["risk","risks","active_risks","risk_control"]) || scan.risk, "Unclear input can create false certainty. Lock the outcome before execution.");
  const priority = compact(firstValue(r,["priority","urgency","pressure_level"]), "High");
  const recommended = compact(firstValue(r,["recommended_command","follow_up_command","next_command","command"]), `Turn this into a 7-step action plan for: ${state.lastCommand || "this objective"}`);
  const summary = compact(firstValue(r,["executive_summary","summary","clear_answer"]) || scan.dominant_insight || nextMove, nextMove);
  const why = compact(firstValue(r,["why_it_matters","business_impact","strategic_value"]), "This matters because the command needs to become an operating path, not a loose answer.");
  const safeActions = actions.length ? actions.slice(0,7) : [
    { title:"Clarify the outcome" }, { title:"Name the owner" }, { title:"Set the deadline" }, { title:"Prepare the required asset" }
  ];
  const safeAssets = assets.length ? assets.slice(0,6) : [{ title:"Execution brief", description:"A working asset created from the latest command." }];
  return { raw:r, summary, why, next_move: nextMove, decision, action_steps:safeActions, ready_assets:safeAssets, risk, priority, recommended_command: recommended, provider_used:r.provider_used || "backend", status:r.status || "success" };
}

function addUserMessage(command){ state.messages.push({ id:uid(), role:"user", content:command, created:now() }); }
function addAssistantLoading(){ const id=uid(); state.messages.push({ id, role:"assistant", status:"loading", created:now() }); return id; }
function replaceMessage(id, patch){ const i=state.messages.findIndex(m=>m.id===id); if(i>=0) state.messages[i] = { ...state.messages[i], ...patch }; }

async function submitCommand(commandOverride){
  const command = (commandOverride || els.input?.value || "").trim();
  if(!command || state.isLoading) return;
  state.lastCommand = command;
  state.isLoading = true;
  addUserMessage(command);
  const loadingId = addAssistantLoading();
  if(els.input) els.input.value = "";
  setComposerValue("");
  renderThread();
  renderButtons();
  try{
    const res = await fetch(API_URL, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(buildPayload(command)) });
    const bodyText = await res.text();
    let data; try{ data = JSON.parse(bodyText); }catch{ data = { executive_summary: bodyText }; }
    if(!res.ok) throw new Error(data.detail || data.error || `Backend returned HTTP ${res.status}`);
    const parsed = parseResponse(data);
    applyRuntimeState(parsed, command);
    replaceMessage(loadingId, { status:"success", response:parsed, content:parsed.summary, created:now() });
  }catch(err){
    replaceMessage(loadingId, { status:"error", content: err?.message || "Frontend could not connect to backend.", created:now() });
  }finally{
    state.isLoading = false;
    renderAll();
  }
}

function applyRuntimeState(r, command){
  state.lastResponse = r;
  state.decisions.unshift({ title:r.decision, command, created:now(), priority:r.priority });
  r.action_steps.forEach((a,i)=> state.actions.unshift({ title: compact(a.title || a.name || a.description || a, `Action ${i+1}`), status:i===0?"Next":"Open", command }));
  r.ready_assets.forEach((a,i)=> state.assets.unshift({ title: compact(a.title || a.name || a.asset_name || a, `Ready asset ${i+1}`), description: compact(a.description || a.summary || a.purpose, "Prepared from latest command."), type:a.type || a.asset_type || "Execution Asset" }));
  state.risks.unshift({ title:r.risk, mitigation:`Mitigation: ${r.next_move}`, command });
  state.contexts.unshift({ command, focus:r.next_move, recommended:r.recommended_command, created:now() });
  state.decisions = state.decisions.slice(0,12); state.actions = state.actions.slice(0,20); state.assets = state.assets.slice(0,20); state.risks = state.risks.slice(0,12); state.contexts = state.contexts.slice(0,12);
}

function renderAll(){ renderThread(); renderSummary(); renderIntel(); renderButtons(); }
function renderButtons(){ if(els.execute){ els.execute.disabled=state.isLoading; els.execute.textContent=state.isLoading ? "Executing..." : "Execute →"; } }

function renderThread(){
  if(!els.thread) return;
  const follow = getComposerHTML();
  const runtime = state.messages.map(renderMessage).join("");
  if(runtime){
    const existingDemo = state.messages.length === 0 ? els.thread.innerHTML : "";
    els.thread.innerHTML = existingDemo || runtime + follow;
  }else{
    // Preserve the approved 28(1) demo thread before the first live command.
    ensureComposerBound();
    return;
  }
  bindRuntimeButtons();
  els.thread.scrollTop = els.thread.scrollHeight;
}

function renderMessage(m){
  if(m.role === "user") return `<div class="msg user-msg"><div class="bubble-avatar">W</div><div><div class="meta"><strong>You</strong><span>${esc(m.created)}</span></div><div class="copy user-copy">${esc(m.content)}</div></div></div>`;
  if(m.status === "loading") return `<div class="msg engine"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div><div class="workflow-card loading-card">Building executive workflow…</div></div></div>`;
  if(m.status === "error") return `<div class="msg engine"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div><div class="risk-block"><strong>Connection issue</strong><p>${esc(m.content)}</p></div></div></div>`;
  return `<div class="msg engine"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(m.created)}</span></div>${renderWorkflowCard(m.response)}</div></div>`;
}

function renderWorkflowCard(r){
  return `<div class="workflow-card">
    <div class="wf-section clear-answer"><span>Clear Answer</span><p>${esc(r.summary)}</p></div>
    <div class="wf-section why"><span>Why it matters</span><p>${esc(r.why)}</p></div>
    <div class="do-next"><span>Do this next</span><strong>${esc(r.next_move)}</strong></div>
    <div class="wf-split"><div class="wf-section"><span>Decision</span><p>${esc(r.decision)}</p></div><div class="wf-section"><span>Priority</span><p>${esc(r.priority)}</p></div></div>
    <div class="task-list">${r.action_steps.map((a,i)=>`<div class="task-row"><span class="check">${i===0?"→":"○"}</span><div><strong>${esc(compact(a.title || a.name || a.description || a, `Action ${i+1}`))}</strong><small>${i===0?"Next":"Open"}</small></div></div>`).join("")}</div>
    <div class="asset-grid">${r.ready_assets.map((a,i)=>`<div class="asset-card"><div class="doc-icon">▤</div><div><strong>${esc(compact(a.title || a.name || a.asset_name || a, `Asset ${i+1}`))}</strong><span>${esc(compact(a.description || a.summary || a.purpose || a.type, "Ready to use"))}</span></div></div>`).join("")}</div>
    <div class="risk-block"><strong>Active risk</strong><p>${esc(r.risk)}</p><small>Mitigation: ${esc(r.next_move)}</small></div>
    <button class="recommended-btn" data-command="${esc(r.recommended_command)}">Continue with recommended command →</button>
    <div class="workflow-actions"><button data-action="plan">Turn into action plan</button><button data-action="asset">Draft asset</button><button data-action="decision">Save decision</button></div>
  </div>`;
}

function getComposerHTML(){ return `<div class="composer runtime-composer"><input id="followInput" placeholder="Ask a follow-up or refine your request..." /><div class="composer-icons"><span>♩</span><button id="followSend" type="button">▷</button></div></div>`; }
function ensureComposerBound(){ setupComposer(); }
function setupComposer(){
  const input = document.getElementById("followInput") || document.querySelector(".composer input");
  const send = document.getElementById("followSend") || document.querySelector(".composer button");
  send?.addEventListener("click", () => submitCommand(input?.value || ""));
  input?.addEventListener("keydown", e => { if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); submitCommand(input.value); } });
}
function setComposerValue(v){ const input = document.getElementById("followInput") || document.querySelector(".composer input"); if(input) input.value = v; }

function bindRuntimeButtons(){
  setupComposer();
  els.thread.querySelectorAll("[data-command]").forEach(btn => btn.addEventListener("click", () => submitCommand(btn.getAttribute("data-command") || "")));
  els.thread.querySelectorAll("[data-action]").forEach(btn => btn.addEventListener("click", () => handleAction(btn.getAttribute("data-action"))));
}

function handleAction(action){
  const r = state.lastResponse; if(!r) return;
  if(action === "plan"){
    const plan = { summary:"Action plan created from the current response.", why:"This converts the answer into trackable execution.", next_move:"Work the first open task now.", decision:r.decision, action_steps:r.action_steps, ready_assets:r.ready_assets, risk:r.risk, priority:r.priority, recommended_command:r.recommended_command };
    state.messages.push({ id:uid(), role:"assistant", status:"success", response:plan, created:now() });
  }
  if(action === "asset"){
    const asset = { title:"Draft asset package", description:r.ready_assets.map(a=>compact(a.title||a)).join("; ") || r.summary, type:"Draft" };
    state.assets.unshift(asset);
    state.messages.push({ id:uid(), role:"assistant", status:"success", response:{...r, summary:"Draft asset package prepared.", why:"This turns the workflow into a usable deliverable.", next_move:"Review the asset card and decide what to send or refine.", ready_assets:[asset], action_steps:[{title:"Review draft asset"},{title:"Confirm audience"},{title:"Send or refine"}]}, created:now() });
  }
  if(action === "decision"){
    state.savedDecisions.unshift({ title:r.decision, created:now() });
    state.messages.push({ id:uid(), role:"assistant", status:"success", response:{...r, summary:"Decision saved to the runtime decision workspace.", why:"Captured decisions create continuity instead of another disposable answer.", next_move:r.recommended_command, action_steps:[{title:"Use the saved decision as the operating assumption"},{title:"Move the next action forward"}]}, created:now() });
  }
  renderAll();
}

function card(color,title,body,count){
  const html = Array.isArray(body) ? `<ul>${body.slice(0,5).map(x=>`<li>${esc(compact(x.title || x.name || x.description || x, ""))}</li>`).join("")}</ul>` : `<p>${esc(compact(body,"—"))}</p>`;
  return `<div class="sum-card ${color}"><div class="badge">${esc(count ?? "")}</div><div class="sum-title">${esc(title)}</div>${html}<div class="note">＋ Add note</div></div>`;
}
function renderSummary(){
  if(!els.summary || !state.lastResponse) return;
  const r = state.lastResponse;
  els.summary.innerHTML = `<div class="section-head">EXECUTIVE SUMMARY</div><div class="section-sub">Live updates from the conversation</div>
    ${card("orange","NEXT MOVE",r.next_move,1)}${card("","DECISION",r.decision,state.decisions.length)}${card("green","ACTION STEPS",r.action_steps,r.action_steps.length)}${card("purple","READY ASSETS",r.ready_assets,r.ready_assets.length)}${card("red","ACTIVE RISKS",r.risk,state.risks.length)}${card("orange","PRIORITY",r.priority,r.priority)}${card("","RECOMMENDED COMMAND",r.recommended_command,1)}
    <div class="half"><div class="sum-card tiny"><div class="sum-title">RECENT DECISIONS</div><ul>${state.decisions.slice(0,2).map(d=>`<li>${esc(d.title)}</li>`).join("")}</ul></div><div class="sum-card tiny green"><div class="sum-title">SYSTEM STATUS</div><p>Runtime state active</p><div class="note">Updated now</div></div></div>`;
}
function renderIntel(){
  if(!els.intel || !state.lastResponse) return;
  const r = state.lastResponse;
  els.intel.innerHTML = `<h3>EXECUTIVE INTELLIGENCE</h3><div class="search">⌕ Search files, notes, and context... <span style="margin-left:auto">☷</span></div>
    <div class="rail-card"><div class="rail-title">◆ CURRENT FOCUS</div><p>${esc(r.next_move)}</p><div class="link">View focus →</div></div>
    <div class="rail-card"><div class="rail-title">▧ ACTIVE RISK</div><p>${esc(r.risk)}</p><div class="link">View mitigation →</div></div>
    <div class="rail-card"><div class="rail-title">▣ WORKSPACE ITEMS</div><div class="priority-row"><div class="num">${state.actions.length}</div><div><strong>Actions</strong><br><span>Runtime tasks created</span></div></div><div class="priority-row"><div class="num">${state.assets.length}</div><div><strong>Assets</strong><br><span>Runtime assets prepared</span></div></div><div class="priority-row"><div class="num">${state.decisions.length}</div><div><strong>Decisions</strong><br><span>Captured from responses</span></div></div><div class="link">View all →</div></div>
    <div class="rail-card"><div class="rail-title">⚡ RECOMMENDED FOLLOW-UP</div><p>${esc(r.recommended_command)}</p><button class="recommended-btn rail-run" data-command="${esc(r.recommended_command)}">Run follow-up →</button></div>`;
  els.intel.querySelectorAll("[data-command]").forEach(btn => btn.addEventListener("click", () => submitCommand(btn.getAttribute("data-command") || "")));
}

function bindNav(){
  document.querySelectorAll(".nav-item").forEach(item => item.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active")); item.classList.add("active");
    const name = item.textContent.trim().toLowerCase();
    if(!state.lastResponse) return;
    let response = null;
    if(name.includes("decision")) response = {...state.lastResponse, summary:"Decision workspace opened.", why:"These are decisions captured from the live thread.", next_move: state.decisions[0]?.title || state.lastResponse.decision, action_steps: state.decisions.map(d=>({title:d.title})), ready_assets: []};
    else if(name.includes("risk")) response = {...state.lastResponse, summary:"Risk monitor opened.", why:"This shows what could block the current objective.", next_move: state.risks[0]?.mitigation || state.lastResponse.next_move, action_steps: state.risks.map(r=>({title:r.title})), ready_assets: []};
    else if(name.includes("active projects") || name.includes("strategy")) response = {...state.lastResponse, summary:"Action workspace opened.", why:"These are the task rows created from the latest command.", next_move: state.actions[0]?.title || state.lastResponse.next_move, action_steps: state.actions.map(a=>({title:a.title})), ready_assets: state.assets};
    if(response){ state.messages.push({ id:uid(), role:"assistant", status:"success", response, created:now() }); renderAll(); }
  }));
}

function initComposer(){
  if(els.composer){
    els.composer.innerHTML = `<input id="followInput" placeholder="Ask a follow-up or refine your request..." /><div class="composer-icons"><span>♩</span><button id="followSend" type="button">▷</button></div>`;
  }
  setupComposer();
}

els.execute?.addEventListener("click", () => submitCommand());
els.clear?.addEventListener("click", () => { if(els.input) els.input.value = ""; });
els.input?.addEventListener("keydown", e => { if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); submitCommand(); } });
document.querySelectorAll(".chip").forEach(chip => chip.addEventListener("click", () => { if(els.input) els.input.value = chip.textContent.trim(); submitCommand(); }));
initComposer();
bindNav();
renderButtons();



/* V37300 — Executive Response Compression Engine */
(function(){
  function esc2(v=""){
    return String(v ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  }

  function arr2(v){
    if(v == null || v === "") return [];
    return Array.isArray(v) ? v : [v];
  }

  function label2(s){
    return String(s || "object").replace(/_/g, " ").replace(/\b\w/g, m => m.toUpperCase());
  }

  function text2(v){
    if(v == null) return "";
    if(typeof v === "string") return v;
    if(typeof v === "number") return String(v);
    if(Array.isArray(v)) return v.map(text2).filter(Boolean).join(", ");
    if(typeof v === "object") return v.title || v.name || v.summary || v.description || v.content || v.next_move || v.executive_summary || JSON.stringify(v);
    return String(v);
  }

  function short(v, max=160){
    const t = text2(v);
    return t.length > max ? t.slice(0, max - 1) + "…" : t;
  }

  function list(items, max=5){
    const clean = arr2(items).filter(Boolean).slice(0, max);
    if(!clean.length) return "<ul><li>Prepared for review.</li></ul>";
    return `<ul>${clean.map(x => `<li>${esc2(short(x, 140))}</li>`).join("")}</ul>`;
  }

  function detailJSON(value){
    try { return JSON.stringify(value || {}, null, 2); }
    catch { return text2(value); }
  }

  window.renderObjectCard = function renderObjectCardCompressed(o){
    const id = "obj_" + Math.random().toString(36).slice(2);
    return `
      <div class="ee-object-card" id="${id}">
        <div class="ee-object-head">
          <div>
            <strong>${esc2(o.title || "Execution Asset")}</strong>
            <small>${esc2(label2(o.type || o.object_type))} · ${esc2(o.status || "Ready")}</small>
          </div>
          <div class="ee-object-actions">
            <button class="ee-mini-btn" onclick="document.getElementById('${id}').classList.toggle('open')">View</button>
            <button class="ee-mini-btn" data-copy="${esc2(detailJSON(o.details || o.payload || o))}">Copy</button>
          </div>
        </div>
        <div class="ee-details"><pre>${esc2(detailJSON(o.details || o.payload || o))}</pre></div>
      </div>
    `;
  };

  window.renderAssistantResponse = function renderAssistantResponseCompressed(r){
    if(!r) return `<div class="copy">Response received.</div>`;

    const actionSteps = arr2(r.action_steps).slice(0, 5);
    const readyAssets = arr2(r.ready_assets).slice(0, 5);
    const objects = arr2(r.execution_objects).slice(0, 6);

    const objectCards = objects.length
      ? `<div class="ee-object-strip">${objects.map(window.renderObjectCard).join("")}</div>`
      : "";

    const assetChips = (objects.length ? objects : readyAssets).slice(0, 4).map((item, i) => {
      const title = item.title || item.asset_name || text2(item);
      const type = item.type || item.object_type || "Ready asset";
      return `<div class="ee-asset-chip"><strong>${esc2(short(title, 70))}</strong><span>${esc2(label2(type))}</span></div>`;
    }).join("");

    return `
      <div class="ee-compressed-response">
        <div class="ee-command-answer">
          <div class="ee-answer-top">
            <div class="ee-answer-cell">
              <div class="ee-label">Clear Answer</div>
              <strong>${esc2(short(r.executive_summary || r.next_move, 190))}</strong>
            </div>
            <div class="ee-answer-cell">
              <div class="ee-label">Decision</div>
              <strong>${esc2(short(r.decision, 170))}</strong>
            </div>
            <div class="ee-answer-cell">
              <div class="ee-label">Priority</div>
              <span class="ee-priority-pill">${esc2(short(r.priority || "High", 20))}</span>
            </div>
          </div>
          <div class="ee-primary-action">
            <div class="ee-label">Do this next</div>
            <strong>${esc2(short(r.next_move, 220))}</strong>
          </div>
        </div>

        <div class="ee-compressed-grid">
          <div class="ee-list-card">
            <div class="ee-label">Action Path</div>
            ${list(actionSteps, 5)}
          </div>
          <div class="ee-assets-card">
            <div class="ee-label">Ready to Review</div>
            <div class="ee-assets-row">${assetChips || `<div class="ee-asset-chip"><strong>Execution package</strong><span>Ready</span></div>`}</div>
          </div>
        </div>

        ${objectCards}

        <div class="ee-risk-card">
          <div class="ee-label">Risk Control</div>
          <p>${esc2(short(r.risk, 220))}</p>
        </div>

        <button class="ee-followup" type="button">${esc2(short(r.recommended_command || "Continue with recommended command", 90))} →</button>

        <div class="ee-action-row">
          <button type="button">Turn into action plan</button>
          <button type="button">Draft asset</button>
          <button type="button">Save decision</button>
        </div>
      </div>
    `;
  };
})();
