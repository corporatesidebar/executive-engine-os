Executive Engine OS V94 Full Package

BUILD V94 — Stability + Memory-Driven Execution Loop

Upload/replace:

frontend/index.html
frontend/robots.txt
frontend/_headers

backend/main.py
backend/requirements.txt
backend/runtime.txt
backend/supabase_schema_v92.sql
backend/supabase_schema_v94.sql
backend/README_BACKEND_V92_CLEAN.txt
backend/README_BACKEND_V93.txt
backend/README_BACKEND_V94.txt

Deploy order:
1. Run backend/supabase_schema_v94.sql in Supabase SQL Editor.
2. Render backend executive-engine-os -> Clear build cache & deploy.
3. Render frontend executive-engine-frontend -> Clear cache & deploy.
4. Test:
   https://executive-engine-os.onrender.com/health
   https://executive-engine-os.onrender.com/stability-check

Expected:
version: V94
supabase_enabled: true
