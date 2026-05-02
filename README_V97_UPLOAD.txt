Executive Engine OS V97 Full Package

BUILD V97 — RIGHT SIDEBAR DB POLISH + DUPLICATE CONTROL

Backend:
- /actions returns deduped rows
- /decisions returns deduped rows
- /save-action prevents duplicate open actions
- /save-decision prevents duplicate decisions
- /engine-state returns clean sidebar state

Frontend:
- Right sidebar rows are one-line and cleaner
- Pulls /engine-state when available
- Save buttons disable after successful save
- Refreshes backend memory after saves
- Duplicate display is reduced

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /engine-state
   /actions
   /decisions
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy

Still locked:
- No bots
- No automation
- Manual execution only
- No Figma yet
