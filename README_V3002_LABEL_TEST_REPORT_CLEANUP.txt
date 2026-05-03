EXECUTIVE ENGINE OS - V3002 LABEL + TEST REPORT CLEANUP

Built from V3001.

BUILD TYPE:
Stability / Label Cleanup Build.

PURPOSE:
V3001 backend was stable, but the test report still showed V3000-visible labels and route lists.
V3002 cleans the current test report, labels, and milestone references so testing is easier and less confusing.

FIXES:
- Keeps V3001 output compatibility fix.
- Rebuilds /test-report-json to show V3002 current routes.
- Adds /revenue-output-compatibility to the report.
- Adds /v3001-milestone to the report.
- Adds /v3002-milestone to the report.
- Updates visible backend labels to V3002 where appropriate.
- Preserves V3000 milestone as /legacy/v3000-milestone.
- Adds README details and PDF documentation.

DO NOT TOUCH RULES FOLLOWED:
- Did not touch Supabase schema.
- Did not activate OAuth.
- Did not add external writes.
- Did not change /run.
- Kept manual execution only.
- Kept auto-loop off.
- Preserved diagnostic routes.
- Preserved legacy routes.

ADDED:
- GET /label-cleanup-status
- GET /v3002-milestone
- PDF: V3002_Label_Test_Report_Cleanup_Details.pdf

PRESERVED:
- /health
- /run
- /test-report
- /test-report-json
- /revenue-shell-status
- /revenue-output-compatibility
- /revenue-command-templates
- /executive-scoreboard
- /client-asset-workflows
- /build-factory-status
- /v3001-milestone
- /diagnostic
- /system-test

DEPLOY:
1. Upload/replace ALL files from this ZIP.
2. Render Backend -> Manual Deploy -> Clear build cache & deploy.
3. Wait for backend Live.
4. Render Frontend -> Manual Deploy.
5. Browser hard refresh: Ctrl + Shift + R.

TEST:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/revenue-shell-status
https://executive-engine-os.onrender.com/revenue-output-compatibility
https://executive-engine-os.onrender.com/label-cleanup-status
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/test-report-json
https://executive-engine-os.onrender.com/v3001-milestone
https://executive-engine-os.onrender.com/v3002-milestone

EXPECTED FRONTEND BADGE:
V3002 Label + Test Report Cleanup · V3002 Backend

PDF render check:
PASS

Backend compile check:
PASS
