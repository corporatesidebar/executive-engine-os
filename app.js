const execute = document.querySelector('.execute');
    const thread = document.querySelector('.thread');
    execute?.addEventListener('click', () => {
      const block = document.createElement('div');
      block.className = 'msg';
      block.innerHTML = `<div class="bubble-avatar engine-avatar">E</div><div><div class="meta"><strong>Executive Engine</strong><span>Now</span></div><div class="copy">Execution package generated. I organized the command into decision, next action, risk, and ready assets.</div><div class="assets"><div class="asset wide" style="color:#2274ff"><div class="asset-icon">▤</div><div><strong>Execution Package</strong><span>Decision • Actions • Risks • Assets</span></div><div class="download">⇩</div></div></div></div>`;
      thread.appendChild(block);
      thread.scrollTop = thread.scrollHeight;
    });

/* === V37060 EXECUTION OBJECT RENDERER ONLY === */
(function(){
  const thread = document.querySelector('.thread');
  const execute = document.querySelector('.execute');
  const summary = document.querySelector('.summary');
  const rail = document.querySelector('.rail');

  function classifyCommand(text){
    const t = (text || '').toLowerCase();
    if (t.includes('proposal')) return 'proposal';
    if (t.includes('meeting') || t.includes('board')) return 'meeting';
    if (t.includes('kpi') || t.includes('performance')) return 'kpi';
    if (t.includes('crm') || t.includes('pipeline')) return 'crm';
    if (t.includes('roadmap') || t.includes('timeline')) return 'roadmap';
    if (t.includes('outreach') || t.includes('email')) return 'outbound';
    return 'workflow';
  }

  function loader(){
    const el = document.createElement('div');
    el.className = 'v37060-loader';
    el.innerHTML = `
      <div class="bubble-avatar engine-avatar">E</div>
      <div class="v37060-stream">
        <div class="meta"><strong>Executive Engine</strong><span>Building execution objects...</span></div>
        <div class="copy">Structuring decision, workflow, risks, assets, and next operating move.</div>
        <div class="v37060-progress"><span></span></div>
      </div>`;
    return el;
  }

  function objectPackage(type){
    const titleMap = {
      proposal: 'Proposal Execution Package',
      meeting: 'Meeting Prep Execution Package',
      kpi: 'KPI Operating Package',
      crm: 'CRM Pipeline Execution Package',
      roadmap: 'Roadmap Implementation Package',
      outbound: 'Outbound Execution Package',
      workflow: 'Workflow Execution Package'
    };
    const title = titleMap[type] || titleMap.workflow;

    return `
      <div class="msg">
        <div class="bubble-avatar engine-avatar">E</div>
        <div>
          <div class="meta"><strong>Executive Engine</strong><span>Now</span></div>
          <div class="copy">Execution package generated. I converted the command into operating objects, ready assets, risks, and next actions.</div>

          <div class="exec-package">
            <div class="exec-head">
              <div><strong>${title}</strong><br><span>Decision-ready operating system</span></div>
              <span class="v37060-pill">Ready</span>
            </div>
            <div class="exec-body">
              <div class="exec-grid">
                <div class="exec-object proposal">
                  <h4>PROPOSAL OBJECT</h4>
                  <p>Scope, positioning, business case, timeline, investment logic, and approval path prepared for executive review.</p>
                </div>
                <div class="exec-object meeting">
                  <h4>MEETING PREP BLOCK</h4>
                  <ul>
                    <li>Opening position</li>
                    <li>Primary talking points</li>
                    <li>Likely objections</li>
                    <li>Recommended responses</li>
                  </ul>
                </div>
                <div class="exec-object workflow">
                  <h4>WORKFLOW CARD</h4>
                  <ul>
                    <li>Confirm objective</li>
                    <li>Assign owner</li>
                    <li>Lock deadline</li>
                    <li>Prepare asset package</li>
                  </ul>
                </div>
                <div class="exec-object kpi">
                  <h4>KPI SNAPSHOT</h4>
                  <div class="exec-kpis">
                    <div class="exec-kpi"><b>3</b><span>Active moves</span></div>
                    <div class="exec-kpi"><b>2</b><span>Risks</span></div>
                    <div class="exec-kpi"><b>5</b><span>Assets</span></div>
                  </div>
                </div>
                <div class="exec-object asset">
                  <h4>ASSET MODULES</h4>
                  <p>Generated documents and operating files are organized below for review, download, and follow-up.</p>
                </div>
                <div class="exec-object outbound">
                  <h4>NEXT COMMAND</h4>
                  <p>Review the package, approve the direction, then generate the final client-ready version.</p>
                </div>
              </div>

              <div class="exec-assets">
                <div class="exec-asset"><strong>Executive Brief</strong><span>1-page decision memo</span><em>⇩</em></div>
                <div class="exec-asset"><strong>Action Plan</strong><span>Owner / deadline / next step</span><em>⇩</em></div>
                <div class="exec-asset"><strong>Risk Register</strong><span>Blockers and mitigation</span><em>⇩</em></div>
              </div>
            </div>
          </div>
        </div>
      </div>`;
  }

  function syncRightRail(type){
    if(!rail) return;
    const labels = {
      proposal: ['Proposal package created', 'Approval path, ROI logic, and client-ready assets are now active.'],
      meeting: ['Meeting prep active', 'Talking points, objections, and board narrative are ready for review.'],
      kpi: ['KPI package active', 'Performance measures and operating indicators are now organized.'],
      crm: ['CRM object active', 'Pipeline stages, owner follow-up, and conversion risk are now visible.'],
      roadmap: ['Roadmap active', 'Timeline, dependencies, and execution blockers are now structured.'],
      outbound: ['Outbound package active', 'Message, audience, follow-up, and conversion path are prepared.'],
      workflow: ['Workflow package active', 'Objective, owner, next action, and delivery path are now structured.']
    };
    const selected = labels[type] || labels.workflow;
    const card = rail.querySelector('.rail-card');
    if(card){
      card.innerHTML = `<div class="rail-title">◆ KEY INSIGHT</div><p>${selected[1]}</p><div class="link">${selected[0]} →</div>`;
    }
  }

  function syncSummary(type){
    if(!summary) return;
    const next = summary.querySelector('.sum-card p');
    if(next){
      next.textContent = type === 'proposal'
        ? 'Review proposal object, confirm stakeholder, and approve final client-ready version.'
        : type === 'meeting'
        ? 'Review meeting prep pack and confirm talking points before the meeting.'
        : 'Review execution package and confirm the next operating move.';
    }
  }

  function getCommandText(){
    const input = document.querySelector('textarea, input[type="text"], .command textarea, .command input');
    return input ? input.value : document.querySelector('.placeholder')?.textContent || '';
  }

  execute?.addEventListener('click', function(){
    if(!thread) return;
    const type = classifyCommand(getCommandText());
    const loading = loader();
    thread.appendChild(loading);
    thread.scrollTop = thread.scrollHeight;

    setTimeout(() => {
      loading.remove();
      thread.insertAdjacentHTML('beforeend', objectPackage(type));
      syncRightRail(type);
      syncSummary(type);
      thread.scrollTop = thread.scrollHeight;
    }, 750);
  });

  document.addEventListener('click', function(e){
    const head = e.target.closest('.exec-head');
    if(!head) return;
    head.closest('.exec-package')?.classList.toggle('collapsed');
  });
})();
