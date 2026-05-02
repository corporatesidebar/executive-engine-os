Executive Engine OS V127 — High-Level Hybrid UI

Purpose:
- Frontend UI polish based on the approved hybrid direction.
- Orange / blue / black / white / grey palette.
- Keeps the backwards EE logo.
- More stylish command input/header.
- Better section separation.
- Backend remains V125.
- No Supabase schema change.
- No backend logic change.

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

README_V127_UPLOAD.txt

Deploy:
1. Upload all files to GitHub.
2. Do NOT change Supabase.
3. Backend can stay V125.
4. Deploy frontend:
   Render -> executive-engine-frontend -> Clear cache & deploy
5. Hard refresh:
   Ctrl + Shift + R

Frontend must show:
V127 UI · V125 Backend

Test:
Run Engine
Add to Action Queue
Save Decision
Verify Save
Audit Save Flow
Check Persistence
