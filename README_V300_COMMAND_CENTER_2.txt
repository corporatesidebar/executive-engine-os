EXECUTIVE ENGINE OS — V300 COMMAND CENTER 2.0

Built from stable V290 baseline.

Rules followed:
- Kept V290 diagnostic/test routes.
- Did not change deployment structure.
- Did not touch Supabase schema.
- Kept manual execution only.
- Kept auto-loop off.
- Included all files in ZIP.

V300 adds:
- Executive Command Center 2.0
- Command templates:
  Daily Brief
  Meeting Prep
  Strategy Decision
  Risk Review
  Revenue Review
  Hiring Decision
  Board Prep
  Execution Reset
- Executive modes:
  CEO
  COO
  CMO
  CTO
  CFO
- Stronger backend system prompt
- Sharper operator-level output requirements
- next_recommended_command support
- Backend routes:
  GET /command-templates
  GET /executive-modes-v300
  GET /next-command
  GET /v300-milestone

Existing V290 routes preserved:
- /diagnostic
- /system-test
- /runtime-proof
- /deployment-fingerprint
- /render-config-check
- /test-links-json
- /stable-baseline

Deploy:
1. Upload all ZIP contents to GitHub.
2. Render backend -> Clear build cache & deploy.
3. Restart backend once deploy is live.
4. Test /diagnostic.
5. Test /system-test.
6. Deploy frontend.
7. Hard refresh.

Test:
- /diagnostic
- /system-test
- /command-templates
- /executive-modes-v300
- /next-command
- /v300-milestone
- /health

Expected frontend badge:
V300 Command Center 2.0 · V300 Backend

Backend compile check:
PASS
