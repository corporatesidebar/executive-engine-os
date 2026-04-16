from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔥 REPLACE THIS WITH YOUR REAL KEY
SUPABASE_URL = "https://xhxnyfrhizbvhlhedhjud.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_sb_publishable_KEY"


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    # Handle preflight (CORS)
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()

    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    # 🔥 OUTPUT (we upgrade later)
    output = {
        "snapshot": f"{mode} context understood",
        "objective": "Clarify outcome and next move",
        "best_move": "Take decisive action"
    }

    # 🔥 SAVE TO SUPABASE (safe)
    try:
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
    except:
        pass

    return jsonify(output)


@app.route("/")
def home():
    return jsonify({"status": "running"})


# 🔥 REQUIRED FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
