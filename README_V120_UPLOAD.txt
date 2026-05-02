Executive Engine OS V120 Ship Lock

This is a clean reset + ship lock package. Delete old repo files and upload this structure exactly.

Files:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/supabase_schema_v120.sql
- frontend/index.html
- frontend/robots.txt
- frontend/_headers
- README_V120_UPLOAD.txt

Render Backend:
- Service: executive-engine-os
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

Backend Environment Variables:
- ALLOWED_ORIGINS=https://executive-engine-frontend.onrender.com
- OPENAI_API_KEY=your_key
- OPENAI_MODEL=gpt-4o-mini
- OPENAI_TIMEOUT_SECONDS=45
- OPENAI_MAX_TOKENS=2800
- SUPABASE_URL=your_supabase_url
- SUPABASE_SERVICE_KEY=your_service_role_key

Render Frontend:
- Service: executive-engine-frontend
- Root Directory: frontend
- Publish Directory: .
- Build Command: leave blank

Deploy order:
1. Run backend/supabase_schema_v120.sql in Supabase SQL Editor.
2. Deploy backend first with Clear build cache & deploy.
3. Test:
   https://executive-engine-os.onrender.com/health
   https://executive-engine-os.onrender.com/v120-smoke
   https://executive-engine-os.onrender.com/ship-lock
   https://executive-engine-os.onrender.com/frontend-version-check
   https://executive-engine-os.onrender.com/button-test-contract
   https://executive-engine-os.onrender.com/next-phase
4. Deploy frontend second with Clear cache & deploy.
5. Hard refresh: Ctrl + Shift + R.
6. Confirm visible badge: V120 · Ship Lock.
7. Run Engine.
8. Add to Action Queue.
9. Save Decision.
10. Check Persistence.
11. Stop building versions and run 10 real commands.

V120 rule:
Do not build V121 until V120 passes 10 real runs.
