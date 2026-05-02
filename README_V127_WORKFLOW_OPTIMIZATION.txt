EXECUTIVE ENGINE OS — V127 WORKFLOW OPTIMIZATION

Purpose:
- No redesign.
- Keep locked frontend layout.
- Upgrade backend intelligence/workflow behavior.
- Add V127 execution helpers:
  - strict JSON cleaning
  - action quality filter
  - mode-specific prompting
  - manual execution loop object
  - stronger executive system prompt

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
1. GitHub: upload all files from this ZIP.
2. Supabase: DO NOT touch unless you reset the DB.
3. Render backend: Clear build cache & deploy.
4. Render frontend: Clear cache & deploy.
5. Hard refresh: Ctrl + Shift + R.

Test:
- /health should show V127 if version replacement appears in backend response.
- /stability-audit should still pass.
- Run a real command.
- Confirm output is sharper, more specific, and actions are executable.

Frontend badge:
LOCKED FRONTEND V3 · V127 Backend
