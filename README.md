<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Executive Engine OS — V35140</title>
  <meta name="description" content="Private executive operating system command center." />
  <style>
    :root {
      --navy-950: #07111f;
      --navy-900: #0b1526;
      --navy-850: #101d31;
      --navy-800: #13243b;
      --navy-700: #1f3554;
      --blue-650: #2457d6;
      --blue-600: #2563eb;
      --blue-100: #dbeafe;
      --orange-600: #f97316;
      --orange-500: #fb923c;
      --orange-100: #ffedd5;
      --slate-950: #020617;
      --slate-800: #1e293b;
      --slate-700: #334155;
      --slate-600: #475569;
      --slate-500: #64748b;
      --slate-400: #94a3b8;
      --slate-300: #cbd5e1;
      --slate-200: #e2e8f0;
      --slate-100: #f1f5f9;
      --slate-50: #f8fafc;
      --white: #ffffff;
      --green-600: #16a34a;
      --green-100: #dcfce7;
      --red-600: #dc2626;
      --red-100: #fee2e2;
      --amber-600: #d97706;
      --amber-100: #fef3c7;
      --shadow-soft: 0 18px 60px rgba(15, 23, 42, 0.08);
      --shadow-card: 0 12px 34px rgba(15, 23, 42, 0.08);
      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --radius-sm: 12px;
      --max-width: 1500px;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--slate-950);
      background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28rem),
        linear-gradient(135deg, #ffffff 0%, #f8fafc 42%, #eef4ff 100%);
      min-height: 100vh;
    }

    button, input, textarea, select { font: inherit; }

    button {
      border: 0;
      cursor: pointer;
    }

    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 296px minmax(0, 1fr);
    }

    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 28px 22px;
      background:
        radial-gradient(circle at top right, rgba(249, 115, 22, 0.12), transparent 15rem),
        linear-gradient(180deg, var(--navy-950), var(--navy-900));
      color: var(--white);
      display: flex;
      flex-direction: column;
      gap: 28px;
      overflow-y: auto;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 13px;
    }

    .brand-mark {
      width: 46px;
      height: 46px;
      border-radius: 15px;
      background: linear-gradient(135deg, var(--orange-600), #ffb36b);
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 900;
      letter-spacing: -0.06em;
      box-shadow: 0 14px 32px rgba(249, 115, 22, 0.25);
    }

    .brand-title {
      font-size: 15px;
      font-weight: 850;
      letter-spacing: -0.03em;
      line-height: 1.05;
    }

    .brand-subtitle {
      color: rgba(255,255,255,0.62);
      font-size: 12px;
      margin-top: 4px;
    }

    .nav-group-label {
      margin: 0 0 9px;
      color: rgba(255,255,255,0.42);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
    }

    .nav-list {
      display: grid;
      gap: 6px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 12px;
      border-radius: 14px;
      color: rgba(255,255,255,0.72);
      text-decoration: none;
      transition: 180ms ease;
      font-size: 14px;
      font-weight: 650;
    }

    .nav-item:hover, .nav-item.active {
      background: rgba(255,255,255,0.08);
      color: #fff;
    }

    .nav-pill {
      min-width: 23px;
      height: 23px;
      padding: 0 7px;
      border-radius: 999px;
      display: inline-grid;
      place-items: center;
      background: rgba(249, 115, 22, 0.18);
      color: #fed7aa;
      font-size: 11px;
      font-weight: 800;
    }

    .operator-card {
      margin-top: auto;
      padding: 16px;
      border-radius: 20px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.09);
    }

    .operator-card strong {
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
    }

    .operator-card p {
      margin: 0;
      color: rgba(255,255,255,0.62);
      font-size: 12px;
      line-height: 1.45;
    }

    .main {
      min-width: 0;
      padding: 28px;
    }

    .workspace {
      max-width: var(--max-width);
      margin: 0 auto;
      display: grid;
      gap: 22px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 14px 16px 14px 22px;
      border: 1px solid rgba(203, 213, 225, 0.72);
      border-radius: 24px;
      background: rgba(255,255,255,0.76);
      backdrop-filter: blur(18px);
      box-shadow: var(--shadow-card);
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--slate-500);
      font-size: 12px;
      font-weight: 850;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--green-600);
      box-shadow: 0 0 0 5px rgba(22, 163, 74, 0.11);
    }

    h1 {
      margin: 6px 0 0;
      font-size: clamp(28px, 4vw, 48px);
      line-height: 0.98;
      letter-spacing: -0.065em;
    }

    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 999px;
      border: 1px solid var(--slate-200);
      background: #fff;
      color: var(--slate-600);
      font-size: 12px;
      font-weight: 750;
      white-space: nowrap;
    }

    .status-chip.good { color: #15803d; background: var(--green-100); border-color: rgba(22, 163, 74, 0.18); }
    .status-chip.warn { color: var(--amber-600); background: var(--amber-100); border-color: rgba(217, 119, 6, 0.18); }
    .status-chip.bad { color: var(--red-600); background: var(--red-100); border-color: rgba(220, 38, 38, 0.18); }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.55fr) minmax(340px, 0.85fr);
      gap: 22px;
      align-items: stretch;
    }

    .command-card {
      border-radius: var(--radius-xl);
      background: #fff;
      border: 1px solid rgba(203, 213, 225, 0.76);
      box-shadow: var(--shadow-soft);
      overflow: hidden;
    }

    .command-header {
      padding: 24px 26px 16px;
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 18px;
    }

    .section-title {
      margin: 0;
      color: var(--slate-950);
      font-size: 18px;
      font-weight: 850;
      letter-spacing: -0.03em;
    }

    .section-note {
      margin: 6px 0 0;
      color: var(--slate-500);
      font-size: 13px;
      line-height: 1.45;
    }

    .mode-tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .mode-btn {
      padding: 9px 11px;
      border-radius: 999px;
      background: var(--slate-100);
      color: var(--slate-600);
      font-size: 12px;
      font-weight: 800;
      transition: 180ms ease;
    }

    .mode-btn:hover, .mode-btn.active {
      background: var(--navy-900);
      color: #fff;
    }

    .command-input-wrap {
      padding: 0 26px 24px;
    }

    .command-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: stretch;
      padding: 10px;
      border: 1px solid var(--slate-200);
      border-radius: 22px;
      background: var(--slate-50);
    }

    textarea {
      min-height: 62px;
      max-height: 180px;
      resize: vertical;
      border: 0;
      outline: none;
      padding: 14px 16px;
      border-radius: 16px;
      background: transparent;
      color: var(--slate-950);
      font-size: 15px;
      line-height: 1.45;
    }

    textarea::placeholder { color: var(--slate-400); }

    .run-btn {
      align-self: stretch;
      padding: 0 22px;
      border-radius: 17px;
      background: linear-gradient(135deg, var(--orange-600), var(--orange-500));
      color: white;
      font-weight: 900;
      letter-spacing: -0.02em;
      box-shadow: 0 16px 30px rgba(249, 115, 22, 0.25);
      transition: 180ms ease;
      min-width: 124px;
    }

    .run-btn:hover { transform: translateY(-1px); box-shadow: 0 18px 38px rgba(249, 115, 22, 0.32); }
    .run-btn:disabled { opacity: 0.68; cursor: wait; transform: none; }

    .quick-capture {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      padding: 0 26px 26px;
    }

    .prompt-card {
      padding: 13px 14px;
      border-radius: 16px;
      border: 1px solid var(--slate-200);
      background: #fff;
      text-align: left;
      color: var(--slate-700);
      font-size: 12px;
      font-weight: 750;
      line-height: 1.35;
      transition: 180ms ease;
    }

    .prompt-card:hover {
      border-color: rgba(37, 99, 235, 0.35);
      background: #f8fbff;
      color: var(--blue-650);
      transform: translateY(-1px);
    }

    .today-card {
      border-radius: var(--radius-xl);
      color: white;
      background:
        radial-gradient(circle at top right, rgba(249, 115, 22, 0.22), transparent 16rem),
        linear-gradient(145deg, var(--navy-950), var(--navy-800));
      box-shadow: var(--shadow-soft);
      padding: 26px;
      position: relative;
      overflow: hidden;
      min-height: 100%;
    }

    .today-card::after {
      content: "";
      position: absolute;
      inset: auto -8rem -9rem auto;
      width: 18rem;
      height: 18rem;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
    }

    .today-card .section-title { color: #fff; }
    .today-card .section-note { color: rgba(255,255,255,0.64); }

    .metrics {
      position: relative;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 22px;
      z-index: 1;
    }

    .metric {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.08);
    }

    .metric-label {
      color: rgba(255,255,255,0.56);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .metric-value {
      margin-top: 9px;
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -0.06em;
    }

    .grid-main {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(350px, 0.9fr);
      gap: 22px;
      align-items: start;
    }

    .output-stack {
      display: grid;
      gap: 14px;
    }

    .output-card, .panel-card {
      border-radius: var(--radius-lg);
      background: rgba(255,255,255,0.88);
      border: 1px solid rgba(203, 213, 225, 0.78);
      box-shadow: var(--shadow-card);
      overflow: hidden;
    }

    .output-card.next-move {
      border-color: rgba(249, 115, 22, 0.28);
      background: linear-gradient(180deg, #ffffff 0%, #fff8f3 100%);
    }

    .output-head, .panel-head {
      padding: 17px 19px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      border-bottom: 1px solid rgba(226, 232, 240, 0.82);
    }

    .output-label {
      display: flex;
      align-items: center;
      gap: 9px;
      color: var(--slate-800);
      font-size: 12px;
      font-weight: 950;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .output-icon {
      width: 28px;
      height: 28px;
      border-radius: 11px;
      display: grid;
      place-items: center;
      color: #fff;
      background: var(--navy-900);
      font-size: 13px;
    }

    .next-move .output-icon { background: var(--orange-600); }

    .output-body {
      padding: 18px 20px 20px;
      color: var(--slate-700);
      font-size: 15px;
      line-height: 1.58;
      min-height: 58px;
    }

    .output-body strong { color: var(--slate-950); }
    .output-body p { margin: 0 0 10px; }
    .output-body p:last-child { margin-bottom: 0; }
    .output-body ul, .output-body ol { margin: 0; padding-left: 20px; }
    .output-body li { margin: 6px 0; }

    .next-move .output-body {
      font-size: 20px;
      line-height: 1.38;
      color: var(--slate-950);
      font-weight: 780;
      letter-spacing: -0.035em;
    }

    .side-stack {
      display: grid;
      gap: 14px;
    }

    .panel-card { padding: 0; }

    .panel-body { padding: 16px 18px 18px; }

    .list { display: grid; gap: 10px; }

    .list-item {
      padding: 13px;
      border-radius: 15px;
      background: var(--slate-50);
      border: 1px solid var(--slate-200);
      display: grid;
      gap: 5px;
    }

    .list-title {
      color: var(--slate-900);
      font-size: 13px;
      font-weight: 850;
      line-height: 1.3;
    }

    .list-meta {
      color: var(--slate-500);
      font-size: 12px;
      line-height: 1.35;
    }

    .risk-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .risk-tile {
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--slate-200);
      background: #fff;
    }

    .risk-tile .label {
      color: var(--slate-500);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }

    .risk-tile .value {
      margin-top: 8px;
      color: var(--slate-950);
      font-size: 15px;
      font-weight: 900;
      letter-spacing: -0.03em;
    }

    .empty-state {
      color: var(--slate-500);
      font-size: 14px;
      line-height: 1.5;
    }

    .loading-line {
      height: 12px;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--slate-100), var(--slate-200), var(--slate-100));
      background-size: 200% 100%;
      animation: shimmer 1.1s infinite linear;
      margin: 8px 0;
    }

    .loading-line.short { width: 58%; }
    .loading-line.mid { width: 82%; }

    @keyframes shimmer {
      from { background-position: 200% 0; }
      to { background-position: -200% 0; }
    }

    .toast {
      position: fixed;
      right: 24px;
      bottom: 24px;
      z-index: 20;
      max-width: 380px;
      padding: 14px 16px;
      border-radius: 16px;
      color: #fff;
      background: var(--navy-900);
      box-shadow: 0 18px 48px rgba(2,6,23,0.22);
      transform: translateY(24px);
      opacity: 0;
      pointer-events: none;
      transition: 220ms ease;
      font-size: 13px;
      line-height: 1.45;
      font-weight: 700;
    }

    .toast.show { transform: translateY(0); opacity: 1; }
    .toast.error { background: var(--red-600); }

    @media (max-width: 1160px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        height: auto;
        padding: 18px;
        flex-direction: row;
        align-items: center;
        overflow: auto;
      }
      .nav-group, .operator-card { display: none; }
      .main { padding: 18px; }
      .hero-grid, .grid-main { grid-template-columns: 1fr; }
    }

    @media (max-width: 760px) {
      .topbar, .command-header { align-items: stretch; flex-direction: column; }
      .topbar-actions, .mode-tabs { justify-content: flex-start; }
      .command-row { grid-template-columns: 1fr; }
      .run-btn { min-height: 52px; }
      .quick-capture, .metrics, .risk-grid { grid-template-columns: 1fr; }
      .main { padding: 12px; }
      .workspace { gap: 14px; }
      .today-card, .command-card { border-radius: 22px; }
      .output-head, .panel-head { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Executive Engine navigation">
      <div class="brand">
        <div class="brand-mark">EE</div>
        <div>
          <div class="brand-title">Executive<br />Engine OS</div>
          <div class="brand-subtitle">Private operator cockpit</div>
        </div>
      </div>

      <div class="nav-group">
        <p class="nav-group-label">Command</p>
        <div class="nav-list">
          <a class="nav-item active" href="#today"><span>Today Command Center</span><span class="nav-pill">Live</span></a>
          <a class="nav-item" href="#quick-capture"><span>Quick Capture</span></a>
          <a class="nav-item" href="#outputs"><span>Execution Output</span></a>
          <a class="nav-item" href="#tomorrow"><span>Tomorrow / Upcoming</span><span class="nav-pill">3</span></a>
        </div>
      </div>

      <div class="nav-group">
        <p class="nav-group-label">Control</p>
        <div class="nav-list">
          <a class="nav-item" href="#ready-assets"><span>Ready Assets</span></a>
          <a class="nav-item" href="#risks"><span>Active Risks</span></a>
          <a class="nav-item" href="#recent"><span>Recent Decisions</span></a>
          <a class="nav-item" href="#status"><span>System Status</span></a>
        </div>
      </div>

      <div class="operator-card">
        <strong>Executive Mode</strong>
        <p>One command in. A clear next move, decision, action path, assets, risk, and recommended command out.</p>
      </div>
    </aside>

    <main class="main">
      <div class="workspace">
        <header class="topbar" id="today">
          <div>
            <div class="eyebrow"><span class="dot"></span> V35140 Clean Frontend</div>
            <h1>Today Command Center</h1>
          </div>
          <div class="topbar-actions" id="status">
            <div id="apiStatus" class="status-chip warn">Backend status: checking</div>
            <div class="status-chip">API: /run</div>
          </div>
        </header>

        <section class="hero-grid">
          <div class="command-card" id="quick-capture">
            <div class="command-header">
              <div>
                <h2 class="section-title">Quick Capture</h2>
                <p class="section-note">Capture the objective. Executive Engine turns it into a structured operator output.</p>
              </div>
              <div class="mode-tabs" role="tablist" aria-label="Execution mode">
                <button class="mode-btn active" data-mode="execution">Execution</button>
                <button class="mode-btn" data-mode="meeting">Meeting</button>
                <button class="mode-btn" data-mode="proposal">Proposal</button>
                <button class="mode-btn" data-mode="strategy">Strategy</button>
                <button class="mode-btn" data-mode="decision">Decision</button>
                <button class="mode-btn" data-mode="revenue">Revenue</button>
              </div>
            </div>

            <div class="command-input-wrap">
              <form id="runForm" class="command-row">
                <textarea id="commandInput" placeholder="What are we trying to win today?" required></textarea>
                <button id="runButton" class="run-btn" type="submit">Run OS</button>
              </form>
            </div>

            <div class="quick-capture" aria-label="Quick command templates">
              <button class="prompt-card" data-prompt="Build a revenue plan for today with the fastest path to a qualified sales conversation.">Build today’s revenue plan</button>
              <button class="prompt-card" data-prompt="Prepare me for a leadership meeting: objectives, risks, key points, and action steps.">Prep a leadership meeting</button>
              <button class="prompt-card" data-prompt="Turn this opportunity into a decision brief with next move, risks, assets, and recommended command.">Create a decision brief</button>
            </div>
          </div>

          <aside class="today-card">
            <h2 class="section-title">Operating Snapshot</h2>
            <p class="section-note">The dashboard prioritizes movement: what matters now, what gets prepared, what needs control.</p>
            <div class="metrics">
              <div class="metric">
                <div class="metric-label">Focus</div>
                <div class="metric-value" id="focusMetric">Next move</div>
              </div>
              <div class="metric">
                <div class="metric-label">Mode</div>
                <div class="metric-value" id="modeMetric">Execution</div>
              </div>
              <div class="metric">
                <div class="metric-label">Priority</div>
                <div class="metric-value" id="priorityMetric">Ready</div>
              </div>
              <div class="metric">
                <div class="metric-label">Runs</div>
                <div class="metric-value" id="runMetric">0</div>
              </div>
            </div>
          </aside>
        </section>

        <section class="grid-main" id="outputs">
          <div class="output-stack">
            <article class="output-card next-move">
              <div class="output-head"><div class="output-label"><span class="output-icon">→</span>NEXT MOVE</div></div>
              <div class="output-body" id="nextMove"><span class="empty-state">Run one command to generate the next executive move.</span></div>
            </article>

            <article class="output-card">
              <div class="output-head"><div class="output-label"><span class="output-icon">✓</span>DECISION</div></div>
              <div class="output-body" id="decision"><span class="empty-state">Decision output will appear here.</span></div>
            </article>

            <article class="output-card">
              <div class="output-head"><div class="output-label"><span class="output-icon">1</span>ACTION STEPS</div></div>
              <div class="output-body" id="actions"><span class="empty-state">Concrete steps will appear here.</span></div>
            </article>

            <article class="output-card" id="ready-assets">
              <div class="output-head"><div class="output-label"><span class="output-icon">◆</span>READY ASSETS</div></div>
              <div class="output-body" id="readyAssets"><span class="empty-state">Prepared assets will appear here when available.</span></div>
            </article>

            <article class="output-card">
              <div class="output-head"><div class="output-label"><span class="output-icon">!</span>RISK</div></div>
              <div class="output-body" id="risk"><span class="empty-state">Risk assessment will appear here.</span></div>
            </article>

            <article class="output-card">
              <div class="output-head"><div class="output-label"><span class="output-icon">P</span>PRIORITY</div></div>
              <div class="output-body" id="priority"><span class="empty-state">Priority will appear here.</span></div>
            </article>

            <article class="output-card">
              <div class="output-head"><div class="output-label"><span class="output-icon">⌘</span>RECOMMENDED COMMAND</div></div>
              <div class="output-body" id="recommendedCommand"><span class="empty-state">Recommended next command will appear here.</span></div>
            </article>
          </div>

          <aside class="side-stack">
            <section class="panel-card" id="risks">
              <div class="panel-head">
                <div>
                  <h2 class="section-title">Active Risks</h2>
                  <p class="section-note">Risk, priority, and readiness controls.</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="risk-grid">
                  <div class="risk-tile"><div class="label">Risk</div><div class="value" id="riskTile">Pending</div></div>
                  <div class="risk-tile"><div class="label">Priority</div><div class="value" id="priorityTile">Ready</div></div>
                </div>
              </div>
            </section>

            <section class="panel-card" id="tomorrow">
              <div class="panel-head">
                <div>
                  <h2 class="section-title">Tomorrow / Upcoming</h2>
                  <p class="section-note">Default executive forward view.</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="list">
                  <div class="list-item"><div class="list-title">Prepare one revenue asset</div><div class="list-meta">Proposal, outreach angle, or decision brief.</div></div>
                  <div class="list-item"><div class="list-title">Review active constraints</div><div class="list-meta">Blockers, risks, dependencies, and next owner.</div></div>
                  <div class="list-item"><div class="list-title">Choose one decisive move</div><div class="list-meta">Create momentum before the day starts.</div></div>
                </div>
              </div>
            </section>

            <section class="panel-card" id="recent">
              <div class="panel-head">
                <div>
                  <h2 class="section-title">Recent Decisions</h2>
                  <p class="section-note">Local frontend run history.</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="list" id="recentList">
                  <div class="empty-state">No recent decisions yet.</div>
                </div>
              </div>
            </section>

            <section class="panel-card">
              <div class="panel-head">
                <div>
                  <h2 class="section-title">System Status</h2>
                  <p class="section-note">Frontend-only V35140. Backend preserved.</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="list">
                  <div class="list-item"><div class="list-title">Backend API URL</div><div class="list-meta">https://executive-engine-os.onrender.com</div></div>
                  <div class="list-item"><div class="list-title">Connection</div><div class="list-meta" id="statusDetail">Checking live backend.</div></div>
                  <div class="list-item"><div class="list-title">Build Rule</div><div class="list-meta">Frontend only. No backend, DB, Supabase, Claude, or routing changes.</div></div>
                </div>
              </div>
            </section>
          </aside>
        </section>
      </div>
    </main>
  </div>

  <div id="toast" class="toast" role="status" aria-live="polite"></div>

  <script>
    const API_URL = "https://executive-engine-os.onrender.com";
    const STORAGE_KEY = "eeos_v35140_recent_runs";
    let selectedMode = "execution";
    let runCount = Number(localStorage.getItem("eeos_v35140_run_count") || 0);

    const $ = (id) => document.getElementById(id);

    const fields = {
      nextMove: $("nextMove"),
      decision: $("decision"),
      actions: $("actions"),
      readyAssets: $("readyAssets"),
      risk: $("risk"),
      priority: $("priority"),
      recommendedCommand: $("recommendedCommand"),
      riskTile: $("riskTile"),
      priorityTile: $("priorityTile"),
      focusMetric: $("focusMetric"),
      modeMetric: $("modeMetric"),
      priorityMetric: $("priorityMetric"),
      runMetric: $("runMetric"),
      apiStatus: $("apiStatus"),
      statusDetail: $("statusDetail"),
      recentList: $("recentList"),
      toast: $("toast"),
      commandInput: $("commandInput"),
      runButton: $("runButton")
    };

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function normalize(value, fallback = "Not returned by backend.") {
      if (value === null || value === undefined || value === "") return fallback;
      if (Array.isArray(value)) return value;
      if (typeof value === "object") return JSON.stringify(value, null, 2);
      return String(value);
    }

    function renderValue(value, fallback) {
      const normalized = normalize(value, fallback);
      if (Array.isArray(normalized)) {
        if (!normalized.length) return `<span class="empty-state">${escapeHtml(fallback)}</span>`;
        return `<ol>${normalized.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>`;
      }
      const text = escapeHtml(normalized);
      return text.split("\n").filter(Boolean).map(line => `<p>${line}</p>`).join("") || `<span class="empty-state">${escapeHtml(fallback)}</span>`;
    }

    function setLoading(isLoading) {
      fields.runButton.disabled = isLoading;
      fields.runButton.textContent = isLoading ? "Running" : "Run OS";
      if (isLoading) {
        [fields.nextMove, fields.decision, fields.actions, fields.readyAssets, fields.risk, fields.priority, fields.recommendedCommand].forEach(el => {
          el.innerHTML = `<div class="loading-line mid"></div><div class="loading-line"></div><div class="loading-line short"></div>`;
        });
      }
    }

    function showToast(message, isError = false) {
      fields.toast.textContent = message;
      fields.toast.className = `toast show${isError ? " error" : ""}`;
      window.clearTimeout(showToast.timer);
      showToast.timer = window.setTimeout(() => fields.toast.className = "toast", 3200);
    }

    function updateStatus(state, label, detail) {
      fields.apiStatus.className = `status-chip ${state}`;
      fields.apiStatus.textContent = label;
      fields.statusDetail.textContent = detail;
    }

    async function checkBackend() {
      try {
        const response = await fetch(`${API_URL}/`, { method: "GET" });
        if (response.ok) {
          updateStatus("good", "Backend status: live", "Live backend reachable. POST /run preserved.");
        } else {
          updateStatus("warn", `Backend status: ${response.status}`, "Backend responded but did not return OK from root.");
        }
      } catch (error) {
        updateStatus("bad", "Backend status: blocked", "Could not reach backend root from this browser session.");
      }
    }

    function mapResponse(data) {
      return {
        nextMove: data.next_move || data.NEXT_MOVE || data.what_to_do_now || data.nextMove || data.recommended_next_move,
        decision: data.decision || data.DECISION || data.result?.decision,
        actions: data.actions || data.action_steps || data.ACTION_STEPS || data.result?.actions,
        readyAssets: data.ready_assets || data.assets || data.READY_ASSETS || data.prepared_assets || data.result?.ready_assets,
        risk: data.risk || data.RISK || data.risks || data.result?.risk,
        priority: data.priority || data.PRIORITY || data.result?.priority,
        recommendedCommand: data.recommended_command || data.RECOMMENDED_COMMAND || data.next_command || data.result?.recommended_command
      };
    }

    function renderOutput(data) {
      const output = mapResponse(data || {});
      fields.nextMove.innerHTML = renderValue(output.nextMove, "No next move returned.");
      fields.decision.innerHTML = renderValue(output.decision, "No decision returned.");
      fields.actions.innerHTML = renderValue(output.actions, "No action steps returned.");
      fields.readyAssets.innerHTML = renderValue(output.readyAssets, "No ready assets returned.");
      fields.risk.innerHTML = renderValue(output.risk, "No risk returned.");
      fields.priority.innerHTML = renderValue(output.priority, "No priority returned.");
      fields.recommendedCommand.innerHTML = renderValue(output.recommendedCommand, "No recommended command returned.");

      fields.riskTile.textContent = String(output.risk || "Returned").slice(0, 44);
      fields.priorityTile.textContent = String(output.priority || "Returned").slice(0, 44);
      fields.priorityMetric.textContent = String(output.priority || "Set").slice(0, 18);
      fields.focusMetric.textContent = "Updated";
    }

    function getRecentRuns() {
      try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
      catch { return []; }
    }

    function saveRecentRun(command, mode, data) {
      const output = mapResponse(data || {});
      const runs = getRecentRuns();
      runs.unshift({
        command,
        mode,
        decision: output.decision || output.nextMove || "Decision returned",
        priority: output.priority || "Priority returned",
        createdAt: new Date().toISOString()
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(runs.slice(0, 8)));
      runCount += 1;
      localStorage.setItem("eeos_v35140_run_count", String(runCount));
      fields.runMetric.textContent = String(runCount);
      renderRecentRuns();
    }

    function renderRecentRuns() {
      const runs = getRecentRuns();
      if (!runs.length) {
        fields.recentList.innerHTML = `<div class="empty-state">No recent decisions yet.</div>`;
        return;
      }
      fields.recentList.innerHTML = runs.map(run => {
        const date = new Date(run.createdAt);
        const time = Number.isNaN(date.getTime()) ? "Recent" : date.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
        return `<div class="list-item">
          <div class="list-title">${escapeHtml(String(run.decision).slice(0, 96))}</div>
          <div class="list-meta">${escapeHtml(run.mode)} · ${escapeHtml(run.priority)} · ${escapeHtml(time)}</div>
        </div>`;
      }).join("");
    }

    async function runExecutiveEngine(command) {
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: command, mode: selectedMode })
        });

        const text = await response.text();
        let data;
        try { data = text ? JSON.parse(text) : {}; }
        catch { data = { decision: text }; }

        if (!response.ok) {
          throw new Error(data.detail || data.error || `POST /run failed with status ${response.status}`);
        }

        renderOutput(data);
        saveRecentRun(command, selectedMode, data);
        updateStatus("good", "Backend status: live", "POST /run returned successfully.");
        showToast("Executive output generated.");
      } catch (error) {
        const message = error?.message || "Connection failed.";
        [fields.nextMove, fields.decision, fields.actions, fields.readyAssets, fields.risk, fields.priority, fields.recommendedCommand].forEach(el => {
          el.innerHTML = `<span class="empty-state">${escapeHtml(message)}</span>`;
        });
        updateStatus("bad", "Backend status: issue", message);
        showToast(message, true);
      } finally {
        setLoading(false);
      }
    }

    document.querySelectorAll(".mode-btn").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".mode-btn").forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        selectedMode = button.dataset.mode;
        fields.modeMetric.textContent = selectedMode.charAt(0).toUpperCase() + selectedMode.slice(1);
      });
    });

    document.querySelectorAll(".prompt-card").forEach(button => {
      button.addEventListener("click", () => {
        fields.commandInput.value = button.dataset.prompt;
        fields.commandInput.focus();
      });
    });

    $("runForm").addEventListener("submit", (event) => {
      event.preventDefault();
      const command = fields.commandInput.value.trim();
      if (!command) {
        showToast("Enter the objective first.", true);
        return;
      }
      runExecutiveEngine(command);
    });

    fields.runMetric.textContent = String(runCount);
    renderRecentRuns();
    checkBackend();
  </script>
</body>
</html>
