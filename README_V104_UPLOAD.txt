Executive Engine OS V104 Full Package

BUILD V104 — VISUAL POLISH ONLY

Backend:
- Version bump to V104
- Adds /visual-brief
- Keeps all V103 stable endpoints
- No backend logic changes

Frontend:
- Premium visual polish
- Better hero card
- Better command card
- Better workflow pills
- Better right-rail rows
- Styled scrollbars
- Adds Visual Polish status box
- No feature logic changes

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /visual-brief
   /layout-brief
   /engine-state
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh frontend.

Next:
V105 should focus on cleanup/bug fix after visual review.
