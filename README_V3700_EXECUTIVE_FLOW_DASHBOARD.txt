EXECUTIVE ENGINE OS - V3700 EXECUTIVE FLOW DASHBOARD

Built from V3600/V3550.

PRODUCT THESIS:
The AI box is not the product. The prepared executive day is the product.

BUILD TYPE:
Product Direction / Frontend UX Pivot.

GOAL:
Move Executive Engine from a command-first AI dashboard to a push-first Executive Flow dashboard.

CORE CHANGE:
- Input is small and thin at the top.
- Dashboard pushes Today and Tomorrow.
- Meetings, deals, people, risks, decisions, and prepared assets are the main experience.
- Users add light context; the system structures and prepares the day.

ADDED:
- Push-first Today dashboard
- Tomorrow preview
- Meetings section
- Revenue / Deals section
- Decisions section
- People section
- Risks / Constraints section
- Prepared For You section
- End-of-day capture
- Universal WHO/WHAT/WHEN/WHERE/WHY/HOW capture model
- Detail/prep panel
- Prepare Assets button using /run
- Executive Flow product vision PDF
- GET /executive-flow-status
- GET /task-capture-model
- GET /push-dashboard-check
- GET /v3700-milestone

PRESERVED:
- V3003 real revenue asset engine
- /run unchanged
- /test-report working
- /test-report-json working
- /real-revenue-asset-status
- /revenue-asset-contract
- Supabase schema unchanged
- OAuth inactive
- External writes blocked
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
https://executive-engine-os.onrender.com/executive-flow-status
https://executive-engine-os.onrender.com/task-capture-model
https://executive-engine-os.onrender.com/push-dashboard-check
https://executive-engine-os.onrender.com/real-revenue-asset-status
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v3700-milestone

EXPECTED FRONTEND BADGE:
V3700 Executive Flow Dashboard · V3700 Backend

PDF render check:
PASS

Backend compile check:
PASS
