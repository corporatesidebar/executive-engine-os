async function runEngine() {
  const input = document.getElementById("input").value.trim();

  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input })
    });

    const data = await res.json();

    document.getElementById("outcome").innerText = data.outcome || "N/A";
    document.getElementById("risk").innerText = data.risk || "N/A";
    document.getElementById("action").innerText = data.action || "N/A";
    document.getElementById("priority").innerText = data.priority || "N/A";
  } catch (err) {
    alert("Backend not responding.");
  }
}
