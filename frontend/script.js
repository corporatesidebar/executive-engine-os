
const API_URL = "https://executive-engine-os.onrender.com/api/command";

let currentMode = "strategy";
let activeActionFilter = "all";
let personalKnowledgeText = "";
let requestAttachmentText = "";

const chatScroll = document.getElementById("chatScroll");
const historyBar = document.getElementById("historyBar");
const historyList = document.getElementById("historyList");
const actionList = document.getElementById("actionList");
const summaryList = document.getElementById("summaryList");
const loading = document.getElementById("loading");

let memory = {
  conversations: JSON.parse(localStorage.getItem("exec_conversations_v8") || "[]"),
  actions: JSON.parse(localStorage.getItem("exec_actions_v8") || "[]"),
  summaries: JSON.parse(localStorage.getItem("exec_summaries_v8") || "[]")
};

document.querySelectorAll(".mode-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    document.querySelectorAll(".mode-btn").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
  });
});

document.getElementById("toggleHistoryBtn").addEventListener("click", ()=>{
  historyBar.classList.toggle("open");
});

document.getElementById("knowledgeFileInput").addEventListener("change", async (e)=>{
  const file = e.target.files[0];
  if(!file){
    personalKnowledgeText = "";
    document.getElementById("knowledgeStatus").textContent = "No personal knowledge file loaded";
    return;
  }
  personalKnowledgeText = await file.text();
  document.getElementById("knowledgeStatus").textContent = "Loaded: " + file.name;
});

document.getElementById("requestFileInput").addEventListener("change", async (e)=>{
  const file = e.target.files[0];
  if(!file){
    requestAttachmentText = "";
    document.getElementById("requestStatus").textContent = "No request file loaded";
    return;
  }
  requestAttachmentText = await file.text();
  document.getElementById("requestStatus").textContent = "Attached: " + file.name;
});

document.querySelectorAll(".filter-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    document.querySelectorAll(".filter-btn").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    activeActionFilter = btn.dataset.filter;
    renderActionItems();
  });
});

document.getElementById("prompt").addEventListener("keydown", (e)=>{
  if(e.key === "Enter" && !e.shiftKey){
    e.preventDefault();
    runEngine();
  }
});

document.getElementById("runBtn").addEventListener("click", runEngine);

function saveLocal(){
  localStorage.setItem("exec_conversations_v8", JSON.stringify(memory.conversations));
  localStorage.setItem("exec_actions_v8", JSON.stringify(memory.actions));
  localStorage.setItem("exec_summaries_v8", JSON.stringify(memory.summaries));
}

function escapeHtml(str=""){
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function linkify(str=""){
  const escaped = escapeHtml(str);
  return escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
}

function semanticClass(title){
  const t = (title || "").toLowerCase();
  if(t.includes("risk")) return "risk";
  if(t.includes("action")) return "action";
  if(t.includes("priority")) return "priority";
  if(t.includes("overview")) return "overview";
  if(t.includes("decision")) return "outcome";
  return "generic";
}

function renderAssistantCards(structured){
  const wrap = document.createElement("div");
  wrap.className = "cards";

  const ordered = [
    ["Decision", structured.decision, "outcome"],
    ["Why", structured.why, "generic"],
    ["Risk", structured.risk, "risk"],
    ["Action", (structured.action_items || []).map((x, i)=>`${i+1}. ${x}`).join("<br>"), "action"],
    ["Priority", structured.priority, "priority"],
    ["Feedback Overview", structured.feedback_overview, "overview"]
  ];

  ordered.forEach(([title, value, klass])=>{
    if(!value || (Array.isArray(value) && !value.length)) return;
    const card = document.createElement("div");
    card.className = "result-card " + klass;
    card.innerHTML = `<h4>${escapeHtml(title)}</h4><div class="body">${typeof value === "string" ? linkify(value) : value}</div>`;
    wrap.appendChild(card);
  });

  return wrap;
}

function addMessage(role, payload){
  const row = document.createElement("div");
  row.className = "message-row " + role;
  const bubble = document.createElement("div");
  bubble.className = "bubble " + role;
  const label = document.createElement("div");
  label.className = "bubble-label";
  label.textContent = role === "user" ? "You" : "Executive Engine";
  bubble.appendChild(label);

  if(role === "ai"){
    bubble.appendChild(renderAssistantCards(payload));
  } else {
    const textEl = document.createElement("div");
    textEl.style.fontSize = "18px";
    textEl.style.lineHeight = "1.5";
    textEl.textContent = payload;
    bubble.appendChild(textEl);
  }

  row.appendChild(bubble);
  chatScroll.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function clearThread(){
  chatScroll.innerHTML = "";
}

function openConversation(item){
  clearThread();
  addMessage("user", item.prompt);
  addMessage("ai", item.structured);
}

function inferPriority(value){
  const text = (value || "").toLowerCase();
  if(text.includes("high") || text.includes("urgent") || text.includes("immediate")) return "high";
  if(text.includes("medium") || text.includes("important") || text.includes("soon")) return "medium";
  return "normal";
}

function renderHistory(){
  historyList.innerHTML = "";
  const conversations = memory.conversations || [];
  conversations.forEach(item=>{
    const btn = document.createElement("button");
    btn.className = "history-chip";
    btn.textContent = `[${item.mode}] ${item.prompt.slice(0,48)}${item.prompt.length>48?"...":""}`;
    btn.onclick = ()=>openConversation(item);
    historyList.appendChild(btn);
  });
}

function renderActionItems(){
  actionList.innerHTML = "";
  const list = activeActionFilter === "all"
    ? (memory.actions || [])
    : (memory.actions || []).filter(x=>x.mode===activeActionFilter);

  if(!list.length){
    actionList.innerHTML = `<div class="action-item" data-priority="normal"><h5>Status</h5><p>No action items yet.</p></div>`;
    return;
  }

  list.forEach(item=>{
    const div = document.createElement("div");
    div.className = "action-item";
    div.dataset.priority = item.priority || "normal";
    div.innerHTML = `<h5>${escapeHtml(item.mode)} · ${escapeHtml(item.priority || "normal")}</h5><p>${escapeHtml(item.action)}</p>`;
    div.onclick = ()=>openConversation(item.conversation);
    actionList.appendChild(div);
  });
}

function renderSummaries(){
  summaryList.innerHTML = "";
  const summaries = memory.summaries || [];
  if(!summaries.length){
    summaryList.innerHTML = `<div class="summary-card"><h5>Status</h5><p>No feedback overview yet.</p></div>`;
    return;
  }
  summaries.forEach(item=>{
    const div = document.createElement("div");
    div.className = "summary-card";
    div.innerHTML = `<h5>${escapeHtml(item.title)}</h5><p>${escapeHtml(item.body)}</p>`;
    div.onclick = ()=>openConversation(item.conversation);
    summaryList.appendChild(div);
  });
}

async function runEngine(){
  const prompt = document.getElementById("prompt").value.trim();
  if(!prompt) return;

  const payload = {
    input: prompt,
    mode: currentMode,
    profile_role: document.getElementById("profile_role").value,
    profile_industry: document.getElementById("profile_industry").value,
    profile_tone: document.getElementById("profile_tone").value,
    profile_goal: document.getElementById("profile_goal").value,
    personal_context: document.getElementById("personal_context").value.trim(),
    uploaded_context: personalKnowledgeText,
    request_attachment_context: requestAttachmentText
  };

  addMessage("user", prompt);
  document.getElementById("prompt").value = "";
  loading.style.display = "inline";

  try{
    const res = await fetch(API_URL, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    const data = await res.json();

    const structured = data.structured || {
      decision: data.error || "No response returned.",
      why: "",
      risk: "",
      action_items: [],
      priority: "",
      feedback_overview: ""
    };

    addMessage("ai", structured);

    const conversation = {
      id: String(Date.now()),
      prompt,
      mode: currentMode,
      structured,
      created_at: new Date().toISOString()
    };

    memory.conversations.unshift(conversation);
    memory.conversations = memory.conversations.slice(0, 30);

    const actions = (structured.action_items || []).map(action => ({
      id: String(Date.now()) + Math.random().toString(16).slice(2),
      mode: currentMode,
      action,
      priority: inferPriority(structured.priority),
      conversation
    }));
    memory.actions = [...actions, ...memory.actions].slice(0, 50);

    const summaryParts = [
      {title:"Objective", body:structured.feedback_overview || structured.why || ""},
      {title:"Priority", body:structured.priority || ""},
      {title:"Risk", body:structured.risk || ""}
    ].filter(x => x.body);

    memory.summaries = summaryParts.map(x => ({
      title: x.title,
      body: x.body,
      conversation
    }));

    saveLocal();
    renderHistory();
    renderActionItems();
    renderSummaries();

    requestAttachmentText = "";
    document.getElementById("requestFileInput").value = "";
    document.getElementById("requestStatus").textContent = "No request file loaded";
  } catch(err){
    addMessage("ai", {
      decision: "Request failed",
      why: err.message,
      risk: "No output returned",
      action_items: ["Retry with shorter context", "Remove large attachment text", "Try again in 10 seconds"],
      priority: "Medium",
      feedback_overview: "The request failed before the engine returned a structured answer."
    });
  } finally{
    loading.style.display = "none";
  }
}

renderHistory();
renderActionItems();
renderSummaries();
