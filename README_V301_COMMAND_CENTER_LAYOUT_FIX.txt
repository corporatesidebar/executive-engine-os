EXECUTIVE ENGINE OS — V301 COMMAND CENTER LAYOUT FIX

This is a hotfix for the V300 frontend layout.

Problem:
- V300 templates pushed the command input down.
- Page looked broken and oversized.
- Context label still showed old V128 wording.
- Command Center flow was not immediate enough.

Fixes:
- Command input visible immediately.
- Executive modes moved into compact toolbar.
- Command templates collapsed behind a button.
- Template drawer opens only when needed.
- Context label updated to V301 Executive.
- Right rail remains readable.
- V300 backend routes and V290 diagnostics preserved.

Backend:
- Version updated to V301.
- GET /v301-milestone added.
- V300 routes preserved:
  /command-templates
  /executive-modes-v300
  /next-command
  /v300-milestone

Deploy:
1. Upload all ZIP contents to GitHub.
2. Render backend -> Clear build cache & deploy.
3. Restart backend once deploy is live.
4. Deploy frontend.
5. Hard refresh.

Test:
- /diagnostic
- /system-test
- /v301-milestone
- /command-templates
- /health

Expected frontend badge:
V301 Layout Fix · V301 Backend

Backend compile check:
PASS
