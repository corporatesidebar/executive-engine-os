const API_BASE = "https://executive-engine-os.onrender.com";
const VERSION = "36250-executive-operational-intelligence-layer";

const seedActions = [
  { id:"abc-roofing-proposal", title:"ABC Roofing Proposal", subtitle:"Proposal draft ready for review", priority:"High", due:"Due today", age:"2h ago", category:"proposal", thread:[] },
  { id:"bob-meeting-strategy", title:"Bob Meeting – Strategy", subtitle:"Strategic planning meeting", priority:"High", due:"Today 3:00 PM", age:"1h ago", category:"meeting", thread:[] },
  { id:"auto-loan-leads-followup", title:"Auto Loan Leads Follow-Up", subtitle:"3 follow-ups pending response", priority:"Medium", due:"Due tomorrow", age:"4h ago", category:"follow_up", thread:[] },
  { id:"q4-sales-push", title:"Q4 Sales Push Strategy", subtitle:"Strategy draft in progress", priority:"Low", due:"Due in 2 days", age:"6h ago", category:"strategy", thread:[] },
  { id:"investor-followup", title:"Investor Follow-Up", subtitle:"Update deck and follow up", priority:"Low", due:"Due in 3 days", age:"1d ago", category:"follow_up", thread:[] },
  { id:"website-redesign", title:"Website Redesign", subtitle:"Gather requirements", priority:"Low", due:"Due in 1 week", age:"2d ago", category:"documents", thread:[] }
];

let actions = JSON.parse(localStorage.getItem("ee_actions_v36200") || "null") || seedActions;
let activeActionId = localStorage.getItem("ee_active_action_v36200") || null;

const $ = (id) => document.getElementById(id);

function save() {
  localStorage.setItem("ee_actions_v36200", JSON.stringify(actions));
  if (activeActionId) localStorage.setItem("ee_active_action_v36200", activeActionId);
}

function level(p) { return (p || "Low").toLowerCase(); }

function getActive() {
  return actions.find(a => a.id === activeActionId);
}

function renderActionsRail() {
  const q = ($("actionSearch").value || "").toLowerCase();
  const filtered = actions.filter(a => (a.title + " " + a.subtitle + " " + a.priority).toLowerCase().includes(q));
  $("actionsRail").innerHTML = filtered.map(a => `
    <div class="action-card ${level(a.priority)}" onclick="openAction('${a.id}')">
      <div class="action-top">
        <div><strong>${escapeHtml(a.title)}</strong><span>${escapeHtml(a.subtitle)}</span></div>
        <em class="badge ${level(a.priority)}">${escapeHtml(a.priority)}</em>
      </div>
      <div class="action-time"><span>${escapeHtml(a.due)}</span><span>${escapeHtml(a.age)}</span></div>
    </div>
  `).join("");
  $("notificationCount").textContent = filtered.length;
}

function renderThread() {
  const active = getActive();
  const stream = $("threadStream");

  if (!active) {
    stream.innerHTML = `
      <div class="welcome-card">
        <div class="msg-kicker">THE ENGINE</div>
        <h2>What are we building and let’s make it happen.</h2>
        <p>Start with a messy note, meeting, proposal, follow-up, idea, or task. The Engine will turn it into an ACTION thread.</p>
      </div>`;
    // scroll preserved; engine box remains top
    return;
  }

  const messages = active.thread || [];
  stream.innerHTML = `
    <div class="welcome-card">
      <div class="msg-kicker">ACTION THREAD</div>
      <h2>${escapeHtml(active.title)}</h2>
      <p>${escapeHtml(active.subtitle)}</p>
    </div>
    ${messages.map((m, i) => renderMessage(m, i)).join("")}
  `;
  // scroll preserved; engine box remains top
}

function renderMessage(m, i) {
  if (m.role === "user") {
    return `<div class="user-msg"><div class="user-bubble">${escapeHtml(m.content)}</div></div>`;
  }

  const id = `detail-${i}`;
  const s = m.short || {};
  const top = m.top_actions || [];
  const d = m.long_detail || {};

  return `
    <div class="assistant-msg">
      <div class="msg-kicker">SHORT VERSION</div>
      <h3>${escapeHtml(s.summary || "Action organized.")}</h3>
      <div class="executive-block">
        <div class="exec-row">
          <div class="exec-label">WHAT MATTERS</div>
          <div class="exec-value">${escapeHtml(s.summary || "Action organized.")}</div>
        </div>

        <div class="exec-row">
          <div class="exec-label">NEXT MOVE</div>
          <div class="exec-value">${escapeHtml(s.next_move || "Review and continue.")}</div>
        </div>

        <div class="exec-row">
          <div class="exec-label">WHY IT MATTERS</div>
          <div class="exec-value">Execution quality improves when decisions, follow-ups, and ownership are clarified immediately.</div>
        </div>

        <div class="exec-row">
          <div class="exec-label">RISKS</div>
          <ul class="exec-list">
            <li>${escapeHtml(s.risk || "Loose notes create missed follow-up.")}</li>
            <li>Operational continuity may stall without a clear next step.</li>
          </ul>
        </div>

        <div class="exec-row">
          <div class="exec-label">RECOMMENDED ACTIONS</div>
          <ul class="exec-list">
            ${(top.slice(0,3).map(a => `<li>${escapeHtml(a)}</li>`).join(""))}
          </ul>
        </div>
      </div>
      <button class="expand-btn" onclick="toggleDetail('${id}')">View Detailed Brief</button>
    </div>
    <div class="detail-block" id="${id}">
      <div class="msg-kicker">DETAILED BRIEF</div>
      <p><strong>Missing info:</strong> ${escapeHtml((d.missing_information || []).join(", ") || "Nothing obvious.")}</p>
      <textarea id="draft-${i}">${escapeHtml(d.draft || "")}</textarea>
      <div class="detail-actions">
        <button class="small-btn" onclick="saveDraft(${i})">Save</button>
        <button class="small-btn" onclick="editDraft(${i}, 'polish')">AI Polish</button>
        <button class="small-btn" onclick="editDraft(${i}, 'client')">Client Ready</button>
        <button class="small-btn" onclick="editDraft(${i}, 'shorten')">Shorten</button>
        <button class="small-btn" onclick="editDraft(${i}, 'followup')">Follow-Up</button>
        <button class="small-btn" onclick="editDraft(${i}, 'proposal')">Proposal</button>
      </div>
    </div>
  `;
}

function openAction(id) {
  activeActionId = id;
  const a = getActive();
  if (a && (!a.thread || a.thread.length === 0)) {
    a.thread = [{
      role: "assistant",
      short: {
        summary: a.subtitle,
        next_move: "Review the ACTION and continue the thread.",
        risk: "The action stalls if the next step is not clear."
      },
      top_actions: ["Review context", "Update draft", "Close follow-up"],
      long_detail: {
        missing_information: [],
        draft: `${a.title}\n\nSHORT VERSION\n${a.subtitle}\n\nNEXT MOVE\nReview the ACTION and continue the thread.`
      }
    }];
  }
  save();
  renderActionsRail();
  renderThread();
}

async function runCommand() {
  const input = $("commandInput").value.trim();
  if (!input) return;

  let active = getActive();

  if (!active) {
    active = {
      id: "action-" + Date.now(),
      title: makeTitle(input),
      subtitle: "Generated from The Engine",
      priority: detectPriority(input),
      due: "New",
      age: "just now",
      category: detectCategory(input),
      thread: []
    };
    actions.unshift(active);
    activeActionId = active.id;
  }

  active.thread = active.thread || [];
  active.thread.push({role:"user", content:input});
  $("commandInput").value = "";
  renderThread();

  let assistantPayload = localAssistant(input, active.category);

  try {
    const res = await fetch(API_BASE + "/thread-run", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        action_id: active.id,
        input,
        title: active.title,
        category: active.category,
        current_thread: active.thread,
        account_id: "default",
        user_id: "owner"
      })
    });
    const data = await res.json();
    if (data && data.assistant_message) {
      assistantPayload = data.assistant_message;
      active.title = data.title || active.title;
      active.category = data.category || active.category;
    }
  } catch(e) {}

  active.subtitle = assistantPayload.short?.summary || active.subtitle;
  active.priority = detectPriority(input);
  active.age = "just now";
  active.thread.push({role:"assistant", ...assistantPayload});
  save();
  renderActionsRail();
  renderThread();
}

function localAssistant(input, category) {
  const cat = category || detectCategory(input);
  let short = {
    summary: "Captured and organized into an active ACTION.",
    next_move: "Review the short version, then expand details only if needed.",
    risk: "Loose notes create missed follow-up and unclear ownership."
  };
  let top = ["Clarify the next decision.", "Create or update the draft.", "Close the follow-up loop."];

  if (cat === "meeting") {
    short = { summary:"Meeting context captured.", next_move:"Prepare talking points and confirm the next step before the meeting ends.", risk:"The meeting creates no value if no owner, deadline, or next action is confirmed." };
    top = ["Prepare 3 talking points.", "Identify likely objection.", "Draft the follow-up before the meeting."];
  } else if (cat === "proposal") {
    short = { summary:"Proposal opportunity detected.", next_move:"Build the proposal overview and identify missing pricing/scope details.", risk:"Proposal value may be missed if scope, budget, and timing stay vague." };
    top = ["Draft proposal overview.", "Identify missing budget/scope/timeline.", "Prepare client-ready next step."];
  }

  return {
    short,
    top_actions: top,
    long_detail: {
      missing_information: [],
      draft: `${makeTitle(input)}\n\nSHORT VERSION\n${short.summary}\n\nNEXT MOVE\n${short.next_move}\n\nACTION ITEMS\n- ${top.join("\n- ")}`
    }
  };
}

function toggleDetail(id) {
  const el = $(id);
  if (el) el.classList.toggle("show");
}

function saveDraft(i) {
  const active = getActive();
  const textarea = $(`draft-${i}`);
  if (!active || !textarea || !active.thread[i]) return;
  active.thread[i].long_detail = active.thread[i].long_detail || {};
  active.thread[i].long_detail.draft = textarea.value;
  save();
}

function editDraft(i, type) {
  const textarea = $(`draft-${i}`);
  if (!textarea) return;

  if (type === "shorten") {
    textarea.value = textarea.value.split("\n").filter(Boolean).slice(0,8).join("\n");
  } else if (type === "client") {
    textarea.value = "CLIENT-READY VERSION\n\n" + textarea.value + "\n\nNext Step:\nPlease confirm the preferred direction, timing, and scope.";
  } else if (type === "followup") {
    textarea.value += "\n\nFOLLOW-UP DRAFT\nThanks for the conversation. I’ll prepare the next-step overview and send over a clear direction with recommended actions, timing, and scope.";
  } else if (type === "proposal") {
    textarea.value += "\n\nPROPOSAL STRUCTURE\n- Problem\n- Recommended scope\n- Timeline\n- Investment range\n- Next step";
  } else {
    textarea.value += "\n\nPOLISH NOTES\n- Make this clearer.\n- Confirm owner, deadline, and next step.\n- Remove vague language.";
  }
  saveDraft(i);
}

function makeTitle(input) {
  const t = input.toLowerCase();
  if (t.includes("bob") && t.includes("auto")) return "Bob — Auto Loan Strategy";
  if (t.includes("proposal")) return "Proposal — " + input.split(/\s+/).slice(0,4).join(" ");
  if (t.includes("meeting")) return "Meeting — " + input.split(/\s+/).slice(0,5).join(" ");
  return input.split(/\s+/).slice(0,6).join(" ") || "New Action";
}

function detectCategory(input) {
  const t = input.toLowerCase();
  if (t.includes("meeting") || t.includes("met with")) return "meeting";
  if (t.includes("proposal")) return "proposal";
  if (t.includes("strategy") || t.includes("marketing") || t.includes("sales")) return "strategy";
  if (t.includes("follow")) return "follow_up";
  return "action";
}

function detectPriority(input) {
  const t = input.toLowerCase();
  if (["urgent","proposal","client","meeting","revenue","today"].some(x => t.includes(x))) return "High";
  if (["follow","strategy","task"].some(x => t.includes(x))) return "Medium";
  return "Low";
}

function scrollThreadBottom() {
  requestAnimationFrame(() => {
    const s = $("threadStream");
    if (s) s.scrollTop = s.scrollHeight;
  });
}

function escapeHtml(str) {
  return String(str || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#039;"
  }[c]));
}

async function health() {
  try {
    const res = await fetch(API_BASE + "/health", {cache:"no-store"});
    const data = await res.json();
    $("backendStatus").textContent = data.status === "ok" ? "Backend Online" : "Backend Check";
    $("backendStatus").classList.toggle("online", data.status === "ok");
  } catch(e) {
    $("backendStatus").textContent = "Backend Offline";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("runCommand").addEventListener("click", runCommand);
  $("commandInput").addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") runCommand();
  });
  $("actionSearch").addEventListener("input", renderActionsRail);
  $("viewAllActions").addEventListener("click", () => {
    activeActionId = null;
    localStorage.removeItem("ee_active_action_v36200");
    renderThread();
  });

  renderActionsRail();
  if (activeActionId && actions.find(a => a.id === activeActionId)) {
    renderThread();
  } else {
    renderThread();
  }
  health();
});
