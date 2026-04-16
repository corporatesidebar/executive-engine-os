from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# 👇 THIS IS WHERE YOU PASTE IT
@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()
    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    prompt = f"""
You are an elite executive strategist.

User input:
{text}

Mode: {mode}

Respond in JSON format:
{{
  "snapshot": "...",
  "objective": "...",
  "best_move": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content

    try:
        return jsonify(eval(content))
    except:
        return jsonify({
            "snapshot": "Error parsing AI response",
            "objective": "",
            "best_move": ""
        })


@app.route("/")
def home():
    return jsonify({"status": "running"})
