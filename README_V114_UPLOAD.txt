Executive Engine OS V114 Full Package

BUILD V114 — DEPLOY VERIFIER + FRONTEND SMOKE TEST

Backend:
- /deploy-verifier
- /frontend-smoke-test
- /v114-check
- Keeps /run-validation and all stable endpoints

Frontend:
- V114 verified direct run path
- Inline output renderer
- Save Action / Save Decision / Refresh Right Panel
- Validate Run button
- Visible smoke-test-ready status
- Keeps aliases for older run functions

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /deploy-verifier
   /frontend-smoke-test
   /v114-check
   /run-validation
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Run smoke test.
