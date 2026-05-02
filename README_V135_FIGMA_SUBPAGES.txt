EXECUTIVE ENGINE OS — V135 UNIQUE FIGMA SUBPAGES + WORKFLOW CONTROL

Purpose:
- Fast-track milestone from V130 to V135.
- Keeps the locked Command Center.
- Replaces generic V130 placeholder pages with Figma-inspired unique subpages.
- Keeps backend/Supabase stable.
- Adds V135 milestone endpoint.

New/Improved Pages:
- Daily Brief: priority initiatives, metrics, recent activity
- Decisions: decision log, impact, status, priority
- Meeting Prep: meetings, agendas, prep actions
- Strategy Board: objectives, OKRs, progress bars, KPI cards
- Risk Monitor: risk severity, impact, owner, mitigation plan
- Action Queue: critical/in-progress/completed lanes
- Analytics: revenue trend, team growth, decision velocity
- Memory: detected patterns, active context, recent recalls
- Profile: executive profile, preferences
- Settings: general, notifications, appearance, integrations

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /v135-milestone
- /pages
- /workflow-audit
- Click every sidebar page.
- Confirm unique page layouts.
- Run Engine.
- Save Action.
- Save Decision.

Expected frontend badge:
V135 Figma Subpages · V135 Backend
