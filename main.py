from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/")
def home():
    return {"status": "running"}

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return '', 200

    try:
        data = request.get_json()
        text = data.get("text", "")
        mode = data.get("mode", "Decision")

        prompt = f"""
You are an elite executive strategist.

{text}

Respond JSON:
{{
  "snapshot": "...",
  "objective": "...",
  "best_move": "..."
}}
"""

        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify(json.loads(r.choices[0].message.content))

    except Exception as e:
        return jsonify({"error": str(e)})
