Executive Engine OS V37 Final

Upload these folders to GitHub:
- frontend/index.html
- backend/main.py
- backend/requirements.txt

Render frontend:
- Root Directory: frontend

Render backend:
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Required Render environment variable:
- OPENAI_API_KEY

Optional Supabase memory:
- SUPABASE_URL
- SUPABASE_KEY
