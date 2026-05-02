EXECUTIVE ENGINE OS — V140 MEMORY + INTELLIGENCE MILESTONE

Purpose:
- Fast-track milestone from V135 to V140.
- Keeps the locked Command Center and Figma-inspired subpages.
- Adds memory intelligence endpoints and a stronger Memory page.
- No Supabase schema changes.

New backend endpoints:
- GET /memory-intelligence
- GET /decision-patterns
- GET /context-brief
- GET /v140-milestone

Frontend changes:
- Memory page upgraded to Memory Intelligence
- Detected Patterns pulled from backend
- Active Constraints pulled from backend
- Decision Patterns pulled from backend
- Next Memory Move shown

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /v140-milestone
- /memory-intelligence
- /decision-patterns
- /context-brief
- Open Memory page
- Run Engine
- Save Action
- Save Decision

Expected frontend badge:
V140 Memory Intelligence · V140 Backend
