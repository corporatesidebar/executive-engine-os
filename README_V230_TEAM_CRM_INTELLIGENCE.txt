EXECUTIVE ENGINE OS — V230 TEAM + CRM INTELLIGENCE

This build includes V225 and V230.

V225 included:
- Team / Chat Pulse
- Draft-only leadership/team message
- Blocker detection from saved actions
- Post remains disabled
- GET /team-pulse
- GET /team-message-draft
- GET /v225-milestone

V230 included:
- CRM / Revenue Intelligence readiness
- Revenue signals from actions/decisions
- Read-only CRM/revenue capability planning
- External CRM writes remain disabled
- GET /crm-intelligence
- GET /revenue-brief
- GET /v230-milestone

Frontend:
- Badge: V230 Revenue Intelligence · V230 Backend
- Settings page includes V225 Team / Chat Pulse
- Settings page includes V230 CRM / Revenue Intelligence
- Shows draft-only message and read-only revenue intelligence
- External posting/writes remain disabled

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /system-test
- /v225-milestone
- /v230-milestone
- /team-pulse
- /team-message-draft
- /crm-intelligence
- /revenue-brief
- Open Settings page
- Confirm Team Pulse appears
- Confirm Revenue Intelligence appears
- Confirm post/write actions remain disabled

Expected frontend badge:
V230 Revenue Intelligence · V230 Backend
