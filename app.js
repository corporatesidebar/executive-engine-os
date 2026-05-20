/* === V37100 REAL FRONTEND STATE CONTROLLER === */
(function () {
  "use strict";

  const API_URL = "https://executive-engine-os.onrender.com/run";

  const state = {
    messages: [],
    currentCommand: "",
    isLoading: false,
    lastResponse: null,
    executionObjects: [],
    activeCategory: "Command",
    rightRailState: null,
    error: null
  };

  const els = {};

  function init() {
    els.thread = document.querySelector("#thread, .thread");
    els.input = document.querySelector("#commandInput, textarea, input[type='text']");
    els.execute = document.querySelector("#executeBtn, .execute");
    els.summary = document.querySelector("#executiveSummary, .summary");
    els.rail = document.querySelector("#rightRail, .rail");

    if (!els.thread || !els.input || !els.execute) {
      console.error("V37100 boot failed: missing required runtime hooks", els);
      return;
    }

    els.execute.addEventListener("click", handleSubmit);
    els.input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleSubmit();
      }
    });

    renderApp();
    console.log("V37100 state controller mounted", { API_URL });
  }

  function uid(prefix = "msg") {
    return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  }

  function now() {
    return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[char]));
  }

  function toText(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return value.map(toText).join(", ");
    if (typeof value === "object") {
      return Object.entries(value).map(([key, val]) => `${key}: ${toText(val)}`).join(" · ");
    }
    return String(value);
  }

  function toArray(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === "string") {
      return value.split(/\n|•|- /).map((item) => item.trim()).filter(Boolean);
    }
    if (typeof value === "object") return Object.values(value).filter(Boolean);
    return [value];
  }

  function normalizeResponse(raw) {
    const data = raw && typeof raw === "object" ? raw : { executive_summary: String(raw || "") };

    const parsed = {
      executive_summary: data.executive_summary || data.summary || data.message || "",
      next_move: data.next_move || data.what_to_do_now || "",
      decision: data.decision || data.recommendation || "",
      action_steps: toArray(data.action_steps || data.actions || data.next_actions),
      ready_assets: toArray(data.ready_assets || data.assets || data.asset),
      risk: data.risk || data.active_risk || "",
      priority: data.priority || "Medium",
      recommended_command: data.recommended_command || data.next_command || "",
      execution_objects: toArray(data.execution_objects || data.objects),
      primary_object: data.primary_object || null,
      deployment_sequence: toArray(data.deployment_sequence || data.sequence),
      executive_scan: data.executive_scan || data.scan || "",
      provider_used: data.provider_used || data.provider || ""
    };

    parsed.execution_objects = parsed.execution_objects.map((object, index) => {
      if (typeof object === "string") {
        return {
          title: `Execution Object ${index + 1}`,
          type: "workflow",
          status: "Ready",
          content: object
        };
      }
      return {
        title: object.title || object.name || object.type || `Execution Object ${index + 1}`,
        type: object.type || object.category || "workflow",
        status: object.status || "Ready",
        content: object.description || object.summary || object.content || object.value || toText(object)
      };
    });

    return parsed;
  }

  function buildPayload(command) {
    return {
      input: command,
      mode: "execution",
      brain: "operator",
      output_type: "standard",
      depth: "auto",
      provider: "openai"
    };
  }

  async function handleSubmit() {
    const command = (els.input.value || "").trim();
    if (!command || state.isLoading) return;

    const loadingId = uid("loading");

    state.currentCommand = command;
    state.error = null;
    state.isLoading = true;
    state.messages.push({
      id: uid("user"),
      role: "user",
      status: "user",
      content: command,
      timestamp: now()
    });
    state.messages.push({
      id: loadingId,
      role: "assistant",
      status: "assistant_loading",
      content: "Running live backend response contract...",
      timestamp: now()
    });

    els.input.value = "";
    renderApp();

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(buildPayload(command))
      });

      const rawText = await response.text();
      let rawData;
      try {
        rawData = JSON.parse(rawText);
      } catch {
        rawData = { executive_summary: rawText };
      }

      console.log("V37100 /run raw response:", rawData);

      if (!response.ok) {
        throw new Error(rawData.detail || rawData.error || rawText || `HTTP ${response.status}`);
      }

      const parsed = normalizeResponse(rawData);
      state.lastResponse = parsed;
      state.executionObjects = parsed.execution_objects;
      state.rightRailState = buildRightRailState(parsed);
      state.messages = state.messages.map((message) => {
        if (message.id !== loadingId) return message;
        return {
          ...message,
          status: "assistant_success",
          content: parsed.executive_summary || parsed.executive_scan || parsed.next_move || "Execution package generated.",
          response: parsed
        };
      });
    } catch (error) {
      console.error("V37100 /run failed:", error);
      state.error = error.message || "Backend request failed.";
      state.messages = state.messages.map((message) => {
        if (message.id !== loadingId) return message;
        return {
          ...message,
          status: "assistant_error",
          content: state.error
        };
      });
    } finally {
      state.isLoading = false;
      renderApp();
    }
  }

  function buildRightRailState(response) {
    return {
      next_move: response.next_move || response.executive_summary || "No next move returned.",
      decision: response.decision || "No decision returned.",
      actions: response.action_steps,
      assets: response.ready_assets,
      risk: response.risk || "No risk returned.",
      priority: response.priority || "Medium",
      recommended_command: response.recommended_command || "Continue the workflow.",
      executive_scan: response.executive_scan || response.executive_summary || response.next_move || "Live backend response received."
    };
  }

  function renderApp() {
    if (els.execute) {
      els.execute.disabled = state.isLoading;
      els.execute.textContent = state.isLoading ? "Executing..." : "Execute →";
    }

    renderThread();
    renderSummary();
    renderRightRail();
  }

  function renderThread() {
    if (!els.thread) return;

    if (!state.messages.length) {
      els.thread.innerHTML = `
        <div class="thread-empty">
          <div>
            <strong>No active command thread yet.</strong><br>
            Enter a command above to create live executive output from the backend.
          </div>
        </div>`;
      return;
    }

    els.thread.innerHTML = state.messages.map(renderMessage).join("");
    els.thread.scrollTop = els.thread.scrollHeight;
  }

  function renderMessage(message) {
    if (message.role === "user") {
      return `
        <div class="msg" data-id="${escapeHtml(message.id)}">
          <div class="bubble-avatar">W</div>
          <div>
            <div class="meta"><strong>You</strong><span>${escapeHtml(message.timestamp)}</span></div>
            <div class="copy">${escapeHtml(message.content)}</div>
          </div>
        </div>`;
    }

    if (message.status === "assistant_loading") {
      return `
        <div class="msg" data-id="${escapeHtml(message.id)}">
          <div class="bubble-avatar engine-avatar">E</div>
          <div>
            <div class="meta"><strong>Executive Engine</strong><span>${escapeHtml(message.timestamp)}</span></div>
            <div class="v37060-stream">
              <div class="copy">Running live backend response contract...</div>
              <div class="v37060-progress"><span></span></div>
            </div>
          </div>
        </div>`;
    }

    if (message.status === "assistant_error") {
      return `
        <div class="msg" data-id="${escapeHtml(message.id)}">
          <div class="bubble-avatar engine-avatar">E</div>
          <div>
            <div class="meta"><strong>Executive Engine</strong><span>${escapeHtml(message.timestamp)}</span></div>
            <div class="runtime-error">${escapeHtml(message.content)}</div>
          </div>
        </div>`;
    }

    return `
      <div class="msg" data-id="${escapeHtml(message.id)}">
        <div class="bubble-avatar engine-avatar">E</div>
        <div>
          <div class="meta"><strong>Executive Engine</strong><span>${escapeHtml(message.timestamp)}</span></div>
          <div class="copy">${escapeHtml(message.content)}</div>
          ${renderResponsePackage(message.response)}
        </div>
      </div>`;
  }

  function renderResponsePackage(response) {
    if (!response) return "";

    const objects = response.execution_objects || [];
    const hasObjects = objects.length > 0;

    return `
      <div class="runtime-package">
        <div class="runtime-package-head">
          <div>
            <strong>${escapeHtml(getPrimaryTitle(response))}</strong><br>
            <span>Live /run response rendered through V37100 controller</span>
          </div>
          <span class="runtime-pill">${escapeHtml(response.priority || "Ready")}</span>
        </div>
        ${hasObjects ? renderExecutionObjects(objects) : renderLegacySections(response)}
        ${renderAssets(response.ready_assets)}
        ${renderDeploymentSequence(response.deployment_sequence)}
      </div>`;
  }

  function getPrimaryTitle(response) {
    const primary = response.primary_object;
    if (primary && typeof primary === "object") return primary.title || primary.name || "Primary Execution Object";
    if (primary && typeof primary === "string") return primary;
    return "Executive Execution Package";
  }

  function renderExecutionObjects(objects) {
    return `
      <div class="runtime-grid">
        ${objects.map((object, index) => `
          <div class="runtime-card">
            <h4>${escapeHtml(object.title || `Execution Object ${index + 1}`)}</h4>
            <p>${escapeHtml(object.type || "workflow")} · ${escapeHtml(object.status || "Ready")}</p>
            <p>${escapeHtml(object.content || "")}</p>
            <div class="runtime-card-actions">
              <button type="button" data-action="details" data-index="${index}">View Details</button>
              <button type="button" data-action="copy" data-copy="${escapeHtml(object.content || object.title || "")}">Copy</button>
            </div>
          </div>
        `).join("")}
      </div>`;
  }

  function renderLegacySections(response) {
    return `
      <div class="runtime-section"><h4>EXECUTIVE SUMMARY</h4><p>${escapeHtml(response.executive_summary || response.executive_scan || "Not returned.")}</p></div>
      <div class="runtime-section"><h4>NEXT MOVE</h4><p>${escapeHtml(response.next_move || "Not returned.")}</p></div>
      <div class="runtime-section"><h4>DECISION</h4><p>${escapeHtml(response.decision || "Not returned.")}</p></div>
      <div class="runtime-section"><h4>ACTION STEPS</h4>${renderList(response.action_steps)}</div>
      <div class="runtime-section"><h4>RISK</h4><p>${escapeHtml(response.risk || "Not returned.")}</p></div>
      <div class="runtime-section"><h4>RECOMMENDED COMMAND</h4><p>${escapeHtml(response.recommended_command || "Not returned.")}</p></div>`;
  }

  function renderAssets(assets) {
    const list = toArray(assets);
    if (!list.length) return "";
    return `
      <div class="runtime-assets">
        ${list.slice(0, 6).map((asset) => {
          const title = asset.title || asset.name || toText(asset).slice(0, 80);
          const meta = asset.type || asset.format || asset.status || "Ready asset";
          return `<div class="runtime-asset"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(meta)}</span><em>⇩</em></div>`;
        }).join("")}
      </div>`;
  }

  function renderDeploymentSequence(sequence) {
    const list = toArray(sequence);
    if (!list.length) return "";
    return `<div class="runtime-section"><h4>DEPLOYMENT SEQUENCE</h4>${renderList(list)}</div>`;
  }

  function renderList(items) {
    const list = toArray(items);
    if (!list.length) return "<p>Not returned.</p>";
    return `<ul>${list.map((item) => `<li>${escapeHtml(toText(item))}</li>`).join("")}</ul>`;
  }

  function renderSummary() {
    if (!els.summary) return;

    const response = state.lastResponse;
    if (!response) {
      els.summary.innerHTML = `
        <div class="section-head">EXECUTIVE SUMMARY</div><div class="section-sub">Live updates from the conversation</div>
        <div class="sum-card orange"><div class="badge">0</div><div class="sum-title">✕ NEXT MOVE</div><p>No command executed yet.</p><div class="note">＋ Awaiting backend response</div></div>
        <div class="sum-card"><div class="badge">0</div><div class="sum-title">ℹ DECISION</div><p>No live decision yet.</p><div class="note">＋ Awaiting backend response</div></div>
        <div class="sum-card green"><div class="badge">0</div><div class="sum-title">✓ ACTION STEPS</div><p>No action steps yet.</p><div class="note">＋ Awaiting backend response</div></div>
        <div class="sum-card purple"><div class="badge">0</div><div class="sum-title">✦ READY ASSETS</div><p>No assets yet.</p><div class="note">＋ Awaiting backend response</div></div>`;
      return;
    }

    els.summary.innerHTML = `
      <div class="section-head">EXECUTIVE SUMMARY</div><div class="section-sub">Live updates from backend /run</div>
      <div class="sum-card orange"><div class="badge">1</div><div class="sum-title">✕ NEXT MOVE</div><p>${escapeHtml(response.next_move || response.executive_summary || "Not returned.")}</p><div class="note">＋ Live response</div></div>
      <div class="sum-card"><div class="badge">1</div><div class="sum-title">ℹ DECISION</div><p>${escapeHtml(response.decision || "Not returned.")}</p><div class="note">＋ Live response</div></div>
      <div class="sum-card green"><div class="badge">${response.action_steps.length}</div><div class="sum-title">✓ ACTION STEPS</div>${renderList(response.action_steps)}<div class="note">＋ Live response</div></div>
      <div class="sum-card purple"><div class="badge">${response.ready_assets.length}</div><div class="sum-title">✦ READY ASSETS</div>${renderList(response.ready_assets)}<div class="note">＋ Live response</div></div>
      <div class="sum-card red"><div class="badge">1</div><div class="sum-title">⚠ ACTIVE RISKS</div><p>${escapeHtml(response.risk || "Not returned.")}</p><div class="note">＋ Live response</div></div>
      <div class="sum-card orange"><div class="sum-title">✪ PRIORITY <span style="margin-left:auto;background:#fff1e8;color:#ff5a13;border-radius:9px;padding:4px 8px">${escapeHtml(response.priority || "Medium")}</span></div><p>${escapeHtml(response.recommended_command || "Continue the workflow.")}</p><div class="note">＋ Recommended command</div></div>`;
  }

  function renderRightRail() {
    if (!els.rail) return;

    const rail = state.rightRailState;
    if (!rail) {
      els.rail.innerHTML = `
        <h3>EXECUTIVE INTELLIGENCE</h3>
        <div class="search">⌕ Awaiting live backend context <span style="margin-left:auto">☷</span></div>
        <div class="rail-card"><div class="rail-title">◆ KEY INSIGHT</div><p>No live backend response yet.</p><div class="link">Execute a command →</div></div>
        <div class="rail-card"><div class="rail-title">▧ MEMORY</div><p>Context will update from the active command thread.</p><div class="link">Waiting →</div></div>`;
      return;
    }

    els.rail.innerHTML = `
      <h3>EXECUTIVE INTELLIGENCE</h3>
      <div class="search">⌕ Live backend context loaded <span style="margin-left:auto">☷</span></div>
      <div class="rail-card"><div class="rail-title">◆ KEY INSIGHT</div><p>${escapeHtml(rail.executive_scan)}</p><div class="link">Live insight →</div></div>
      <div class="rail-card"><div class="rail-title">▣ NEXT MOVE</div><p>${escapeHtml(rail.next_move)}</p><div class="link">View next move →</div></div>
      <div class="rail-card"><div class="rail-title">ℹ DECISION</div><p>${escapeHtml(rail.decision)}</p><div class="link">View decision →</div></div>
      <div class="rail-card"><div class="rail-title">✓ EXECUTION STATUS</div><p>${rail.actions.length} action step(s). ${rail.assets.length} ready asset(s).</p><div class="link">View execution →</div></div>
      <div class="rail-card"><div class="rail-title">⚠ ACTIVE RISK</div><p>${escapeHtml(rail.risk)}</p><div class="link">Monitor risk →</div></div>
      <div class="rail-card"><div class="rail-title">⌘ RECOMMENDED COMMAND</div><p>${escapeHtml(rail.recommended_command)}</p><div class="link">Run next →</div></div>`;
  }

  document.addEventListener("click", async (event) => {
    const copyButton = event.target.closest("[data-action='copy']");
    if (copyButton) {
      const text = copyButton.getAttribute("data-copy") || "";
      try {
        await navigator.clipboard.writeText(text);
        copyButton.textContent = "Copied";
      } catch {
        copyButton.textContent = "Copy failed";
      }
      setTimeout(() => copyButton.textContent = "Copy", 1200);
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
