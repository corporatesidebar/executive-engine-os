const BACKEND_URL = "PASTE_YOUR_RENDER_BACKEND_URL_HERE/chat";

const chatWindow = document.getElementById("chatWindow");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const modeButtons = document.querySelectorAll(".mode-btn");
const activeModeTitle = document.getElementById("activeModeTitle");

let activeMode = "strategy";

const modeTitles = {
  strategy: "Strategy Mode",
  decision: "Decision Mode",
  meeting: "Meeting Mode",
  proposal: "Proposal Mode",
};

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    modeButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    activeMode = button.dataset.mode;
    activeModeTitle.textContent = modeTitles[activeMode] || "Strategy Mode";
  });
});

function addUserMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "message user";
  wrapper.innerHTML = `
    <div class="message-header">
      <span class="message-role">You</span>
    </div>
    <div class="user-text"></div>
  `;
  wrapper.querySelector(".user-text").textContent = text;
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function addLoadingMessage() {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";
  wrapper.id = "loadingMessage";
  wrapper.innerHTML = `
    <div class="message-header">
      <span class="message-role">Executive Engine</span>
    </div>
    <div class="loading">Running executive analysis...</div>
  `;
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function removeLoadingMessage() {
  const loading = document.getElementById("loadingMessage");
  if (loading) loading.remove();
}

function createList(items) {
  if (!items || !items.length) return `<div class="summary">None.</div>`;
  return `<ul class="clean-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function createActions(actions) {
  if (!actions || !actions.length) return `<div class="summary">No actions returned.</div>`;

  return `
    <div class="action-list">
      ${actions.map((action) => `
        <div class="action-item">
          <div class="action-title">${escapeHtml(action.title || "Action")}</div>
          <div class="action-detail">${escapeHtml(action.detail || "")}</div>
          <div class="action-meta">
            <span class="meta-pill">Owner: ${escapeHtml(action.owner || "You")}</span>
            <span class="meta-pill">Timing: ${escapeHtml(action.timing || "Now")}</span>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function getPriorityClass(priority) {
  const value = (priority || "").toLowerCase();
  if (value === "medium") return "priority-medium";
  if (value === "low") return "priority-low";
  return "priority-high";
}

function renderAssistantMessage(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";

  const summary = data.executive_summary || "";
  const outcome = data.outcome || "";
  const priority = data.priority || "High";
  const risks = Array.isArray(data.risks) ? data.risks : [];
  const assumptions = Array.isArray(data.assumptions) ? data.assumptions : [];
  const followUps = Array.isArray(data.follow_up_questions) ? data.follow_up_questions : [];
  const actions = Array.isArray(data.actions) ? data.actions : [];

  wrapper.innerHTML = `
    <div class="message-header">
      <span class="message-role">Executive Engine</span>
    </div>
    <div class="exec-layout">
      <div class="exec-main">
        <div class="card">
          <h3>Outcome</h3>
          <div class="outcome">${escapeHtml(outcome)}</div>
        </div>
        <div class="card">
          <h3>Actions</h3>
          ${createActions(actions)}
        </div>
        <div class="card">
          <h3>Risks</h3>
          ${createList(risks)}
        </div>
      </div>
      <div class="exec-side">
        <div class="card">
          <h3>Executive Summary</h3>
          <div class="summary">${escapeHtml(summary)}</div>
        </div>
        <div class="card">
          <h3>Priority</h3>
          <div class="priority-badge ${getPriorityClass(priority)}">${escapeHtml(priority)}</div>
        </div>
        <div class="card">
          <h3>Assumptions</h3>
          ${createList(assumptions)}
        </div>
        <div class="card">
          <h3>Follow-Up Questions</h3>
          ${createList(followUps)}
        </div>
      </div>
    </div>
  `;
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
    .replaceAll("\n", "<br>");
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  addUserMessage(text);
  messageInput.value = "";
  sendButton.disabled = true;
  addLoadingMessage();

  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        mode: activeMode
      })
    });

    const data = await response.json();
    removeLoadingMessage();

    if (!response.ok || !data.response) {
      renderAssistantMessage({
        executive_summary: "The system returned an error.",
        outcome: "Review backend URL, environment variables, and deployment status.",
        priority: "High",
        risks: ["The backend request failed or returned invalid data."],
        actions: [
          { title: "Check backend URL", detail: "Confirm script.js points to the live /chat endpoint.", owner: "You", timing: "Now" },
          { title: "Check env vars", detail: "Verify OpenAI and Supabase keys in Render.", owner: "You", timing: "Now" }
        ],
        assumptions: [],
        follow_up_questions: []
      });
      return;
    }

    renderAssistantMessage(data.response);
  } catch (error) {
    removeLoadingMessage();
    renderAssistantMessage({
      executive_summary: "The frontend could not reach the backend.",
      outcome: "Confirm the Render backend URL and that CORS/deployment are working.",
      priority: "High",
      risks: ["Network error or wrong endpoint."],
      actions: [
        { title: "Verify backend URL", detail: "Replace the placeholder BACKEND_URL in script.js with your live Render backend /chat endpoint.", owner: "You", timing: "Now" },
        { title: "Check backend health", detail: "Open the /health route on the backend and confirm the service is live.", owner: "You", timing: "Now" }
      ],
      assumptions: [],
      follow_up_questions: []
    });
  } finally {
    sendButton.disabled = false;
  }
}

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    sendMessage();
  }
});
