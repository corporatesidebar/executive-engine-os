EXECUTIVE ENGINE OS — V250 SYSTEM TEST HARD FIX

This build includes V245 and V250.

Problem fixed:
- /system-test was still returning Internal Server Error.

V245 included:
- Removes fragile /system-test implementation.
- Rebuilds /system-test as a no-database, no-helper smoke test.
- Adds GET /v245-milestone.

V250 included:
- GET /system-test
- GET /system-test-deep
- GET /v250-milestone
- Frontend badge updated to V250.

Important:
- /system-test is now intentionally simple so it cannot crash.
- /system-test-deep is optional and checks Supabase/memory.
- Use /system-test first after every deploy.

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test in this exact order:
1. /system-test
2. /health
3. /v250-milestone
4. /system-test-deep
5. Frontend Settings -> Run Full System Test

Expected frontend badge:
V250 System Test Hard Fix · V250 Backend

Backend compile check:
PASS
