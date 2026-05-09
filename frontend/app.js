const API_BASE = "https://executive-engine-os.onrender.com";
const VERSION = "36170-layout-lock-clean-frontend";

const seedActions = [
  {
    id: "abc-roofing-proposal",
    title: "ABC Roofing Proposal",
    subtitle: "Proposal draft ready for review",
    priority: "High",
    due: "Due today",
    age: "2h ago",
    icon: "!",
    type: "proposal",
    draft: "PROPOSAL OVERVIEW\n\nObjective:\nPrepare a client-ready proposal direction.\n\nCurrent Status:\nProposal draft is ready for review.\n\nNext Move:\nConfirm scope, timing, and investment range before sending."
  },
  {
    id: "bob-meeting-strategy",
    title: "Bob Meeting – Strategy",
    subtitle: "Strategic planning meeting",
    priority: "High",
    due: "Today 3:00 PM",
    age: "1h ago",
    icon: "◷",
    type: "meeting",
    draft: "MEETING BRIEF\n\nObjective:\nPrepare for Bob meeting and identify next decision.\n\nTalking Points:\n- Confirm business objective\n- Identify constraints\n- Clarify next step\n\nFollow-Up:\nSend recap with decision, owner, and timeline."
  },
  {
    id: "auto-loan-leads-followup",
    title: "Auto Loan Leads Follow-Up",
    subtitle: "3 follow-ups pending response",
    priority: "Medium",
    due: "Due tomorrow",
    age: "4h ago",
    icon: "◎",
    type: "follow-up",
    draft: "FOLLOW-UP ACTION\n\nSummary:\nThree follow-ups are pending.\n\nNext Move:\nSend concise recap and ask for confirmation on next step."
  },
  {
    id: "q4-sales-push",
    title: "Q4 Sales Push Strategy",
    subtitle: "Strategy draft in progress",
    priority: "Low",
    due: "Due in 2 days",
    age: "6h ago",
    icon: "↗",
    type: "strategy",
    draft: "STRATEGY ACTION\n\nFocus:\nQ4 sales push.\n\nNext Move:\nDefine target segment, offer, timeline, and owner."
  },
  {
    id: "investor-followup",
    title: "Investor Follow-Up",
    subtitle: "Update deck and follow up",
    priority: "Low",
    due: "Due in 3 days",
    age: "1d ago",
    icon: "✉",
    type: "follow-up",
    draft: "INVESTOR FOLLOW-UP\n\nNext Move:\nUpdate deck and send follow-up with clear ask."
  },
  {
    id: "website-redesign",
    title: "Website Redesign",
    subtitle: "Gather requirements",
    priority: "Low",
    due: "Due in 1 week",
    age: "2d ago",
    icon: "▣",
    type: "documents",
    draft: "WEBSITE REDESIGN\n\nNext Move:\nGather requirements, define scope, and identify conversion goals."
  }
];

let actions = JSON.parse(localStorage.getItem("ee_actions_v36170") || "null") || seedActions;
let activeActionId = null;

const $ = (id) => document.getElementById(id);

function saveActions() {
  localStorage.setItem("ee_actions_v36170", JSON.stringify(actions));
}

function priorityLevel(p) {
  return (p || "Low").toLowerCase();
}

function renderPriorities() {
  const top = actions.slice(0, 3);
  $("priorityList").innerHTML = top.map((a) => `
    <div class="priority-row" onclick="openAction('${a.id}')">
      <div class="icon-box ${a.priority === "High" ? "icon-red" : a.priority === "Medium" ? "icon-yellow" : "icon-blue"}">${a.icon || "•"}</div>
      <div class="priority-main">
        <strong>${escapeHtml(a.title)}</strong>
        <span>${escapeHtml(a.subtitle)}</span>
      </div>
      <div class="priority-meta ${priorityLevel(a.priority)}">
        ${escapeHtml(a.priority)} Priority
        <span>${escapeHtml(a.due)}</span>
      </div>
      <div class="arrow">›</div>
    </div>
  `).join("");
}

function renderActionsRail() {
  const q = ($("actionSearch").value || "").toLowerCase();
  const filtered = actions.filter(a => (a.title + " " + a.subtitle + " " + a.priority).toLowerCase().includes(q));
  $("actionsRail").innerHTML = filtered.map((a) => `
    <div class="action-card ${priorityLevel(a.priority)}" onclick="openAction('${a.id}')">
      <div class="action-top">
        <div>
          <strong>${escapeHtml(a.title)}</strong>
          <span>${escapeHtml(a.subtitle)}</span>
        </div>
        <em class="badge ${priorityLevel(a.priority)}">${escapeHtml(a.priority)}</em>
      </div>
      <div class="action-time">
        <span>${escapeHtml(a.due)}</span>
        <span>${escapeHtml(a.age)}</span>
      </div>
    </div>
  `).join("");
  $("notificationCount").textContent = filtered.length;
}

function openAction(id) {
  activeActionId = id;
  const a = actions.find(x => x.id === id);
  if (!a) return;

  $("actionWorkspace").innerHTML = `
    <div class="workspace-head">
      <div>
        <div class="section-label">ACTION WORKSPACE</div>
        <h2>${escapeHtml(a.title)}</h2>
        <p>${escapeHtml(a.subtitle)}</p>
      </div>
      <em class="badge ${priorityLevel(a.priority)}">${escapeHtml(a.priority)}</em>
    </div>

    <div class="workspace-grid">
      <div class="workspace-card">
        <h3>Editable Draft</h3>
        <textarea id="workspaceEditor" class="workspace-editor">${escapeHtml(a.draft || "")}</textarea>
        <div class="workspace-actions">
          <button class="small-btn" onclick="saveDraft()">Save</button>
          <button class="small-btn" onclick="workspaceCommand('polish')">AI Polish</button>
          <button class="small-btn" onclick="workspaceCommand('client')">Client Ready</button>
          <button class="small-btn" onclick="workspaceCommand('shorten')">Shorten</button>
          <button class="small-btn" onclick="workspaceCommand('followup')">Follow-Up</button>
          <button class="small-btn" onclick="workspaceCommand('proposal')">Proposal</button>
        </div>
      </div>

      <div class="workspace-card">
        <h3>Short Version</h3>
        <p><strong>What matters:</strong> ${escapeHtml(a.subtitle)}</p>
        <p><strong>Next move:</strong> Review, edit, and close the next step.</p>
        <p><strong>Risk:</strong> This action stalls if the owner, deadline, or scope is unclear.</p>
        <h3>Operational Timeline</h3>
        <p>Captured → Draft ready → Review → Follow-up → Decision</p>
      </div>
    </div>
  `;
}

function saveDraft() {
  const a = actions.find(x => x.id === activeActionId);
  const editor = $("workspaceEditor");
  if (!a || !editor) return;
  a.draft = editor.value;
  a.age = "just now";
  saveActions();
  renderAll();
}

async function workspaceCommand(type) {
  const a = actions.find(x => x.id === activeActionId);
  const editor = $("workspaceEditor");
  if (!a || !editor) return;

  const commandMap = {
    polish: "polish and improve this",
    client: "make this client ready",
    shorten: "shorten this for executive review",
    followup: "create follow-up draft",
    proposal: "add proposal structure"
  };

  try {
    const res = await fetch(API_BASE + "/action-command", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        action_id: a.id,
        command: commandMap[type] || type,
        current_draft: editor.value,
        account_id: "default",
        user_id: "owner"
      })
    });
    const data = await res.json();
    editor.value = data.updated_draft || editor.value;
  } catch (e) {
    const additions = {
      polish: "\n\nPOLISH NOTES\n- Make this clearer and more direct.\n- Confirm owner, deadline, and next step.",
      client: "\n\nCLIENT-READY NEXT STEP\nPlease confirm preferred direction, timing, and scope.",
      shorten: "",
      followup: "\n\nFOLLOW-UP DRAFT\nThanks for the conversation. I’ll prepare the next-step overview and send a clear direction with recommended actions, timing, and scope.",
      proposal: "\n\nPROPOSAL STRUCTURE\n- Problem\n- Recommended scope\n- Timeline\n- Investment range\n- Next step"
    };
    if (type === "shorten") {
      editor.value = editor.value.split("\n").filter(Boolean).slice(0, 8).join("\n");
    } else {
      editor.value += additions[type] || "";
    }
  }

  saveDraft();
}

async function createActionFromCommand() {
  const input = $("commandInput").value.trim();
  if (!input) return;

  let newAction = {
    id: "action-" + Date.now(),
    title: makeTitle(input),
    subtitle: "Generated from The Engine",
    priority: detectPriority(input),
    due: "New",
    age: "just now",
    icon: detectIcon(input),
    type: detectType(input),
    draft: buildDraft(input)
  };

  try {
    const res = await fetch(API_BASE + "/action-capture", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        input,
        category: newAction.type,
        account_id: "default",
        user_id: "owner"
      })
    });
    const data = await res.json();
    if (data && data.action) {
      newAction = {
        id: data.action.action_id || newAction.id,
        title: data.action.title || newAction.title,
        subtitle: data.action.short?.summary || newAction.subtitle,
        priority: "High",
        due: "New",
        age: "just now",
        icon: detectIcon(input),
        type: data.action.category || newAction.type,
        draft: data.action.details?.draft || newAction.draft
      };
    }
  } catch (e) {}

  actions.unshift(newAction);
  $("commandInput").value = "";
  saveActions();
  renderAll();
  openAction(newAction.id);
}

function makeTitle(input) {
  const lower = input.toLowerCase();
  if (lower.includes("bob") && lower.includes("auto")) return "Bob — Auto Loan Strategy";
  if (lower.includes("proposal")) return "Proposal — " + input.split(/\s+/).slice(0, 4).join(" ");
  if (lower.includes("meeting")) return "Meeting — " + input.split(/\s+/).slice(0, 5).join(" ");
  return input.split(/\s+/).slice(0, 5).join(" ") || "New Action";
}

function detectPriority(input) {
  const t = input.toLowerCase();
  if (["urgent", "proposal", "client", "meeting", "revenue", "today"].some(x => t.includes(x))) return "High";
  if (["follow", "strategy", "task"].some(x => t.includes(x))) return "Medium";
  return "Low";
}

function detectIcon(input) {
  const t = input.toLowerCase();
  if (t.includes("proposal")) return "!";
  if (t.includes("meeting")) return "◷";
  if (t.includes("follow")) return "◎";
  return "↗";
}

function detectType(input) {
  const t = input.toLowerCase();
  if (t.includes("meeting")) return "meeting";
  if (t.includes("proposal")) return "proposal";
  if (t.includes("follow")) return "follow-up";
  if (t.includes("strategy")) return "strategy";
  return "action";
}

function buildDraft(input) {
  return `ACTION NOTES\n\n${input}\n\nSHORT VERSION\nWhat matters: organize this into one active ACTION.\nNext move: review, edit, and close the next step.\nRisk: loose notes create missed follow-up.`;
}

function escapeHtml(str) {
  return String(str || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    "\"":"&quot;",
    "'":"&#039;"
  }[c]));
}

function renderAll() {
  renderPriorities();
  renderActionsRail();
}

async function health() {
  try {
    const res = await fetch(API_BASE + "/health", {cache: "no-store"});
    const data = await res.json();
    $("backendStatus").textContent = data.status === "ok" ? "Backend Online" : "Backend Check";
    $("backendStatus").classList.toggle("online", data.status === "ok");
  } catch (e) {
    $("backendStatus").textContent = "Backend Offline";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("runCommand").addEventListener("click", createActionFromCommand);
  $("commandInput").addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") createActionFromCommand();
  });
  $("actionSearch").addEventListener("input", renderActionsRail);
  $("viewAllActions").addEventListener("click", () => {
    activeActionId = null;
    $("actionWorkspace").innerHTML = `
      <div class="empty-workspace">
        <h3>All ACTIONS are visible on the right.</h3>
        <p>Select one to open the ACTION workspace here.</p>
      </div>`;
  });

  renderAll();
  health();
});
