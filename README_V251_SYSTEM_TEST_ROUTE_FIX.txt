EXECUTIVE ENGINE OS — V251 SYSTEM TEST ROUTE FIX

Answer:
README files do NOT affect the app runtime.
Deleting old README files did NOT break /system-test.

Actual issue:
FastAPI can keep an older duplicate /system-test route active if multiple routes exist.
This build removes duplicate /system-test routes and adds ONE simple guaranteed route.

Fix:
- Removed all previous /system-test route blocks.
- Removed old /v235, /v240, /v245, /v250 test milestone route blocks.
- Added one simple /system-test endpoint only.
- Added /system-test-deep for optional Supabase read diagnostics.
- Added /v251-milestone.
- Backend compile check: PASS

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh frontend.

Test first:
- /system-test

Then:
- /health
- /v251-milestone
- /system-test-deep

Expected frontend badge:
V251 System Test Route Fix · V251 Backend
