# Executive Engine OS V92.2 Clean Backend Upload

Use this when you want to delete the current backend folder contents and replace them cleanly.

Upload these files into GitHub /backend:

- main.py
- requirements.txt
- runtime.txt
- supabase_schema_v92.sql
- README_BACKEND_V92_CLEAN.txt

Render settings for executive-engine-os:

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT

Environment variables required:

OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=45
OPENAI_MAX_TOKENS=2800
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
ALLOWED_ORIGINS=https://executive-engine-frontend.onrender.com

Deploy:

Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Test:

https://executive-engine-os.onrender.com/health

Expected:

"version": "V92.2"
"supabase_enabled": true
