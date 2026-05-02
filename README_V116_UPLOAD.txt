Executive Engine OS V116 Full Package

BUILD V116 — OUTPUT BUTTONS FIX

Problem:
The output card appeared, but Add to Action Queue, Save Decision, and Validate Run did not reliably work.

Fix:
- All output buttons now have inline onclick handlers.
- Added document-level event delegation.
- Added direct global functions:
  - saveV116Actions()
  - saveV116Decision()
  - validateV116Run()
  - refreshV116Rail()
  - runV116Command()
- All older aliases point to V116.
- Visible success/error messages appear below command box.

Deploy:
1. Backend first:
   Render -> executive-engine-os -> Clear build cache & deploy
2. Test:
   /health
   /button-action-contract
   /v116-smoke
   /run-validation
3. Frontend second:
   Render -> executive-engine-frontend -> Clear cache & deploy
4. Hard refresh.
5. Run output and test all buttons.
