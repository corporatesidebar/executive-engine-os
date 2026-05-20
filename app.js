
/* === V37070 CONNECT FRONTEND TO BACKEND RESPONSE CONTRACT === */
(function(){
const API_URL="https://executive-engine-os.onrender.com/run";
const thread=document.querySelector("#thread,.thread");
const execute=document.querySelector("#executeBtn,.execute");
const input=document.querySelector("#commandInput,textarea,input[type='text']");
const summary=document.querySelector("#executiveSummary,.summary");
const rail=document.querySelector("#rightRail,.rail");

function esc(v){return String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;")}
function arr(v){if(!v)return[];if(Array.isArray(v))return v;if(typeof v==="string")return v.split(/\n|•|- /).map(x=>x.trim()).filter(Boolean);if(typeof v==="object")return Object.values(v).filter(Boolean);return[v]}
function txt(v){if(v==null)return"";if(typeof v==="string")return v;if(Array.isArray(v))return v.map(txt).join(", ");if(typeof v==="object")return Object.entries(v).map(([k,val])=>`${k}: ${txt(val)}`).join(" · ");return String(v)}
function time(){return new Date().toLocaleTimeString([],{hour:"numeric",minute:"2-digit"})}
function list(v){let a=arr(v);return a.length?`<ul>${a.map(i=>`<li>${esc(txt(i))}</li>`).join("")}</ul>`:"<p>Not returned by backend.</p>"}

function userMsg(t){thread.insertAdjacentHTML("beforeend",`<div class="msg"><div class="bubble-avatar">W</div><div><div class="meta"><strong>You</strong><span>${esc(time())}</span></div><div class="copy">${esc(t)}</div></div></div>`);thread.scrollTop=thread.scrollHeight}
function loader(){let el=document.createElement("div");el.className="v37060-loader";el.innerHTML=`<div class="bubble-avatar engine-avatar">E</div><div class="v37060-stream"><div class="meta"><strong>Executive Engine</strong><span>Connecting to backend...</span></div><div class="copy">Running live /run contract and building execution objects from the response.</div><div class="v37060-progress"><span></span></div></div>`;thread.appendChild(el);thread.scrollTop=thread.scrollHeight;return el}
function errorMsg(m){thread.insertAdjacentHTML("beforeend",`<div class="msg"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(time())}</span></div><div class="exec-error">Backend connection failed: ${esc(m)}</div></div></div>`);thread.scrollTop=thread.scrollHeight}

function objects(data){let o=arr(data.execution_objects);if(!o.length)return"";return`<div class="exec-grid">${o.map((x,i)=>{let title=x.title||x.type||x.name||`Execution Object ${i+1}`;let body=x.description||x.summary||x.content||x.value||txt(x);let type=String(x.type||title).toLowerCase();let k=type.includes("proposal")?"proposal":type.includes("meeting")?"meeting":type.includes("kpi")?"kpi":type.includes("asset")?"asset":type.includes("outbound")?"outbound":"workflow";return`<div class="exec-object ${k}"><h4>${esc(title)}</h4><p>${esc(body)}</p></div>`}).join("")}</div>`}
function assets(data){let a=arr(data.ready_assets);if(!a.length)return"";return`<div class="exec-assets">${a.slice(0,6).map(x=>{let title=x.title||x.name||txt(x).slice(0,80);let meta=x.type||x.format||x.status||"Ready asset";return`<div class="exec-asset"><strong>${esc(title)}</strong><span>${esc(meta)}</span><em>⇩</em></div>`}).join("")}</div>`}

function response(data){
let has=Array.isArray(data.execution_objects)&&data.execution_objects.length;
let primary=data.primary_object||data.executive_summary||data.next_move||"Executive response generated.";
return`<div class="msg"><div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>${esc(time())}</span></div><div class="copy">${esc(txt(primary))}</div><div class="exec-package"><div class="exec-head"><div><strong>${esc(data.primary_object?.title||data.primary_object||"Live Backend Execution Package")}</strong><br><span>Rendered from /run response contract</span></div><span class="v37060-pill">${esc(data.priority||"Ready")}</span></div><div class="exec-body">${has?objects(data):`<div class="exec-legacy"><div class="exec-legacy-section"><h4>EXECUTIVE SUMMARY</h4><p>${esc(txt(data.executive_summary||data.executive_scan||"Not returned by backend."))}</p></div><div class="exec-legacy-section"><h4>NEXT MOVE</h4><p>${esc(txt(data.next_move||""))}</p></div><div class="exec-legacy-section"><h4>DECISION</h4><p>${esc(txt(data.decision||""))}</p></div><div class="exec-legacy-section"><h4>ACTION STEPS</h4>${list(data.action_steps)}</div><div class="exec-legacy-section"><h4>RISK</h4><p>${esc(txt(data.risk||""))}</p></div><div class="exec-legacy-section"><h4>RECOMMENDED COMMAND</h4><p>${esc(txt(data.recommended_command||""))}</p></div></div>`}${assets(data)}${data.deployment_sequence?`<div class="exec-object workflow" style="margin-top:10px"><h4>DEPLOYMENT SEQUENCE</h4>${list(data.deployment_sequence)}</div>`:""}</div></div></div></div>`;
}

function updateSummary(data){
if(!summary)return;let actions=arr(data.action_steps), assetsA=arr(data.ready_assets);
summary.innerHTML=`<div class="section-head">EXECUTIVE SUMMARY</div><div class="section-sub">Live updates from backend /run</div>
<div class="sum-card orange"><div class="badge">1</div><div class="sum-title">✕ NEXT MOVE</div><p>${esc(txt(data.next_move||data.executive_summary||"Live response received."))}</p><div class="note">＋ Live response</div></div>
<div class="sum-card"><div class="badge">1</div><div class="sum-title">ℹ DECISION</div><p>${esc(txt(data.decision||"Decision not returned."))}</p><div class="note">＋ Live response</div></div>
<div class="sum-card green"><div class="badge">${actions.length}</div><div class="sum-title">✓ ACTION STEPS</div>${list(actions)}<div class="note">＋ Live response</div></div>
<div class="sum-card purple"><div class="badge">${assetsA.length}</div><div class="sum-title">✦ READY ASSETS</div>${list(assetsA)}<div class="note">＋ Live response</div></div>
<div class="sum-card red"><div class="badge">1</div><div class="sum-title">⚠ ACTIVE RISKS</div><p>${esc(txt(data.risk||"No active risk returned."))}</p><div class="note">＋ Live response</div></div>
<div class="sum-card orange"><div class="sum-title">✪ PRIORITY <span style="margin-left:auto;background:#fff1e8;color:#ff5a13;border-radius:9px;padding:4px 8px">${esc(data.priority||"Medium")}</span></div><p>${esc(txt(data.recommended_command||"Continue with next executive command."))}</p><div class="note">＋ Recommended command</div></div>`;
}
function updateRail(data){
if(!rail)return;let assetsA=arr(data.ready_assets), actions=arr(data.action_steps);
rail.innerHTML=`<h3>EXECUTIVE INTELLIGENCE</h3><div class="search">⌕ Live backend context loaded <span style="margin-left:auto">☷</span></div>
<div class="rail-card"><div class="rail-title">◆ KEY INSIGHT</div><p>${esc(txt(data.executive_scan||data.executive_summary||data.next_move||"Live backend intelligence received."))}</p><div class="link">Live insight →</div></div>
<div class="rail-card"><div class="rail-title">▧ ACTIVE RISK</div><p>${esc(txt(data.risk||"No backend risk returned."))}</p><div class="link">Monitor risk →</div></div>
<div class="rail-card"><div class="rail-title">▣ READY ASSETS</div><p>${esc(assetsA.length?`${assetsA.length} backend asset(s) ready.`:"No ready assets returned.")}</p><div class="link">View assets →</div></div>
<div class="rail-card"><div class="rail-title">✓ EXECUTION STATUS</div><p>${esc(actions.length?`${actions.length} action step(s) generated from live response.`:"Awaiting action steps from backend.")}</p><div class="link">View execution →</div></div>
<div class="rail-card"><div class="rail-title">⌘ RECOMMENDED COMMAND</div><p>${esc(txt(data.recommended_command||"Continue the workflow."))}</p><div class="link">Run next →</div></div>`;
}

async function run(){
if(!thread||!execute)return;let command=(input?.value||"").trim();if(!command){errorMsg("Enter a command before executing.");return}
userMsg(command);if(input)input.value="";execute.disabled=true;let old=execute.textContent;execute.textContent="Executing...";let loading=loader();
try{
let res=await fetch(API_URL,{method:"POST",headers:{"Content-Type":"application/json","Accept":"application/json"},body:JSON.stringify({input:command,mode:"execution",brain:"executive",output_type:"execution_package",depth:"standard"})});
let raw=await res.text();let data;try{data=JSON.parse(raw)}catch(e){data={executive_summary:raw,status:res.status}}
console.log("V37070 /run response:",data);
if(!res.ok)throw new Error(data.detail||data.error||`HTTP ${res.status}`);
loading.remove();thread.insertAdjacentHTML("beforeend",response(data));updateSummary(data);updateRail(data);thread.scrollTop=thread.scrollHeight;
}catch(e){loading.remove();console.error("V37070 /run error:",e);errorMsg(e.message||"Unknown API error.")}
finally{execute.disabled=false;execute.textContent=old||"Execute →"}
}
execute?.addEventListener("click",run);
input?.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key==="Enter")run()});
})();
