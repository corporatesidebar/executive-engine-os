Executive Engine OS V99 Full Package

BUILD V99 — LEARNING DASHBOARD

Backend:
- /learning
- /learning-events
- /operator-brief
- Summarizes runs, actions, decisions, memory, constraints, risks, decision patterns.

Frontend:
- Learning page now pulls /learning.
- Shows learning metrics and operator read.

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /learning
   /operator-brief
   /learning-events
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy

Still locked:
- No bots
- No automation
- No Figma yet
