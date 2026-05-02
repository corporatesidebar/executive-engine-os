Executive Engine OS V107 Full Package

BUILD V107 — FRONTEND REVIEW FIXES + DIAGNOSTICS

Backend:
- /frontend-diagnostics
- /v107-check
- Keeps all stable endpoints
- Version V107

Frontend:
- Frontend Diagnostics box
- More robust command area sizing
- Better mobile wrapping
- Confirms API constant
- No risky redesign

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /frontend-diagnostics
   /v107-check
   /engine-state
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh frontend.

Next:
Send screenshot before V108.
