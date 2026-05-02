Executive Engine OS V109 Full Package

BUILD V109 — RUN ENGINE BUTTON FIX

Problem:
V108 frontend showed the command box, but Run Engine did not work.

Fix:
- Run button now calls runV109Command()
- Reads the visible command textarea directly
- Syncs visible command into the original input
- Attempts existing sendMessage()
- Falls back to direct POST /run if sendMessage fails
- Shows inline run status
- Adds backend /run-button-diagnostics

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /run-button-diagnostics
   /frontend-stability
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Type in command box and click Run Engine.
