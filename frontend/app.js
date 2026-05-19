const API_URL = window.EXECUTIVE_ENGINE_API || 'https://executive-engine-os.onrender.com';
const $ = (id) => document.getElementById(id);
let latestDetail = null;
let localTurns = [];

function detectCategory(text){
  const t = text.toLowerCase();
  const rules = [
    ['proposal', ['proposal','quote','scope','deal','pitch','pricing']],
    ['meeting', ['meeting','call','agenda','prep','board']],
    ['decision', ['decision','decide','choose','option','should i','approve']],
    ['risk', ['risk','issue','problem','broken','blocked','fails','terrible','not working']],
    ['follow-up', ['follow up','follow-up','reply','message','check in']],
    ['strategy', ['strategy','market','positioning','growth','roadmap']],
    ['revenue', ['revenue','sales','lead','pipeline','close','conversion','cpa','roi']],
    ['execution', ['build','launch','fix','ship','implement','execute','deploy','create']]
  ];
  for(const [cat, keys] of rules){ if(keys.some(k => t.includes(k))) return cat; }
  return 'general';
}
function li(items){ return (items||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join('') || '<li>No items.</li>'; }
function escapeHtml(str){return String(str||'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}

function renderResponse(data, userInput){
  latestDetail = data.detail || data;
  $('pressureScore').textContent = data.pressure_score ?? 0;
  $('nextMove').textContent = data.next_move || 'No next move returned.';
  $('decision').textContent = data.decision || 'No decision returned.';
  $('actions').innerHTML = li(data.action_steps);
  $('assets').innerHTML = li(data.ready_assets);
  $('push').innerHTML = li(data.push_intelligence);
  $('risk').textContent = data.risk || 'No active risk.';
  $('openLatest').disabled = false;

  localTurns.push({userInput, data, at:new Date().toLocaleString()});
  $('threadCount').textContent = `${localTurns.length} items`;
  $('thread').classList.remove('empty');
  $('thread').innerHTML = localTurns.map(turn => `
    <article class="turn">
      <div class="user-msg"><b>User input</b>${escapeHtml(turn.userInput)}<div class="meta">${escapeHtml(turn.at)} • ${escapeHtml(turn.data.category || '')}</div></div>
      <div class="system-msg"><b>System response</b>
        <p><strong>Clear Answer:</strong> ${escapeHtml(turn.data.executive_brief || turn.data.next_move)}</p>
        <div class="mini-grid">
          <div class="mini"><strong>Next Move</strong><br>${escapeHtml(turn.data.next_move)}</div>
          <div class="mini"><strong>Priority</strong><br>${escapeHtml(turn.data.priority)}</div>
          <div class="mini"><strong>Decision</strong><br>${escapeHtml(turn.data.decision)}</div>
          <div class="mini"><strong>Risk</strong><br>${escapeHtml(turn.data.risk)}</div>
        </div>
      </div>
    </article>`).join('');
  $('thread').scrollTop = $('thread').scrollHeight;
}

async function execute(){
  const input = $('commandInput').value.trim();
  if(!input) return;
  let category = $('categorySelect').value;
  if(category === 'auto') category = detectCategory(input);
  $('executeBtn').disabled = true; $('executeBtn').textContent = 'Executing…';
  try{
    const res = await fetch(`${API_URL}/run`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({input, category, mode:category})});
    if(!res.ok) throw new Error(`Backend returned ${res.status}`);
    const data = await res.json();
    renderResponse(data, input);
    $('commandInput').value = '';
    $('categorySelect').value = 'auto';
  }catch(err){
    renderResponse({
      category:'risk', pressure_score:82, next_move:'Backend connection failed. Verify API URL, Render status, and /run route before changing UI.',
      decision:'Treat this as a deployment/API issue, not a product redesign issue.',
      action_steps:['Open backend /health and confirm status ok.','Check browser Network tab for the failing request.','Fix API_URL only if the frontend is pointing to the wrong backend.'],
      ready_assets:['Deployment checklist','API test command','Failure report'], risk:String(err.message||err), priority:'Critical — restore backend connection', recommended_command:'Run /health and /test-report-json, then retest /run.', push_intelligence:['Do not redesign while API is failing.','One contained fix only.','Confirm contract fields after backend recovers.'], executive_brief:'The frontend could not reach the backend. Fix the connection before judging intelligence quality.'
    }, input);
  }finally{$('executeBtn').disabled=false; $('executeBtn').textContent='Execute';}
}

async function boot(){
  try{ const r = await fetch(`${API_URL}/health`); const h = await r.json(); $('statusText').textContent='Online'; $('versionText').textContent=h.version || 'connected'; }
  catch{ $('statusText').textContent='Local/Disconnected'; $('versionText').textContent='Check backend URL'; }
}

$('executeBtn').addEventListener('click', execute);
$('commandInput').addEventListener('input', e=>{ if($('categorySelect').value==='auto'){ /* visual auto label kept by select */ }});
$('commandInput').addEventListener('keydown', e=>{ if((e.ctrlKey||e.metaKey) && e.key==='Enter') execute(); });
$('clearBtn').addEventListener('click', ()=>{$('commandInput').value='';});
$('openLatest').addEventListener('click', ()=>{ if(!latestDetail) return; $('detailTitle').textContent = latestDetail.title || 'Workflow Detail'; $('detailBody').textContent = JSON.stringify(latestDetail,null,2); $('detailModal').showModal(); });
$('closeModal').addEventListener('click', ()=>$('detailModal').close());
$('downloadDetail').addEventListener('click', ()=>{ const blob = new Blob([JSON.stringify(latestDetail||{},null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='executive-engine-workflow-detail.json'; a.click(); URL.revokeObjectURL(a.href); });
document.querySelectorAll('.nav').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.nav').forEach(b=>b.classList.remove('active')); btn.classList.add('active');}));
boot();
