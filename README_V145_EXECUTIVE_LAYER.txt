EXECUTIVE ENGINE OS — V145 EXECUTIVE LAYER MILESTONE

Purpose:
- Fast-track milestone from V140 to V145.
- Keeps locked Command Center and V135 subpages.
- Adds executive/board-level operating layer.
- No Supabase schema changes.

New backend endpoints:
- GET /executive-brief
- GET /daily-brief
- GET /meeting-prep-brief
- GET /board-brief
- GET /executive-modes
- GET /v145-milestone

Frontend upgrades:
- Daily Brief pulls live executive brief
- Strategy Board includes board-level summary
- Profile includes CEO/COO/CMO/CTO/CFO modes
- Settings includes executive layer status
- Badge: V145 Executive Layer · V145 Backend

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /v145-milestone
- /executive-brief
- /daily-brief
- /meeting-prep-brief
- /board-brief
- /executive-modes
- Open Daily Brief, Strategy Board, Profile, Settings
- Run Engine and save action/decision

Expected frontend badge:
V145 Executive Layer · V145 Backend
