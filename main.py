from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "live"}

@app.post("/command")
def command(data: dict):
    situation = data.get("situation", "")

    return {
        "outcome": f"Received: {situation}",
        "required_action": "Process input"
    }
