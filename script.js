let currentMode = "strategy";
let uploadedText = "";
let historyItems = [];

const modeTabs = document.querySelectorAll(".mode-tab");
const chatThread = document.getElementById("chatThread");
const loading = document.getElementById("loading");
const fileStatus = document.getElementById("fileStatus");
const historyList = document.getElementById("historyList");

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

async function send() {
  const input = document.getElementById("input").value.trim();
  if (!input) return;

  const payload = {
    input: input,
    mode: currentMode,
    profile_role: document.getElementById("profile_role").value,
    profile_industry: document.getElementById("profile_industry").value,
    profile_work_style: document.getElementById("profile_work_style").value,
    profile_tone: document.getElementById("profile_tone").value,
    profile_goal: document.getElementById("profile_goal").value,
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
    addMessage("assistant", data.output || data.error || "No response returned.", true);
  } catch (err) {
    addMessage("assistant", "Error: " + err.message, true);
  } finally {
    loading.classList.add("hidden");
  }
}

loadHistory();
