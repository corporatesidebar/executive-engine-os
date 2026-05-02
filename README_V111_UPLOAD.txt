Executive Engine OS V111 Full Package

BUILD V111 — RUN ENGINE FINAL FIX

Problem:
The visible command UI could still fail because the original app message flow and the simplified visible command box were not fully aligned.

Fix:
- Run Engine now posts directly to /run.
- Reads visible command box directly.
- Renders output inline under the command center.
- Saves latest output in window.__lastV111Output.
- Adds direct Add to Action Queue and Save Decision buttons.
- Refreshes right panel after run/save.
- Adds /run-execution-check backend endpoint.

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /run-execution-check
   /frontend-live-status
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Type command and click Run Engine.
