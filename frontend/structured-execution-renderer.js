/* Executive Engine OS — V36800 Structured Execution Object Renderer
   Frontend helper only. Does not change shell/layout/navigation/API URL.
*/

(function () {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderList(items) {
    if (!Array.isArray(items)) return "";
    return `<ul>${items.map(item => `<li>${escapeHtml(typeof item === "string" ? item : JSON.stringify(item))}</li>`).join("")}</ul>`;
  }

  function renderObjectPayload(payload) {
    if (!payload || typeof payload !== "object") return `<p>${escapeHtml(payload)}</p>`;

    return Object.entries(payload).map(([key, value]) => {
      const label = key.replaceAll("_", " ").toUpperCase();

      if (Array.isArray(value)) {
        return `<div class="seo-row"><div class="seo-label">${escapeHtml(label)}</div>${renderList(value)}</div>`;
      }

      if (typeof value === "object" && value !== null) {
        return `<div class="seo-row"><div class="seo-label">${escapeHtml(label)}</div><pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre></div>`;
      }

      return `<div class="seo-row"><div class="seo-label">${escapeHtml(label)}</div><p>${escapeHtml(value)}</p></div>`;
    }).join("");
  }

  function renderExecutionObject(obj) {
    const type = obj.object_type || "object";
    const title = obj.title || "Execution Object";
    const payload = obj.payload || {};

    return `
      <section class="seo-object seo-${escapeHtml(type)}">
        <div class="seo-object-header">
          <span class="seo-object-type">${escapeHtml(type.replaceAll("_", " "))}</span>
          <h3>${escapeHtml(title)}</h3>
        </div>
        <div class="seo-object-body">
          ${renderObjectPayload(payload)}
        </div>
      </section>
    `;
  }

  window.renderStructuredExecutionObjects = function renderStructuredExecutionObjects(data) {
    const scan = data.executive_scan || {};
    const objects = Array.isArray(data.execution_objects) ? data.execution_objects : [];

    return `
      <article class="seo-response">
        <header class="seo-scan">
          <div class="seo-kicker">Executive Scan</div>
          <h2>${escapeHtml(scan.dominant_insight || data.executive_summary || data.next_move || "Execution object generated.")}</h2>
          <div class="seo-scan-grid">
            <div><strong>Decision</strong><span>${escapeHtml(scan.decision || data.decision || "")}</span></div>
            <div><strong>Move</strong><span>${escapeHtml(scan.move || data.next_move || "")}</span></div>
            <div><strong>Risk</strong><span>${escapeHtml(scan.risk || data.risk || "")}</span></div>
          </div>
        </header>

        <section class="seo-objects">
          ${objects.map(renderExecutionObject).join("")}
        </section>
      </article>
    `;
  };
})();
