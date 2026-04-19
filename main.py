from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
return {"status": "live"}

@app.post("/command")
def command(data: dict):
situation = data.get("situation", "")

```
return {
    "outcome": f"Received: {situation}",
    "required_action": "Process input"
}
```
