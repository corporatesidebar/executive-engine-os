EXECUTIVE ENGINE OS — V240 SYSTEM TEST FIX + STABILITY HARDENING

This build includes V235 and V240.

V235 included:
- Fixes /system-test Internal Server Error
- Replaces fragile test logic with hardened no-crash diagnostics
- GET /v235-milestone

V240 included:
- Stability hardening
- /system-test always returns JSON PASS/FAIL cards
- Optional module failures no longer crash system test
- GET /v240-milestone

Backend:
- Version updated to V240
- GET /system-test
- GET /v235-milestone
- GET /v240-milestone

Frontend:
- Badge: V240 System Stable · V240 Backend
- Settings System Test note added
- Run Full System Test uses fixed /system-test endpoint

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /system-test
- /v235-milestone
- /v240-milestone
- Open Settings page
- Click Run Full System Test
- Run Engine
- Save Action
- Save Decision

Expected frontend badge:
V240 System Stable · V240 Backend

Compile check:
PASS
