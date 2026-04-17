from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/analyze")
def analyze():
    return {
        "what_matters": ["Clarity", "Leverage", "Execution"],
        "risks": ["Unclear objective", "Weak positioning"],
        "leverage": ["Reframe narrative", "Control timing"],
        "best_move": "Simplify and execute decisively"
    }
