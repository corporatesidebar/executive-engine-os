let currentMode = "strategy";
let knowledgeText = "";
let requestAttachmentText = "";
let historyItems = [];
let actionItems = [];
let currentSummaryText = "";
let activeActionFilter = "all";

const modeTabs = document.querySelectorAll(".mode-pill");
const chatThread = document.getElementById("chatThread");
const loading = document.getElementById("loading");
const historyList = document.getElementById("historyList");
const actionList = document.getElementById("actionList");
const settingsBtn = document.getElementById("settingsBtn");
const settingsMenu = document.getElementById("settingsMenu");
const knowledgeStatus = document.getElementById("knowledgeFileStatus");
const requestStatus = document.getElementById("requestFileStatus");
const summaryContent = document.getElementById("summaryContent");

document.querySelectorAll(".action-filter").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".action-filter").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeActionFilter = btn.dataset.filter;
    renderActionItems();
  });
});

document.getElementById("historyBtn").addEventListener("click", () => {
  document.getElementById("historyPanel").classList.toggle("hidden");
});
document.getElementById("closeHistoryBtn").addEventListener("click", () => {
  document.getElementById("historyPanel").classList.add("hidden");
});

document.querySelectorAll(".settings-item").forEach(btn => {
  btn.addEventListener("click", () => {
    if (btn.dataset.topView === "history") {
      document.getElementById("historyPanel").classList.remove("hidden");
    }
    settingsMenu.classList.add("hidden");
  });
});

settingsBtn.addEventListener("click", () => {
  settingsMenu.classList.toggle("hidden");
});

document.addEventListener("click", (e) => {
  if (!settingsBtn.contains(e.target) && !settingsMenu.contains(e.target)) {
    settingsMenu.classList.add("hidden");
  }
});

modeTabs.forEach(btn => {
  btn.addEventListener("click", () => {
    modeTabs.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
  });
});

document.getElementById("runBtn").addEventListener("click", send);
document.getElementById("newChatBtn").addEventListener("click", () => {
  chatThread.innerHTML = "";
  document.getElementById("input").value = "";
});

document.getElementById("knowledgeFileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) {
    knowledgeText = "";
    knowledgeStatus.textContent = "No personal knowledge file loaded";
    return;
  }
  try {
    knowledgeText = await file.text();
    knowledgeStatus.textContent = `Loaded: ${file.name}`;
  } catch {
    knowledgeText = "";
    knowledgeStatus.textContent = "Could not read personal knowledge file";
  }
});

document.getElementById("requestFileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) {
    requestAttachmentText = "";
    requestStatus.textContent = "No request file loaded";
    return;
  }
  try {
    requestAttachmentText = await file.text();
    requestStatus.textContent = `Attached: ${file.name}`;
  } catch {
    requestAttachmentText = "";
    requestStatus.textContent = "Could not read request file";
  }
});

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function makeLinksClickable(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
}
function parseSections(text) {
  const lines = text.split("\n");
  const sections = [];
  let current = null;
  lines.forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) return;
    if (/^[A-Za-z ]+:$/.test(trimmed)) {
      if (current) sections.push(current);
      current = { title: trimmed.replace(":", ""), body: [] };
    } else {
      if (!current) current = { title: "Response", body: [] };
      current.body.push(trimmed);
    }
  });
  if (current) sections.push(current);
  return sections;
}
function renderAssistantCards(text) {
  const sections = parseSections(text);
  const wrap = document.createElement("div");
  wrap.className = "response-cards";
  if (!sections.length) {
    const fallback = document.createElement("div");
    fallback.className = "response-card";
    fallback.innerHTML = `<h3>Response</h3><div class="card-body">${makeLinksClickable(text)}</div>`;
    wrap.appendChild(fallback);
    return wrap;
  }
  sections.forEach(section => {
    const card = document.createElement("div");
    card.className = "response-card";
    card.innerHTML = `<h3>${escapeHtml(section.title)}</h3><div class="card-body">${makeLinksClickable(section.body.join("<br>"))}</div>`;
    wrap.appendChild(card);
  });
  return wrap;
}
function addMessage(role, content, structured = false) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  const label = document.createElement("div");
  label.className = "bubble-label";
  label.textContent = role === "user" ? "You" : "Executive Engine";
  bubble.appendChild(label);
  if (role === "assistant" && structured) {
    bubble.appendChild(renderAssistantCards(content));
  } else {
    const text = document.createElement("div");
    text.className = "bubble-text";
    text.textContent = content;
    bubble.appendChild(text);
  }
  row.appendChild(bubble);
  chatThread.appendChild(row);
  chatThread.scrollTop = chatThread.scrollHeight;
}
function saveHistory(prompt) {
  const item = { prompt, mode: currentMode, timestamp: new Date().toISOString() };
  historyItems.unshift(item);
  historyItems = historyItems.slice(0, 20);
  localStorage.setItem("executive_os_history", JSON.stringify(historyItems));
  renderHistory();
}
function loadHistory() {
  try {
    historyItems = JSON.parse(localStorage.getItem("executive_os_history") || "[]");
  } catch {
    historyItems = [];
  }
  renderHistory();
}
function renderHistory() {
  historyList.innerHTML = "";
  historyItems.forEach(item => {
    const btn = document.createElement("button");
    btn.className = "history-item";
    btn.type = "button";
    btn.textContent = `[${item.mode}] ${item.prompt.slice(0, 56)}${item.prompt.length > 56 ? "..." : ""}`;
    btn.addEventListener("click", () => {
      document.getElementById("input").value = item.prompt;
      currentMode = item.mode;
      modeTabs.forEach(tab => tab.classList.toggle("active", tab.dataset.mode === item.mode));
    });
    historyList.appendChild(btn);
  });
}
function extractActionItems(text) {
  const numbered = text.match(/(^|\n)\s*\d+\.\s.+/g) || [];
  numbered.forEach(item => {
    const clean = item.replace(/^\n?\s*/, "").trim().replace(/<br>/g, " ");
    actionItems.unshift({ text: clean, mode: currentMode });
  });
  actionItems = actionItems.slice(0, 30);
  renderActionItems();
}
function renderActionItems() {
  actionList.innerHTML = "";
  const filtered = activeActionFilter === "all" ? actionItems : actionItems.filter(item => item.mode === activeActionFilter);
  if (!filtered.length) {
    actionList.innerHTML = '<div class="action-item">No action items for this filter yet.</div>';
    return;
  }
  filtered.forEach(item => {
    const div = document.createElement("div");
    div.className = "action-item";
    div.innerHTML = `<strong>[${item.mode}]</strong> ${escapeHtml(item.text)}`;
    actionList.appendChild(div);
  });
}
function renderSummary(summaryText) {
  currentSummaryText = summaryText || "";
  if (!summaryText) {
    summaryContent.innerHTML = '<div class="summary-empty"><div class="summary-empty-title">No summary yet</div><div class="summary-empty-copy">Submit a prompt and the executive summary will update automatically.</div></div>';
    return;
  }
  const sections = parseSections(summaryText);
  if (!sections.length) {
    summaryContent.innerHTML = `<div class="summary-card"><div class="summary-card-title">Summary</div><div class="summary-card-body">${escapeHtml(summaryText)}</div></div>`;
    return;
  }
  summaryContent.innerHTML = "";
  sections.forEach(section => {
    const card = document.createElement("div");
    card.className = "summary-card";
    card.innerHTML = `<div class="summary-card-title">${escapeHtml(section.title)}</div><div class="summary-card-body">${escapeHtml(section.body.join("\n"))}</div>`;
    summaryContent.appendChild(card);
  });
}
async function send() {
  const input = document.getElementById("input").value.trim();
  if (!input) return;

  const payload = {
    input,
    mode: currentMode,
    profile_role: document.getElementById("profile_role").value,
    profile_industry: document.getElementById("profile_industry").value,
    profile_tone: document.getElementById("profile_tone").value,
    profile_goal: document.getElementById("profile_goal").value,
    personal_context: document.getElementById("personal_context").value.trim(),
    uploaded_context: knowledgeText,
    request_attachment_context: requestAttachmentText,
    prior_summary: currentSummaryText
  };

  addMessage("user", input, false);
  saveHistory(input);
  document.getElementById("input").value = "";
  requestAttachmentText = "";
  document.getElementById("requestFileInput").value = "";
  requestStatus.textContent = "No request file loaded";
  loading.classList.remove("hidden");

  try {
    const res = await fetch("https://executive-engine-os.onrender.com/api/command", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    const output = data.output || data.error || "No response returned.";
    addMessage("assistant", output, true);
    extractActionItems(output);
    if (data.summary) renderSummary(data.summary);
  } catch (err) {
    addMessage("assistant", "Error: " + err.message, true);
  } finally {
    loading.classList.add("hidden");
  }
}
loadHistory();
renderActionItems();
renderSummary("");
