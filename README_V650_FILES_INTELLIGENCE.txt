EXECUTIVE ENGINE OS — V650 FILES INTELLIGENCE + NOTIFICATION UPGRADE

Built from V600 Calendar Intelligence.

Rules followed:
- Kept V600 stable baseline.
- Did not remove diagnostic routes.
- Did not touch Supabase schema.
- Did not change deployment structure.
- Did not add autonomous automation.
- Did not add real Google Drive OAuth.
- Did not add token storage.
- Did not fetch live Google Drive files.
- Manual execution only.
- Auto-loop off.

V650 adds:
- Files Intelligence panel
- Files status contract
- Files prep summary
- Manual file/project context summary
- Decision-needed extraction from manual context
- Action-needed extraction from manual context
- Send file context to Run Command
- Send file context to Daily Brief
- Send file context to End Day Summary
- Files alerts
- Notification Center upgrade

Backend routes added:
- GET /files/status
- GET /files/prep-summary
- POST /files/context-to-command
- GET /files/alerts
- GET /notification-upgrade
- GET /v650-milestone

Preserved:
- /diagnostic
- /system-test
- /calendar/status
- /calendar/events/today
- /calendar/events/upcoming
- /calendar/day-load
- /calendar/alerts
- /integrations/status
- /integrations/safety-check
- /integrations/context-preview
- /executive-cockpit
- /notifications
- /daily-workflow
- /end-day-summary
- /health

Not added:
- Real Google Drive OAuth
- Google token storage
- Live Drive file fetch
- File write access
- File parsing pipeline
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
- /files/status
- /files/prep-summary
- /files/alerts
- /notification-upgrade
- /v650-milestone
- /health

Expected frontend badge:
V650 Files Intelligence · V650 Backend

Backend compile check:
PASS
