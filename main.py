from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow frontend to talk to backend

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

class InputData(BaseModel):
situation: str

@app.get("/")
def root():
return {"status": "Executive Engine API is live"}

@app.post("/command")
def command(data: InputData):
return {
"outcome": f"Handled: {data.situation}",
"context": "System is working correctly",
"required_action": "Proceed with next step"
}
