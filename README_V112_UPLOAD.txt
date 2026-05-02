Executive Engine OS V112 Full Package

BUILD V112 — RUN VALIDATION + UI RECOVERY

Backend:
- /run-validation
- /frontend-recovery
- Keeps all V111 stable endpoints

Frontend:
- Stronger visible output renderer
- Direct /run execution
- Direct save action / save decision buttons
- Visible run status and error box
- Right panel refresh after run/save
- Does not depend on old hidden chat renderer

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /run-validation
   /frontend-recovery
   /run-execution-check
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Type command and click Run Engine.
