# Executive Engine OS — Frontend Runtime Test Checklist

## Deployment Type

Frontend only.

## Do Not Touch

- Backend
- API URL
- /run contract
- Supabase
- DB schema
- Provider routing

## Test Steps

1. Deploy `frontend/index.html` to the frontend service.
2. Open https://executive-engine-frontend.onrender.com/
3. Confirm approved layout is preserved:
   - Dark left sidebar
   - White main workspace
   - Three-column structure
   - Main workflow/chat area
   - Executive Summary column
   - Executive Intelligence right panel
   - Orange Execute button
4. Type a command into the main input.
5. Press Enter.
6. Confirm the user command appears as a right-side message bubble.
7. Confirm loading state appears as an assistant-side bubble.
8. Confirm Network tab shows POST to:
   - https://executive-engine-os.onrender.com/run
9. Confirm assistant response appears as a left-side structured message bubble.
10. Confirm response renders in this exact order:
   - NEXT MOVE
   - DECISION
   - ACTION STEPS
   - READY ASSETS
   - RISK
   - PRIORITY
   - RECOMMENDED COMMAND
11. Type a follow-up command.
12. Confirm follow-up appears in the same conversation thread.
13. Confirm Executive Summary updates from latest response.
14. Confirm Executive Intelligence updates from latest response/context.
15. Click sidebar sections:
   - Today Command
   - Decisions
   - Action Workspace
   - Ready Assets
   - Risk Monitor
   - Context
16. Confirm each sidebar section shows real state-derived content, not static filler.
17. Disable backend or block request temporarily.
18. Confirm visible error state appears.

## Expected Result

PASS if the frontend behaves like real software, posts to the locked backend, displays real runtime state, and preserves the approved layout.
