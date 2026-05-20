const API_URL = window.EXECUTIVE_ENGINE_API_URL || 'https://executive-engine-os.onrender.com';
const STORAGE_KEY = 'ee_exact_reference_v37030';
const $ = (id)=>document.getElementById(id);
let state = { page:'command', entries:load(), selected:null, projects:[
  {title:'Market Expansion Strategy',status:'Active'}, {title:'Q2 Board Preparation',status:'Active'}, {title:'Pricing Optimization',status:'Active'}
] };

function load(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]')}catch{return []}}
function save(){localStorage.setItem(STORAGE_KEY, JSON.stringify(state.entries.slice(0,60)))}
function esc(s=''){return String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function time(){return new Date().toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})}
function date(){return new Date().toLocaleDateString([], {month:'numeric',day:'numeric',year:'numeric'})}
function uid(){return Math.random().toString(36).slice(2)+Date.now().toString(36)}
function arr(v){if(v==null||v==='')return[]; return Array.isArray(v)?v:[v]}
function first(v){if(!v)return''; if(typeof v==='string')return v; if(Array.isArray(v))return first(v[0]); if(typeof v==='object')return v.title||v.name||v.summary||v.description||v.next_move||v.executive_summary||''; return String(v)}
function copy(txt){navigator.clipboard?.writeText(txt).catch(()=>{})}
function detectCategory(text){const t=(text||'').toLowerCase(); const map={Meeting:['meeting','board','agenda','talking','client','call','prep','objection'],Proposal:['proposal','pitch','scope','pricing','quote','offer'],Decision:['decision','decide','approve','choose','tradeoff'],Risk:['risk','blocker','threat','issue','concern'],Execution:['build','deploy','execute','fix','launch','workflow','make'],Strategy:['strategy','market','growth','position','go-to-market','revenue','expansion']}; for(const [k,words] of Object.entries(map)){if(words.some(w=>t.includes(w)))return k} return 'General'}

async function runCommand(text){
  const input=(text||$('commandInput').value||$('followInput').value).trim(); if(!input) return;
  $('commandInput').value=''; $('followInput').value='';
  const entry={id:uid(), input, category:detectCategory(input), created:`${date()}, ${time()}`, loading:true};
  state.entries.push(entry); save(); render();
  const btn=$('executeBtn'); btn.disabled=true; btn.textContent='Executing...';
  try{
    const res=await fetch(`${API_URL}/run`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input,category:entry.category,render_target:'hybrid_execution_objects'})});
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    const data=await res.json();
    entry.response=normalize(data,input,entry.category); entry.loading=false;
  }catch(e){
    entry.response=normalize(fallback(input,entry.category),input,entry.category); entry.loading=false; entry.warning='Fallback used: live backend unavailable.';
  }
  save(); render(); btn.disabled=false; btn.innerHTML='Execute <span>→</span>';
}

function normalize(data,input,category){
  const r={...(data||{})};
  r.category=r.category||category;
  r.executive_summary=r.executive_summary||r.executive_read||r.clear_answer||r.summary||`I converted this into a ${category.toLowerCase()} execution thread.`;
  r.next_move=r.next_move||r.best_move||'Move the highest-leverage action forward now.';
  r.decision=r.decision||'Proceed with a focused execution path and validate the next dependency.';
  r.action_steps=arr(r.action_steps||r.actions||r.next_steps).slice(0,6);
  r.ready_assets=arr(r.ready_assets||r.assets||r.generated_assets);
  r.risk=r.risk||first(r.risks)||'Execution drift if ownership, timeline, and next command are not locked.';
  r.priority=r.priority||'High';
  r.recommended_command=r.recommended_command||'Create the next execution package with owner, timeline, risk, and ready asset.';
  r.execution_objects=collectObjects(r,input,category);
  return r;
}
function collectObjects(r,input,category){
  const objects=[]; const keys={execution_packages:'execution_package',execution_package:'execution_package',execution_objects:'execution_package',proposal:'proposal',proposal_assets:'proposal',crm_system:'crm',kpi_system:'kpi',outbound_systems:'outbound',deployment_sequence:'deployment',automation_stack:'automation',implementation_plan:'implementation',delegation_map:'delegation',operational_workflows:'workflow'};
  Object.entries(keys).forEach(([k,type])=>{ if(r[k]) arr(r[k]).forEach((x,i)=>objects.push(normalizeObj(x,type,i))) });
  if(!objects.length) objects.push({type:'execution_package',title:`${category} Execution Package`,purpose:r.executive_summary, status:'Ready', preview:r.action_steps, details:r});
  return objects.slice(0,8);
}
function normalizeObj(x,type,i){
  if(typeof x==='string') return {type,title:`${label(type)} ${i+1}`,purpose:x,status:'Ready',preview:[x],details:x};
  if(Array.isArray(x)) return {type,title:`${label(type)} ${i+1}`,purpose:'Operational sequence generated.',status:'Ready',preview:x,details:x};
  const o={...(x||{})}; return {type:o.type||type,title:o.title||o.name||o.package_title||`${label(type)} ${i+1}`,purpose:o.purpose||o.summary||o.business_purpose||o.description||first(o)||'Execution asset generated.',status:o.status||o.deployment_priority||'Ready',preview:arr(o.preview||o.steps||o.deployment_steps||o.deliverables||o.items).slice(0,4),details:o};
}
function label(s){return String(s||'asset').replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase())}
function fallback(input,category){
  if(input.replace(/[^a-z0-9]/gi,'').length<8) return {category:'Clarify',priority:'Medium',executive_summary:'I need a clearer business objective before creating an execution package.',next_move:'State the desired outcome, stakeholder, deadline, and asset you need.',decision:'Do not create fake operational work from unclear input.',action_steps:['Clarify the business objective','Choose the workflow category','Add deadline and stakeholder','Name the asset required'],risk:'Low-signal input creates false certainty.',ready_assets:['Clarifying command'],recommended_command:'Clarify the objective, deadline, stakeholder, and asset needed.'};
  return {category,priority:'High',executive_summary:`Understood. I will convert this ${category.toLowerCase()} request into an executive execution package with assets, next move, risk, and follow-up command.`,next_move:'Create the first operational asset and lock the next decision.',decision:'Proceed with a compact execution path rather than a long text response.',action_steps:['Identify the outcome','Build the primary asset','Define owner and timeline','Surface risk and dependency','Recommend next command'],ready_assets:['Execution package','Action sequence','Follow-up command'],risk:'Execution loses value if it stays as advice instead of saved operational assets.',recommended_command:'Build the full execution package with asset cards, owners, timeline, and risk controls.'}
}

function render(){renderNav(); renderProjects(); renderConversation(); renderSummary(); renderIntel(); renderPressure();}
function renderNav(){document.querySelectorAll('.nav-link').forEach(b=>{b.classList.toggle('active',b.dataset.page===state.page); b.onclick=()=>{state.page=b.dataset.page; renderPageMode(); renderNav();}})}
function renderProjects(){ $('projectList').innerHTML=state.projects.map(p=>`<div class="project-item"><span>▱</span><div><b>${esc(p.title)}</b><small>${esc(p.status)}</small></div></div>`).join('') }
function renderPageMode(){ const conv=$('conversation'); if(state.page==='command'){renderConversation();return;} conv.innerHTML=`<section class="page-mode"><h2>${esc(pageName(state.page))}</h2><p>This page uses the approved cockpit shell. Content will populate from live execution objects and saved workflows.</p><div class="page-grid">${state.entries.slice(-4).reverse().map(e=>`<div class="page-tile"><h3>${esc(e.category)} — ${esc(e.input)}</h3><p>${esc(first(e.response?.executive_summary)||'No response yet.')}</p></div>`).join('') || '<div class="page-tile"><h3>No live items yet</h3><p>Run a command to populate this workspace.</p></div>'}</div></section>` }
function pageName(p){return {daily:'Daily Brief',decisions:'Decisions',meeting:'Meeting Prep',insights:'Insights',strategy:'Strategy Board',risks:'Risk Monitor',team:'Team Pulse',finance:'Financial Snapshot',projects:'Active Projects',files:'Files',notes:'Notes',upload:'Upload Context'}[p]||'Command'}
function renderConversation(){ if(state.page!=='command')return renderPageMode(); const entries=state.entries.length?state.entries:[]; $('conversation').innerHTML= entries.length ? entries.map(turns).join('') : `<div class="empty"><b>No active command thread yet.</b><br/>Enter a command above to create live executive output. No fake thread data is preloaded.</div>`; document.querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>openDetail(b.dataset.detail)); document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=()=>copy(b.dataset.copy));}
function turns(e){ const r=e.response; return `<div class="turn"><div class="turn-avatar">W</div><div class="turn-body"><div class="turn-head"><b>You</b><time>${esc(e.created)}</time></div><p>${esc(e.input)}</p></div></div><div class="turn engine"><div class="turn-avatar">E</div><div class="turn-body"><div class="turn-head"><b>Executive Engine</b><time>${esc(e.created)}</time></div>${e.loading?'<p>Building execution objects...</p>':responseBlock(e)}</div></div>` }
function responseBlock(e){ const r=e.response; const cards=(r.execution_objects||[]).map((o,i)=>assetCard(o,e.id,i)).join(''); return `<p>${esc(r.executive_summary)}</p>${cards?`<div class="asset-row">${cards}</div>`:''}` }
function assetCard(o,id,i){ const color=o.type==='proposal'?'green':o.type==='kpi'?'blue':''; return `<div class="asset-card"><div class="asset-icon ${color}">${icon(o.type)}</div><div><b>${esc(o.title)}</b><small>${esc(label(o.type))} · ${esc(o.status||'Ready')}</small></div><button title="Open" data-detail="${id}:${i}">⌄</button></div>` }
function icon(t){return t==='proposal'?'▤':t==='kpi'?'▥':t==='crm'?'▦':t==='outbound'?'✉':'□'}
function renderSummary(){ const latest=[...state.entries].reverse().find(e=>e.response)?.response; const r=latest||fallback('default','Execution'); const cards=[['orange','NEXT MOVE',r.next_move,1],['blue','DECISION',r.decision,1],['green','ACTION STEPS',r.action_steps,arr(r.action_steps).length||3],['purple','READY ASSETS',r.ready_assets,arr(r.ready_assets).length||3],['red','ACTIVE RISKS',r.risk,2],['yellow','PRIORITY',r.priority,'High'],['blue','RECOMMENDED COMMAND',r.recommended_command,1]]; $('summaryCards').innerHTML=cards.map(card).join('')+splitMini();}
function card([color,title,body,count]){ const content=Array.isArray(body)?`<ul>${body.slice(0,4).map(x=>`<li>${esc(first(x))}</li>`).join('')}</ul>`:`<p>${esc(first(body))}</p>`; return `<article class="summary-card ${color}"><div class="summary-head"><span class="num-dot">${symbol(title)}</span><h3>${title}</h3><span class="count-pill">${esc(count)}</span></div>${title==='PRIORITY'?'<span class="priority-badge">High</span>':''}${content}<button class="add-note">+ Add note</button></article>`}
function symbol(t){return t.includes('MOVE')?'➜':t.includes('DECISION')?'2':t.includes('ACTION')?'✓':t.includes('ASSET')?'⌘':t.includes('RISK')?'△':t.includes('PRIORITY')?'✦':'⚡'}
function splitMini(){return `<div class="split-mini"><article class="summary-card blue"><div class="summary-head"><span class="num-dot">✓</span><h3>RECENT DECISIONS</h3></div><ul><li>Execution path approved</li><li>Renderer lock preserved</li></ul><button class="add-note">+ Add note</button></article><article class="summary-card green"><div class="summary-head"><span class="num-dot">✓</span><h3>SYSTEM STATUS</h3></div><p>All systems operating normally</p><button class="add-note">Last updated: now</button></article></div>`}
function renderIntel(){ $('intelCards').innerHTML = [intel('⌖','KEY INSIGHT','Executive Engine should convert commands into saved execution assets, not text-only replies.','View insight →'),intel('⌬','MEMORY','You prefer concise proposals with clear ROI, risk analysis, and operator-grade next moves.','View all memory →'),upcoming(),team(),intel('☷','EXECUTIVE SUMMARY','Focus: execution object rendering, design lock, and reduced cognitive load.','View full summary →')].join('') }
function intel(ic,t,b,l){return `<article class="intel-card"><div class="intel-title"><span class="intel-icon">${ic}</span><h3>${t}</h3></div><p>${b}</p><a>${l}</a></article>`}
function upcoming(){return `<article class="intel-card"><div class="intel-title"><span class="intel-icon">□</span><h3>UPCOMING PRIORITIES</h3></div><div class="upcoming"><div class="upcoming-row"><span class="rank">1</span><p><b>Board Meeting</b><br/>May 27, 2026 · 10:00 AM</p></div><div class="upcoming-row"><span class="rank">2</span><p><b>Investor Update</b><br/>May 30, 2026 · 1:00 PM</p></div><div class="upcoming-row"><span class="rank">3</span><p><b>Strategy Review</b><br/>June 2, 2026 · 9:00 AM</p></div></div><a>View all →</a></article>`}
function team(){return `<article class="intel-card"><div class="intel-title"><span class="intel-icon">♙</span><h3>TEAM PULSE</h3></div><div class="team-row"><span>Sales</span><b class="ok">On Track</b></div><div class="team-row"><span>Marketing</span><b class="ok">On Track</b></div><div class="team-row"><span>Operations</span><b class="bad">At Risk</b></div><a>View team pulse →</a></article>`}
function renderPressure(){ const latest=[...state.entries].reverse().find(e=>e.response); const score=latest?Math.min(88,Math.max(18,(latest.response.action_steps?.length||2)*9 + (latest.response.priority==='High'?26:12))):26; $('pressureScore').textContent=score; $('pressureLabel').textContent=score>=60?'High':score>=25?'Medium':'Low'; }
function openDetail(key){ const [id,idx]=key.split(':'); const entry=state.entries.find(e=>e.id===id); const obj=entry?.response?.execution_objects?.[Number(idx)]; if(!obj)return; const drawer=document.createElement('div'); drawer.className='detail-drawer'; drawer.innerHTML=`<div class="drawer-head"><div><h2>${esc(obj.title)}</h2><p>${esc(label(obj.type))} · ${esc(obj.status||'Ready')}</p></div><button id="closeDrawer">×</button></div><div class="detail-section"><h3>Purpose</h3><p>${esc(obj.purpose||'Execution asset generated.')}</p></div><div class="detail-section"><h3>Preview</h3><ul>${arr(obj.preview).map(x=>`<li>${esc(first(x))}</li>`).join('')}</ul></div><div class="detail-section"><h3>Full Object</h3><pre>${esc(JSON.stringify(obj.details||obj,null,2))}</pre></div><button class="copy-btn" id="copyObj">Copy Object</button>`; document.body.appendChild(drawer); $('closeDrawer').onclick=()=>drawer.remove(); $('copyObj').onclick=()=>copy(JSON.stringify(obj.details||obj,null,2)); }

$('executeBtn').onclick=()=>runCommand(); $('sendFollowBtn').onclick=()=>runCommand($('followInput').value); $('clearBtn').onclick=()=>{$('commandInput').value='';$('followInput').value=''}; $('commandInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey))runCommand()}); $('followInput').addEventListener('keydown',e=>{if(e.key==='Enter')runCommand($('followInput').value)}); document.querySelectorAll('.quick-chips button').forEach(b=>b.onclick=()=>runCommand(b.dataset.prompt)); $('newProjectBtn').onclick=()=>{state.projects.unshift({title:'New Executive Workflow',status:'Active'});renderProjects()};
render();
