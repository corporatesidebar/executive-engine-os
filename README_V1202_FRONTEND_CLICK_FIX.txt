EXECUTIVE ENGINE OS — V1202 FRONTEND CLICK FIX

Problem:
- Frontend loaded but showed old V1200 badge.
- Sidebar/buttons/test links were not clickable.
- The old frontend had too much accumulated JS and broken handlers.

Fix:
- Replaced frontend/index.html with a clean stable clickable shell.
- Added direct backend test links in the frontend.
- Added backend GET /v1202-milestone.
- Kept backend routes preserved.
- Kept manual execution only.
- Kept auto-loop off.

Important:
Upload the full V1202 ZIP contents. Do not mix old frontend files with this hotfix.

Deploy:
1. Upload all files from this ZIP to GitHub.
2. Backend -> Manual Deploy -> Clear build cache & deploy.
3. Wait for backend live.
4. Frontend -> Manual Deploy.
5. Hard refresh browser with Ctrl+Shift+R.

Expected frontend badge:
V1202 Frontend Click Fix · V1202 Backend

Test first:
- /health
- /diagnostic
- /system-test
- /v1202-milestone

Backend compile check:
PASS
