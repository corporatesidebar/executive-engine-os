EXECUTIVE ENGINE OS — V128 OPERATOR LOOP

Purpose:
- No redesign.
- Keeps locked frontend layout.
- Backend upgraded from V127 to V128.
- Adds real operator-loop endpoints.

New/updated:
- Stronger /run execution loop
- GET /operator-brief
- GET /next-action
- POST /complete-action
- GET /workflow-audit
- Manual execution stays ON
- Auto-loop stays OFF

Files:
backend/
  main.py
  requirements.txt
  runtime.txt
  supabase_schema_v125.sql

frontend/
  index.html
  robots.txt
  _headers

Deploy:
1. Upload all files from this ZIP to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /workflow-audit
- /operator-brief
- /next-action
- Run one real command in frontend.
- Save Action.
- Save Decision.

Expected frontend badge:
LOCKED FRONTEND V3 · V128 Backend
