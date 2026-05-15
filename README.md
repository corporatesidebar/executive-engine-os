# Executive Engine OS — V35140 Frontend Chat Rendering Fix

## Version
V35140 — Frontend Layout Restore / Chat Workflow Rendering Patch

## Deployment type
Frontend only.

## Backend URL preserved
https://executive-engine-os.onrender.com

## What was fixed
- User commands now render as compact right-side message bubbles.
- Assistant responses now render as compact left-side structured response cards.
- `/run` response fields render inside the assistant card in the required order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. READY ASSETS
  5. RISK
  6. PRIORITY
  7. RECOMMENDED COMMAND
- Response spacing was tightened to reduce vertical height.
- Conversation history remains readable above the pinned follow-up input.
- Follow-up input remains at the bottom of the workflow panel.

## What was not changed
- Backend was not changed.
- Supabase was not changed.
- Database was not changed.
- Provider routing was not changed.
- API URL was not changed.
- `/run` contract was not changed.
- Sidebar, header, Executive Summary column, Executive Intelligence column, and overall layout were preserved.

## Files included
- `frontend/index.html`
- `README.md`
- `test-checklist.md`
