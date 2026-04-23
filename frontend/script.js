let currentMode = "Strategy";

document.querySelectorAll(".mode").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode").forEach(b => b.classList.remove("mode-active"));
    btn.classList.add("mode-active");
    currentMode = btn.dataset.mode;
    document.getElementById("currentMode").innerText = currentMode;
  });
});

async function runEngine() {
  const input = document.getElementById("input").value.trim();

  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input, mode: currentMode })
    });

    const data = await res.json();

    document.getElementById("outcome").innerText = data.outcome || "";
    document.getElementById("risk").innerText = data.risk || "";
    document.getElementById("action").innerText = data.action || "";
    document.getElementById("priority").innerText = data.priority || "";
  } catch (err) {
    alert("API error.");
  }
}
