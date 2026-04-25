from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os,json

app=FastAPI()

app.add_middleware(
 CORSMiddleware,
 allow_origins=["*"],
 allow_methods=["*"],
 allow_headers=["*"],
)

client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Req(BaseModel):
 input:str

@app.post("/run")
async def run(req:Req):
 prompt=f"Return JSON with decision,next_move,actions,risk,priority. Input:{req.input}"
 res=client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role":"user","content":prompt}]
 )
 try:
  return json.loads(res.choices[0].message.content)
 except:
  return {"next_move":"","actions":[]}
