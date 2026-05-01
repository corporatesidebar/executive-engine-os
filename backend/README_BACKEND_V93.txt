# Executive Engine OS V93

V93 = Frontend DB integration + V92 backend memory.

Backend:
- Keeps V92.2 clean backend structure.
- Version reports V93.
- Requires runtime.txt pinned to Python 3.12.8.

Frontend:
- Calls backend /health and shows Memory Status.
- Loads /recent-runs into Your Engine.
- Loads /actions into Action Queue.
- Loads /decisions into Recent Decisions.
- Add to Action Queue writes to /save-action when DB is live.
- Save Decision writes to /save-decision when DB is live.
- Profile saves to /profile when DB is live.
- Falls back to localStorage if backend/Supabase is offline.

Render backend settings:
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

Deploy:
1. Upload /backend and /frontend files.
2. Commit to main.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Test /health.
