EXECUTIVE ENGINE OS — V1850 CORE OS QUALITY UPGRADE

Built from V1800.

Rules followed:
- Kept /test-report working.
- Did not remove diagnostic routes.
- Did not touch Supabase schema.
- Did not activate OAuth.
- Did not add external writes.
- Kept manual execution only.
- Kept auto-loop off.
- Preserved V1800 integration prep.

V1850 improves:
- Stronger /run system prompt.
- Better core output contract.
- Adds What to Cut.
- Adds Current Constraint.
- Adds Next Decision.
- Adds Execution Score.
- Adds Recommended Command discipline.
- Makes frontend output executive-readable with cards.
- Reduces raw JSON feel.
- Adds Core Quality page.
- Adds Execution Loop page.
- Keeps Calendar/OAuth parked.

Backend routes added:
- GET /core-quality-status
- GET /core-output-contract
- GET /execution-loop
- GET /core-command-templates
- GET /v1850-milestone

Preserved:
- /test-report
- /test-report-json
- /integration-prep-status
- /calendar/readiness-dashboard
- /product-candidate-status
- /product-dashboard
- /workflow-dashboard
- /intelligence-board
- /operator-console
- /health
- /diagnostic
- /system-test
- /run

Deploy:
1. Upload/replace ALL files from this ZIP.
2. Render Backend -> Manual Deploy -> Clear build cache & deploy.
3. Wait for Live.
4. Render Frontend -> Manual Deploy.
5. Browser hard refresh: Ctrl + Shift + R.

Test:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/core-quality-status
https://executive-engine-os.onrender.com/core-output-contract
https://executive-engine-os.onrender.com/execution-loop
https://executive-engine-os.onrender.com/core-command-templates
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v1850-milestone

Expected frontend badge:
V1850 Core OS Quality · V1850 Backend

Backend compile check:
PASS
