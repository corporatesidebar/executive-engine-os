Executive Engine OS V115 Full Package

BUILD V115 — FRONTEND CONTRACT LOCK + SHIP READINESS

Backend:
- /frontend-contract
- /v115-smoke
- /ship-readiness
- Keeps /deploy-verifier and /run-validation

Frontend:
- Locks visible command box -> direct /run contract
- Inline output renderer
- Save Action / Save Decision / Refresh Right Panel / Validate Run
- Visible status and error messages
- Aliases all old run functions to V115

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /frontend-contract
   /v115-smoke
   /ship-readiness
   /run-validation
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Run V115 smoke test.
