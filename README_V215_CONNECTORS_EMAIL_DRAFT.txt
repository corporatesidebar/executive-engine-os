EXECUTIVE ENGINE OS — V215 CONNECTORS + EMAIL DRAFT

This build includes V210 and V215.

V210 included:
- Calendar + Files connector preparation
- Read-only-first connector policy
- GET /connector-prep
- GET /calendar-files-readiness
- GET /v210-milestone

V215 included:
- Email draft-only layer
- Sample follow-up draft generation
- Send remains disabled
- GET /email-draft-mode
- GET /draft-follow-up
- GET /v215-milestone

Frontend:
- Badge: V215 Email Draft · V215 Backend
- Settings page includes V210 Connector Preparation
- Settings page includes V215 Email Draft Layer
- Shows draft capabilities and blocked actions
- No external send/automation enabled

Deploy:
1. Upload all ZIP contents to GitHub.
2. Do NOT touch Supabase.
3. Render backend -> Clear build cache & deploy.
4. Render frontend -> Clear cache & deploy.
5. Hard refresh -> Ctrl + Shift + R.

Test:
- /health
- /system-test
- /v210-milestone
- /v215-milestone
- /connector-prep
- /calendar-files-readiness
- /email-draft-mode
- /draft-follow-up
- Open Settings page
- Confirm Connector Preparation appears
- Confirm Email Draft Layer appears
- Confirm send remains disabled

Expected frontend badge:
V215 Email Draft · V215 Backend
