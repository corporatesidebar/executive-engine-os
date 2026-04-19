from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

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
return {"status": "live"}

@app.post("/command")
def command(data: InputData):
return {
"outcome": f"Handled: {data.situation}",
"context": "System operational",
"required_action": "Proceed with next step"
}
