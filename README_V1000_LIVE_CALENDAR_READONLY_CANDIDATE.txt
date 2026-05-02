EXECUTIVE ENGINE OS — V1000 LIVE CALENDAR READ-ONLY OAUTH CANDIDATE

Built from V950 Token Storage + Disconnect Flow Candidate.

Rules followed:
- Kept V950 stable baseline.
- Did not remove diagnostic routes.
- Did not touch Supabase schema.
- Did not change deployment structure.
- Did not add autonomous automation.
- Added live Calendar OAuth route layer candidate.
- Did not enable live token exchange.
- Did not add real encrypted token storage.
- Did not create Supabase token table.
- Did not fetch live Google Calendar events using OAuth token.
- Did not add calendar writes.
- Manual execution only.
- Auto-loop off.

V1000 adds:
- Calendar Connect Status
- Calendar Auth URL route
- Calendar OAuth Callback route
- Calendar Live Candidate Status
- Calendar Today Live Candidate
- Calendar Context Approval
- Calendar OAuth Test Page
- Calendar OAuth Candidate UI

Backend routes added:
- GET /calendar/connect-status
- GET /calendar/auth-url
- GET /calendar/oauth/callback
- GET /calendar/status-live-candidate
- GET /calendar/events/today-live-candidate
- POST /calendar/context-approval
- GET /calendar/oauth-test-page
- GET /v1000-milestone

Preserved:
- /diagnostic
- /system-test
- /tokens/storage-plan
- /tokens/encryption-check
- /calendar/disconnect-flow
- /calendar/refresh-policy
- /calendar/connection-state-candidate
- /calendar/oauth-candidate/status
- /calendar/auth-url-candidate
- /calendar/token-storage-plan
- /calendar/readiness-report
- /google/connector-blueprint
- /oauth/activation-prep
- /security-gates
- /calendar/status
- /calendar/events/today
- /files/status
- /integrations/status
- /executive-cockpit
- /notifications
- /daily-workflow
- /end-day-summary
- /health

Not added:
- Live token exchange
- Real encrypted token storage
- Supabase token table migration
- Live Calendar fetch using stored OAuth token
- Calendar writes
- Background sync
- Automation loop

Deploy:
1. Upload all ZIP contents to GitHub.
2. Render backend -> Clear build cache & deploy.
3. Restart backend once deploy is live.
4. Deploy frontend.
5. Hard refresh.

Test:
- /diagnostic
- /system-test
- /calendar/connect-status
- /calendar/auth-url
- /calendar/status-live-candidate
- /calendar/events/today-live-candidate
- /calendar/oauth-test-page
- /v1000-milestone
- /health

Expected frontend badge:
V1000 Calendar OAuth · V1000 Backend

Backend compile check:
PASS

Recommended next build:
V1050 Real Token Exchange + Encrypted Storage Candidate
