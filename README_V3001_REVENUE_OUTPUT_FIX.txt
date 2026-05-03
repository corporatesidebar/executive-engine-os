EXECUTIVE ENGINE OS — V3001 REVENUE OUTPUT COMPATIBILITY FIX

Built from V3000.

PROBLEM:
V3000 routes were stable, but frontend revenue cards could show blank sections when /run returned older or partial JSON fields.

FIX:
- Added frontend output normalization.
- Added fallback mapping from older /run fields to V3000 revenue fields.
- Added useful default copy when fields are missing.
- Preserved V3000 revenue shell.

ADDED:
- GET /revenue-output-compatibility
- GET /v3001-milestone

PRESERVED:
- /health
- /run
- /test-report
- /test-report-json
- /revenue-shell-status
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
https://executive-engine-os.onrender.com/revenue-shell-status
https://executive-engine-os.onrender.com/revenue-output-compatibility
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v3001-milestone

Expected frontend badge:
V3001 Revenue Output Fix · V3001 Backend

Backend compile check:
PASS
