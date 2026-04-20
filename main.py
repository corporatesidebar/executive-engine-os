from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is live"

@app.route("/add", methods=["POST"])
def add_item():
    data = request.json

    payload = {
        "input": data.get("input"),
        "output": data.get("output"),
        "mode": data.get("mode")
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/items",
        json=payload,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    )

    return jsonify(response.json())
