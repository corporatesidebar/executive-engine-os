Executive Engine OS V126 — Executive Cockpit UI

Frontend design/layout upgrade only.
Backend remains V125.
No Supabase schema change.
No backend logic change.

Included:
backend/
  main.py
  requirements.txt
  runtime.txt
  supabase_schema_v125.sql

frontend/
  index.html
  robots.txt
  _headers

README_V126_UPLOAD.txt

Deploy:
1. Upload all files to GitHub.
2. Backend can stay V125. Deploy backend only if you want a clean full upload.
3. Deploy frontend:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh:
   Ctrl + Shift + R

Frontend must show:
V126 UI · V125 Backend

Test:
Run Engine
Add to Action Queue
Save Decision
Verify Save
Audit Save Flow
Check Persistence
