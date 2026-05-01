Executive Engine OS V93 Full Package

Upload/replace:

frontend/index.html
frontend/robots.txt
frontend/_headers

backend/main.py
backend/requirements.txt
backend/runtime.txt
backend/supabase_schema_v92.sql
backend/README_BACKEND_V92_CLEAN.txt
backend/README_BACKEND_V93.txt

Deploy backend first:
Render -> executive-engine-os -> Clear build cache & deploy

Then deploy frontend:
Render -> executive-engine-frontend -> Clear cache & deploy

Expected backend health:
https://executive-engine-os.onrender.com/health

Should show:
version: V93
supabase_enabled: true
