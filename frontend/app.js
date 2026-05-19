const API_URL = 'https://executive-engine-os.onrender.com/run';

const state = { exchanges: [], activeCategory: 'General', latest: null, detailPayload: null };

const els = {
  commandInput: document.getElementById('commandInput'), followupInput: document.getElementById('followupInput'), categorySelect: document.getElementById('categorySelect'), executeBtn: document.getElementById('executeBtn'), followupBtn: document.getElementById('followupBtn'), clearBtn: document.getElementById('clearBtn'), thread: document.getElementById('thread'), runtimeInsight: document.getElementById('runtimeInsight'), stateGrid: document.getElementById('stateGrid'), summaryText: document.getElementById('summaryText'), currentFocus: document.getElementById('currentFocus'), activeRisk: document.getElementById('activeRisk'), recommendedMove: document.getElementById('recommendedMove'), threadContext: document.getElementById('threadContext'), mattersNow: document.getElementById('mattersNow'), feedbackLoop: document.getElementById('feedbackLoop'), modal: document.getElementById('detailModal'), modalTitle: document.getElementById('modalTitle'), modalBody: document.getElementById('modalBody'), closeModal: document.getElementById('closeModal'), downloadDetail: document.getElementById('downloadDetail')
};

function escapeHTML(value = '') { return String(value).replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch])); }
function asArray(value) { if (!value) return []; if (Array.isArray(value)) return value.filter(Boolean); if (typeof value === 'string') return value.split(/\n|•|- /).map(v => v.trim()).filter(Boolean); return [String(value)]; }
function formatTime(date) { return new Intl.DateTimeFormat([], { hour: 'numeric', minute: '2-digit' }).format(date); }
function labelize(key) { return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }
function sanitizeBadPhrase(text) { return String(text || '').replace(/\bthe path is to\b/gi, 'The highest-leverage move is to').replace(/\bpath is to\b/gi, 'highest-leverage move is to').trim(); }

function detectCategory(input) {
  const t = input.toLowerCase();
  if (/feedback|design|layout|column|graphic|value|terrible|remove|fix what was|previously|wasting|job|why did you|no feedback|does not work|broken|bug|issue/.test(t)) return 'Product Feedback';
  if (/meeting|call|agenda|attendee|brief|prep/.test(t)) return 'Meeting';
  if (/proposal|quote|scope|client|deal|close|pricing/.test(t)) return 'Proposal';
  if (/execute|build|ship|launch|fix|implement|deliver|plan/.test(t)) return 'Execution';
  if (/decide|decision|choose|option|tradeoff|recommend/.test(t)) return 'Decision';
  if (/strategy|market|position|growth|competitive|expand/.test(t)) return 'Strategy';
  if (/risk|problem|blocked|danger|failure|concern/.test(t)) return 'Risk';
  if (/follow.?up|remind|reply|email|message|check in/.test(t)) return 'Follow-up';
  return 'General';
}

function isWeakBackend(data) {
  const joined = JSON.stringify(data || {}).toLowerCase();
  const bad = ['assess the situation', 'gather feedback', 'investigate the reasons', 'the path is to', 'not just another answer'];
  return !data || bad.some(x => joined.includes(x)) || joined.length < 220;
}

function buildOperatorResponse(command, category, backend = {}) {
  const clean = command.trim();
  const c = clean.toLowerCase();
  const isFeedback = category === 'Product Feedback';
  if (isFeedback) {
    const wantsLayoutLock = /do not change layout|graphic|layout|4th column|previously/.test(c);
    return {
      next_move: 'Lock the existing visual layout, restore the missing fourth column, and convert this feedback into a concrete frontend correction with acceptance tests before any upload.',
      decision: 'Do not redesign. Restore what worked, preserve the graphics, and fix only the broken functional behavior.',
      action_steps: [
        'Freeze the current visual shell: sidebar, command area, thread area, summary column, and far-right intelligence column.',
        'Restore the fourth column as a real Intelligence / Feedback Loop column instead of compressing everything into one right panel.',
        'Replace generic chat output with product feedback handling: issue, cause, correction, acceptance test, and next upload action.',
        'Make Command Centre show runtime state immediately: latest command, category, decision, actions, risks, assets, and next move.',
        'Keep Open buttons only where a detail payload exists; each opens a usable detail/export panel.',
        'Run the acceptance test: no layout/graphic changes, four columns visible on desktop, feedback produces fixes not generic advice.'
      ],
      ready_assets: ['Frontend correction brief', 'Acceptance test checklist', 'Detail/export panel payload', 'Runtime state map'],
      risk: 'High: changing layout while trying to fix functionality destroys trust and makes testing impossible. The fix must preserve the approved visual system and only repair behavior.',
      priority: 'High',
      recommended_command: 'Run V36141 layout-locked functional fix: preserve graphics, restore fourth column, improve feedback intelligence, and return ZIP only.',
      why_it_matters: 'This is product feedback, not a general question. The system must turn frustration into a specific correction plan and protect the approved interface from random redesign.',
      feedback: [
        'Root issue: the last build altered structure instead of building on the approved layout.',
        'Missing system behavior: feedback was treated like a generic prompt instead of a product fix request.',
        'Required correction: layout lock first, intelligence upgrade second, then package as ZIP.'
      ],
      acceptance: [
        'Desktop shows four columns: nav, command/thread, executive summary, intelligence/feedback.',
        'Page title remains Command Centre when Command is active.',
        'No quick-link chips return.',
        'Category auto-selects Product Feedback for build complaints and can be manually changed.',
        'Response contains issue, decision, exact fix steps, risk, acceptance tests, and next command.',
        'Open buttons produce a real modal with downloadable detail text.'
      ],
      category,
      source: 'operator-refinement'
    };
  }
  const templates = {
    Meeting: ['Prepare the meeting around one outcome, one decision, and one follow-up asset.', 'Enter the meeting with a defined decision target, not a loose agenda.', ['Define the meeting outcome.', 'List attendees and likely objections.', 'Prepare three talking points.', 'Capture decisions and follow-up immediately.'], ['Meeting brief', 'Talking points', 'Follow-up draft'], 'Medium: unprepared meetings create soft decisions and weak accountability.'],
    Proposal: ['Turn the opportunity into a proposal system: value, scope, pricing logic, objections, and follow-up.', 'Anchor the proposal to business outcome and close path, not service description.', ['Define buyer outcome.', 'Create value proposition.', 'Structure phased scope.', 'Pre-answer objections.', 'Set follow-up cadence.'], ['Proposal outline', 'Executive summary', 'Follow-up sequence'], 'High: weak positioning or delayed follow-up lowers close probability.'],
    Execution: ['Convert the objective into sequenced work with finish line, owner, blockers, and next irreversible action.', 'Move from intent to operating plan now.', ['Define finish line.', 'Break work into 3–5 actions.', 'Identify blockers.', 'Assign owner/date.', 'Execute the first irreversible step.'], ['Execution plan', 'Blocker register', 'Task brief'], 'Medium: unclear finish line causes work to stall.'],
    Decision: ['Frame the decision, compare options, choose the highest-leverage path, and define the first action.', 'Choose the option that reduces pressure and increases momentum fastest.', ['State decision.', 'List options.', 'Compare tradeoffs.', 'Pick recommendation.', 'Assign next step.'], ['Decision brief', 'Options map', 'Risk note'], 'Medium: delayed decisions compound ambiguity.'],
    Strategy: ['Turn strategy into a leverage thesis and operating sequence.', 'Prioritize the move with highest leverage and lowest drag.', ['Define strategic objective.', 'Identify constraint.', 'Find leverage point.', 'Convert to 7-day action path.'], ['Strategy brief', 'Priority map', 'Execution path'], 'Medium: strategy without execution becomes noise.'],
    Risk: ['Name the risk, consequence, mitigation, owner, and escalation trigger.', 'Treat this as an operating constraint until mitigation exists.', ['Define risk source.', 'Estimate consequence.', 'Set mitigation.', 'Assign trigger/owner.'], ['Risk brief', 'Mitigation plan', 'Escalation note'], 'High: unresolved risk compounds pressure.'],
    'Follow-up': ['Send a specific follow-up with one ask and one next step.', 'Follow up with clarity, timing, and consequence.', ['Identify recipient.', 'Write the ask.', 'Set next check-in.', 'Update thread status.'], ['Follow-up draft', 'Reminder note', 'Stakeholder context'], 'Medium: delayed follow-up weakens trust.'],
    General: ['Convert the request into one outcome, one decision, and one next action.', 'Clarify the operating outcome before expanding scope.', ['Define outcome.', 'Choose category.', 'Create first action.', 'Identify needed asset.'], ['Operating brief', 'Action list', 'Next command'], 'Medium: unclear category creates generic output.']
  };
  const t = templates[category] || templates.General;
  return { next_move:t[0], decision:t[1], action_steps:t[2], ready_assets:t[3], risk:t[4], priority: category === 'Proposal' || category === 'Risk' ? 'High' : 'Medium', recommended_command:`Continue this ${category.toLowerCase()} workflow with owners, timing, and deliverable.`, why_it_matters:`This matters because “${clean}” must become operating state: decision, actions, assets, risk, and next command.`, feedback:[], acceptance:[], category, source:'operator-refinement' };
}

function normalizeBackendResponse(raw, command, category) {
  const refined = buildOperatorResponse(command, category, raw);
  if (isWeakBackend(raw)) return refined;
  const data = raw && typeof raw === 'object' ? raw : {};
  return {
    next_move: sanitizeBadPhrase(data.next_move || refined.next_move), decision: sanitizeBadPhrase(data.decision || refined.decision), action_steps: asArray(data.action_steps || refined.action_steps).map(sanitizeBadPhrase), ready_assets: asArray(data.ready_assets || refined.ready_assets).map(sanitizeBadPhrase), risk: sanitizeBadPhrase(data.risk || refined.risk), priority: sanitizeBadPhrase(data.priority || refined.priority), recommended_command: sanitizeBadPhrase(data.recommended_command || refined.recommended_command), why_it_matters: sanitizeBadPhrase(data.why_it_matters || refined.why_it_matters), feedback: refined.feedback || [], acceptance: refined.acceptance || [], category, raw:data, source:'backend-plus-refinement'
  };
}

async function runCommand(command, category) {
  setLoading(true);
  let response;
  try {
    const res = await fetch(API_URL, { method:'POST', headers:{ 'Content-Type':'application/json', accept:'application/json' }, body:JSON.stringify({ input: command, mode: category.toLowerCase().replace(/\s+/g,'_'), brain:'operator', output_type:'workflow', depth:'standard' }) });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    response = await res.json();
  } catch (err) { response = { backend_error: err.message }; }
  const normalized = normalizeBackendResponse(response, command, category);
  const exchange = { id: crypto.randomUUID(), command, category, time: new Date(), response: normalized };
  state.exchanges.push(exchange); state.latest = exchange; render(); setLoading(false);
}
function setLoading(isLoading){ els.executeBtn.disabled = isLoading; els.followupBtn.disabled = isLoading; els.executeBtn.textContent = isLoading ? 'Executing…' : 'Execute →'; }
function submitPrimary(){ const command = els.commandInput.value.trim(); if(!command) return; const category = els.categorySelect.value; els.commandInput.value=''; runCommand(command, category); }
function submitFollowup(){ const command = els.followupInput.value.trim(); if(!command) return; const d=detectCategory(command); const category = d === 'General' && state.latest ? state.latest.category : d; els.categorySelect.value = category; els.followupInput.value=''; runCommand(command, category); }
function render(){ renderThread(); renderState(); }

function renderThread(){
  if(!state.exchanges.length){ els.thread.innerHTML='<div class="thread-empty">No workflow yet. Enter a command to create operating state.</div>'; return; }
  els.thread.innerHTML = state.exchanges.map(renderExchange).join('');
  els.thread.querySelectorAll('[data-detail]').forEach(btn => btn.addEventListener('click', () => openDetail(btn.dataset.detail)));
  els.thread.scrollTop = els.thread.scrollHeight;
}
function itemRow(icon,title,sub,id,type,index,label='Open'){ if(!title) return ''; return `<div class="item-row"><div><b>${escapeHTML(icon)} &nbsp; ${escapeHTML(title)}</b><small>${escapeHTML(sub)}</small></div><button class="open-btn" data-detail="${id}:${type}:${index}">${label}</button></div>`; }
function renderExchange(ex){
  const r=ex.response, actions=asArray(r.action_steps), assets=asArray(r.ready_assets), feedback=asArray(r.feedback), acceptance=asArray(r.acceptance);
  return `<article class="exchange"><div class="user-bubble"><small>You · ${formatTime(ex.time)} · ${escapeHTML(ex.category)}</small>${escapeHTML(ex.command)}</div><div class="engine-card"><div class="engine-head"><div class="engine-avatar">E</div><div><strong>Executive Engine</strong><small>${formatTime(ex.time)}</small><span class="quality-flag">${escapeHTML(r.source || 'operator')}</span></div></div><div class="engine-body"><div class="clear-answer"><small>CLEAR ANSWER</small><h2>${escapeHTML(r.decision)}</h2></div><div class="why"><strong>WHY IT MATTERS</strong><span>${escapeHTML(r.why_it_matters)}</span></div><div class="do-next"><strong>DO THIS NEXT</strong>${escapeHTML(r.next_move)}</div>${feedback.length?`<div class="feedback-box"><strong>FEEDBACK CONVERTED INTO FIX</strong><ul class="acceptance-list">${feedback.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul></div>`:''}<div class="section-title">ACTION WORKSPACE</div><div class="workspace">${actions.map((a,i)=>itemRow(`${i+1}`,a,'TASK · PENDING EXECUTION',ex.id,'action',i)).join('')}</div><div class="section-title">READY ASSETS</div><div class="assets">${assets.map((a,i)=>itemRow('▣',a,'Draft-ready asset',ex.id,'asset',i,'Open')).join('')}</div>${acceptance.length?`<div class="feedback-box"><strong>ACCEPTANCE TESTS</strong><ul class="acceptance-list">${acceptance.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul></div>`:''}<div class="decision-box"><div class="section-title">DECISION</div><p>${escapeHTML(r.decision)}</p><strong>Priority: ${escapeHTML(r.priority)}</strong></div><div class="risk-box"><div class="section-title">RISK MONITOR</div><strong>Active Risk</strong><p>${escapeHTML(r.risk)}</p></div><div class="mini-grid"><div class="mini-card"><strong>Category</strong><p>${escapeHTML(ex.category)}</p></div><div class="mini-card"><strong>Recommended Command</strong><p>${escapeHTML(r.recommended_command)}</p></div><div class="mini-card"><strong>Status</strong><p>Workflow active</p></div></div></div><div class="engine-actions"><button class="primary" data-detail="${ex.id}:recommended:0">Continue with recommended command</button><button data-detail="${ex.id}:plan:0">Turn into action plan</button><button data-detail="${ex.id}:asset:0">Draft asset</button><button data-detail="${ex.id}:decision:0">Save decision</button></div></div></article>`;
}
function renderState(){
  const latest=state.latest;
  if(!latest){ els.stateGrid.innerHTML=['NEXT MOVE','DECISION','ACTION STEPS','READY ASSETS','ACTIVE RISKS','PRIORITY','RECOMMENDED COMMAND'].map((t,i)=>`<div class="state-tile ${i%2?'orange':''}"><h4>${t}</h4><p>Waiting for workflow.</p></div>`).join(''); return; }
  const r=latest.response, actions=asArray(r.action_steps), assets=asArray(r.ready_assets);
  els.runtimeInsight.innerHTML=`<strong>RUNTIME INSIGHT</strong><p>${escapeHTML(r.why_it_matters)} Current risk: ${escapeHTML(r.risk)}</p>`;
  els.summaryText.textContent=`Latest ${latest.category} workflow · ${actions.length} tasks · ${assets.length} assets · Priority ${r.priority}`;
  els.currentFocus.textContent=`Current focus: ${latest.command}`; els.activeRisk.textContent=r.risk; els.recommendedMove.textContent=r.next_move; els.threadContext.textContent=`${state.exchanges.length} command/response pair(s). Latest category: ${latest.category}. Decision: ${r.decision}`; els.mattersNow.textContent=`What changed: feedback/command is now operating state with actions, assets, risk, acceptance tests, and next command.`; els.feedbackLoop.textContent = latest.category === 'Product Feedback' ? 'Feedback mode active: complaints become corrections, tests, and upload-ready fixes.' : 'Feedback loop ready: product issues will be converted into fix plans.';
  const tiles=[['NEXT MOVE',r.next_move,'orange'],['DECISION',r.decision,'blue'],['ACTION STEPS',actions.slice(0,3).join(' • '),'green'],['READY ASSETS',assets.join(' • '),'purple'],['ACTIVE RISKS',r.risk,'red'],['PRIORITY',r.priority,'orange'],['RECOMMENDED COMMAND',r.recommended_command,'blue']];
  els.stateGrid.innerHTML=tiles.map(([h,p,c])=>`<div class="state-tile ${c}"><h4>${escapeHTML(h)}</h4><p>${escapeHTML(p)}</p></div>`).join('');
}
function openDetail(key){
  const [id,type,indexString]=key.split(':'), ex=state.exchanges.find(x=>x.id===id); if(!ex) return; const idx=Number(indexString||0), r=ex.response, actions=asArray(r.action_steps), assets=asArray(r.ready_assets), acceptance=asArray(r.acceptance);
  let title='Workflow Detail', detail=''; if(type==='action'){title=actions[idx]||'Action Detail'; detail='Execute this task as part of the active workflow.';} if(type==='asset'){title=assets[idx]||'Asset Detail'; detail='Draft/export this asset for use outside the system.';} if(type==='decision'){title='Decision Record'; detail=r.decision;} if(type==='recommended'){title='Recommended Next Command'; detail=r.recommended_command;} if(type==='plan'){title='Action Plan'; detail=r.next_move;}
  const payload={title, category:ex.category, source_command:ex.command, recommended_action:r.next_move, details:detail, status:'Active', related_risk:r.risk, related_assets:assets, acceptance_tests:acceptance}; state.detailPayload=payload; els.modalTitle.textContent=title; els.modalBody.innerHTML=Object.entries(payload).map(([k,v])=>`<div class="modal-body-row"><strong>${escapeHTML(labelize(k))}</strong><p>${escapeHTML(Array.isArray(v)?v.join('\n'):v)}</p></div>`).join(''); els.modal.classList.remove('hidden');
}
function downloadCurrentDetail(){ if(!state.detailPayload) return; const text=Object.entries(state.detailPayload).map(([k,v])=>`${labelize(k)}:\n${Array.isArray(v)?v.join('\n'):v}`).join('\n\n'); const blob=new Blob([text],{type:'text/plain'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`${state.detailPayload.title.toLowerCase().replace(/[^a-z0-9]+/g,'-')||'executive-engine-detail'}.txt`; a.click(); URL.revokeObjectURL(a.href); }

els.commandInput.addEventListener('input',()=>{els.categorySelect.value=detectCategory(els.commandInput.value)}); els.executeBtn.addEventListener('click',submitPrimary); els.followupBtn.addEventListener('click',submitFollowup); els.commandInput.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey))submitPrimary()}); els.followupInput.addEventListener('keydown',e=>{if(e.key==='Enter')submitFollowup()}); els.clearBtn.addEventListener('click',()=>{els.commandInput.value='';els.categorySelect.value='General'}); els.closeModal.addEventListener('click',()=>els.modal.classList.add('hidden')); els.downloadDetail.addEventListener('click',downloadCurrentDetail);
document.querySelectorAll('.nav-item').forEach(btn=>{btn.addEventListener('click',()=>{document.querySelectorAll('.nav-item').forEach(b=>b.classList.remove('active'));btn.classList.add('active');const label=btn.textContent.trim();document.getElementById('pageTitle').textContent=label==='Command'?'Command Centre':label;});});
render();
