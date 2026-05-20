
(function(){
"use strict";

const API_URL = "https://executive-engine-os.onrender.com/run";

function $(sel){ return document.querySelector(sel); }
function esc(v){ return String(v ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[c])); }
function text(v){
  if(v == null) return "";
  if(typeof v === "string") return v;
  if(Array.isArray(v)) return v.map(text).join(", ");
  if(typeof v === "object") return Object.entries(v).map(([k,val]) => `${k}: ${text(val)}`).join(" · ");
  return String(v);
}
function arr(v){
  if(!v) return [];
  if(Array.isArray(v)) return v;
  if(typeof v === "string") return v.split(/\n|•|- /).map(x => x.trim()).filter(Boolean);
  if(typeof v === "object") return Object.values(v).filter(Boolean);
  return [v];
}
function now(){ return new Date().toLocaleTimeString([], {hour:"numeric", minute:"2-digit"}); }

function boot(){
  const thread = $("#thread") || $(".thread");
  const btn = $("#executeBtn") || $(".execute");
  const input = $("#commandInput") || $("textarea") || $("input[type='text']");
  const summary = $("#executiveSummary") || $(".summary");
  const rail = $("#rightRail") || $(".rail");

  if(!thread || !btn || !input){
    console.error("V37080 boot failed", {thread, btn, input});
    return;
  }

  function scroll(){ thread.scrollTop = thread.scrollHeight; }

  function userMessage(command){
    thread.insertAdjacentHTML("beforeend", `
      <div class="msg">
        <div class="bubble-avatar">W</div>
        <div>
          <div class="meta"><strong>You</strong><span>${esc(now())}</span></div>
          <div class="copy">${esc(command)}</div>
        </div>
      </div>`);
    scroll();
  }

  function loader(){
    const el = document.createElement("div");
    el.className = "msg";
    el.innerHTML = `
      <div class="bubble-avatar engine-avatar">E</div>
      <div>
        <div class="meta"><strong>Executive Engine</strong><span>${esc(now())}</span></div>
        <div class="v37060-stream">
          <div class="copy">Executing live backend request…</div>
          <div class="v37060-progress"><span></span></div>
        </div>
      </div>`;
    thread.appendChild(el);
    scroll();
    return el;
  }

  function errorMessage(msg){
    thread.insertAdjacentHTML("beforeend", `
      <div class="msg">
        <div class="bubble-avatar engine-avatar">E</div>
        <div>
          <div class="meta"><strong>Executive Engine</strong><span>${esc(now())}</span></div>
          <div class="runtime-error">${esc(msg)}</div>
        </div>
      </div>`);
    scroll();
  }

  function list(items){
    const a = arr(items);
    if(!a.length) return "<p>Not returned.</p>";
    return `<ul>${a.map(i => `<li>${esc(text(i))}</li>`).join("")}</ul>`;
  }

  function cards(data){
    const objs = arr(data.execution_objects);
    if(objs.length){
      return `<div class="runtime-grid">${objs.map((o,i)=>{
        const title = o.title || o.name || o.type || `Execution Object ${i+1}`;
        const body = o.description || o.summary || o.content || o.value || text(o);
        return `<div class="runtime-card"><h4>${esc(title)}</h4><p>${esc(body)}</p></div>`;
      }).join("")}</div>`;
    }

    return `
      <div class="runtime-section"><h4>EXECUTIVE SUMMARY</h4><p>${esc(text(data.executive_summary || data.executive_scan || data.summary || "Live backend response received."))}</p></div>
      <div class="runtime-section"><h4>NEXT MOVE</h4><p>${esc(text(data.next_move || ""))}</p></div>
      <div class="runtime-section"><h4>DECISION</h4><p>${esc(text(data.decision || ""))}</p></div>
      <div class="runtime-section"><h4>ACTION STEPS</h4>${list(data.action_steps)}</div>
      <div class="runtime-section"><h4>READY ASSETS</h4>${list(data.ready_assets)}</div>
      <div class="runtime-section"><h4>RISK</h4><p>${esc(text(data.risk || ""))}</p></div>
      <div class="runtime-section"><h4>RECOMMENDED COMMAND</h4><p>${esc(text(data.recommended_command || ""))}</p></div>`;
  }

  function responseMessage(data){
    console.log("V37080 parsed backend response", data);
    const top = data.primary_object || data.executive_summary || data.executive_scan || data.next_move || data.message || "Response generated.";
    thread.insertAdjacentHTML("beforeend", `
      <div class="msg">
        <div class="bubble-avatar engine-avatar">E</div>
        <div>
          <div class="meta"><strong>Executive Engine</strong><span>${esc(now())}</span></div>
          <div class="copy">${esc(text(top))}</div>
          <div class="runtime-package">${cards(data)}</div>
        </div>
      </div>`);
    scroll();
  }

  function updateSummary(data){
    if(!summary) return;
    const actions = arr(data.action_steps), assets = arr(data.ready_assets);
    summary.innerHTML = `
      <div class="section-head">EXECUTIVE SUMMARY</div><div class="section-sub">Live backend response</div>
      <div class="sum-card orange"><div class="badge">1</div><div class="sum-title">✕ NEXT MOVE</div><p>${esc(text(data.next_move || data.executive_summary || "Live response received."))}</p><div class="note">＋ Backend</div></div>
      <div class="sum-card"><div class="badge">1</div><div class="sum-title">ℹ DECISION</div><p>${esc(text(data.decision || "Decision not returned."))}</p><div class="note">＋ Backend</div></div>
      <div class="sum-card green"><div class="badge">${actions.length}</div><div class="sum-title">✓ ACTION STEPS</div>${list(actions)}<div class="note">＋ Backend</div></div>
      <div class="sum-card purple"><div class="badge">${assets.length}</div><div class="sum-title">✦ READY ASSETS</div>${list(assets)}<div class="note">＋ Backend</div></div>
      <div class="sum-card red"><div class="badge">1</div><div class="sum-title">⚠ ACTIVE RISKS</div><p>${esc(text(data.risk || "No risk returned."))}</p><div class="note">＋ Backend</div></div>
      <div class="sum-card orange"><div class="sum-title">✪ PRIORITY <span style="margin-left:auto;background:#fff1e8;color:#ff5a13;border-radius:9px;padding:4px 8px">${esc(data.priority || "Medium")}</span></div><p>${esc(text(data.recommended_command || "Continue the workflow."))}</p></div>`;
  }

  function updateRail(data){
    if(!rail) return;
    const actions = arr(data.action_steps), assets = arr(data.ready_assets);
    rail.innerHTML = `
      <h3>EXECUTIVE INTELLIGENCE</h3>
      <div class="search">⌕ Live backend context loaded <span style="margin-left:auto">☷</span></div>
      <div class="rail-card"><div class="rail-title">◆ KEY INSIGHT</div><p>${esc(text(data.executive_scan || data.executive_summary || data.next_move || "Live backend intelligence received."))}</p><div class="link">Live insight →</div></div>
      <div class="rail-card"><div class="rail-title">▧ ACTIVE RISK</div><p>${esc(text(data.risk || "No backend risk returned."))}</p><div class="link">Monitor risk →</div></div>
      <div class="rail-card"><div class="rail-title">▣ READY ASSETS</div><p>${assets.length ? `${assets.length} backend asset(s) ready.` : "No ready assets returned."}</p><div class="link">View assets →</div></div>
      <div class="rail-card"><div class="rail-title">✓ EXECUTION STATUS</div><p>${actions.length ? `${actions.length} action step(s) generated.` : "No action steps returned."}</p><div class="link">View execution →</div></div>
      <div class="rail-card"><div class="rail-title">⌘ RECOMMENDED COMMAND</div><p>${esc(text(data.recommended_command || "Continue the workflow."))}</p><div class="link">Run next →</div></div>`;
  }

  async function run(){
    const command = input.value.trim();
    if(!command){ errorMessage("Enter a command before executing."); return; }

    userMessage(command);
    input.value = "";
    btn.disabled = true;
    const old = btn.textContent;
    btn.textContent = "Executing...";
    const load = loader();

    try{
      const res = await fetch(API_URL, {
        method:"POST",
        headers:{ "Content-Type":"application/json", "Accept":"application/json" },
        body: JSON.stringify({ input: command, mode: "execution", brain: "executive", output_type: "execution_package", depth: "standard" })
      });

      const raw = await res.text();
      let data;
      try { data = JSON.parse(raw); }
      catch { data = { executive_summary: raw, status: res.status }; }

      console.log("V37080 /run status", res.status);
      console.log("V37080 /run raw", raw);
      console.log("V37080 /run json", data);

      if(!res.ok) throw new Error(data.detail || data.error || raw || `HTTP ${res.status}`);

      load.remove();
      responseMessage(data);
      updateSummary(data);
      updateRail(data);
    }catch(e){
      load.remove();
      console.error("V37080 /run failed", e);
      errorMessage(e.message || "API request failed.");
    }finally{
      btn.disabled = false;
      btn.textContent = old || "Execute →";
    }
  }

  btn.onclick = run;
  input.addEventListener("keydown", e => {
    if((e.ctrlKey || e.metaKey) && e.key === "Enter") run();
  });

  console.log("V37080 runtime connected", { API_URL, thread: !!thread, button: !!btn, input: !!input });
}

if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();

})();
