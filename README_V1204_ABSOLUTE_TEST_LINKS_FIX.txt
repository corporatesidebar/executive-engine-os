EXECUTIVE ENGINE OS — V1204 ABSOLUTE TEST LINKS FIX

Problem:
The frontend static test page showed route labels like /health. If opened from the frontend static domain, those routes can fail because backend routes live on:
https://executive-engine-os.onrender.com

Fix:
- /test-links now shows full backend URLs.
- Static test pages also show full backend URLs.
- Each link has a Copy button.
- Frontend badge updates to V1204.
- Backend milestone: /v1204-milestone.

Upload instructions:
1. Download this ZIP.
2. Upload/replace ALL files in GitHub.
3. Render Backend -> Manual Deploy -> Clear build cache & deploy.
4. Wait until backend says Live.
5. Render Frontend -> Manual Deploy.
6. Browser hard refresh: Ctrl + Shift + R.

First tests:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/diagnostic
https://executive-engine-os.onrender.com/system-test
https://executive-engine-os.onrender.com/test-links
https://executive-engine-os.onrender.com/v1204-milestone

Expected frontend badge:
V1204 Absolute Test Links · V1204 Backend

Backend compile check:
PASS
