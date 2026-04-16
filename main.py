from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

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

    data = request.get_json()
    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    prompt = f"""
You are an elite executive strategist.

User input:
{text}

Mode: {mode}

Respond ONLY in JSON format:
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
            "snapshot": content,
            "objective": "",
            "best_move": ""
        })
