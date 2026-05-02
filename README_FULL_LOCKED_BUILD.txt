EXECUTIVE ENGINE OS — FULL LOCKED BUILD

This is the clean full upload package:
- Backend: V125 stable backend
- Frontend: LOCKED FRONTEND V2 visual layout
- Supabase: keep existing V125 schema unless you intentionally want to rerun it
- Target badge in frontend: LOCKED FRONTEND V2 · V125 Backend

IMPORTANT:
This package is for a full GitHub repo clean upload.

DO THIS EXACTLY:

1. GitHub
   - Open repo: executive-engine-os
   - Delete ALL existing files and folders
   - Upload everything from this ZIP
   - Commit changes

2. Supabase
   - DO NOT change Supabase if V125 is already working.
   - If you wiped/reset Supabase, run backend/supabase_schema_v125.sql.

3. Render Backend
   - Service: executive-engine-os
   - Root Directory: backend
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   - Manual Deploy -> Clear build cache & deploy

4. Test Backend
   - https://executive-engine-os.onrender.com/health
   - https://executive-engine-os.onrender.com/stability-audit
   - https://executive-engine-os.onrender.com/engine-state

5. Render Frontend
   - Service: executive-engine-frontend
   - Root Directory: frontend
   - Publish Directory: .
   - Build Command: blank
   - Manual Deploy -> Clear cache & deploy

6. Browser
   - Open frontend
   - Hard refresh: Ctrl + Shift + R
   - Confirm badge: LOCKED FRONTEND V2 · V125 Backend

7. Smoke Test
   - Type: Give me the next move for Executive Engine OS.
   - Click Run Engine
   - Confirm right preview updates
   - Click Add to Action Queue
   - Click Save Decision
   - Click Verify Save
   - Click Audit Save Flow
   - Click Check Persistence
