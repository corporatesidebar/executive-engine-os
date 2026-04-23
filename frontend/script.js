async function runEngine() {
    const input = document.getElementById("input").value;

    const res = await fetch("https://YOUR-BACKEND-URL.onrender.com/run-engine", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ input })
    });

    const data = await res.json();

    document.getElementById("outcome").innerText = data.outcome;
    document.getElementById("risk").innerText = data.risk;
    document.getElementById("action").innerText = data.action;
    document.getElementById("priority").innerText = data.priority;
}
