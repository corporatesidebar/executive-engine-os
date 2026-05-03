EXECUTIVE ENGINE OS — V1207 TEST REPORT RUNTIME FIX

Problem:
- /health works as V1206.
- /v1206-milestone works.
- /test-report returns Internal Server Error.

Fix:
- Renames previous broken /test-report route.
- Rebuilds /test-report using local Starlette HTMLResponse import inside the route.
- Keeps Run Report.
- Keeps Copy All Results.
- Keeps one clean copy/paste report with headers.

Upload:
1. Upload/replace ALL files from this ZIP.
2. Render Backend -> Manual Deploy -> Clear build cache & deploy.
3. Wait for Live.
4. Render Frontend -> Manual Deploy.
5. Ctrl + Shift + R.

Test:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/test-report-json
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v1207-milestone

Expected frontend badge:
V1207 Test Report Runtime Fix · V1207 Backend

Backend compile check:
PASS
