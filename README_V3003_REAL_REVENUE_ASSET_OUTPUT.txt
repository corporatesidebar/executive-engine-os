EXECUTIVE ENGINE OS — V3003 REAL REVENUE ASSET OUTPUT

Built from V3002.

BUILD TYPE:
Fix / Revenue Output Quality Build.

PROBLEM:
V3002 was stable and no longer blank, but /run still produced generic execution output instead of actual client-ready revenue assets.

FIX:
- Rewrites backend /run system prompt to force real revenue asset creation.
- Requires actual proposal draft.
- Requires actual pitch deck outline.
- Requires actual sales email draft.
- Requires actual follow-up sequence.
- Requires actual objection handling.
- Requires actual close plan.
- Blocks generic placeholder-style output.
- Updates frontend rendering for actual asset sections.

ADDED:
- GET /real-revenue-asset-status
- GET /revenue-asset-contract
- GET /v3003-milestone

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
- /diagnostic
- /system-test

SAFETY:
- Supabase schema unchanged
- OAuth inactive
- External writes blocked
- Manual execution only
- Auto-loop off

TEST:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/real-revenue-asset-status
https://executive-engine-os.onrender.com/revenue-asset-contract
https://executive-engine-os.onrender.com/revenue-shell-status
https://executive-engine-os.onrender.com/revenue-output-compatibility
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v3003-milestone

FRONTEND TEST COMMAND:
I need to pitch a $50k consulting package to a hesitant client. Build a client-ready proposal, pitch angle, sales email, follow-up sequence, objection handling, and close plan.

EXPECTED FRONTEND BADGE:
V3003 Real Revenue Asset Output · V3003 Backend

Backend compile check:
PASS
