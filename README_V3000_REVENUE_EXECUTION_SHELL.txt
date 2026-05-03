EXECUTIVE ENGINE OS — V3000 REVENUE EXECUTION SHELL

Built from V2075.

BUILD TYPE:
Revenue / Product Build.

GOAL:
Transform the frontend into a revenue-first executive command center.

PRODUCT PROMISE:
Make money. Save time. Feel in control.

Rules followed:
- Kept V2075 Build Command Center hidden/admin.
- Kept V2050 Build Factory.
- Kept /test-report working.
- Did not remove diagnostic routes.
- Did not delete legacy routes.
- Did not touch Supabase schema.
- Did not activate OAuth.
- Did not add external writes.
- Kept /run working.
- Kept manual execution only.
- Kept auto-loop off.

Backend routes added:
- GET /revenue-shell-status
- GET /revenue-command-templates
- GET /executive-scoreboard
- GET /client-asset-workflows
- GET /v3000-milestone

Frontend added:
- Revenue-first executive dashboard
- "What are you trying to win today?" headline
- Build Proposal quick action
- Build Pitch Deck quick action
- Build Sales Email quick action
- Build Follow-Up quick action
- Build Close Plan quick action
- Make Decision quick action
- Reduce Work quick action
- Executive Scoreboard
- Today’s Wins
- Revenue output cards
- Follow-up command copy
- Build Factory hidden under System/Admin

Preserved:
- /build-factory-status
- /build-command-center-status
- /build-command-template
- /build-protocol
- /product-candidate-v2000
- /memory-action-intelligence
- /test-report
- /test-report-json
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
https://executive-engine-os.onrender.com/revenue-shell-status
https://executive-engine-os.onrender.com/revenue-command-templates
https://executive-engine-os.onrender.com/executive-scoreboard
https://executive-engine-os.onrender.com/client-asset-workflows
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v3000-milestone

Expected frontend badge:
V3000 Revenue Execution Shell · V3000 Backend

Backend compile check:
PASS
