let currentMode = "strategy";
let uploadedText = "";

document.querySelectorAll(".mode-tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
  });
});

document.getElementById("runBtn").addEventListener("click", send);

document.getElementById("fileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  const status = document.getElementById("fileStatus");
  if (!file) {
    uploadedText = "";
    status.textContent = "No file loaded";
    return;
  }

  try {
    uploadedText = await file.text();
    status.textContent = `Loaded: ${file.name}`;
  } catch (e) {
    uploadedText = "";
    status.textContent = "Could not read file";
  }
});

function makeLinksClickable(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return escaped.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
  );
}

function renderStructuredOutput(text) {
  const shell = document.getElementById("responseShell");
  const cards = document.getElementById("responseCards");
  const raw = document.getElementById("rawOutput");
  cards.innerHTML = "";
  raw.textContent = text;

  const sections = text.split(/\n\s*\n/).filter(Boolean);

  if (sections.length === 0) {
    cards.innerHTML = '<div class="response-card"><h3>Response</h3><div class="card-body">No response returned.</div></div>';
    shell.classList.remove("hidden");
    return;
  }

  let rendered = false;

  sections.forEach(section => {
    const lines = section.split("\n").filter(Boolean);
    if (lines.length === 0) return;

    const first = lines[0];
    let title = "Response";
    let bodyLines = lines;

    if (first.includes(":")) {
      const idx = first.indexOf(":");
      title = first.slice(0, idx).trim();
      const remainder = first.slice(idx + 1).trim();
      bodyLines = [];
      if (remainder) bodyLines.push(remainder);
      bodyLines.push(...lines.slice(1));
    }

    const card = document.createElement("div");
    card.className = "response-card";

    const heading = document.createElement("h3");
    heading.textContent = title;

    const body = document.createElement("div");
    body.className = "card-body";
    body.innerHTML = makeLinksClickable(bodyLines.join("<br>"));

    card.appendChild(heading);
    card.appendChild(body);
    cards.appendChild(card);
    rendered = true;
  });

  if (!rendered) {
    cards.innerHTML = '<div class="response-card"><h3>Response</h3><div class="card-body">' + makeLinksClickable(text) + '</div></div>';
  }

  shell.classList.remove("hidden");
}

async function send() {
  const input = document.getElementById("input").value.trim();
  const profile = document.getElementById("profile").value.trim();
  const loading = document.getElementById("loading");
  const shell = document.getElementById("responseShell");

  if (!input) return;

  loading.classList.remove("hidden");
  shell.classList.add("hidden");

  try {
    const res = await fetch("https://executive-engine-os.onrender.com/api/command", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        input: input,
        mode: currentMode,
        profile: profile,
        uploaded_context: uploadedText
      })
    });

    const data = await res.json();
    renderStructuredOutput(data.output || data.error || "No response returned.");
  } catch (err) {
    renderStructuredOutput("Error: " + err.message);
  } finally {
    loading.classList.add("hidden");
  }
}
