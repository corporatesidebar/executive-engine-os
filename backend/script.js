
const API_URL = "https://executive-engine-os.onrender.com/api/command";
let activeMode = "strategy";
let historyItems = [];

const messagesEl = document.getElementById("messages");
const actionItemsEl = document.getElementById("actionItems");
const feedbackOverviewEl = document.getElementById("feedbackOverview");
const historyListEl = document.getElementById("historyList");
const statusTextEl = document.getElementById("statusText");

document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeMode = btn.dataset.mode;
  });
});

document.getElementById("runBtn").addEventListener("click", runEngine);
document.getElementById("clearBtn").addEventListener("click", () => {
  messagesEl.innerHTML = '<div class="empty-state"><h3>Ready</h3><p>Type a situation and get a sharper decision, risk view, and action plan.</p></div>';
});

function getValue(id){ return document.getElementById(id).value.trim(); }

function addUserMessage(text){
  if (messagesEl.querySelector(".empty-state")) messagesEl.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "message user";
  wrap.innerHTML = `
    <div class="bubble">
      <div class="msg-label">You</div>
      <div>${escapeHtml(text)}</div>
    </div>
  `;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addAIMessage(data){
  const wrap = document.createElement("div");
  wrap.className = "message ai";
  wrap.innerHTML = `
    <div class="bubble">
      <div class="msg-label">Executive Engine</div>
      <div class="structured">
        <div class="card"><h4>Decision</h4><p>${escapeHtml(data.decision || "")}</p></div>
        <div class="card"><h4>Why</h4><p>${escapeHtml(data.why || "")}</p></div>
        <div class="card risk"><h4>Risk</h4><p>${escapeHtml(data.risk || "")}</p></div>
        <div class="card action"><h4>Action Items</h4><ul>${(data.action_items || []).map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul></div>
        <div class="card priority"><h4>Priority</h4><p>${escapeHtml(data.priority || "")}</p></div>
      </div>
    </div>
  `;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderActionItems(items){
  if (!items || !items.length){
    actionItemsEl.innerHTML = '<div class="placeholder">No action items yet.</div>';
    return;
  }
  actionItemsEl.innerHTML = items.map((item, idx) => `
    <div class="stack-item">
      <strong>Action ${idx+1}</strong>
      <div>${escapeHtml(item)}</div>
    </div>
  `).join("");
}

function renderFeedbackOverview(data){
  const blocks = [
    ["Decision", data.decision],
    ["Why", data.why],
    ["Risk", data.risk],
    ["Feedback Overview", data.feedback_overview || ""]
  ].filter(x => x[1] && x[1].trim());

  if (!blocks.length){
    feedbackOverviewEl.innerHTML = '<div class="placeholder">No feedback overview yet.</div>';
    return;
  }
  feedbackOverviewEl.innerHTML = blocks.map(([title, body]) => `
    <div class="stack-item">
      <strong>${escapeHtml(title)}</strong>
      <div>${escapeHtml(body)}</div>
    </div>
  `).join("");
}

function renderHistory(){
  if (!historyItems.length){
    historyListEl.innerHTML = '<div class="placeholder">No history yet.</div>';
    return;
  }
  historyListEl.innerHTML = historyItems.map(item => `
    <div class="stack-item">
      <strong>${escapeHtml(item.mode)}</strong>
      <div>${escapeHtml(item.prompt.slice(0, 90))}</div>
    </div>
  `).join("");
}

async function runEngine(){
  const prompt = getValue("promptInput");
  if (!prompt) return;

  addUserMessage(prompt);
  statusTextEl.textContent = "Running...";

  const payload = {
    input: prompt,
    mode: activeMode,
    profile_role: getValue("roleTarget"),
    profile_industry: getValue("industry"),
    profile_tone: getValue("tone"),
    profile_goal: getValue("goal"),
    personal_context: getValue("personalContext"),
    uploaded_context: getValue("knowledgeContext")
  };

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    const structured = data.structured || data;

    addAIMessage(structured);
    renderActionItems(structured.action_items || []);
    renderFeedbackOverview(structured);

    historyItems.unshift({ mode: activeMode, prompt });
    historyItems = historyItems.slice(0, 8);
    renderHistory();

    statusTextEl.textContent = "Done";
  } catch (err) {
    addAIMessage({
      decision: "Request failed",
      why: "The frontend could not reach the backend.",
      risk: String(err),
      action_items: [
        "Check backend is live",
        "Check the backend route exists",
        "Try the request again"
      ],
      priority: "High",
      feedback_overview: "Frontend to backend connection failed."
    });
    statusTextEl.textContent = "Error";
  }
}

function escapeHtml(str){
  return (str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
