Executive Engine OS V117 Full Package

BUILD V117 — BUTTON PERSISTENCE VERIFIER

Backend:
- /button-persistence-check
- /v117-smoke
- /frontend-button-map
- Keeps V116/V115 endpoints

Frontend:
- V117 output card
- Save buttons show stronger saved state
- Adds Check Persistence button
- Auto-checks persistence after save
- All old aliases map to V117

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /button-persistence-check
   /v117-smoke
   /frontend-button-map
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Run command, save actions, save decision, check persistence.
