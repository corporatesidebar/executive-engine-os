EXECUTIVE ENGINE OS — V200 BETA CANDIDATE

This build includes V195 and V200.

V195 included:
- Connector UI/roadmap foundation
- GET /connector-plan
- GET /connector-readiness
- GET /v195-milestone

V200 included:
- Internal beta candidate readiness
- Beta test protocol
- Product baseline
- Release plan toward V205/V210/V250
- GET /beta-candidate
- GET /beta-test-plan
- GET /v200-milestone

Frontend:
- Badge: V200 Beta Candidate · V200 Backend
- Settings page includes V195 Connector Plan
- Settings page includes V200 Beta Candidate
- Shows connector priorities, beta blockers, and beta test protocol

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /v195-milestone
- /v200-milestone
- /connector-plan
- /connector-readiness
- /beta-candidate
- /beta-test-plan
- Open Settings page
- Confirm Connector Plan appears
- Confirm Beta Candidate appears
- Run Engine
- Save Action
- Save Decision

Expected frontend badge:
V200 Beta Candidate · V200 Backend
