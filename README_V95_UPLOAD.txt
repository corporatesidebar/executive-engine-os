Executive Engine OS V95 Full Package

BUILD V95 — Stability + Memory-Driven Execution Loop

Do not build bot team yet.
Do not add external automation yet.
Manual execution only.

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
backend/README_BACKEND_V95.txt

Deploy order:
1. Backend: executive-engine-os -> Clear build cache & deploy
2. Frontend: executive-engine-frontend -> Clear cache & deploy

Test:
GET https://executive-engine-os.onrender.com/health
POST https://executive-engine-os.onrender.com/run-test
GET https://executive-engine-os.onrender.com/memory
GET https://executive-engine-os.onrender.com/stability-check

Expected:
version: V95
supabase_enabled: true
manual_execution_only: true
auto_loop_enabled: false
