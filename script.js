let currentMode = "strategy";
let uploadedText = "";
let historyItems = [];
let actionItems = [];

const modeTabs = document.querySelectorAll(".mode-tab");
const chatThread = document.getElementById("chatThread");
const loading = document.getElementById("loading");
const fileStatus = document.getElementById("fileStatus");
const historyList = document.getElementById("historyList");
const actionList = document.getElementById("actionList");
const settingsBtn = document.getElementById("settingsBtn");
const settingsMenu = document.getElementById("settingsMenu");

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    showSidebarView(btn.dataset.leftView);
  });
});

function showSidebarView(view) {
  document.getElementById("engineSidebar").classList.add("hidden");
  document.getElementById("actionsSidebar").classList.add("hidden");
  document.getElementById("historySidebar").classList.add("hidden");

  if (view === "actions") {
    document.getElementById("actionsSidebar").classList.remove("hidden");
  } else if (view === "history") {
    document.getElementById("historySidebar").classList.remove("hidden");
  } else {
    document.getElementById("engineSidebar").classList.remove("hidden");
  }
}

document.querySelectorAll(".settings-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const view = btn.dataset.topView;
    if (view === "history") {
      document.querySelector('.nav-item[data-left-view="history"]').click();
    } else {
      document.querySelector('.nav-item[data-left-view="engine"]').click();
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

document.getElementById("fileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) {
    uploadedText = "";
    fileStatus.textContent = "No file loaded";
    return;
  }
  try {
    uploadedText = await file.text();
    fileStatus.textContent = `Loaded: ${file.name}`;
  } catch (e) {
    uploadedText = "";
    fileStatus.textContent = "Could not read file";
  }
});

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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

  if (sections.length === 0) {
    const fallback = document.createElement("div");
    fallback.className = "response-card";
    fallback.innerHTML = `<h3>Response</h3><div class="card-body">${makeLinksClickable(text)}</div>`;
    wrap.appendChild(fallback);
    return wrap;
  }

  sections.forEach(section => {
    const card = document.createElement("div");
    card.className = "response-card";
    const bodyHtml = makeLinksClickable(section.body.join("<br>"));
    card.innerHTML = `<h3>${escapeHtml(section.title)}</h3><div class="card-body">${bodyHtml}</div>`;
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
  const item = {
    prompt,
    mode: currentMode,
    timestamp: new Date().toISOString()
  };
  historyItems.unshift(item);
  historyItems = historyItems.slice(0, 12);
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
    btn.textContent = `[${item.mode}] ${item.prompt.slice(0, 50)}${item.prompt.length > 50 ? "..." : ""}`;
    btn.addEventListener("click", () => {
      document.getElementById("input").value = item.prompt;
      currentMode = item.mode;
      modeTabs.forEach(tab => {
        tab.classList.toggle("active", tab.dataset.mode === item.mode);
      });
    });
    historyList.appendChild(btn);
  });
}

function extractActionItems(text) {
  const matches = text.match(/\n\s*\d+\.\s.+/g) || [];
  matches.forEach(item => {
    const clean = item.replace(/^\n\s*/, "").trim();
    if (!actionItems.includes(clean)) actionItems.push(clean);
  });
  actionItems = actionItems.slice(-20);
  renderActionItems();
}

function renderActionItems() {
  actionList.innerHTML = "";
  if (actionItems.length === 0) {
    actionList.innerHTML = '<div class="action-item">No action items yet.</div>';
    return;
  }
  actionItems.forEach(item => {
    const div = document.createElement("div");
    div.className = "action-item";
    div.textContent = item;
    actionList.appendChild(div);
  });
}

async function send() {
  const input = document.getElementById("input").value.trim();
  if (!input) return;

  const payload = {
    input: input,
    mode: currentMode,
    profile_role: document.getElementById("profile_role").value,
    profile_industry: document.getElementById("profile_industry").value,
    profile_tone: document.getElementById("profile_tone").value,
    profile_goal: document.getElementById("profile_goal").value,
    personal_context: document.getElementById("personal_context").value.trim(),
    uploaded_context: uploadedText
  };

  addMessage("user", input, false);
  saveHistory(input);
  document.getElementById("input").value = "";
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
  } catch (err) {
    addMessage("assistant", "Error: " + err.message, true);
  } finally {
    loading.classList.add("hidden");
  }
}

loadHistory();
renderActionItems();
showSidebarView("engine");
