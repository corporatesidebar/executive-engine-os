from flask import Flask, request, jsonify
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()

    text = data.get("text", "")
    mode = data.get("mode", "Decision")

    output = {
        "snapshot": f"{mode} context understood",
        "objective": "Clarify outcome and next move",
        "best_move": "Take decisive action"
    }

    return jsonify(output)


@app.route("/")
def home():
    return jsonify({"status": "running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
