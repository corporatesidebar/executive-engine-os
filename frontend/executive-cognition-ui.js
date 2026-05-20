/* =========================================================
   Executive Engine OS — V36600 Executive Cognition UI Engine
   Optional renderer helper. Does not call backend or change routes.
   Use window.renderExecutiveCognitionBrief(response) if wanted.
   ========================================================= */

(function () {
  function safe(value, fallback = "") {
    if (value === null || value === undefined) return fallback;
    if (Array.isArray(value)) return value.filter(Boolean).join(" ");
    return String(value);
  }

  function escapeHtml(str) {
    return safe(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getDominantInsight(data) {
    return (
      data?.executive_pressure?.dominant_truth ||
      data?.executive_briefing?.dominant_insight ||
      data?.executive_presence?.truth ||
      data?.executive_reasoning?.truth ||
      data?.strategic_inference?.hidden_bottleneck ||
      data?.next_move ||
      "Choose the move that reduces pressure fastest."
    );
  }

  function getDecision(data) {
    return data?.decision || data?.executive_briefing?.decision || "Lock the decision and execute.";
  }

  function getRisk(data) {
    return data?.risk || data?.executive_pressure?.warning || data?.executive_briefing?.warning || "The risk is staying organized but unfocused.";
  }

  function getMove(data) {
    return data?.what_to_do_now || data?.next_move || data?.recommended_command || "Execute the next move.";
  }

  function getStopItems(data) {
    const stops =
      data?.executive_pressure?.stop ||
      data?.executive_briefing?.stop_doing ||
      data?.executive_presence?.stop ||
      [];

    if (Array.isArray(stops) && stops.length) return stops.slice(0, 3);

    const steps = Array.isArray(data?.action_steps) ? data.action_steps : [];
    return steps.filter(step => /stop|ignore|remove|kill|delay|cut/i.test(step)).slice(0, 3);
  }

  window.renderExecutiveCognitionBrief = function renderExecutiveCognitionBrief(data) {
    const insight = escapeHtml(getDominantInsight(data));
    const decision = escapeHtml(getDecision(data));
    const risk = escapeHtml(getRisk(data));
    const move = escapeHtml(getMove(data));
    const stopItems = getStopItems(data);

    const stopHtml = stopItems.length
      ? stopItems.map(item => `<div class="ee-stop-item">${escapeHtml(item).replace(/^stop:\s*/i, "")}</div>`).join("")
      : `<div class="ee-stop-item">Do not reopen the loop.</div>`;

    return `
      <section class="ee-cognition-brief">
        <header class="ee-dominant-insight">
          <div class="ee-kicker">Executive Briefing</div>
          <div class="ee-insight">${insight}</div>
        </header>

        <div class="ee-brief-body">
          <div class="ee-brief-row">
            <div class="ee-brief-label">Decision</div>
            <div class="ee-brief-value strong">${decision}</div>
          </div>

          <div class="ee-brief-row">
            <div class="ee-brief-label">Pressure / Risk</div>
            <div class="ee-brief-value">${risk}</div>
          </div>

          <div class="ee-brief-row">
            <div class="ee-brief-label">Remove</div>
            <div class="ee-stop-list">${stopHtml}</div>
          </div>

          <div class="ee-brief-row ee-final-move">
            <div class="ee-brief-label">Move</div>
            <div class="ee-brief-value strong">${move}</div>
          </div>
        </div>
      </section>
    `;
  };
})();
