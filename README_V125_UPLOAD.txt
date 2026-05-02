Executive Engine OS V125 Stability Audit Lock

Purpose:
- Keeps V123 save-flow fix.
- Adds backend stability audit.
- Adds backend run/save audit.
- Adds frontend Audit Save Flow button.
- Locks V125 as a stable baseline candidate.

Files:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/supabase_schema_v125.sql
- frontend/index.html
- frontend/robots.txt
- frontend/_headers
- README_V125_UPLOAD.txt

Deploy:
1. Upload V125 files to GitHub.
2. Supabase SQL is non-destructive; run supabase_schema_v125.sql only if needed.
3. Render backend -> Clear build cache & deploy.
4. Test:
   /health
   /v125-smoke
   /stability-audit
   /run-save-audit
   /version-lock
5. Render frontend -> Clear cache & deploy.
6. Hard refresh.
7. Test prompt:
   V125 final test — create one action called "Review V125 system tomorrow" and one decision called "Lock V125 as stable baseline."
8. Run Engine.
9. Click Add to Action Queue.
10. Click Save Decision.
11. Click Verify Save.
12. Click Audit Save Flow.
13. Check Persistence.

Rule:
Do not build V126 until V125 passes 10 real commands.
