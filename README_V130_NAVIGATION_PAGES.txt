EXECUTIVE ENGINE OS — V130 NAVIGATION + PAGES MILESTONE

Purpose:
- Fast-track milestone from V128 to V130.
- Keeps locked design direction.
- Adds clickable navigation/pages.
- No Supabase schema change.
- Backend includes V128 operator loop plus V130 page endpoints.

New frontend pages:
- Command Center
- Daily Brief
- Decisions
- Meeting Prep
- Strategy Board
- Risk Monitor
- Action Queue
- Analytics
- Memory
- Profile
- Settings

New backend:
- GET /pages
- GET /v130-milestone

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /v130-milestone
- /pages
- /workflow-audit
- /operator-brief
- Click each left nav page.
- Run Engine.
- Save Action.
- Save Decision.

Expected frontend badge:
V130 Navigation · V128 Operator Loop
