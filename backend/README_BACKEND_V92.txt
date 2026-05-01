# Executive Engine OS V92 Backend

Lock V92 — stability + auto-execution loop.

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/supabase_schema_v92.sql
- backend/README_BACKEND_V92.txt

Render environment variables:
- OPENAI_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY

Optional:
- OPENAI_MODEL=gpt-4o-mini
- OPENAI_TIMEOUT_SECONDS=45
- OPENAI_MAX_TOKENS=2800
- ALLOWED_ORIGINS=*

Endpoints:
- GET /
- GET /health
- GET /debug
- GET /schema
- POST /run
- POST /auto-loop
- GET /recent-runs
- GET /memory
- GET /actions
- POST /save-action
- GET /decisions
- POST /save-decision
- GET /profile
- POST /profile
- GET /robots.txt

Auto-loop:
- Internal planning only.
- It does not send emails or perform external actions.
- It produces next prompts and execution steps.

Security:
- Frontend -> Render Backend -> Supabase.
- Never expose SUPABASE_SERVICE_ROLE_KEY in frontend.
- Run backend/supabase_schema_v92.sql in Supabase SQL Editor before connecting memory.
