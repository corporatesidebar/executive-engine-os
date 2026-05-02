Executive Engine OS V110 Full Package

BUILD V110 — FRONTEND LIVE STATUS HARDENING

Backend:
- /frontend-live-status
- /v110-check
- Keeps /run-button-diagnostics
- Keeps all stable endpoints

Frontend:
- Backend Live Status box
- V110 Run Engine runner
- Backward-compatible V109 runner alias
- Improved backend state visibility
- No risky redesign

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /frontend-live-status
   /v110-check
   /run-button-diagnostics
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Type one command and click Run Engine.
