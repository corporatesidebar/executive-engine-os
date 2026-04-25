Executive Engine V22

Includes:
- Working sidebar pages: Command / Tasks / Memory
- Local persistent tasks
- Supabase memory integration
- /memory endpoint
- Action-first command feed

Render Backend:
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Environment Variables:
OPENAI_API_KEY=your key
OPENAI_MODEL=gpt-4o-mini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your Supabase key

Important:
Upload extracted folders, not the ZIP itself.
Repo must look like:
backend/main.py
backend/requirements.txt
frontend/index.html
