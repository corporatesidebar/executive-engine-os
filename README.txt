EXECUTIVE ENGINE OS - MEMORY LAYER V1

FILES:
- /backend/main.py
- /backend/requirements.txt
- /backend/supabase_items_table.sql

RENDER BACKEND SETTINGS:
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

ENVIRONMENT VARIABLES:
OPENAI_API_KEY=your OpenAI key
OPENAI_MODEL=gpt-4o-mini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your Supabase service role key or anon key with policy access

ENDPOINTS:
GET /
GET /memory
POST /run

POST /run input:
{
  "input": "text",
  "mode": "strategy"
}

POST /run output:
{
  "decision": "",
  "next_move": "",
  "actions": [],
  "risk": "",
  "priority": ""
}
