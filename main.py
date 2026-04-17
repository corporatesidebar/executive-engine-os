from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, base64
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def execute(text):
    t = text.lower()

    if "deploy" in t:
        return deploy()

    if "update" in t or "ui" in t or "code" in t:
        return update_code()

    return ai(text)

def deploy():
    hook = os.environ.get("RENDER_DEPLOY_HOOK")
    if not hook:
        return "Missing deploy hook"
    requests.post(hook)
    return "Deploy triggered"

def update_code():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")

    url = f"https://api.github.com/repos/{repo}/contents/index.html"
    headers = {"Authorization": f"token {token}"}

    res = requests.get(url, headers=headers)
    sha = res.json()["sha"]

    ai_res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":"Improve UI. Return full HTML only."}]
    )

    content = base64.b64encode(ai_res.choices[0].message.content.encode()).decode()

    requests.put(url, json={
        "message":"auto update",
        "content":content,
        "sha":sha
    }, headers=headers)

    return "Code updated + pushed"

def ai(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":text}]
    )
    return r.choices[0].message.content

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text","")
    return jsonify({"response": execute(text)})

@app.route("/")
def home():
    return {"status":"running"}
