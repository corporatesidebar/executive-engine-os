const API_URL = 'https://executive-engine-os.onrender.com/run';

const state = {
  exchanges: [],
  activeCategory: 'General',
  latest: null,
  detailPayload: null,
};

const els = {
  commandInput: document.getElementById('commandInput'),
  followupInput: document.getElementById('followupInput'),
  categorySelect: document.getElementById('categorySelect'),
  executeBtn: document.getElementById('executeBtn'),
  followupBtn: document.getElementById('followupBtn'),
  clearBtn: document.getElementById('clearBtn'),
  thread: document.getElementById('thread'),
  runtimeInsight: document.getElementById('runtimeInsight'),
  stateGrid: document.getElementById('stateGrid'),
  summaryText: document.getElementById('summaryText'),
  currentFocus: document.getElementById('currentFocus'),
  activeRisk: document.getElementById('activeRisk'),
  recommendedMove: document.getElementById('recommendedMove'),
  threadContext: document.getElementById('threadContext'),
  mattersNow: document.getElementById('mattersNow'),
  modal: document.getElementById('detailModal'),
  modalTitle: document.getElementById('modalTitle'),
  modalBody: document.getElementById('modalBody'),
  closeModal: document.getElementById('closeModal'),
  downloadDetail: document.getElementById('downloadDetail'),
};

function escapeHTML(value = '') {
  return String(value).replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));
}

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string') {
    return value.split(/\n|•|- /).map(v => v.trim()).filter(Boolean);
  }
  return [String(value)];
}

function firstText(value, fallback = 'Not specified yet.') {
  if (Array.isArray(value)) return value[0] || fallback;
  return value || fallback;
}

function detectCategory(input) {
  const t = input.toLowerCase();
  if (/meeting|call|agenda|attendee|brief|prep/.test(t)) return 'Meeting';
  if (/proposal|quote|scope|client|deal|close|pricing/.test(t)) return 'Proposal';
  if (/execute|build|ship|launch|fix|implement|deliver|plan/.test(t)) return 'Execution';
  if (/decide|decision|choose|option|tradeoff|recommend/.test(t)) return 'Decision';
  if (/strategy|market|position|growth|competitive|expand/.test(t)) return 'Strategy';
  if (/risk|problem|blocked|issue|danger|failure|concern/.test(t)) return 'Risk';
  if (/follow.?up|remind|reply|email|message|check in/.test(t)) return 'Follow-up';
  return 'General';
}

function localExecutiveResponse(command, category) {
  const clean = command.trim();
  const objective = clean || 'Create operational clarity.';
  const categoryMap = {
    Meeting: {
      next: 'Prepare the meeting brief, define the desired outcome, and identify the decision needed before the meeting starts.',
      decision: 'Enter the meeting with one clear objective and one preferred outcome.',
      actions: ['Define the meeting objective.', 'List attendees and their likely concerns.', 'Prepare 3 talking points.', 'Capture decisions immediately after the meeting.'],
      assets: ['Meeting brief', 'Talking points', 'Follow-up draft'],
      risk: 'Medium: entering without a decision target creates wasted discussion and weak follow-through.',
      recommended: 'Prepare a meeting brief with objective, attendees, decisions, and follow-up.'
    },
    Proposal: {
      next: 'Turn the request into a proposal outline with value, scope, pricing logic, objections, and follow-up sequence.',
      decision: 'Build the proposal around the business outcome, not a list of services.',
      actions: ['Define the buyer and outcome.', 'Write the value proposition.', 'Structure scope into phases.', 'Add objection handling.', 'Set follow-up timing.'],
      assets: ['Proposal outline', 'Executive summary', 'Follow-up message'],
      risk: 'High: weak positioning or delayed follow-up reduces close probability.',
      recommended: 'Draft the proposal asset and follow-up sequence.'
    },
    Execution: {
      next: 'Convert the objective into a short execution sequence with owner, timeline, blocker, and completion definition.',
      decision: 'Move from idea to operating plan now.',
      actions: ['Define the finish line.', 'Break work into 3–5 execution steps.', 'Identify blockers.', 'Set the next irreversible action.'],
      assets: ['Execution plan', 'Task list', 'Blocker register'],
      risk: 'Medium: execution stalls when the finish line and next action are unclear.',
      recommended: 'Turn this into a sequenced action plan with blockers and due dates.'
    },
    Decision: {
      next: 'Frame the decision, compare options, select the highest-leverage path, and define the next action.',
      decision: 'Choose the option that reduces pressure and increases operational momentum fastest.',
      actions: ['State the decision clearly.', 'List 2–3 options.', 'Compare risks and upside.', 'Pick the recommended path.', 'Define the first action.'],
      assets: ['Decision brief', 'Option comparison', 'Risk note'],
      risk: 'Medium: delaying the decision compounds ambiguity and slows execution.',
      recommended: 'Create a decision brief with recommendation, risks, and next step.'
    },
    Strategy: {
      next: 'Clarify the strategic objective, identify the leverage point, and convert it into an execution path.',
      decision: 'Prioritize the move with the highest leverage and lowest operational drag.',
      actions: ['Define the strategic goal.', 'Identify constraints.', 'Select leverage point.', 'Convert into near-term action.'],
      assets: ['Strategy brief', 'Priority map', 'Execution path'],
      risk: 'Medium: strategy without execution path becomes abstract and non-operational.',
      recommended: 'Build the strategy brief and identify the next operating move.'
    },
    Risk: {
      next: 'Identify the risk source, consequence, mitigation, owner, and escalation trigger.',
      decision: 'Treat the risk as an operating constraint until it has an owner and mitigation path.',
      actions: ['Define the risk.', 'Estimate consequence.', 'Assign mitigation.', 'Set escalation trigger.'],
      assets: ['Risk brief', 'Mitigation plan', 'Escalation note'],
      risk: 'High: unresolved risk compounds pressure and creates downstream execution drag.',
      recommended: 'Create a mitigation plan with owner, timeline, and escalation rule.'
    },
    'Follow-up': {
      next: 'Create the follow-up message, define the ask, and set the next reminder.',
      decision: 'Follow up with a specific ask and a clear next step.',
      actions: ['Identify recipient.', 'Write the follow-up.', 'Include one clear ask.', 'Set next check-in.'],
      assets: ['Follow-up draft', 'Reminder note', 'Stakeholder context'],
      risk: 'Medium: delayed follow-up weakens trust and slows momentum.',
      recommended: 'Draft the follow-up message now.'
    },
    General: {
      next: 'Convert the request into one clear objective, one decision, and one next action.',
      decision: 'Start by clarifying the operational outcome and the first concrete move.',
      actions: ['Define the outcome.', 'Identify the category.', 'Create the first action.', 'Decide what asset is needed.'],
      assets: ['Operating brief', 'Action list', 'Next command'],
      risk: 'Low to Medium: unclear category can create generic output unless converted into workflow state.',
      recommended: 'Clarify the objective and turn this into a workflow.'
    }
  };
  const r = categoryMap[category] || categoryMap.General;
  return {
    next_move: r.next,
    decision: r.decision,
    action_steps: r.actions,
    ready_assets: r.assets,
    risk: r.risk,
    priority: category === 'Proposal' || category === 'Risk' ? 'High' : 'Medium',
    recommended_command: r.recommended,
    why_it_matters: `This matters because “${objective}” needs to become operating state: a decision, action sequence, assets, risks, and follow-up — not just another answer.`,
    category,
    source: 'local-fallback'
  };
}

function normalizeBackendResponse(raw, command, category) {
  const fallback = localExecutiveResponse(command, category);
  const data = raw && typeof raw === 'object' ? raw : {};
  return {
    next_move: sanitizeBadPhrase(data.next_move || fallback.next_move),
    decision: sanitizeBadPhrase(data.decision || fallback.decision),
    action_steps: asArray(data.action_steps || fallback.action_steps).map(sanitizeBadPhrase),
    ready_assets: asArray(data.ready_assets || fallback.ready_assets).map(sanitizeBadPhrase),
    risk: sanitizeBadPhrase(data.risk || fallback.risk),
    priority: sanitizeBadPhrase(data.priority || fallback.priority),
    recommended_command: sanitizeBadPhrase(data.recommended_command || fallback.recommended_command),
    why_it_matters: sanitizeBadPhrase(data.why_it_matters || fallback.why_it_matters),
    category,
    raw: data
  };
}

function sanitizeBadPhrase(text) {
  return String(text || '')
    .replace(/\bthe path is to\b/gi, 'The highest-leverage move is to')
    .replace(/\bpath is to\b/gi, 'highest-leverage move is to')
    .trim();
}

async function runCommand(command, category) {
  setLoading(true);
  let response;
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
      body: JSON.stringify({ input: command, mode: category.toLowerCase(), brain: 'operator', output_type: 'workflow', depth: 'standard' })
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    response = await res.json();
  } catch (err) {
    response = localExecutiveResponse(command, category);
    response.backend_error = err.message;
  }

  const normalized = normalizeBackendResponse(response, command, category);
  const exchange = { id: crypto.randomUUID(), command, category, time: new Date(), response: normalized };
  state.exchanges.push(exchange);
  state.latest = exchange;
  render();
  setLoading(false);
}

function setLoading(isLoading) {
  els.executeBtn.disabled = isLoading;
  els.followupBtn.disabled = isLoading;
  els.executeBtn.textContent = isLoading ? 'Executing…' : 'Execute →';
}

function submitPrimary() {
  const command = els.commandInput.value.trim();
  if (!command) return;
  const category = els.categorySelect.value;
  els.commandInput.value = '';
  runCommand(command, category);
}

function submitFollowup() {
  const command = els.followupInput.value.trim();
  if (!command) return;
  const category = detectCategory(command) === 'General' && state.latest ? state.latest.category : detectCategory(command);
  els.categorySelect.value = category;
  els.followupInput.value = '';
  runCommand(command, category);
}

function render() {
  renderThread();
  renderState();
}

function renderThread() {
  if (!state.exchanges.length) {
    els.thread.innerHTML = '<div class="thread-empty">No workflow yet. Enter a command to create operating state.</div>';
    return;
  }
  els.thread.innerHTML = state.exchanges.map(renderExchange).join('');
  els.thread.querySelectorAll('[data-detail]').forEach(btn => {
    btn.addEventListener('click', () => openDetail(btn.dataset.detail));
  });
  els.thread.scrollTop = els.thread.scrollHeight;
}

function renderExchange(ex) {
  const r = ex.response;
  const actions = asArray(r.action_steps);
  const assets = asArray(r.ready_assets);
  return `
    <article class="exchange">
      <div class="user-bubble"><small>You · ${formatTime(ex.time)} · ${escapeHTML(ex.category)}</small>${escapeHTML(ex.command)}</div>
      <div class="engine-card">
        <div class="engine-head"><div class="engine-avatar">E</div><div><strong>Executive Engine</strong><small>${formatTime(ex.time)}</small></div></div>
        <div class="engine-body">
          <div class="clear-answer"><small>CLEAR ANSWER</small><h2>${escapeHTML(r.decision)}</h2></div>
          <div class="why"><strong>WHY IT MATTERS</strong><span>${escapeHTML(r.why_it_matters)}</span></div>
          <div class="do-next"><strong>DO THIS NEXT</strong>${escapeHTML(r.next_move)}</div>
          <div class="section-title">ACTION WORKSPACE</div>
          <div class="workspace">
            ${actions.map((a, i) => itemRow(`${i + 1}`, a, 'TASK · PENDING EXECUTION', ex.id, 'action', i)).join('')}
          </div>
          <div class="section-title">READY ASSETS</div>
          <div class="assets">
            ${assets.map((a, i) => itemRow('▣', a, 'Draft-ready asset', ex.id, 'asset', i, 'Draft')).join('')}
          </div>
          <div class="decision-box"><div class="section-title">DECISION</div><p>${escapeHTML(r.decision)}</p><strong>Priority: ${escapeHTML(r.priority)}</strong></div>
          <div class="risk-box"><div class="section-title">RISK MONITOR</div><strong>Active Risk</strong><p>${escapeHTML(r.risk)}</p></div>
          <div class="mini-grid">
            <div class="mini-card"><strong>Category</strong><p>${escapeHTML(ex.category)}</p></div>
            <div class="mini-card"><strong>Recommended Command</strong><p>${escapeHTML(r.recommended_command)}</p></div>
            <div class="mini-card"><strong>Status</strong><p>Workflow active</p></div>
          </div>
        </div>
        <div class="engine-actions">
          <button class="primary" data-detail="${ex.id}:recommended:0">Continue with recommended command</button>
          <button data-detail="${ex.id}:plan:0">Turn into action plan</button>
          <button data-detail="${ex.id}:asset:0">Draft asset</button>
          <button data-detail="${ex.id}:decision:0">Save decision</button>
        </div>
      </div>
    </article>`;
}

function itemRow(icon, title, sub, id, type, index, label = 'Open') {
  if (!title) return '';
  return `<div class="item-row"><div><b>${escapeHTML(icon)} &nbsp; ${escapeHTML(title)}</b><small>${escapeHTML(sub)}</small></div><button class="open-btn" data-detail="${id}:${type}:${index}">${label}</button></div>`;
}

function renderState() {
  const latest = state.latest;
  if (!latest) {
    els.stateGrid.innerHTML = ['Next Move', 'Decision', 'Action Steps', 'Ready Assets', 'Active Risks', 'Priority', 'Recommended Command']
      .map((t, i) => `<div class="state-tile ${i % 2 ? 'orange' : ''}"><h4>${t}</h4><p>Waiting for workflow.</p></div>`).join('');
    return;
  }
  const r = latest.response;
  els.runtimeInsight.innerHTML = `<strong>RUNTIME INSIGHT</strong><p>${escapeHTML(r.why_it_matters)} Current Risk: ${escapeHTML(r.risk)}</p>`;
  els.summaryText.textContent = `Latest ${latest.category} workflow · ${asArray(r.action_steps).length} tasks · ${asArray(r.ready_assets).length} assets · Priority ${r.priority}`;
  els.currentFocus.textContent = `Current focus: ${latest.command}`;
  els.activeRisk.textContent = r.risk;
  els.recommendedMove.textContent = r.next_move;
  els.threadContext.textContent = `${state.exchanges.length} thread message pair(s). Latest category: ${latest.category}. Decision: ${r.decision}`;
  els.mattersNow.textContent = `The command is now organized into ${asArray(r.action_steps).length} action step(s), ${asArray(r.ready_assets).length} asset(s), one risk, and one recommended follow-up.`;
  const tiles = [
    ['NEXT MOVE', r.next_move, 'orange'],
    ['DECISION', r.decision, 'blue'],
    ['ACTION STEPS', asArray(r.action_steps).slice(0, 3).join(' • '), 'green'],
    ['READY ASSETS', asArray(r.ready_assets).join(' • '), 'purple'],
    ['ACTIVE RISKS', r.risk, 'red'],
    ['PRIORITY', r.priority, 'orange'],
    ['RECOMMENDED COMMAND', r.recommended_command, 'blue'],
  ];
  els.stateGrid.innerHTML = tiles.map(([h, p, c]) => `<div class="state-tile ${c}"><h4>${escapeHTML(h)}</h4><p>${escapeHTML(p)}</p></div>`).join('');
}

function openDetail(key) {
  const [id, type, indexString] = key.split(':');
  const ex = state.exchanges.find(x => x.id === id);
  if (!ex) return;
  const idx = Number(indexString || 0);
  const r = ex.response;
  const actions = asArray(r.action_steps);
  const assets = asArray(r.ready_assets);
  let title = 'Workflow Detail';
  let detail = '';
  if (type === 'action') { title = actions[idx] || 'Action Detail'; detail = 'Execute this task as part of the active workflow.'; }
  if (type === 'asset') { title = assets[idx] || 'Asset Detail'; detail = 'Draft or export this asset for use outside the system.'; }
  if (type === 'decision') { title = 'Decision Record'; detail = r.decision; }
  if (type === 'recommended') { title = 'Recommended Next Command'; detail = r.recommended_command; }
  if (type === 'plan') { title = 'Action Plan'; detail = r.next_move; }
  const payload = { title, category: ex.category, source_command: ex.command, recommended_action: r.next_move, details: detail, status: 'Active', related_risk: r.risk, related_assets: assets };
  state.detailPayload = payload;
  els.modalTitle.textContent = title;
  els.modalBody.innerHTML = Object.entries(payload).map(([k, v]) => `<div class="modal-body-row"><strong>${escapeHTML(labelize(k))}</strong><p>${escapeHTML(Array.isArray(v) ? v.join(', ') : v)}</p></div>`).join('');
  els.modal.classList.remove('hidden');
}

function downloadCurrentDetail() {
  if (!state.detailPayload) return;
  const text = Object.entries(state.detailPayload).map(([k, v]) => `${labelize(k)}:\n${Array.isArray(v) ? v.join(', ') : v}`).join('\n\n');
  const blob = new Blob([text], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${state.detailPayload.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'executive-engine-detail'}.txt`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function labelize(key) { return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }
function formatTime(date) { return new Intl.DateTimeFormat([], { hour: 'numeric', minute: '2-digit' }).format(date); }

els.commandInput.addEventListener('input', () => { els.categorySelect.value = detectCategory(els.commandInput.value); });
els.executeBtn.addEventListener('click', submitPrimary);
els.followupBtn.addEventListener('click', submitFollowup);
els.commandInput.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submitPrimary(); });
els.followupInput.addEventListener('keydown', e => { if (e.key === 'Enter') submitFollowup(); });
els.clearBtn.addEventListener('click', () => { els.commandInput.value = ''; els.categorySelect.value = 'General'; });
els.closeModal.addEventListener('click', () => els.modal.classList.add('hidden'));
els.downloadDetail.addEventListener('click', downloadCurrentDetail);

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const label = btn.textContent.trim();
    document.getElementById('pageTitle').textContent = label === 'Command' ? 'Command Centre' : label;
  });
});

render();
