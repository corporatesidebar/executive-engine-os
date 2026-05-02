Executive Engine OS V98 Full Package

BUILD V98 — PROFILE-AWARE OUTPUT

Backend:
- Saved profile is injected into /run.
- Default founder/operator profile is used when no profile exists.
- New /profile-status endpoint.
- Keeps V97 duplicate control.
- Keeps /engine-state.

Frontend:
- Shows profile-aware status in right panel.
- Refreshes profile status from backend.
- Keeps right-sidebar DB polish.

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /profile-status
   /project-context
   /engine-state
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy

Still locked:
- No bots
- No automation
- No Figma yet
