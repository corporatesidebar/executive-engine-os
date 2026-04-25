Executive Engine V16

Includes:
- Real task system UI
- Clickable tasks
- Memory panel
- /memory endpoint
- Supabase memory save/read

Render Backend:
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Environment Variables:
OPENAI_API_KEY=your key
OPENAI_MODEL=gpt-4o-mini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your Supabase key

Upload:
- /frontend/index.html to frontend/static service
- /backend files to backend/web service
