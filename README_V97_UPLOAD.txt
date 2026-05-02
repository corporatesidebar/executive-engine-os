Executive Engine OS V97 Full Package

BUILD V97 — Frontend Memory Polish + Engine State

Upload/replace:

Backend:
backend/main.py
backend/requirements.txt
backend/runtime.txt
backend/README_BACKEND_V97.txt

Frontend:
frontend/index.html
frontend/robots.txt
frontend/_headers

Deploy order:
1. Backend first: executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /engine-state
   /project-context
3. Frontend second: executive-engine-frontend -> Clear cache & deploy

Expected:
/health version: V97
/engine-state returns right-panel state
Supabase enabled: true

No bots. No automation. Manual execution only.
