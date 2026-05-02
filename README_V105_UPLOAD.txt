Executive Engine OS V105 Full Package

BUILD V105 — CLEANUP / BUGFIX

Backend:
- /frontend-config
- /cleanup-check
- Keeps all stable endpoints
- Version V105
- No major backend logic changes

Frontend:
- Cleanup status box
- More robust startup
- Better mobile command layout
- Correct API constant
- Better disabled/saving button state
- No feature logic changes

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /frontend-config
   /cleanup-check
   /engine-state
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh frontend.

Next:
V106 should only happen after checking frontend screenshots/logs.
