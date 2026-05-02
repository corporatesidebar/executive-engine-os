Executive Engine OS V121 Explicit Save Fix

Bug fixed:
- The buttons worked, but when the prompt asked for an exact action/decision name, the save buttons stored the AI-generated output instead of the explicit requested text.
- V121 parses prompts like:
  create one action called "Review V121 system tomorrow"
  and one decision called "Lock V121 as stable baseline"

Files:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/supabase_schema_v121.sql
- frontend/index.html
- frontend/robots.txt
- frontend/_headers
- README_V121_UPLOAD.txt

Deploy:
1. Upload V121 files to GitHub.
2. Run backend/supabase_schema_v121.sql in Supabase if needed. It is non-destructive.
3. Deploy backend with Clear build cache & deploy.
4. Test:
   /health
   /v121-smoke
   /save-verification
5. Deploy frontend with Clear cache & deploy.
6. Hard refresh.
7. Test exact command:
   V121 final test — create one action called "Review V121 system tomorrow" and one decision called "Lock V121 as stable baseline."
8. Run Engine.
9. Click Add to Action Queue.
10. Click Save Decision.
11. Click Verify Latest Save.
