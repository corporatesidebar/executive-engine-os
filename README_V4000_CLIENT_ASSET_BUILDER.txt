EXECUTIVE ENGINE OS - V4000 CLIENT ASSET BUILDER

Built from V3710.

DECISION:
Go big: promote Executive Flow into a usable asset-building workflow.

BUILD TYPE:
Product Feature / Asset Builder.

GOAL:
Turn push-based flow items into client-ready assets executives can use in meetings, proposals, deals, follow-ups, and people conversations.

ADDED:
- Client Asset Builder section
- Asset type selector
- Asset detail inputs
- Build Asset button using /run
- Copy Asset button
- Meeting Brief asset
- Proposal Draft asset
- Pitch Deck Outline asset
- Sales Email asset
- Follow-Up Sequence asset
- Objection Handling asset
- Close Plan asset
- People Script asset
- /client-asset-builder-status
- /asset-builder-contract
- /v4000-milestone

PRESERVED:
- V3710 clickable Executive Flow
- V3003 real revenue asset engine
- /run unchanged
- /test-report working
- /test-report-json working
- /executive-flow-status
- /task-capture-model
- /push-dashboard-check
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
https://executive-engine-os.onrender.com/client-asset-builder-status
https://executive-engine-os.onrender.com/asset-builder-contract
https://executive-engine-os.onrender.com/executive-flow-status
https://executive-engine-os.onrender.com/real-revenue-asset-status
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v4000-milestone

EXPECTED FRONTEND BADGE:
V4000 Client Asset Builder · V4000 Backend

Backend compile check:
PASS
