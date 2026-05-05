EXECUTIVE ENGINE OS - V6000 FULL SYSTEM LINKED QA

Built from V5220.

DECISION:
Move to V6000 as a large-shot linked QA baseline.

BUILD TYPE:
Product Candidate / Full Frontend Link QA.

GOAL:
Make every primary frontend link/card/button work so the system can be tested in one large pass.

ADDED:
- /v6000-status
- /full-link-map
- /v6000-milestone
- QA Panel
- Full system admin link map
- All dashboard items open workspace pages
- All sidebar sections open workspace pages
- Workspace tabs switch
- Workspace Send button works
- Workspace Build Section Asset calls /run
- Back to Dashboard works
- System links open backend diagnostics

PRESERVED:
- V5220 real page navigation
- V5200 proactive follow-up engine contract routes
- Organization/project workspace model
- Client Asset Builder concept
- V3003 real revenue asset engine
- /run unchanged
- /test-report working
- Supabase schema unchanged
- OAuth inactive
- External writes blocked
- No external notifications sent
- Manual execution only
- Auto-loop off

DEPLOY:
1. Upload/replace ALL files from this ZIP.
2. Render Backend -> Manual Deploy -> Clear build cache & deploy.
3. Wait for backend Live.
4. Render Frontend -> Manual Deploy.
5. Browser hard refresh: Ctrl + Shift + R.

TEST:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/v6000-status
https://executive-engine-os.onrender.com/full-link-map
https://executive-engine-os.onrender.com/page-navigation-status
https://executive-engine-os.onrender.com/section-pages-status
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v6000-milestone

EXPECTED FRONTEND BADGE:
V6000 Full System Linked QA · V6000 Backend

Backend compile check:
PASS
