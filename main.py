from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app = Flask(__name__) 
CORS(app)
# 🔥 REPLACE THESE WITH YOUR REAL VALUES
SUPABASE_URL = "https://xhxnyfrhizbvhlhedhjud.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_sb_publishable_KEY"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    # BASIC OUTPUT (we upgrade later)
    output = {
        "snapshot": f"{mode} context understood",
        "objective": "Clarify outcome and next move",
        "best_move": "Take decisive action"
    }

    # 🔥 SAVE TO SUPABASE
    requests.post(
        f"{SUPABASE_URL}/rest/v1/items",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json={
            "mode": mode,
            "content": text,
            "output": str(output),
            "status": "active"
        }
    )

    return jsonify(output)

@app.route("/")
def home():
    return {"status": "running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
