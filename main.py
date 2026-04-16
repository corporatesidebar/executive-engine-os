@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()
    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    from openai import OpenAI
    import os

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
            "snapshot": content,
            "objective": "",
            "best_move": ""
        })
