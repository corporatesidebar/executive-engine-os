EXECUTIVE ENGINE OS - V9100 SMART INTAKE ROUTER

Built from V9000.

FIX:
Long messy input now routes to the correct workspace.
The house renovation/rental input routes to Investment, not Assets.
Asset Library is for generated documents only.

PRESERVED:
- /run unchanged
- /test-report working
- localStorage persistence
- Supabase schema unchanged
- OAuth inactive
- external writes blocked
- manual execution only

DEPLOY:
1. Upload/replace ALL files.
2. Render Backend -> Clear build cache & deploy.
3. Render Frontend -> Manual Deploy.
4. Hard refresh.
5. Click Reset once if old V9000 browser data is confusing.

TEST:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/v9100-status
https://executive-engine-os.onrender.com/smart-intake-status
https://executive-engine-os.onrender.com/workflow-os-status
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v9100-milestone

Expected frontend badge:
V9100 Smart Intake Router · V9100 Backend

Backend compile check:
PASS
