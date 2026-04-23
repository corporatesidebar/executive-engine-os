from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI()

class CommandInput(BaseModel):
    input: str

@app.post("/api/command")
def command(data: CommandInput):
    text = (data.input or "").strip()
    if not text:
        text = "No input provided"

    return {
        "outcome": f"Processed: {text}",
        "risk": "Low",
        "action": "Review and execute",
        "priority": "Medium"
    }

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/style.css")
def style():
    return FileResponse(FRONTEND_DIR / "style.css")

@app.get("/script.js")
def script():
    return FileResponse(FRONTEND_DIR / "script.js")

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
