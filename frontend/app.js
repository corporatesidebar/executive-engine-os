const API_URL = window.EXECUTIVE_ENGINE_API_URL || 'https://executive-engine-os.onrender.com';
const STORAGE_KEY = 'ee_entries_v36810';
const $ = (id) => document.getElementById(id);
const pageNames = {command:'Command Centre',workflows:'Active Workflows',meetings:'Meetings',proposals:'Proposals',decisions:'Decisions',risks:'Risks',calendar:'Calendar',contacts:'Contacts',knowledge:'Knowledge Base',reports:'Reports',settings:'Settings',actions:'Priority Actions',nextMoves:'Next Moves',alerts:'Industry Alerts',opportunities:'Opportunities',insights:'Insights Feed',detail:'Workflow Detail'};
let state = { page:'command', entries: safeLoad(), latest:null, filter:null, detailId:null };

function safeLoad(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]')}catch(e){return []}}
function save(){localStorage.setItem(STORAGE_KEY, JSON.stringify(state.entries.slice(0,100)));}
function escapeHtml(s=''){return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function nowLabel(){return new Date().toLocaleString([], {year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'2-digit'});}
function uid(){return Math.random().toString(36).slice(2)+Date.now().toString(36);}
function asArray(v){if(v===undefined||v===null||v==='')return[];return Array.isArray(v)?v:[v];}
function titleCase(s=''){return String(s).replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase());}
function firstText(v){if(!v)return''; if(typeof v==='string')return v; if(Array.isArray(v))return firstText(v[0]); if(typeof v==='object')return v.title||v.name||v.package_title||v.label||v.summary||''; return String(v);}

function detectCategory(text){const t=(text||'').toLowerCase();const rules=[['Meeting',['meeting','agenda','talking points','client call','investor','prep','call']],['Proposal',['proposal','pitch','quote','pricing','offer','scope']],['Decision',['decide','decision','choose','tradeoff','should i','option']],['Risk',['risk','problem','blocker','threat','issue','concern','compliance','broken','error']],['Execution',['build','execute','launch','implement','fix','deploy','workflow','make it functional','system']],['Strategy',['strategy','growth','market','positioning','revenue','seo','ads','cpa','executive engine','cognition']]];for(const [cat,words] of rules){if(words.some(w=>t.includes(w)))return cat;}return 'General';}
function selectedCategory(){const val=$('categorySelect').value;return val==='Auto select'?detectCategory($('commandInput').value):val;}

async function executeCommand(){
  const input=$('commandInput').value.trim(); if(!input){$('commandInput').focus();return;}
  const category=selectedCategory(); $('categorySelect').value=category;
  const button=$('executeBtn'); button.disabled=true; button.textContent='Executing...';
  const placeholder={id:uid(), input, category, created_at:nowLabel(), response:null, loading:true};
  state.entries.unshift(placeholder); state.latest=placeholder; save(); renderAll();
  try{
    const res=await fetch(`${API_URL}/run`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input,category,render_target:'structured_objects'})});
    if(!res.ok) throw new Error(`Backend returned ${res.status}`);
    const data=await res.json();
    placeholder.response=normalizeResponse(data, category, input); placeholder.loading=false; placeholder.category=placeholder.response.category||category;
  }catch(err){
    placeholder.response=normalizeResponse(localFallback(input, category), category, input); placeholder.loading=false; placeholder.error=`Live backend unavailable: ${err.message}`;
  }
  $('commandInput').value=''; save(); renderAll(); button.disabled=false; button.textContent='Execute';
}

function normalizeResponse(data, fallbackCategory, input=''){
  const normalized={...data};
  normalized.category=normalized.category||fallbackCategory;
  normalized.executive_summary=normalized.executive_summary||normalized.clear_answer||normalized.executive_read||normalized.next_move||'';
  normalized.strategic_diagnosis=normalized.strategic_diagnosis||normalized.diagnosis||normalized.decision||'';
  normalized.best_move=normalized.best_move||normalized.next_move||'';
  normalized.action_steps=asArray(normalized.action_steps||normalized.actions||normalized.next_steps);
  normalized.ready_assets=asArray(normalized.ready_assets||normalized.assets||normalized.generated_assets);
  normalized.risks=asArray(normalized.risks||normalized.risk);
  normalized.push_intelligence=asArray(normalized.push_intelligence||normalized.insights||normalized.signals);
  normalized.recommended_command=normalized.recommended_command||'';
  normalized.execution_objects=collectExecutionObjects(normalized, input, fallbackCategory);
  return normalized;
}

function collectExecutionObjects(r, input, category){
  const objects=[];
  const map=[
    ['execution_packages','execution_package'],['execution_package','execution_package'],['execution_objects','execution_object'],['proposal','proposal'],['proposals','proposal'],['proposal_assets','proposal'],['crm_system','crm'],['crm','crm'],['kpi_system','kpi'],['kpis','kpi'],['outbound_systems','outbound'],['outbound_system','outbound'],['deployment_sequence','deployment'],['implementation_plan','implementation'],['automation_stack','automation'],['delegation_map','delegation'],['operational_workflows','workflow'],['workflows','workflow'],['sops','sop'],['pricing_structure','pricing'],['onboarding_system','onboarding'],['hiring_system','hiring']
  ];
  for(const [key,type] of map){
    if(r[key]!==undefined){
      asArray(r[key]).forEach((item,i)=>objects.push(normalizeObject(item,type,key,i)));
    }
  }
  if(!objects.length){objects.push(legacyToExecutionPackage(r,input,category));}
  return objects.filter(Boolean);
}

function normalizeObject(item,type,key,i){
  if(item===null||item===undefined)return null;
  if(typeof item==='string')return {type,title:titleCase(type),summary:item,source:key};
  if(Array.isArray(item))return {type,title:titleCase(type),items:item,source:key};
  const o={...item,type:item.type||type,source:key};
  o.title=o.title||o.name||o.package_title||o.system_name||titleCase(type)+' '+(i+1);
  return o;
}
function legacyToExecutionPackage(r,input,category){
  return {type:'execution_package',title:`${category||'Executive'} Execution Package`,deployment_priority:r.priority||'High',business_purpose:r.executive_summary||`Convert "${input}" into operational movement.`,deployment_steps:r.action_steps||[],operational_content:{best_move:r.best_move||r.next_move,decision:r.decision,ready_assets:r.ready_assets,risks:r.risks,recommended_command:r.recommended_command}};
}

function localFallback(input, category){
  const t=input.toLowerCase(); const weak=t.replace(/[^a-z0-9]/g,'').length<6 || /^(wow+|lol+|haha+|a girl)$/i.test(input.trim());
  if(weak){return {category:'Clarify',pressure:18,priority:'Medium',executive_summary:'The input is too low-signal to create a trusted executive workflow.',strategic_diagnosis:'Executive Engine should not fake certainty from vague input. It should ask for the missing objective before creating an execution object.',best_move:'Capture the outcome, category, deadline, stakeholder, and required asset.',action_steps:['State the business outcome.','Choose the workflow category.','Add deadline, stakeholder, and required output.'],ready_assets:['Clarifying prompt','Objective checklist'],risks:['Fake certainty from unclear input.'],recommended_command:'Clarify the objective, category, deadline, and desired output.'};}
  return {category,pressure:44,priority:'High',executive_summary:`Executive Engine should convert this ${category.toLowerCase()} command into operational objects, not generic text.`,strategic_diagnosis:'The valuable output is the execution package, deployment sequence, assets, owners, risks, and next command.',best_move:'Create a deployable execution package and attach it to the active workflow.',action_steps:['Define the operational objective.','Generate the primary execution package.','Create the first asset.','Assign the next action and owner.','Set the follow-up command.'],ready_assets:['Execution package','Action sequence','Follow-up command'],risks:['Generic answer instead of operational system.'],recommended_command:'Generate the primary execution package with deployment steps, assets, owners, and follow-up command.'};
}

function renderAll(){renderNav();renderPage();renderSidebars();renderPressure();}
function renderNav(){document.querySelectorAll('.nav-item').forEach(b=>b.classList.toggle('active', b.dataset.page===state.page)); $('pageTitle').textContent=pageNames[state.page]||'Command Centre';}
function renderPressure(){const latest=state.entries.find(e=>e.response); const score=latest?.response?.pressure || 0; $('pressureScore').textContent=score; $('pressureLabel').textContent=score>=55?'High':score>=25?'Medium':'Idle';}
function renderPage(){const el=$('pageContent'); if(state.page==='command') return renderThread(el); if(state.page==='detail') return renderDetail(el); return renderListPage(el, state.page);}

function renderThread(el){
  const entries=state.filter?state.entries.filter(e=>e.category===state.filter):state.entries;
  el.innerHTML=`<section class="thread-card"><div class="thread-head"><div><h3>⌘ Command Thread</h3><small>${state.filter?`Filtered: ${state.filter}`:'Latest at the top'}</small></div><div class="head-actions"><button id="filterBtn">▽ Filter</button><button id="exportBtn">⇩ Export</button></div></div><div id="thread" class="thread"></div></section>`;
  $('filterBtn').onclick=()=>{state.filter=state.filter?null:selectedCategory();renderAll();}; $('exportBtn').onclick=exportJson;
  const thread=$('thread');
  if(!entries.length){thread.innerHTML='<div class="empty"><b>No commands yet.</b><br>Run a command to create live execution objects. No static filler is rendered in the command thread.</div>'; return;}
  thread.innerHTML=entries.map(entryHtml).join('');
  document.querySelectorAll('.view-detail').forEach(btn=>btn.onclick=()=>{state.detailId=btn.dataset.id;state.page='detail';renderAll();});
}
function entryHtml(e){const r=e.response;return `<div class="entry-pair ${e.loading?'loading':''}"><div class="icon">♟</div><article class="msg"><span class="tag">${escapeHtml(e.category)}</span><h4>User Input</h4><p>${escapeHtml(e.input)}</p><small>${escapeHtml(e.created_at)} • ${escapeHtml(e.category)}</small></article><div class="icon system">▰</div><article class="msg ${e.error?'error':''}"><h4>System Response</h4>${e.loading?'<p>Building operational objects...</p>':responseHtml(r,e.error)}<button class="view-detail" data-id="${e.id}">View Full Detail</button><small>${escapeHtml(e.created_at)} • ${escapeHtml(r?.category||e.category)}</small></article></div>`;}

function responseHtml(r,err){
  if(!r)return'<p>No response yet.</p>';
  const structured = renderStructuredObjects(r.execution_objects||[]);
  return `${err?`<p><b>${escapeHtml(err)}</b></p>`:''}<div class="executive-read"><h5>Executive Read</h5><p>${escapeHtml(r.executive_summary)}</p></div>${structured}<div class="legacy-compact"><details><summary>Legacy cognition fields</summary><h5>Strategic Diagnosis</h5><p>${escapeHtml(r.strategic_diagnosis)}</p><h5>Best Move</h5><p>${escapeHtml(r.best_move||r.next_move)}</p><h5>Recommended Command</h5><p>${escapeHtml(r.recommended_command)}</p></details></div>`;
}

function renderStructuredObjects(objects){
  if(!objects.length)return '';
  const priority=['execution_package','deployment','proposal','crm','kpi','workflow','automation','delegation','outbound','implementation','pricing','sop','onboarding','hiring','execution_object'];
  const sorted=[...objects].sort((a,b)=>priority.indexOf(a.type)-priority.indexOf(b.type));
  return `<div class="object-stack">${sorted.map(renderObject).join('')}</div>`;
}
function renderObject(o){
  const type=(o.type||'execution_object').toLowerCase();
  const renderers={proposal:renderProposal,crm:renderCrm,kpi:renderKpi,outbound:renderOutbound,deployment:renderDeployment,implementation:renderImplementation,automation:renderAutomation,delegation:renderDelegation,workflow:renderWorkflow,pricing:renderPricing,sop:renderSop,onboarding:renderWorkflow,hiring:renderWorkflow,execution_package:renderPackage,execution_object:renderPackage};
  return (renderers[type]||renderPackage)(o);
}
function objectHeader(o,label){return `<div class="object-header"><span class="object-badge">${escapeHtml(label||titleCase(o.type))}</span><strong>${escapeHtml(o.title||titleCase(o.type))}</strong>${o.deployment_priority?`<em>${escapeHtml(o.deployment_priority)}</em>`:''}</div>`;}
function renderPackage(o){return `<section class="object-card package">${objectHeader(o,'Execution Package')}<p>${escapeHtml(o.business_purpose||o.summary||o.purpose||'Operational package generated from command.')}</p>${renderField('Deployment Steps',o.deployment_steps||o.steps||o.items)}${renderKeyValues(o.operational_content)}</section>`;}
function renderProposal(o){return `<section class="object-card proposal">${objectHeader(o,'Proposal')}<div class="object-grid">${kv('Pricing',o.pricing||o.price)}${kv('Scope',o.scope)}${kv('CTA',o.cta||o.call_to_action)}</div>${renderField('Deliverables',o.deliverables||o.assets)}${renderField('Terms / Assumptions',o.terms||o.assumptions)}</section>`;}
function renderCrm(o){return `<section class="object-card crm">${objectHeader(o,'CRM System')}<p>${escapeHtml(o.summary||o.purpose||'Pipeline and ownership system.')}</p>${renderField('Pipeline Stages',o.pipeline_stages||o.stages)}${renderField('Automation Rules',o.automation_rules||o.rules)}${renderField('Follow-up Timing',o.follow_up_timing||o.followups)}</section>`;}
function renderKpi(o){const metrics=asArray(o.metrics||o.kpis||o.targets);return `<section class="object-card kpi">${objectHeader(o,'KPI System')}<div class="metric-grid">${metrics.length?metrics.map(m=>metricHtml(m)).join(''):metricHtml({name:o.name||'Target',target:o.target||'Define target',owner:o.owner||'Owner TBD'})}</div>${renderField('Reporting Frequency',o.reporting_frequency||o.frequency)}</section>`;}
function renderOutbound(o){return `<section class="object-card outbound">${objectHeader(o,'Outbound System')}${renderField('Subject Lines',o.subject_lines||o.subjects)}${renderField('Message Sequence',o.message_sequence||o.sequence||o.messages)}${renderField('Follow-up Cadence',o.follow_up_cadence||o.cadence)}</section>`;}
function renderDeployment(o){return `<section class="object-card deployment">${objectHeader(o,'Deployment Sequence')}${renderField('Phases',o.phases||o.sequence||o.steps)}${renderField('Dependencies',o.dependencies)}${renderField('Timeline',o.timeline)}</section>`;}
function renderImplementation(o){return `<section class="object-card implementation">${objectHeader(o,'Implementation Plan')}${renderField('Rollout Phases',o.rollout_phases||o.phases||o.steps)}${renderField('Owners',o.owners)}${renderField('Dependencies',o.dependencies)}</section>`;}
function renderAutomation(o){return `<section class="object-card automation">${objectHeader(o,'Automation Stack')}${renderField('Triggers',o.triggers)}${renderField('Actions',o.actions||o.steps)}${renderField('Tools',o.tools)}</section>`;}
function renderDelegation(o){return `<section class="object-card delegation">${objectHeader(o,'Delegation Map')}${renderTable(o.assignments||o.owners||o.items,['owner','responsibility','deadline','status'])}</section>`;}
function renderWorkflow(o){return `<section class="object-card workflow">${objectHeader(o,'Workflow')}${renderField('Steps',o.steps||o.workflow_steps||o.items)}${renderField('Owner',o.owner)}${renderField('Output',o.output||o.deliverable)}</section>`;}
function renderPricing(o){return `<section class="object-card pricing">${objectHeader(o,'Pricing System')}<div class="object-grid">${Object.entries(o).filter(([k])=>!['type','title','source'].includes(k)).map(([k,v])=>kv(titleCase(k),v)).join('')}</div></section>`;}
function renderSop(o){return `<section class="object-card sop">${objectHeader(o,'SOP')}${renderField('Procedure',o.procedure||o.steps||o.items)}${renderField('Quality Standard',o.quality_standard||o.standard)}</section>`;}
function renderField(label,val){const arr=asArray(val); if(!arr.length)return''; if(arr.length===1 && typeof arr[0]!=='object')return `<div class="object-field"><h6>${escapeHtml(label)}</h6><p>${escapeHtml(arr[0])}</p></div>`; return `<div class="object-field"><h6>${escapeHtml(label)}</h6><ul class="object-list">${arr.map(item=>`<li>${formatObjectItem(item)}</li>`).join('')}</ul></div>`;}
function formatObjectItem(item){if(typeof item==='string'||typeof item==='number')return escapeHtml(item); if(Array.isArray(item))return item.map(formatObjectItem).join(', '); if(typeof item==='object')return Object.entries(item).map(([k,v])=>`<b>${escapeHtml(titleCase(k))}:</b> ${escapeHtml(firstText(v)||JSON.stringify(v))}`).join(' · '); return escapeHtml(String(item));}
function renderKeyValues(obj){if(!obj||typeof obj!=='object')return'';return `<div class="object-grid">${Object.entries(obj).filter(([,v])=>v!==undefined&&v!==null&&v!=='').map(([k,v])=>kv(titleCase(k),v)).join('')}</div>`;}
function kv(label,val){if(val===undefined||val===null||val==='')return'';return `<div class="kv"><span>${escapeHtml(label)}</span><b>${escapeHtml(Array.isArray(val)?val.map(firstText).join(', '):firstText(val)||String(val))}</b></div>`;}
function metricHtml(m){if(typeof m==='string')m={name:m};return `<div class="metric"><span>${escapeHtml(m.name||m.metric||'Metric')}</span><b>${escapeHtml(m.target||m.value||'Target TBD')}</b><em>${escapeHtml(m.owner||m.frequency||'Owner TBD')}</em></div>`;}
function renderTable(rows,cols){rows=asArray(rows); if(!rows.length)return'<p class="muted">No delegation data yet.</p>';return `<table class="object-table"><thead><tr>${cols.map(c=>`<th>${escapeHtml(titleCase(c))}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${escapeHtml((typeof r==='object'?(r[c]||r[titleCase(c)]):r)||'')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}

function renderDetail(el){const e=state.entries.find(x=>x.id===state.detailId)||state.entries[0]; if(!e){state.page='command';return renderThread(el);} const r=e.response||{};el.innerHTML=`<section class="detail-card"><button class="text-btn" id="backBtn">← Back to Command Thread</button><h3>${escapeHtml(e.category)} Workflow Detail</h3><p class="muted">${escapeHtml(e.created_at)}</p><div class="detail-section"><h4>User Input</h4><p>${escapeHtml(e.input)}</p></div><div class="detail-section"><h4>Structured Operational Objects</h4>${renderStructuredObjects(r.execution_objects||[])}</div><div class="detail-grid"><div class="detail-section"><h4>Executive Read</h4><p>${escapeHtml(r.executive_summary||'')}</p></div><div class="detail-section"><h4>Strategic Diagnosis</h4><p>${escapeHtml(r.strategic_diagnosis||'')}</p></div><div class="detail-section"><h4>Best Move</h4><p>${escapeHtml(r.best_move||r.next_move||'')}</p></div><div class="detail-section"><h4>Recommended Command</h4><p>${escapeHtml(r.recommended_command||'')}</p></div></div></section>`; $('backBtn').onclick=()=>{state.page='command';renderAll();};}
function renderListPage(el,page){const title=pageNames[page]||'Workspace';const rows=rowsForPage(page);el.innerHTML=`<section class="page-card"><h3>${title}</h3><p class="muted">Live page generated from command thread, execution objects, and workflow state.</p>${rows.length?rows.map(rowHtml).join(''):'<div class="empty">No live records yet. Run a command to populate this page.</div>'}</section>`;}
function rowHtml(row){return `<div class="list-row"><div><b>${escapeHtml(row.title)}</b><p>${escapeHtml(row.desc||'')}</p></div><span class="pill">${escapeHtml(row.meta||'Open')}</span></div>`;}
function allObjects(){return state.entries.flatMap(e=>asArray(e.response?.execution_objects).map(o=>({...o,entry:e})));}
function rowsForPage(page){const entries=state.entries.filter(e=>e.response); const objs=allObjects(); if(page==='proposals')return objs.filter(o=>o.type==='proposal'||o.entry.category==='Proposal').map(o=>({title:o.title||o.entry.input,desc:o.business_purpose||o.summary||o.entry.response?.best_move,meta:o.type||o.entry.category})); if(page==='workflows')return objs.map(o=>({title:o.title||o.entry.input,desc:o.business_purpose||o.summary||o.entry.response?.next_move,meta:o.type})); if(page==='actions')return entries.flatMap(e=>asArray(e.response?.action_steps).map(x=>({title:x,desc:e.input,meta:e.category}))); if(page==='nextMoves')return entries.map(e=>({title:e.response?.next_move||e.response?.best_move,desc:e.input,meta:e.category})); if(page==='risks')return entries.flatMap(e=>asArray(e.response?.risks).map(x=>({title:x,desc:e.input,meta:e.category}))); if(page==='opportunities')return entries.flatMap(e=>asArray(e.response?.ready_assets).map(x=>({title:x,desc:'Asset/opportunity created from workflow',meta:e.category}))); if(page==='insights')return entries.flatMap(e=>asArray(e.response?.push_intelligence).map(x=>({title:x,desc:e.input,meta:e.category}))); if(page==='meetings')return entries.filter(e=>e.category==='Meeting').map(e=>({title:e.input,desc:e.response?.best_move,meta:e.category})); if(page==='decisions')return entries.filter(e=>e.category==='Decision').map(e=>({title:e.input,desc:e.response?.decision,meta:e.category})); if(page==='reports')return [{title:'Execution objects',desc:String(objs.length),meta:'Live count'},{title:'Open action items',desc:String(entries.reduce((n,e)=>n+asArray(e.response?.action_steps).length,0)),meta:'Live count'}]; if(page==='settings')return [{title:'Frontend mode',desc:'V36810 Structured Object Renderer. Backend untouched.',meta:'Locked'},{title:'Storage key',desc:STORAGE_KEY,meta:'Local'}]; return entries.map(e=>({title:e.input,desc:e.response?.executive_summary,meta:e.category}));}
function renderSidebars(){const entries=state.entries.filter(e=>e.response); const latest=entries[0]?.response; const objects=allObjects(); fill('priorityActions', asArray(latest?.action_steps).slice(0,3)); fill('nextMoves', entries.slice(0,3).map(e=>e.response?.next_move||e.response?.best_move)); fill('activeWorkflows', objects.slice(0,3).map(o=>`${o.title||o.entry.input} | ${o.type}`)); fill('industryAlerts', asArray(latest?.push_intelligence).slice(0,3)); fill('opportunities', asArray(latest?.ready_assets).slice(0,3)); fill('risksMonitor', asArray(latest?.risks).slice(0,3)); fill('insightsFeed', entries.slice(0,3).map(e=>e.response?.strategic_diagnosis)); $('tracker').innerHTML=`<span>Execution objects</span><b>${objects.length}</b><span>Action items</span><b>${entries.reduce((n,e)=>n+asArray(e.response?.action_steps).length,0)}</b><span>Assets</span><b>${entries.reduce((n,e)=>n+asArray(e.response?.ready_assets).length,0)}</b><span>Static filler</span><b>0</b>`;}
function fill(id,items){items=asArray(items).filter(Boolean);$(id).innerHTML=items.length?items.map(x=>`<li>${escapeHtml(String(x).replace(' | ',' — '))}</li>`).join(''):'<li class="muted">No live data yet.</li>';}
function exportJson(){const blob=new Blob([JSON.stringify(state.entries,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='executive-engine-thread-export-v36810.json';a.click();URL.revokeObjectURL(a.href);}

document.addEventListener('click',(e)=>{const page=e.target?.dataset?.page;if(page){state.page=page;state.filter=null;renderAll();}});
$('executeBtn').onclick=executeCommand;$('clearBtn').onclick=()=>{$('commandInput').value='';$('categorySelect').value='Auto select';$('commandInput').focus();};
$('commandInput').addEventListener('input',()=>{if($('categorySelect').value==='Auto select')$('categoryNote').textContent=`Category auto-detected: ${detectCategory($('commandInput').value)}. You can change it anytime.`;});
$('commandInput').addEventListener('keydown',(e)=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')executeCommand();});
renderAll();
